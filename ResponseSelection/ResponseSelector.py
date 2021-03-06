import json
import requests
import urllib
import datetime
from Preprocessing import config
from Preprocessing import DataPreprocessing
from Data import Database, DataAccess

class ResponseSelector:

    @staticmethod
    def requestUserName(req, action):
        originalRequest = req.get("originalRequest")
        data = originalRequest.get("data")
        sender = data.get("sender")
        id = sender.get("id")
        access_token = config.access_token
        rs = urllib.urlopen(config.graph_api_url + id + "?fields=first_name&access_token=" + access_token)
        name = json.load(rs).get("first_name")
        print(name)
        event_name = ""
        if ("welcome" in action):
            event_name = "FACEBOOK_WELCOME"
            ResponseSelector().registerUser(id)
        elif ("help" in action):
            event_name = "help_name_event"
        return {
            "speech": "",
            "displayText": "",
            "data": {},
            "contextOut": [],
            "source": "webhook-ResponseSelector-requestUserName",
            "followupEvent": {"name": event_name, "data": {"user": name}}
        }

    def registerUser(self, pageScopedID):
        db = Database.Database()
        appScopedID = self.getAppScopedID(pageScopedID)
        db.insert("User", ["Page_ScopedID", "App_ScopedID"], [pageScopedID, appScopedID], ["Page_ScopedID", "App_ScopedID"], "")

    def getAppScopedID(self, pageScopedID):
        first_name, last_name = self.getName(pageScopedID)

        # Get conversations, then get the sender with the required name, then get the appScopedID and return it.
        conversations = self.getConversations()
        print conversations
        for conversation in conversations:
            participants = conversation.get("participants").get("data")
            for participant in participants:
                if participant.get("name").startswith(first_name) and participant.get("name").endswith(last_name):
                    return participant.get("id")

    def getName(self, pageScopedID):
        access_token = config.access_token
        url = config.graph_api_url + str(pageScopedID) + "?access_token=" + access_token + "&fields=first_name,last_name"
        r = requests.get(url)
        print(r.status_code, r.reason)
        result = json.loads(r.text)
        name = result.get("first_name") + " " + result.get("last_name")
        print(name)
        return result.get("first_name"), result.get("last_name")

    def getUsersToNotify(self):
        ids = []
        conversations = self.getConversations()
        for conversation in conversations:
            updated_time = conversation.get("updated_time")
            updated_time = updated_time.replace("T", " ")  # Replace separator of date and time by " " instead of T -- To match current_time format
            millisecondsIndex = updated_time.find("+")  # Get milliseconds index
            updated_time = updated_time[:millisecondsIndex - len(updated_time)]  # Remove milliseconds
            updated_time = datetime.datetime.strptime(updated_time, "%Y-%m-%d %H:%M:%S")  # Convert to datetime object
            current_time = datetime.datetime.now() + datetime.timedelta(hours=2)  # Convert to GMT (now + (-2)H)
            resultedTime = current_time - updated_time  # Didn't talk since...
            dayIndex = str(resultedTime).find("day")  # Get day index in result, -1 if not exist
            if dayIndex > 0 and int(str(resultedTime)[:dayIndex-1]) >= 2:  # If day exists and number of days more than 2 ,, then notify user.
                conversationData = conversation.get("participants").get("data")
                for participant in conversationData:
                    if participant.get("id") != config.page_id:  # Current participant isn't the page
                        appScopedID = participant.get("id")
                        pageScopedID = DataAccess.DataAccess().select("User", ["Page_ScopedID"], ["App_ScopedID"], [appScopedID], "")
                        if pageScopedID != []:
                            print conversation.get("participants").get("data")[0].get("name")
                            ids.append(pageScopedID[0][0])
                            break
        return ids

    def getConversations(self):
        access_token = config.access_token
        url = config.graph_api_url + "me/conversations?access_token=" + access_token + "&fields=participants,updated_time"

        r = requests.get(url)
        print(r.status_code, r.reason)
        conversations = json.loads(r.text)
        return conversations.get("data")

    def notifyUser(self):
        listOfUsersToNotify = self.getUsersToNotify()

        access_token = config.access_token
        url = config.graph_api_url + "me/messages?access_token=" + access_token

        for userID in listOfUsersToNotify:
            paramRecipient = { "id": userID}
            content = DataAccess.DataAccess().selectRandom("Notification", ["Message", "Attachment", "Type"], [], [], "")
            msg = DataPreprocessing.DataPreprocessing().addSinqleQuotes(content[0][0])
            attachment = content[0][1]
            if(attachment != None): #If there's an attachment, send it before the message itself
                if content[0][2] == "GIF":
                    attachedGif = DataAccess.DataAccess().selectRandom("Gifs", ["Url"], ["Gif_Tag"], ["'" + attachment + "'"], "")
                    requestJSON = {'recipient': '{"id": ' + str(userID) + '}',
                                   "message": '{ "attachment": { "type":"image", "payload":{ "url":' + '"' + attachedGif[0][0] + '"' + ' } } }'
                                   }
                    r = requests.post(url, data=requestJSON, headers={'Content-type': 'application/json'})
                    print(r.status_code, r.reason)
                    print(r.text[:300] + '...')
                elif content[0][2] == "Button":
                    requestJSON = { "recipient": '{ "id": ' + str(userID) + ' }',
           "message": '{ "attachment": { "type":"template", "payload":{ "template_type":"button", "text":' + '"' + msg + '"' + ', "buttons":[ { "type":"postback", "title":"' + attachment + '"' + ', "payload":"' + attachment + '"' + ' }]}}}'
    }
                    r = requests.post(url, data=requestJSON, headers={'Content-type': 'application/json'})
                    print(r.status_code, r.reason)
                    print(r.text[:300] + '...')
            if attachment == None or content[0][2] == "GIF": #If no attachment or there were a GIF then send the message, if button then the message was already sent
                paramMessage = {"text": msg}
                requestJSON = {}
                requestJSON["recipient"] = json.dumps(paramRecipient, ensure_ascii=False)
                requestJSON["message"] = json.dumps(paramMessage, ensure_ascii=False)

                r = requests.post(url, data = requestJSON, headers={'Content-type': 'application/json'})
                print(r.status_code, r.reason)
                print(r.text[:300] + '...')

    def about(self):
        page_id = config.page_id
        access_token = config.access_token
        url = config.graph_api_url + page_id + "?access_token=" + access_token + "&fields=about"
        r = requests.get(url)
        print(r.status_code, r.reason)
        result = json.loads(r.text)
        about = result.get("about")
        print(about)
        return {
            "speech": about,
            "displayText": "",
            "data": {},
            "contextOut": [],
            "source": "webhook-ResponseSelector-about"
        }

    def webSearch(self, query):
        url = "https://www.googleapis.com/customsearch/v1?key=" \
              + config.api_key + "&cx=" + config.engine_id + "&q=" + query
        response = requests.get(url)
        jData = response.json()
        results = jData.get("items")
        if not results:
            print("JSON: ", 0)
            return {
                "speech": "",
                "displayText": "",
                "data": {},
                "contextOut": [],
                "source": "webhook-ResponseSelector-webSearch",
                "followupEvent": {"name": "fallback"}
            }
        first = results[0]
        second = results[1]
        third = results[2]
        fourth = results[3]
        return {
            "speech": "",
            "displayText": "",
            "data": {
                "facebook": [
                    {
                        "text":"Here are the top results from the web"
                    },
                    {
                        "attachment": {
                            "type": "template",
                            "payload": {
                                "template_type": "list",
                                "top_element_style": "compact",
                                "elements": [
                                    {
                                        "title": first.get("title"),
                                        "subtitle": first.get("snippet"),
                                        "default_action": {
                                            "type": "web_url",
                                            "url": first.get("link")
                                        },
                                        "buttons": [
                                            {
                                                "title": "View",
                                                "type": "web_url",
                                                "url": first.get("link")
                                            }
                                        ]
                                    },
                                    {
                                        "title": second.get("title"),
                                        "subtitle": second.get("snippet"),
                                        "default_action": {
                                            "type": "web_url",
                                            "url": second.get("link")
                                        },
                                        "buttons": [
                                            {
                                                "title": "View",
                                                "type": "web_url",
                                                "url": second.get("link")
                                            }
                                        ]
                                    },
                                    {
                                        "title": third.get("title"),
                                        "subtitle": third.get("snippet"),
                                        "default_action": {
                                            "type": "web_url",
                                            "url": third.get("link")
                                        },
                                        "buttons": [
                                            {
                                                "title": "View",
                                                "type": "web_url",
                                                "url": third.get("link")
                                            }
                                        ]
                                    },
                                    {
                                        "title": fourth.get("title"),
                                        "subtitle": fourth.get("snippet"),
                                        "default_action": {
                                            "type": "web_url",
                                            "url": fourth.get("link")
                                        },
                                        "buttons": [
                                            {
                                                "title": "View",
                                                "type": "web_url",
                                                "url": fourth.get("link")
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                ]
            },
            "contextOut": [],
            "source": "webhook-FeatureOneSelector-webSearch"
        }

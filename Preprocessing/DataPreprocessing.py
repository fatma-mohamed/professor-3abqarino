from Data.Database import Database
from Data.DataAccess import DataAccess
from NLP.TextParser import TextParser
from NLP.WordRecognizer import WordRecognizer


class DataPreprocessing:
    def __run__(self):
        d = Database()
        d.__deleteTables__()
        d.__createTables__()
        self.insertAnswers_and_keywords()
        self.insertQuestions_Answers()
        self.insertGifs()
        self.insertNotifications()
        print("Data preprocessing done!")

    @staticmethod
    def insertAnswers_and_keywords():
        db = Database()
        db_access = DataAccess()
        parser = TextParser()
        recognizer = WordRecognizer()
        file = open("Preprocessing/essay_questions.txt", "r")

        while True:
            line = file.readline()
            if (line == ''):
                print("no question!")
                break
            question = DataPreprocessing.removeSinqleQuotes(line.strip('-'))
            line = file.readline()
            if (line == ''):
                print("no answer!")
                break
            answer = DataPreprocessing.removeSinqleQuotes(line.strip('\n'))
            cols = ["answer"]
            values = ["'" + answer + "'"]
            db.insert("Answers", cols, values, "", "")

            cols = ["id"]
            parameters = ["answer"]
            values = ["'" + answer + "'"]
            answer_id = db_access.select("Answers", cols, parameters, values, "")

            tokens = parser.tokenize(question)
            keywords = parser.removeStopWords(tokens)
            keywords_id = []
            for k in keywords:

                cols = ["id"]
                parameters = ["keyword"]
                values = ["'" + k + "'"]
                keyword_id = db_access.select("Keywords", cols, parameters, values, "")
                if len(keyword_id) == 0:
                    cols = ["keyword"]
                    values = ["'" + k + "'"]
                    conflict_fields = ["keyword"]
                    db.insert("Keywords", cols, values, conflict_fields, "")

                    cols = ["id"]
                    parameters = ["keyword"]
                    values = ["'" + k + "'"]
                    id = db_access.select("Keywords", cols, parameters, values, "")
                    keywords_id.append(id[0][0])
                    synonyms = recognizer.getSynonym(k)
                    for s in synonyms:
                        cols = ["key_id", "synonym"]
                        values = [str(id[0][0]) + ", '" + s + "'"]
                        db.insert("Synonyms", cols, values, "", "")
                else:
                    keywords_id.append(keyword_id[0][0])
            for i in keywords_id:
                cols = ["answer_id", "keyword_id"]
                values = [str(answer_id[0][0]) + "," + str(i)]
                conflict_fields = ["answer_id", "keyword_id"]
                db.insert("Answers_Keywords", cols, values, conflict_fields, "")
        print ("Inserted Answers_Keywords rows")

    def insertQuestions_Answers(self):
        db = Database()
        f = open("Preprocessing/Question_Answers.txt", 'r')
        i = 0
        while True:
            Question = Question = DataPreprocessing.removeSinqleQuotes(f.readline().rstrip())
            if Question == "":
                print("------Finished reading------")
                break
            A1 = DataPreprocessing.removeSinqleQuotes(f.readline().rstrip())
            A2 = DataPreprocessing.removeSinqleQuotes(f.readline().rstrip())
            A3 = DataPreprocessing.removeSinqleQuotes(f.readline().rstrip())
            CA_ID = f.readline().rstrip()
            cols = ["Question", "Answer_1", "Answer_2", "Answer_3", "Correct_AnswerID"]
            values = ["'" + Question + "'", "'" + A1 + "'", "'" + A2 + "'", "'" + A3 + "'", "'" + str(CA_ID) + "'"]
            conflict_fields = ["Question", "Answer_1", "Answer_2", "Answer_3", "Correct_AnswerID"]
            i += 1
            print ("-----Row " + (str)(i) + " -----")
            db.insert("Questions_Answers", cols, values, conflict_fields, '')
        print ("Inserted Questions_Answers rows")

    @staticmethod
    def insertGifs():
        db = Database()
        file = open("Preprocessing/gifs.txt", "r")

        while True:
            line = file.readline()
            if (line == ''):
                print("EOF!")
                break
            arr = line.split(" ")
            name = "'" + arr[0].strip("\n") + "'"
            url = "'" + arr[1].strip("\n") + "'"
            tag = "'" + arr[2].strip("\n") + "'"
            db.insert("Tag", ["tag"], [tag], ["tag"], "")
            db.insert("Gifs", ["name", "url", "gif_tag"], [name, url, tag], "", "")
        print ("Inserted Tags & Gifs")

    @staticmethod
    def insertNotifications():
        db = Database()
        db_access = DataAccess()
        f = open("Preprocessing/Notifications.txt", 'r')
        i = 0
        while True:
            Notification = DataPreprocessing.removeSinqleQuotes(f.readline().rstrip())
            if Notification == "":
                print("------Finished reading------")
                break

            cols = []
            values = []
            noAttachment = True
            if "Attachment" in Notification:
                content = Notification.split(" Attachment: ")
                Notification = content[0]
                content = content[1].split("-")
                if content[1] == "GIF":
                    rows = db_access.select("Tag", ["Tag"], ["Tag"], ["'" + content[0] + "'"], "")
                    row = rows[0][0]
                    if row is not None:  # Check the existence of the tag used as an attachment.
                        cols = ["Message", "Attachment", "Type"]
                        values = ["'" + Notification + "'", "'" + content[0] + "'", "'GIF'"]
                        noAttachment = False
                elif content[1] == "Button":
                    cols = ["Message", "Attachment", "Type"]
                    values = ["'" + Notification + "'", "'" + content[0] + "'", "'Button'"]
                    noAttachment = False
            if noAttachment == True:
                cols = ["Message"]
                values = ["'" + Notification + "'"]
            conflict_fields = ["Message"]
            i += 1
            print ("-----Notification number :: " + (str)(i) + " -----")
            db.insert("Notification", cols, values, conflict_fields, "")
        print ("Inserted Notification messages")

    @staticmethod
    def removeSinqleQuotes(s):
        res = s.replace("'", '"')
        return res

    @staticmethod
    def addSinqleQuotes(s):
        res = s.replace('"', "'")
        return res

from ResponseSelection.ResponseSelector import ResponseSelector
from Data import DataAccess
from Preprocessing import DataPreprocessing
from random import randint

class FeatureTwoSelector:
    
    def getRandomQuestion(self,answerFeedback = "", imageURL = ""):
        rows = DataAccess.DataAccess().selectRandom("Questions_Answers",
                                                   ["Question", "Answer_1", "Answer_2", "Answer_3", "Correct_AnswerID"],
                                                   [], [], "")

        row = rows[0]
        if imageURL == "":
            return {
                "speech": "",
                "displayText": "",
                "data": {},
                "contextOut": [],
                "source": "webhook-FeatureTwoSelector-get-random-question",
                "followupEvent": {
                    "name": "Question_Answers",
                    "data": {
                       "Question": DataPreprocessing.DataPreprocessing().addSinqleQuotes(row[0]),
                       "A1": DataPreprocessing.DataPreprocessing().addSinqleQuotes(row[1]),
                       "A2": DataPreprocessing.DataPreprocessing().addSinqleQuotes(row[2]),
                       "A3": DataPreprocessing.DataPreprocessing().addSinqleQuotes(row[3]),
                        "CA_ID": row[4],
                        "AnswerFeedback": answerFeedback
                        }
                    }
                }
        else:
            return {
                "speech": "",
                "displayText": "",
                "data": {},
                "contextOut": [],
                "source": "webhook-FeatureTwoSelector-get-random-question",
                "followupEvent": {
                    "name": "Question_Answers",
                    "data": {
                       "Question": DataPreprocessing.DataPreprocessing().addSinqleQuotes(row[0]),
                       "A1": DataPreprocessing.DataPreprocessing().addSinqleQuotes(row[1]),
                       "A2": DataPreprocessing.DataPreprocessing().addSinqleQuotes(row[2]),
                       "A3": DataPreprocessing.DataPreprocessing().addSinqleQuotes(row[3]),
                        "CA_ID": row[4],
                        "AnswerFeedback": answerFeedback,
                        "imageURL": imageURL
                        }
                    }
                }
        
    def CheckAnswerCorrectness(self,request):
        correctAnswer= request.get("correctAnswerID")
        chosenAnswer= str(request.get("chosenAnswer"))
        randomNum = randint(0,19)
        if correctAnswer == chosenAnswer:
            if randomNum < 10:
                return self.getRandomQuestion(answerFeedback="Correct Answer :)")
            else:
                d = DataAccess.DataAccess()
                url = d.selectRandom("Gifs" , ["url"] , ["gif_tag"] , ["'correct'"], "")
                url = url[0][0]
                return self.getRandomQuestion(answerFeedback="Correct Answer :)", imageURL=url)
        elif correctAnswer != chosenAnswer:
            return

    def getCorrectAnswer(self, request):
        question = request.get("sentQuestion")
        CA_ID = request.get("CA_ID")
        print "-------Sent Question :: ", question
        print "---------CA_ID :: ", CA_ID
        CA_ID = CA_ID[:CA_ID.find(".") - len(CA_ID)] #Remove .0 ,, CA_ID = 1.0 or 2.0 or 3.0
        row = DataAccess.DataAccess().select("Questions_Answers", ["Answer_" + CA_ID], ["Question"], ["'" + question + "'"], '')
        answer = row[0][0]
        return {
            "speech": "",
            "displayText": "",
            "data": {},
            "contextOut": [],
            "source": "webhook-FeatureTwoSelector-get-correct-answer",
            "followupEvent": {
                "name": "Cant_Answer",
                "data": {
                    "Answer": answer
                }
            }
        }


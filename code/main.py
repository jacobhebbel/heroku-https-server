from bot import SocialMediaChatbot



"""
Program Structure:
1. someone @s my bot
2. my bot reads their message
3. my bot adds it to its userPrompt input
4. my bot makes the api call to gpt, gets a response
5. my bot responds with the text from gpt
"""

def getClient():
    pass


def main():

    socialMediaClient = getClient()
    myBot = SocialMediaChatbot()

    while True:

        if socialMediaClient.getsNotification():
            notification = socialMediaClient.getMostRecentNotification()
            user = notification.userId
            message = notification.message

            response = myBot.sendMessage(message, user)

            socialMediaClient.postResponse(response.text)



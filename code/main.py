from bot import SocialMediaChatbot
import random
import time


def main():

    bot = SocialMediaChatbot()
    bot.authenticate()

    timeSpentRespondingToMentions = 10000       # in seconds
    requestDelay = 60
    subjectPool = ['sports', 'the weather', 'lightbulb manufacturing practices', 'the internet', 'fun facts']
    randomSubject = random.choice(subjectPool)
    
    bot.postTweetFromSubjectPool(chosenSubject=randomSubject)
    bot.respondToMentionsViaPolling(duration=timeSpentRespondingToMentions, interval=requestDelay)

if __name__ == '__main__':
    main()
        


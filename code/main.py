from bot import SocialMediaChatbot
import random
import time


def main():

    bot = SocialMediaChatbot()
    timeSpentRespondingToMentions = 10000       # in seconds
    requestDelay = 60
    subjectPool = ['sports', 'the weather', 'lightbulb manufacturing practices', 'the internet', 'fun facts']
    
    while True:
        
        print('starting loop')
        randomSubject = random.choice(subjectPool)
        #bot.respondToMentionsViaPolling(duration=timeSpentRespondingToMentions, interval=requestDelay)
        bot.postTweetFromSubjectPool(chosenSubject=randomSubject)
        time.sleep(100)

if __name__ == '__main__':
    main()
        


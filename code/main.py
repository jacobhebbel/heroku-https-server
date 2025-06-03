from bot import SocialMediaChatbot
import random


def main():

    bot = SocialMediaChatbot()
    timeSpentRespondingToMentions = 10000       # in seconds
    subjectPool = ['sports', 'the weather', 'lightbulb manufacturing practices', 'the internet', 'fun facts']
    
    while True:
        
        randomSubject = random.choice(subjectPool)

        bot.respondToMentions(duration=timeSpentRespondingToMentions)
        bot.postTweetFromSubjectPool(chosenSubject=randomSubject)

if __name__ == '__main__':
    main()
        


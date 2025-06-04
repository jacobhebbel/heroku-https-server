import os
from openai import OpenAI
import tweepy
import time
import queue
from dotenv import load_dotenv

load_dotenv(override=True)

'''
userID: [chats between user and bot as dictionaries]
element of .get(userID):
{
    message: text,
    fromUser: bool,
    isReply: bool,
    replyId: text
}

'''

class SocialMediaChatbot:

    def __init__(self):
        self.model = ModelInterface()
        self.twitter = TwitterInterface()
        self.stream = StreamInterface()
        self.userHistories = {}             # maps a user id to their message history with the bot
        self.mostRecentMentionId = None

        print('testing env variables')
        print('bearer:\t' + str(os.getenv('TWITTER_BEARER_TOKEN')))
        print('access token:\t' + str(os.getenv('TWITTER_ACCESS_TOKEN')))
        print('access secret:\t' + str(os.getenv('TWITTER_ACCESS_SECRET')))
        print('consumer key:\t' + str(os.getenv('TWITTER_CONSUMER_KEY')))
        print('consumer secret:\t' + str(os.getenv('TWITTER_CONSUMER_SECRET')))

    def __str__(self):
        s = 'Beep Boop, I\'m a bot!\nI send messages to twitter with the help of OpenAI'
        s += f'\nI am using openAI\'s {self.model.modelType} to respond to queries'
        return s

    def respondToMentionsViaStream(self, duration=100):

        # 1. start the stream
        # 2. if a tweet is found then fetch it
        # 3. give tweet to model
        # 4. respond to the tweet

        self.stream.startStream()
        startTime = time.time()
        mentionsQueue = self.stream.mentionsQueue
        while self.stream.isRunning() and time.time() - startTime < duration:
            
            try:
                mention = mentionsQueue.get(timeout=1)
                user = mention.author_id
                message = mention.text
                messageId = mention.id

                self.saveMention(mention)
                self.printMention(mention)
                response = self.model.writeMentionResponse(userMessage=message, userId=user)
                self.twitter.respondToMention(messageId, response)

            except queue.Empty:
                continue
                
        self.stream.endStream()

    def respondToMentionsViaPolling(self, duration=10000, interval=900):
        print('starting polling process. sleeping for 15 mins then pulling data')
        startTime = time.time()

        while time.time() - startTime < duration:
            
            time.sleep(interval)
            unseenMentions = self.twitter.getNewMentions(sinceId=self.mostRecentMentionId)
            print(f'got {len(unseenMentions)} mentions from twitter api call')

            for mention in unseenMentions:
                self.processMention(mention)
        
        print('stopping polling for mentions')
    
    def processMention(self, mention):
        user = mention.author_id
        message = mention.text
        messageId = mention.id
        userChatHistory = self.getUserHistory(user)
        
        modelResponse = self.model.writeMentionResponse(message, userChatHistory)
        tweet = self.twitter.respondToMention(messageId, modelResponse.output_text)

        self.saveMention(mention, tweet)
        self.printInteraction(mention, tweet)
        self.updateMostRecentMention(messageId)
    
    def postTweetFromSubjectPool(self, chosenSubject):
        tweet = self.model.writeRandomTweet(f'{chosenSubject}')
        self.twitter.postTweet(tweet)

    def getUserHistory(self, userID):
        history = self.userHistories.get(userID) if userID in self.userHistories.keys() else []
        return history[-5:]

    def saveMention(self, mention, reply):

        userID = mention.author_id
        if userID not in self.userHistories.keys():
            self.userHistories.update({f'{userID}': []})
        
        # adds an entry for the user's mention and an entry for the model's response
        self.userHistories.get(userID).extend([
            {'message': str(mention.text), 'messageID': str(mention.id), 'fromUser': False, 'isReply': False, 'replyID': ''},
            {'message': str(reply.text), 'messageID': str(reply.id), 'fromUser': True, 'isReply': True, 'replyID': ''}
        ])

    def printInteraction(self, mention, reply):

        s = f'''\n
        from {mention.author_id}:\n
        \n
        \t@jacob's_twitter_bot\n
        \t{mention.text}\n\n
        message id={mention.id}\n
        \n\n
        from jacob's_twitter_bot:\n
        \t@user\n
        \t{reply.text}\n\n
        message id={reply.id}\n
        ------------------------- END OF MESSAGE -------------------------
        '''
        print(s)

    def updateMostRecentMention(self, id):
        self.mostRecentMentionId = id


class ModelInterface:

    def __init__(self):
        self.key = str(os.getenv('OPENAI_API_KEY'))
        self.client = OpenAI()

        self.modelInput = []
        self.modelType = 'gpt-3.5-turbo-0125'

    def writeMentionResponse(self, message, history):
        self.clearPromptHistory()
        self.injectUserChatHistory(history)
        prompt = message
        self.addUserPrompt(prompt)
        response = self.getModelResponse()
        print(response.output_text)
        return response
    
    def writeRandomTweet(self, subject):
        self.clearPromptHistory()
        prompt = 'Write a short twitter post about this subject:\n' + f'{subject}'
        self.addUserPrompt(prompt)
        response = self.getModelResponse()
        print(response.output_text)
        return response

    def getModelResponse(self):
        print(self.modelInput)
        return self.client.responses.create(
            model=self.modelType,                               # sets the model type to use
            input=self.modelInput                               # gives model instructions, user history, and user prompt
        )

    def injectUserChatHistory(self, history):
        for chat in history:
            if chat.fromUser:
                self.addUserPrompt(chat)
            else:
                self.addAssistantPrompt(chat)

    def clearPromptHistory(self):
        self.modelInput = [{'role': 'system', 'content': 'You are a dignified and playful twitter account that interacts with users via mentions and makes random tweets'}]

    def validatePrompt(self, prompt):
        if not prompt or not isinstance(prompt, str):
            raise Exception(f'Systme prompt provided to Model Interface is null or not type string: \nprompt: {prompt}\nprompt type: {type(prompt)}')

    def setSystemPrompt(self, prompt):
        self.validatePrompt(self, prompt)
        for entry in self.modelInput:
            if isinstance(entry, dict) and 'system' in entry.keys():
                self.modelInput.remove(entry)
        self.modelInput.append({'role': 'system', 'content': str(prompt)})
        
    def addAssistantPrompt(self, prompt):
        self.validatePrompt(self, prompt)
        self.modelInput.append({'role': 'assistant', 'content': str(prompt)})

    def addUserPrompt(self, prompt):
        self.validatePrompt(prompt)
        self.modelInput.append({'role': 'user', 'content': str(prompt)})

    def setModel(self, modelType):
        if modelType is None or not isinstance(modelType, str):
            raise Exception(f'provided model type is not acceptable:\nmodel={modelType}\n model type={type(modelType)}')

        self.modelType = modelType


class StreamClient(tweepy.StreamingClient):
    
    def __init__(self, bearer_token, mentionsQueue):
        super().__init__(bearer_token)
        self.mentionsQueue = mentionsQueue

    def on_connect(self):
        print('stream is connected')
    
    def on_disconnect(self):
        print('stream is closed')

    def on_tweet(self, tweet):
        self.saveMention(tweet)
        self.printMention(tweet)
        self.mentionsQueue.put(tweet)

    def on_error(self, error):
        raise Exception(f'error occurred during streaming: {error}')


class StreamInterface:

    def __init__(self):
        self.mentionsQueue = queue.Queue()
        self.client = StreamClient(bearer_token=str(os.getenv('TWITTER_BEARER_TOKEN')),
                                   mentionsQueue=self.mentionsQueue)
        
        self.defaultRule = tweepy.StreamRule(value='(@jacob\'s_twitter_bot OR to:jacob\'s_twitter_bot) -is:retweet ',
                                             tag='gets all mentions of this bot (excluding retweets)')
        self.rules = [self.defaultRule]

    def startStream(self):
        self.client.add_rules(self.rules)
        self.client.filter()

    def addStreamRule(self, rule):
        if isinstance(rule, tweepy.StreamRule):
            self.rules.append(rule)
        else:
            raise Exception(f'rule must be type tweepyStreamRule, was type {type(rule)}')
    
    def clearStreamRules(self):
        self.client.delete_rules(self.rules)
        self.rules = [self.defaultRule]

    def isRunning(self):
        return self.client.running
    
    def endStream(self):
        self.client.disconnect()


class TwitterInterface:
    # this interface uses v2 of twitter (X) api

    def __init__(self):
        self.client = self.getClient()
        self.id = self.client.get_me().data.id

    def getClient(self):
        return tweepy.Client(
            bearer_token=str(os.getenv("TWITTER_BEARER_TOKEN")),
            consumer_key=str(os.getenv('TWITTER_CONSUMER_KEY')),
            consumer_secret=str(os.getenv('TWITTER_CONSUMER_SECRET')),
            access_token=str(os.getenv('TWITTER_ACCESS_TOKEN')),
            access_token_secret=str(os.getenv('TWITTER_ACCESS_SECRET'))
        )
    
    def getNewMentions(self, sinceID=None):
        return self.client.get_users_mentions(
            id=self.id,
            since_id=sinceID
        ).data or []
    
    def postTweet(self, message):

        try:
            response = self.client.create_tweet(text=str(message))
            tweetID = response.data['id']
            return self.client.get_tweet(tweetID)
        
        except tweepy.errors.Forbidden as e:
            print("403 Forbidden:", e.response.text)
            raise
    
    def respondToMention(self, userID, reply):
        response = self.client.create_tweet(text=str(reply), in_reply_to_tweet_id=userID)
        tweetID = response.data['id']
        return self.client.get_tweet(tweetID)


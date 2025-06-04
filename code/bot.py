import os
from openai import OpenAI
import tweepy
import time
import queue
from dotenv import load_dotenv
import requests

load_dotenv(override=True)

'''
userID: [chats between user and bot as dictionaries]
element of .get(userID):
{
    fromUser: bool,
    isReply: bool,
    message: text,
    messageID: int,
    conversationID: int,
    timestamp: time,
    handle: text
}

'''

class SocialMediaChatbot:

    def __init__(self):
        self.model = ModelInterface()
        self.twitter = TwitterInterface()
        self.stream = StreamInterface()
        self.userHistories = {}             # maps a user id to their message history with the bot
        self.mostRecentMentionId = None

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
        print('starting polling. sleeping for 15 mins then pulling data')
        startTime = time.time()

        while time.time() - startTime < duration:
            
            time.sleep(interval)
            unseenMentions = self.twitter.getNewMentions(sinceId=self.mostRecentMentionId)
            print(f'got {len(unseenMentions)} new mentions')

            for mention in unseenMentions:
                self.processMention(mention)
        
        print('stopping polling')
    
    def processMention(self, mention):
        mention = self.formatTweet(mention)
        userChatHistory = self.getUserHistory(mention['userID'])
        
        modelResponse = self.model.writeMentionResponse(mention['message'], userChatHistory)
        response = self.twitter.respondToMention(mention['userID'], modelResponse.output_text)
        response = self.formatTweet(response)

        self.saveInteraction(mention, response)
        self.printInteraction(mention, response)
        self.updateMostRecentMention(mention['messageID'])
    
    def postTweetFromSubjectPool(self, chosenSubject):
        tweet = self.model.writeRandomTweet(f'{chosenSubject}')
        self.twitter.postTweet(tweet)

    def getUserHistory(self, userID):
        history = self.userHistories.get(userID, [])
        return history[-6:]

    def saveInteraction(self, mention, reply):
        userID = mention['userID']
        if userID not in self.userHistories:
            self.userHistories[userID] = []

        self.userHistories.get(userID).append(mention)
        self.userHistories.get(userID).append(reply)

    def printInteraction(self, mention, reply):

        s = f'''\n
        from {mention['handle']}, id={mention['userID']}:\n
        \n
        \t@jacob's_twitter_bot\n
        \t{mention['message']}\n\n
        at {mention['timestamp']}\n
        message id={mention['messageID']}\n
        conversation id={mention['conversationID']}\n
        \n\n
        from jacob's_twitter_bot, id={reply['userID']}:\n
        \t@{mention['handle']}\n
        \t{reply['text']}\n\n
        at {reply['timestamp']}\n
        message id={reply['messageID']}\n
        conversation id={reply['conversationID']}
        ------------------------- END OF MESSAGE -------------------------
        '''
        print(s)

    def updateMostRecentMention(self, id):
        self.mostRecentMentionId = id

    def formatTweet(self, tweet):
        tweetData = tweet.data
        users = tweet.includes.get("users", [])
        
        handle = ""
        if tweetData.author_id == self.twitter.id:
            handle = 'jacob_hebbel'
        else:
            for user in users:
                if user.id == tweetData.author_id:
                    handle = user.username
                    break
        
        fromUser = True if tweetData.author_id != self.twitter.id else False
        isReply = True if tweetData.conversation_id != tweetData.id else False

        return {
            "fromUser": fromUser,
            "isReply": isReply,
            "message": tweetData.text,
            "messageID": str(tweetData.id),
            "conversationID": str(tweetData.conversation_id),
            'userID': str(tweetData.author_id),
            "timestamp": str(tweetData.created_at),
            "handle": handle
        }


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
        self.authTokens = None
        self.client = self.getClient()
        self.id = self.client.get_me().data.id

    def getClient(self):
        auth = tweepy.OAuth2UserHandler(
            client_id=str(os.getenv('TWITTER_CLIENT_ID')),
            redirect_uri='http://localhost:8000/auth',
            scope=['tweet.write', 'tweet.read', 'users.read', 'offline.access']
        )

        print('Open this link and log into twitter')
        print(str(auth.get_authorization_url()))
        authURL = None

        while authURL is None:
            response = requests.get('http://localhost:8000/get')
            if response.status_code == 200:
                authURL = response.json().get('data')

            time.sleep(5)

        self.authTokens = auth.fetch_token(authURL)
        return tweepy.Client(access_token=self.authTokens["access_token"])
    
    def getNewMentions(self, sinceID=None):
        self.validateClient()
        return self.client.get_users_mentions(
            id=self.id,
            since_id=sinceID,
            expansions=["author_id"],
            tweet_fields=["conversation_id", "created_at"],
            user_fields=["username"]
        ).data or []
    
    def postTweet(self, message):
        self.validateClient()
        response = self.client.create_tweet(text=str(message))
        tweetID = response.data.id
        return self.client.get_tweet(
                                        id=tweetID,
                                        expansions=["author_id"],
                                        tweet_fields=["conversation_id", "created_at"],
                                        user_fields=["username"]
                                        )
    
    def respondToMention(self, userID, userHandle, reply):
        self.validateClient()
        reply = f'@{userHandle}\n\n' + reply
        response = self.client.create_tweet(text=str(reply), in_reply_to_tweet_id=userID)
        tweetID = response.data['id']
        return self.client.get_tweet(
                                        id=tweetID,
                                        expansions=["author_id"],
                                        tweet_fields=["conversation_id", "created_at"],
                                        user_fields=["username"]
                                        )

    def validateClient(self):
        if self.client is None:
            raise Exception('Client is being accessed while None')
        
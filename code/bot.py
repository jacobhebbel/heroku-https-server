import os
from openai import OpenAI
import tweepy
import time
import queue
from dotenv import load_dotenv

load_dotenv()


class SocialMediaChatbot:

    def __init__(self):
        self.model = ModelInterface()
        self.twitter = TwitterInterface()
        self.stream = StreamInterface()
        self.mentions = []

    def __str__(self):
        s = 'Beep Boop, I\'m a bot!\nI send messages to twitter with the help of OpenAI'
        s += f'\nI am using openAI\'s {self.model.model} to respond to queries'
        return s

    # returns true if a mention is heard
    def respondToMentions(self, duration=100):

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

    def postTweetFromSubjectPool(self, chosenSubject):
        
        tweet = self.model.writeStatusUpdate(
            message=f'Write a short status about {chosenSubject} that is engaging and family friendly'
        )
        self.twitter.postTweet(tweet)

    def saveMention(self, tweet):

        authorId = tweet.author_id
        message = tweet.text
        messageId = tweet.id
        conversationId = tweet.conversation_id

        self.mentions.append({
            'userId': str(authorId),
            'message': str(message),
            'messageId': str(messageId),
            'conversationId': str(conversationId)
        })

    def printMention(self, tweet):

        authorId = tweet.author_id
        message = tweet.text
        messageId = tweet.id
        conversationId = tweet.conversation_id

        s = f'''\n
        from {authorId}\n
        \n
        \t@jacob's_twitter_bot\n
        \t{message}\n\n
        message id={messageId}\n
        conversation id={conversationId}
        ------------------------- END OF MESSAGE -------------------------
        '''
        print(s)


class ModelInterface:

    def __init__(self):
        self.key = os.getenv('TWITTER_API_KEY')
        self.client = OpenAI()
        self.previousConversationId = None
        self.userToLastConversationId = {}

        self.instructions = 'You are a friendly twitter account responding to mentions'
        self.statelessConversation = True
        self.modelInput = []
        self.model = 'gpt-3.5-turbo-0125'

    def validatePrompt(self, prompt):
        if not prompt or not isinstance(prompt, str):
            raise Exception(f'Systme prompt provided to Model Interface is null or not type string: \nprompt: {prompt}\nprompt type: {type(prompt)}')

    def setSystemPrompt(self, prompt):
        self.validatePrompt(self, prompt)

        # O(n) operation
        for entry in self.modelInput:
            if isinstance(entry, dict) and 'system' in entry.keys():
                self.modelInput.remove(entry)

        self.modelInput.append({'system': f'{prompt}'})
        
    def addAssistantPrompt(self, prompt):
        self.validatePrompt(self, prompt)

        self.modelInput.append({'assistant': f'{prompt}'})

    def clearAssistantPrompts(self):
        
        # O(n) operation
        for entry in self.modelInput:
            if isinstance(entry, dict) and 'assistant' in entry.keys():
                self.modelInput.remove(entry)

    def setUserPrompt(self, prompt):
        self.validatePrompt(prompt)

        # O(n) operation
        for entry in self.modelInput:
            if isinstance(entry, dict) and 'user' in entry.keys():
                self.modelInput.remove(entry)

        self.modelInput.append({'user': f'{prompt}'})

    def setModel(self, modelType):

        if modelType is None or not isinstance(modelType, str):
            raise Exception(f'provided model type is not acceptable:\nmodel={modelType}\n model type={type(modelType)}')

        self.model = modelType

    def getModelResponse(self, message, user=None):
        
        # checking if this user has talked to the model before
        if user and isinstance(user, str):
            self.previousConversationId = self.userToLastConversationId.get(user)

        self.setUserPrompt(message)

        response = self.client.responses.create(
            model=self.model,                                   # controls which model the bot uses
            instructions=self.instructions,                     # controls how the model acts 
            input=self.modelInput,                              # controls the inputs
            previous_response_id=self.previousConversationId    # references the last conversation with the user

        )
        
        id = response.id
        self.userToLastConversationId.update({f'{user}': f'{id}'})

        return response.text

    def writeMentionResponse(self, userMessage, userId):
        
        userMessage = 'The following message is a prompt for writing a response to a mention from a twitter user:\n' + userMessage
        return self.getModelResponse(userMessage, userId)

    def writeStatusUpdate(self, statusPrompt):

        statusPrompt = 'The following message is a prompt for writing a twitter status update:\n' + statusPrompt
        return self.getModelResponse(statusPrompt)


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
        self.client = StreamClient(bearer_token=f'{os.getenv('TWITTER_BEARER_TOKEN')}',
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

    def getClient(self):
        return tweepy.Client(
            consumer_key=f'{os.getenv('TWITTER_CONSUMER_KEY')}',
            consumer_secret=f'{os.getenv('TWITTER_CONSUMER_SECRET')}',
            access_token_key=f'{os.getenv('TWITTER_ACCESS_TOKEN')}',
            access_token_secret=f'{os.getenv('TWITTER_ACCESS_SECRET')}'
        )
    
    def postTweet(self, message):
        self.client.create_tweet(text=f'{message}')
    
    def respondToMention(self, userId, reply):
        self.client.create_tweet(text=f'{reply}', in_reply_to_tweet_id=userId)


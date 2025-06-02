import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()



class GPTInterface:

    def __init__(self):
        
        self.client = OpenAI()
        self.apiKey = os.getenv('OPENAI_API_KEY') 
        self.previousConversationId = None
        self.userReferenceDictionary = {}

        self.instructions = 'Speak like a friendly social media account'
        self.statelessConversation = True
        self.input = []
        self.model = 'gpt-3.5-turbo-0125'

    def __str__(self):
        name = 'SocialMediaChatbot'
        instructions = self.instructions
        model = self.model
        params = self.input

        return f'''
            beep boop! my name is {name}, a {model} type chatbot!\n
            I've been instructed to {instructions}\n
            Here are my parameters:\n{params}\n\n
            To send a prompt to my model, call sendMessage()
            '''

    def addSystemPrompt(self, prompt):
        self.input.append({'system': f'{prompt}'})

    def addAssistantPrompt(self, prompt):
        self.input.append({'assistant': f'{prompt}'})

    def addUserPrompt(self, prompt):
        self.input.append({'user': f'{prompt}'})

    def removeMostRecentUserPrompt(self):
        
        for promptIndex in range(len(self.input)-1, -1, -1):
            prompt = self.input[promptIndex]

            if prompt.get('role') == 'user':
                self.input.remove(prompt)
                return
    
    def changeModel(self, modelType):
        if modelType == '':
            raise Exception('model name parameter is empty')
        else:
            self.model = f'{modelType}'

    def setInput(self, customInput):
        if customInput == []:
            raise Exception('Custom Input is empty of contents')
        else:
            self.input = customInput
    
    def sendMessage(self, message, user):
        
        previousCoversationId = None if self.statelessConversation or user not in self.userReferenceDictionary.keys() else self.userReferenceDictionary[f'{user}']
        self.addUserPrompt(message)

        response = self.client.responses.create(
            model=self.model,                               # controls which model the bot uses
            instructions=self.instructions,                 # controls how the model acts 
            input=self.input,                               # controls the inputs
            previous_response_id=previousCoversationId      # references the last conversation with the user

        )
        
        id = response.id
        self.userReferenceDictionary.update({f'{user}': f'{id}'})
        self.removeMostRecentUserPrompt()

        return response
    

class SocialMediaChatbot:

    def __init__(self):
        self.model = ModelInterface()
        self.twitter = TwitterInterface()
        pass

    def __str__(self):
        print('Beep Boop, I\'m a bot!\nI send messages to twitter with the help of OpenAI')
        pass

    # returns true if a mention is heard
    def listenForMentions(self, duration):
        pass
 
    def postTweet(self, tweet):
        
        
        pass

    def respondToMention(self, user, mention):
        pass


class ModelInterface:

    def __init__(self):
        self.key = os.getenv('TWITTER_API_KEY')
        self.client = OpenAI()
        self.previousConversationId = None
        self.userToLastConversationId = {}

        self.instructions = 'Speak like a friendly social media account'
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

    def useCustomInputJSON(self, customInputJSON):
        pass

    def sendModelRequest(self, user, message):
        pass

    def getModelResponse(self, message, user=None):
        
        # checking if this user has talked to the model before
        if user and isinstance(user, str):
            self.lastConversationId = self.userToLastConversationId.get(user)

        self.setUserPrompt(message)

        response = self.client.responses.create(
            model=self.model,                               # controls which model the bot uses
            instructions=self.instructions,                 # controls how the model acts 
            input=self.input,                               # controls the inputs
            previous_response_id=self.previousCoversationId # references the last conversation with the user

        )
        
        id = response.id
        self.userReferenceDictionary.update({f'{user}': f'{id}'})

        return response.text

class TwitterInterface:

    def __init__(self):
        pass

    def getClient(self):
        pass
    
    def openStream(self):
        pass

    def getMentions(self):
        pass

    def postTweet(self, message):
        pass
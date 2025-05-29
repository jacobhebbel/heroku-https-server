import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class SocialMediaChatbot:

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
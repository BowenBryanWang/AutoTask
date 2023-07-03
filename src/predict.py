import math
import numpy as np
import openai
import pandas as pd
import scipy
from page.init import Screen
from model import Model

import openai

openai.api_key = "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"

from reliablegpt import reliableGPT

openai.ChatCompletion.create = reliableGPT(
    openai.ChatCompletion.create,
    user_email= "saltyp0rridge20@gmail.com",
    queue_requests=True,
    fallback_strategy=['gpt-3.5-turbo', 'text-davinci-003', 'gpt-3.5-turbo'],
    model_limits_dir = {"gpt-4": {"max_token_capacity": 90000, "max_request_capacity": 3500	}}
) # type: ignore


class Predict(Model):
    """
    A class for predicting the possible controls that appear when a specific UI element is clicked.

    Attributes:
    -----------
    prompts : list
        A list of prompts for the prediction module.
    current_comp : list
        A list of the current page's components.
    next_comp : list
        A list of the next page's components, where each item is a list that corresponds to current_comp.
    comp_json : dict
        A dictionary of the prediction module's JSON, where each item is a component and its corresponding next page's components.
    """
    nodes=[]
    prompts = []
    current_comp = []
    next_comp = []
    comp_json = {}
    
    def __init__(self, nodes):
        """
        Initializes a Predict object.

        Parameters:
        -----------
        node : str
            The HTML attributes of the UI element being clicked.
        """
        self.nodes=nodes
        for node in nodes:
            self.current_comp.append(node)
            self.prompts.append([
                {
                    "role": "system",
                    "content": "You are an intelligent UI automation assistant that can predict the possible controls that appear when a specific UI element is clicked. Your task is to predict the potential controls that will be displayed after clicking a particular button on the UI."
                },
                {
                    "role": "user",
                    "content": """
                    The current scenario is within the WeChat application's home screen.
                    The UI element is a button with the following attributes:
                    ```HTML
                    <button id=1 class='Dropdown menu' description='More function buttons'>  </button>
                    ```
                    Think step by step.
                    """
                },
                {
                    "role": "assistant",
                    "content": """
                    ```HTML
                    <div>Money</div>
                    <div>Scan</div>
                    <div>Add Contacts</div>
                    <div>New Chat</div>
                    ```
                    """
                },
                {
                    "role": "user",
                    "content": """
                    The current scenario is {}.
                    The UI element is a button with the following attributes:
                    ```HTML
                    {}
                    ```
                    Think step by step.Must give the HTML code warped with ```HTML```.
                    """.format(self.screen.page_description, node)
                }
            ])
    
    def predict(self):
        """
        Predicts the possible controls that appear when a specific UI element is clicked.
        """
        for (node,prompt) in zip(self.nodes,self.prompts):
            if self.query(node):
                self.next_comp.append(self.query(node))
                continue
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=prompt,
                temperature=0.5,
            )
            print(response["choices"][0]["message"]["content"])
            response_text = response["choices"][0]["message"]["content"]
            response_text = response_text[response_text.find("```HTML")+7:response_text.find("```")].split("\n")
            print(response_text)
            self.next_comp.append(response_text)
            
        for i in range(len(self.current_comp)):
            self.comp_json[self.current_comp[i]] = self.next_comp[i]
            
         
    
    def query(self,node):
        """
        Queries the knowledge from KB
        """
        return False


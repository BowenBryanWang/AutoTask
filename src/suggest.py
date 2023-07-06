import math
import numpy as np
import openai
import pandas as pd
import scipy
from page.init import Screen
from model import Model

import openai

openai.api_key = "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"


class Suggest:
    def __init__(self, model: Model) -> None:
        self.model = model
        self.prompt = [
            {
                "role": "system",
                "content": "You are an AI assistant specialized in UI Automation. Based on user's intent and the current screen's components, your task is to analyze, understand the screen. SELECT the top five most possible components to the user's intent thinking step by step. Summarize your selections at the end of your response."
            },
            {
                "role": "user",
                "content": """
                    User's intention is to 'Turn off Dark mode in WeChat'. Here are the details of the current pages and components:
                    Current path: Wechat Homepage > Me > 
                    Current page Components:
                    '''HTML
                    '''
                    Think step by step, select the top five most possible components to the user's intent. Summarize your selections at the end of your response warpped by '''HTML and '''.
                """
            },
            {
                "role": "assistant",
                "content": """
                """
            },
            {
                "role": "user",
                "content": """
                    User's intention is to '{}'. Here are the details of the current pages and components:
                    Current path: {}
                    Current page Components:
                    '''HTML
                    {}
                    '''
                    Think step by step, select the top five most possible components to the user's intent. Summarize your selections at the end of your response warpped by '''HTML and '''.
                """.format(self.model.task, self.model.current_path_str, self.model.screen.semantic_nodes)
            },
        ]

    def suggest(self):

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.prompt,
            temperature=0.5,
        )
        print(response["choices"][0]["message"]["content"])
        response_text = response["choices"][0]["message"]["content"]
        candidate = response_text[response_text.find(
            "```HTML")+7:response_text.find("```")].split("\n")
        self.model.candidate = candidate
        print(candidate)

    def plan(self):
        """
        Plans the next step of the user's intent.
        """
        pass

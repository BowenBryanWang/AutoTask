import math
import numpy as np
import openai
import pandas as pd
import scipy
from page.init import Screen
from model import Model

import openai

openai.api_key = "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"


class Plan():
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
                """
            },
            {
                "role": "assistant",
                "content": """
                """
            }
        ]

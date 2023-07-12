import math
import numpy as np
import openai
import pandas as pd
import scipy
from page.init import Screen
from model import Model
from loguru import logger
import json

import openai

openai.api_key = "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"


class Suggest:
    def __init__(self, model) -> None:
        self.model = model
        self.prompt = [
            {
                "role": "system",
                "content": "You are an AI assistant specialized in UI Automation. Based on user's intent and the current screen's components, your task is to analyze, understand the screen. SELECT the top five most possible components to the user's intent thinking step by step. Summarize your selections at the end of your response."
            },
            {
                "role": "user",
                "content": """
                    User's intention is to 'Turn on Dark mode in Whatsapp'. Here are the details of the current pages and components:
                    Current path: [Homepage]
                    Current page Components:
                    '''HTML
                    <p id=1 class='com.whatsapp:id/fab' description='New chat'>  </p>
                    <button id=2 class='com.whatsapp:id/home_tab_layout' description='Calls'> Calls </button>
                    <button id=3 class='com.whatsapp:id/home_tab_layout' description='Status'> Status </button>
                    <button id=4 class='com.whatsapp:id/home_tab_layout' description='Community'>  </button>
                    <button id=5 class='com.whatsapp:id/menuitem_overflow' description='More options'>  </button>
                    <p id=6 class='com.whatsapp:id/menuitem_search' description='Search'>  </p>
                    <p id=7 class='com.whatsapp:id/menuitem_camera' description='Camera'>  </p>
                    <p id=8 class='' description='end-to-end encrypted'>  </p>
                    <button id=9 class='com.whatsapp:id/contact_photo' description='Yellow'>  </button>
                    <button id=10 class='com.whatsapp:id/contact_photo' description='Wang Bowen'>  </button>
                    '''
                    Think step by step, select the top five most possible components to the user's intent. Summarize your selections at the end of your response warpped by '''HTML and '''.
                """
            },
            {
                "role": "assistant",
                "content": """
                <button id=5 class='com.whatsapp:id/menuitem_overflow' description='More options'>: This component represents the overflow menu, which often contains additional settings and options. It's a common place to find settings related to appearance and themes, including Dark mode.
                <button id=10 class='com.whatsapp:id/contact_photo' description='Wang Bowen'>: This component likely represents a contact or profile photo. Tapping on a contact or profile photo often reveals additional options and settings, which may include Dark mode or appearance-related settings.
                <button id=2 class='com.whatsapp:id/home_tab_layout' description='Calls'>: While this component represents the "Calls" tab, it is worth exploring as some apps provide accessibility options, including Dark mode, within the tab navigation.
                <button id=3 class='com.whatsapp:id/home_tab_layout' description='Status'>: Similar to the "Calls" tab, the "Status" tab might contain accessibility or appearance-related options, including Dark mode.
                <button id=4 class='com.whatsapp:id/home_tab_layout' description='Community'>: Although the description is empty for this component, it is worth exploring as it could potentially lead to settings related to appearance or themes, including Dark mode.
                So the top five most possible components to the user's intent are:
                '''HTML
                <button id=5 class='com.whatsapp:id/menuitem_overflow' description='More options'> </button>
                <button id=10 class='com.whatsapp:id/contact_photo' description='Wang Bowen'> </button>
                <button id=2 class='com.whatsapp:id/home_tab_layout' description='Calls'> </button>
                <button id=3 class='com.whatsapp:id/home_tab_layout' description='Status'> </button>
                <button id=4 class='com.whatsapp:id/home_tab_layout' description='Community'> </button>
                '''
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

        log_file = logger.add("logs/suggest.log", rotation="500 MB")
        logger.debug("Suggest for Model {}".format(self.model.index))
        logger.info("Current Page: {}".format(self.model.screen.page_description))
        logger.info("Current Path: {}".format(self.model.current_path_str))
        logger.info("Task: {}".format(self.model.task))
        logger.info("Prompt: {}".format(json.dumps(self.prompt[-1])))

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

        logger.warning("Response: {}".format(candidate))
        logger.debug("Suggest for Model {} Done".format(self.model.index))
        logger.remove(log_file)

    def plan(self):
        """
        Plans the next step of the user's intent.
        """
        pass

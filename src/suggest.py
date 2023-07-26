

import os
import openai


from loguru import logger
import json

import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


class Suggest:
    def __init__(self, model) -> None:
        self.model = model
        self.prompt = [
            {
                "role": "system",
                "content": """You are an AI assistant specialized in UI Automation. Based on user's intent and the current screen's components, your task is to analyze, understand the screen. SELECT the top five most possible components to the user's intent thinking step by step. Summarize your selections at the end of your response.
                Think step by step, select the top five most possible components to the user's intent.
                    Output a JSON object structured like {"result":[]-the number of selected candidate} at the end of your response.
                    Do not select after-click components."""
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
                {
                    "result": [5,10,2,3,4]
                }
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
                """.format(self.model.task, self.model.current_path_str, self.model.extended_info)
            },
        ]

    def suggest(self):

        log_file = logger.add("logs/suggest.log", rotation="500 MB")
        logger.debug("Suggest for Model {}".format(self.model.index))
        logger.info("Current Page: {}".format(
            self.model.screen.page_description))
        logger.info("Current Path: {}".format(self.model.current_path_str))
        logger.info("Task: {}".format(self.model.task))
        logger.info("Prompt: {}".format(json.dumps(self.prompt[-1])))

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.prompt,
            temperature=0.5,
        )
        response_text = response["choices"][0]["message"]["content"]
        print(response_text)
        candidate: list[int] = json.loads(
            response_text[response_text.find("{"):response_text.find("}")+1])["result"]

        self.model.candidate = candidate
        self.model.candidate_str = [self.model.screen.semantic_info[i-1] for i in candidate]
        print(candidate)

        logger.warning("Response: {}".format(candidate))
        logger.debug("Suggest for Model {} Done".format(self.model.index))
        logger.remove(log_file)

    def plan(self):
        """
        Plans the next step of the user's intent.
        """
        pass

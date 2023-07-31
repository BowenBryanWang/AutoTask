

import os
import openai


from loguru import logger
import json

import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


class Suggest:
    def __init__(self, model) -> None:
        self.model = model

    def suggest(self):
        self.prompt_select = [
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
        with open("logs/log{}.log".format(self.model.index), "a") as f:
            f.write("--------------------Suggest--------------------\n")
        log_file = logger.add(
            "logs/log{}.log".format(self.model.index), rotation="500 MB")
        logger.debug("Suggest for Model {}".format(self.model.index))
        logger.info("Current Page: {}".format(
            self.model.page_description))
        logger.info("Current Path: {}".format(self.model.current_path_str))
        logger.info("Task: {}".format(self.model.task))
        logger.info("Prompt: {}".format(json.dumps(self.prompt_select[-1])))

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.prompt_select,
            temperature=0,
        )
        response_text = response["choices"][0]["message"]["content"]
        print(response_text)
        candidate: list[int] = json.loads(
            response_text[response_text.find("{"):response_text.find("}")+1])["result"]

        self.model.candidate = candidate
        self.model.candidate_str = [
            self.model.screen.semantic_info[i-1] for i in candidate]
        print(candidate)

        logger.warning("Response: {}".format(candidate))
        logger.debug("Suggest for Model {} Done".format(self.model.index))
        logger.remove(log_file)

    def plan(self):
        """
        Plans the next step of the user's intent.
        """
        self.prompt_plan = [
            {
                "role": "system",
                "content":
                """You are an AI assistant specialized in UI Automation. Now you have successfully obtained the top five UI components that are most likely to align with the user's intent. Now, you need to determine the actions to be performed on each of these UI components. 
                There are two main types of actions: 
                    1,clicking on a component (no text parameter needed) 
                    2,editing a component (you should also determine the text parameter).
For each of the top five components, analyze the possible action to be taken and, if it involves an editing action, provide the corresponding text parameter as well. 
Reason step by step to provide the actions and text parameters for each component based on the user's intent and the context of the current screen.
Output a JSON object structured like 
{"candidate1":{"action": the action to be taken, "text": the text parameter for the action if any (Optional),"reason": the reason},
"candidate2":same as above,
"candidate3":same as above,
"candidate4":same as above,
"candidate5":same as above,
} 
including each candidate although which may be irrelevant"""
            },
            {
                "role": "user",
                "content": """
                Task: send a message "Hello" to Bowen
Current Page : Whatsapp homepage:
Candidates:
["<button id=8 class='com.whatsapp:id/contact_photo' description='Wang Bowen'> </button>", "<p id=5 class='com.whatsapp:id/menuitem_search' description='Search'> </p>", "<button id=1 class='com.whatsapp:id/home_tab_layout' description='Calls'> </button>", "<button id=2 class='com.whatsapp:id/home_tab_layout' description='Status'> </button>", "<button id=3 class='com.whatsapp:id/home_tab_layout' description='Community'> </button>"]"""
            },
            {
                "role": "assistant",
                "content": """{
  "candidate1": {
    "action": "click",
    "text": null,
    "reason": "To open Bowen's chat window to send a message."
  },
  "candidate2": {
    "action": "edit",
    "text": "Bowen",
    "reason": "To filter contacts and find Bowen's chat to send a message."
  },
  "candidate3": {
    "action": "click",
    "text": null,
    "reason": "Switching to the 'Calls' tab is not relevant to sending a message."
  },
  "candidate4": {
    "action": "click",
    "text": null,
    "reason": "Switching to the 'Status' tab is not relevant to sending a message."
  },
  "candidate5": {
    "action": "click",
    "text": null,
    "reason": "Switching to the 'Community' tab is not relevant to sending a message."
  }
}"""},
            {
                "role": "user",
                "content": """
                Task: {},
Current Page : {}:
Candidates:{}""".format(self.model.task, self.model.page_description, self.model.candidate_str)
            }
        ]

        with open("logs/log{}.log".format(self.model.index), "a") as f:
            f.write("--------------------Suggest--------------------\n")
        log_file = logger.add(
            "logs/log{}.log".format(self.model.index), rotation="500 MB")
        logger.debug("Plan for Model {}".format(self.model.index))
        logger.info("Prompt: {}".format(json.dumps(self.prompt_plan[-1])))
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.prompt_plan,
            temperature=0,
        )
        response_text = response["choices"][0]["message"]["content"]
        response = json.loads(
            response_text)
        print(response)
        self.model.candidate_action = [None]*5
        self.model.candidate_text = [None]*5
        # self.model.candidate_reason = [None]*5
        for i in range(1, 6):
            self.model.candidate_action[i -
                                        1] = response["candidate{}".format(i)]["action"]
            self.model.candidate_text[i -
                                      1] = response["candidate{}".format(i)]["text"]
            # self.model.candidate_reason[i-1] = response["candidate{}".format(i)]["reason"]
        logger.warning("Candidate Action: {}".format(
            self.model.candidate_action))
        logger.warning("Candidate Text: {}".format(self.model.candidate_text))
        logger.debug("Plan for Model {} Done".format(self.model.index))
        logger.remove(log_file)

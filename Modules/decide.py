import json
import openai
import os

from Modules.utility import GPT, decide_prompt
from UI.init import Screen

openai.api_key = os.getenv('OPENAI_API_KEY')


class Decide:
    """Decide mofule of AutoTask, representing the deciding process of the workflow

    Attributes:
        model (Model): the model object
    """

    def __init__(self, model) -> None:
        """
        Initialize a Decide object
        """
        self.model = model

    def log_decorator(func):
        """Log decorator for Decide module, logging the output of the module to the log file"""

        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            self.model.log_json["@Module"].append({
                "Name": "Decide",
                "Description": "This module is a decision module, deciding the final action based on the evaluation result, whether complete or wrong or go on",
                "Output": self.answer
            })
            self.model.log_json["@Successive_Page"] = self.model.next_model.screen.semantic_info_all_warp
            with open("logs/log{}.json".format(self.model.index+1), "w", encoding="utf-8") as f:
                json.dump(self.model.log_json, f, indent=4)
            return result
        return wrapper

    @log_decorator
    def decide(self, new_screen: Screen, ACTION_TRACE: dict, flag: str):
        """
        Deciding process: calling GPT API to start deciding procedures
        """
        prompt = decide_prompt(
            self.model.task, self.model.prev_model.current_action if self.model.prev_model else "", ACTION_TRACE, new_screen.semantic_info_all_warp, self.model.decision_knowledge)
        if flag == "debug":
            prompt.append({"role": "user",
                           "content": """Please note the following special additional information:
You are currently in the backtracking and error correction phase, which means that you have reached this page due to backtracking after the last several steps in ACTION_TRACE were executed but did not meet the task requirements. As the decision module, you need to determine whether to continue exploring on the current UI. If so, please output the status as 'go on'; if not (i.e., it is not possible to continue and further backtracking is needed), please output 'wrong'.
For this purpose, please carefully analyze each step in ACTION_TRACE, and the information of the new page entered by each step, especially the information caused by backtracking, to judge whether further exploration is needed on that page.
If there have been multiple explorations and backtrackings, then it is highly probable that 'wrong' needs to be output to backtrack one more step to look for earlier errors.
"""})
        self.answer = GPT(prompt, tag="decide"+str(self.model.index+1))
        if flag == "debug":
            self.model.wrong_reason = self.answer["reason"]
            return self.answer["status"]
        else:
            self.model.wrong_reason = self.answer["reason"]
            if self.answer["status"] == "completed":
                with open("logs/final.json", "w", encoding="utf-8") as f:
                    json.dump(ACTION_TRACE, f, indent=4)
            return self.answer["status"]

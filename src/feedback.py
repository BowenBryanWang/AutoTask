import json
import re
import openai
from loguru import logger
import requests
import os

from src.utility import GPT
openai.api_key = os.getenv('OPENAI_API_KEY')


class Feedback:
    def __init__(self, model) -> None:
        self.model = model

    def feedback(self, reason):
        with open("logs/log{}.json".format(self.model.index+1), "r", encoding="utf-8") as f:
            print("· log{} Read".format(self.model.index+1))
            print(self.model.log_json)
            self.info: dict = json.loads(f.read())
        self.prompt = [
            {
                "role": "system",
                "content": """You are an expert in UI automation and robust error handling. Your task is to critic a operation sequence produced by a [primitive LLM],following user task but inaccurate. 
Utilizing the log files from each module of current step of the [primitive LLM], you should locate error in the final element chosen to operate on.
[primitive LLM] works in which they cannot see further information on UI, but you are in the backtracking process so you should utilize further information observed from subsequent UI to help correct possible errors.
Specifically, you should analyze the [Latest Action] and the [Successive Page] information to determine the extent of error on fulfilling the task, and then output the punishment coefficient to it.
Follow the steps below and think step by step:
a. Understand the information given and synthize, especially [Latest Action] and its subsequent result [Successive Page];
b, Think step by step about the scoring result by [Evaluation Module], try to identify error causes on the LATEST ACTION and give [Punishment Coefficient] from 1-10, where 1 means no error and 10 means totally wrong;
Finally, output a JSON format like this example:
{
    "punishment":
    {
        "id_x": 1,
        ......(replace x to the element with id that you think causes the error, output your punishment coefficient from 0-10)
    }
}
"""}
        ]
        self.prompt.append({
            "role": "user",
            "content": """
                Wrong reason: {}
                """.format(reason)
        })
        self.prompt.append({
            "role": "user",
            "content": """
                User intent: {}
                """.format(self.info["@User_intent"])
        })
        self.prompt.append({
            "role": "user",
            "content": """
                Page components: {}
                """.format(self.info["@Page_components"])
        })
        self.prompt.append({
            "role": "user",
            "content": """
                Previous Steps: {}
                """.format(self.info["@History_operation"])
        })
        self.prompt.append({
            "role": "user",
            "content": """
                Action on this step: {}
                """.format(self.info["@Current_Action"])
        })
        if self.info["@Successive_Page"]:
            self.prompt.append({
                "role": "user",
                "content": """
                    Latest Page: {}
                    """.format(self.info["@Successive_Page"])
            })
        else:
            self.prompt.append({
                "role": "user",
                "content": "Latest Page is the same as last one! Last action did not cause any changes so it's wrong"
            })
        self.prompt.append({
            "role": "user",
            "content": """
                Modules: {}
                """.format(self.info["@Module"][1])
        })
        response = GPT(self.prompt, tag="feedback"+str(self.model.index))
        p_score = response.get("punishment")
        self.model.evaluate_module.update_weights(p_score)
        return "yes", "yes"

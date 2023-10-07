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

    def feedback(self,reason):
        with open("logs/log{}.json".format(self.model.index), "r",encoding="utf-8") as f:
            print("· log{} Read".format(self.model.index))
            print(self.model.log_json)
            self.info: dict = json.loads(f.read())
        self.prompt = [
    {
        "role": "system",
        "content": """You are an expert in UI automation and robust error handling. Your task is to critically evaluate an action trace on UI produced by a [primitive LLM], which follows human instruction but is known for its inaccuracies. 
Basically, the working process of [primitive LLM] is:
    Follow the user's intent -> observe UI elements on UI screen -> select UI elements and rate them -> select the top one and execute it
Utilizing the log files from each module of current step of the [primitive LLM], you should determine whether this step caused error or not.
The only way you could do in correction is to control the rating scores by outputing different weights to them.
[primitive LLM] works in which they cannot see further information on UI, but as an error handling expert in the backtracking process you should utilize further information that you observed on subsequent UI to help correct possible errors.
In some situations there is no error and is relatively correct, it depends so you should think step by step.
Follow the steps below and think step by step:
a. Understand the information given and synthize;
b, determine whether this step caused error;
c, if so, think step by step about the scoring result, try to identify error-cause and give Punishment coefficient from 0-10;
d, if you identify no error in this step,we could move on to previous steps, so output "no error".
Finally, output a JSON format like this example:
{
    "result": "error" or "no error",
    "punishment":
    {
        "id_x": 1,
        "id_y": 2,
        ......(for UI elements selected with id , output your punishment coefficient from 0-10)
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
                Similar Tasks: {}
                """.format(self.info["@Similar_tasks"])
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
                Page description: {}
                """.format(self.info["@Page_description"])
        })
        self.prompt.append({
            "role": "user",
            "content": """
                Previous Steps: {}
                """.format(self.info["@Previous_Step"])
        })
        self.prompt.append({
            "role": "user",
            "content": """
                Action on this steo: {}
                """.format(self.info["@Action"])
        })
        self.prompt.append({
            "role": "user",
            "content": """
                Latest Page: {}
                """.format(self.info["@Successive_Page"])
        })
        self.prompt.append({
            "role": "user",
            "content": """
                Modules: {}
                """.format(self.info["@Module"])
        })
        response = GPT(self.prompt)


        self.error_status = response.get("result")
        if self.error_status == "no error":
            return None,None
        else:
            p_score = response.get("punishment")
            self.model.evaluate_module.update_weights(p_score)
            return "yes","yes"

import json
import re
import openai
from loguru import logger
import requests
import os
openai.api_key = os.getenv('OPENAI_API_KEY')

class Feedback:
    def __init__(self, model) -> None:
        self.model = model

    def feedback(self):
        with open("logs/log{}.json".format(self.model.index), "r") as f:
            print("· log{} Read".format(self.model.index))
            print(self.model.log_json)
            self.info: dict = json.loads(f.read())
        self.prompt = [
    {
        "role": "system",
        "content": """
You are an expert in UI automation and robust error handling. Your task is to critically evaluate an action trace produced by a primitive LLM, which tracks human intent but is known for its inaccuracies. Utilizing the log files from each module of this primitive LLM, you should identify errors and provide actionable feedback for improvements.
Use the following steps to respond to user inputs. Fully restate each step before proceeding. i.e. "Step 1: Reason...".
Step 1: Evaluate the Rationality of the Current Step:

a. Analyze the user intent for the task "@User_intent" and compare with similar examples "@Similar_task".
b. Review the components "@Page_components" and the description "@Page_description" of the current page.
c. Assess previous steps "@Previous_Steps", the "@Action" taking in this step and the subsequent page "@Successive_Page", ensuring they align with user's intent
Step 2: Analyze "@Module" Log Details:

a. Given the current and subsequent page components, inspect the logs of the "predict" module. Identify any misjudgments that could mislead subsequent modules if any.
b. Examine the "select" module logs. This module selects the 5 possible component (equally, without relativity ranking) to be acted on catering to user's intent. Identify any omissions.These 5 candidates can contain wrong components but should not miss any correct ones.
c. Scrutinize the "plan" module. This module independently plans action on the candidates selected by Select Module ignoring whether they are rational. Just Determine if the action (either click or edit) is logical.
d. Reassess the "evaluate" module logs and their scoring reasons. Re-evaluate candidate scores, cross-referencing with information from the successive page.
e. Skip the "decide" module, assuming its accuracy.

Each part works independently, so you need to diagnose each part individually during your analyzing.
Step 3: Format your findings into a JSON structure as follows:
{
  "predict module": {
    "status": "error" if major errors occur; "right" if no need to modify it,
    "reason": "Detailed reason",
    "feedback": "Specific feedback suggestions"
  },
  "select module" : {
    "status": "error" if any omission occurs; "right" if 5 candidates did not miss any relatively correct one, (selecting some irrelevant components is ok, you just need to justify if this module missed any correct component.You don't need to analyze the correctness of each candidate in this step.)
    "reason": "Detailed reason",
    "feedback": Provide the missing component.
  },
  "plan module" : {
    "status": "error" if any action type is wrong; "right" if no need to change each action type,
    "reason": "Detailed reason",
    "feedback": Provide the specific modified action type.
  },
  "evaluate module" : {
    "status": "error" if top-scored component is wrong; "right" if no need to change top-scored component,
    "reason": "Detailed reason",
    "feedback": "Specific feedback suggestions"
  },

}
Your feedback json would be directily integrated into the prompt of each module of the primitive LLM for training.
Ensure your feedback is practical and specific."""
            }
        ]
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
                """.format(self.info["@Similar_task"])
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
                Action: {}
                """.format(self.info["@Action"])
        })
        self.prompt.append({
            "role": "user",
            "content": """
                Successive Page: {}
                """.format(self.info["@Successive_Page"])
        })
        self.prompt.append({
            "role": "user",
            "content": """
                Modules: {}
                """.format(self.info["@Module"])
        })
        response = requests.post("http://166.111.139.119:12321/query", headers={
            'content-type': 'application/json',
        }, data=json.dumps({
            'msg': self.prompt,
            'temp': 1,
        }))
        match = re.search(r'{.*?}', response.choices[0].message.content)
        if match:
            json_str = match.group(0)
            try:
                response = json.loads(json_str)
                print(response)
            except json.JSONDecodeError:
                print("Invalid JSON found in the response string.")
        else:
            print("No JSON found in the response string.")

        self.predict_advice = response.get("predict module")
        self.select_advice = response.get("select module")
        self.plan_advice = response.get("plan module")
        self.evaluate_advice = response.get("evaluate module")
        if all(advice.get("status") == "right" for advice in [self.predict_advice, self.select_advice, self.plan_advice, self.evaluate_advice]) or not self.model.prev_model:
            return True
        if self.predict_advice and self.select_advice and self.plan_advice and self.evaluate_advice:
            if self.predict_advice.get("status") == "wrong":
                self.model.predict_module.update(self.predict_advice)
            if self.select_advice.get("status") == "wrong":
                self.model.select_module.update(self.select_advice)
            if self.plan_advice.get("status") == "wrong":
                self.model.plan_module.update(self.plan_advice)
            if self.evaluate_advice.get("status") == "wrong":
                self.model.evaluate_module.update(self.evaluate_advice)
        return False
            
        


# with open("../logs/log{}.json".format(0), "r") as f:
#     print("· log{} Read".format(0))
#     info: dict = json.loads(f.read())
# prompt = [
#     {
#         "role": "system",
#         "content": """
# You are an expert in UI automation and robust error handling. Your task is to critically evaluate an action trace produced by a primitive LLM, which tracks human intent but is known for its inaccuracies. Utilizing the log files from each module of this primitive LLM, you should identify errors and provide actionable feedback for improvements.
# Use the following steps to respond to user inputs. Fully restate each step before proceeding. i.e. "Step 1: Reason...".
# Step 1: Evaluate the Rationality of the Current Step:

# a. Analyze the user intent for the task "@User_intent" and compare with similar examples "@Similar_task".
# b. Review the components "@Page_components" and the description "@Page_description" of the current page.
# c. Assess previous steps "@Previous_Steps", the "@Action" taking in this step and the subsequent page "@Successive_Page", ensuring they align with user's intent
# Step 2: Analyze "@Module" Log Details:

# a. Given the current and subsequent page components, inspect the logs of the "predict" module. Identify any misjudgments that could mislead subsequent modules if any.
# b. Examine the "select" module logs. This module selects the 5 possible component (equally, without relativity ranking) to be acted on catering to user's intent. Identify any omissions.These 5 candidates can contain wrong components but should not miss any correct ones.
# c. Scrutinize the "plan" module. This module independently plans action on the candidates selected by Select Module ignoring whether they are rational. Just Determine if the action (either click or edit) is logical.
# d. Reassess the "evaluate" module logs and their scoring reasons. Re-evaluate candidate scores, cross-referencing with information from the successive page.
# e. Skip the "decide" module, assuming its accuracy.

# Each part works independently, so you need to diagnose each part individually during your analyzing.
# Step 3: Format your findings into a JSON structure as follows:
# {
#   "predict module": {
#     "status": "error" if major errors occur; "right" if no need to modify it,
#     "reason": "Detailed reason",
#     "feedback": "Specific feedback suggestions"
#   },
#   "select module" : {
#     "status": "error" if any omission occurs; "right" if 5 candidates did not miss any relatively correct one, (selecting some irrelevant components is ok, you just need to justify if this module missed any correct component.You don't need to analyze the correctness of each candidate in this step.)
#     "reason": "Detailed reason",
#     "feedback": Provide the missing component.
#   },
#   "plan module" : {
#     "status": "error" if any action type is wrong; "right" if no need to change each action type,
#     "reason": "Detailed reason",
#     "feedback": Provide the specific modified action type.
#   },
#   "evaluate module" : {
#     "status": "error" if top-scored component is wrong; "right" if no need to change top-scored component,
#     "reason": "Detailed reason",
#     "feedback": "Specific feedback suggestions"
#   },

# }
# Your feedback json would be directily integrated into the prompt of each module of the primitive LLM for training.
# Ensure your feedback is practical and specific.
# """
#     },
#     {
#         "role": "user",
#         "content": """
#         {}
#         """.format(info)
#     },
# ]
# response = openai.ChatCompletion.create(
#     model="gpt-3.5-turbo",
#     messages=prompt,
#     temperature=1,
# )
# print(response)

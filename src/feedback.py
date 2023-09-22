import json
import re
import openai
from loguru import logger
import requests
import os
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.organization = 'org-veTDIexYdGbOKcYt8GW4SNOH'
class Feedback:
    def __init__(self, model) -> None:
        self.model = model

    def feedback(self,reason):
        with open("logs/log{}.json".format(self.model.index), "r") as f:
            print("· log{} Read".format(self.model.index))
            print(self.model.log_json)
            self.info: dict = json.loads(f.read())
        self.prompt = [
    {
        "role": "system",
        "content": """
You are an expert in UI automation and robust error handling. Your task is to critically evaluate an action trace produced by a primitive LLM, which follows human intent but is known for its inaccuracies. Utilizing the log files from each module of this primitive LLM, you should identify possible errors.
You should:
a. Analyze the user intent for the task "@User_intent" and can refer to similar examples "@Similar_task".
b. Review the components "@Page_components" and the description "@Page_description" of the current page.
c. Analyze previous steps "@Previous_Steps", the "@Action" taking in this step and the subsequent page "@Successive_Page", identify if the Action in this step directly cause the error.
d. If you do think the error is caused by this step's Action, output the new modified action that is chose from the "@Page_components".
e. If you think the error is in the earlier steps but not this step thus we should move a step back in the history traces to identify the error, output "Back".

Finally, output a JSON format:
{
    "result": "back" or "modify",
    "modify": {
        "comp":the right component that you corrected,
        "type":"click" or "edit",
        "para": the edit parameter.
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

        self.error_status = response.get("result")
        if self.error_status == "back":
            return None,None
        else:
            action = response.get("modify")
            action_comp = action.get("comp")
            action_type = action.get("type")
            action_para = action.get("para")
            self.model.node_selected_id = int(action_comp.split("id=")[1].split(" ")[0])
            current_action = process_action_info(action_type, action_para, action_comp)
            nodes = self.model.screen.semantic_nodes["nodes"]
            node = nodes[self.model.node_selected_id - 1]
            if action_type == "click":
                center = {"x": (node.bound[0] + node.bound[2]) // 2, "y": (node.bound[1] + node.bound[3]) // 2}
                perform = {"node_id": 1, "trail": "[" + str(center["x"]) + "," + str(center["y"]) + "]", "action_type": "click"}
                print(perform)
                return "yes",perform
            elif action_type == "edit":
                perform = {"node_id": 1, "trail": "[0,0]", "action_type": "text", "text": action_para,"ori_absolute_id":node.absolute_id}
                print(perform)
                return "yes",perform
            
            
def process_action_info(action, params, node):
    if action == "click":
        return "Action: Click on {}".format(node)
    elif action == "edit":
        return "Action: Edit {} with {}".format(node, params)


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

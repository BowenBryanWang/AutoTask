import json
import openai
from loguru import logger
import requests
import os

openai.api_key = os.getenv('OPENAI_KEY', default="sk-dXUeoKXznBmiycgc06831a96F6Be42149e9aD25eDfA15e8c")
openai.api_base = "https://api.ai-yyds.com/v1"

class Decide:
    def __init__(self, model) -> None:
        """
        Initializes a Decide object with a given OpenAI model.

        Args:
            model (str): The name of the OpenAI model to use.
        """
        self.model = model

    def decide(self, new_screen):
        """
        Uses the OpenAI model to generate a response to the prompt.

        Returns:
            str: The status of the decision made by the model.
        """
        with open("./src/KB/pagejump.csv", "a") as f:
            f.write("{},{},{}\n".format(self.model.screen.semantic_info_str.replace('\n', '').replace(",",";;"),self.model.current_path[-1].replace('\n', '').replace(",",";;"), new_screen.semantic_info_str.replace('\n', '').replace(",",";;")))
        print("___________________________decide___________________________")
        self.prompt = [{
            "role": "system",
            "content": """You are a professor with in-depth knowledge of User Interface (UI) tasks and their action traces. You are assigned a specific UI task along with an action trace. Your task is to evaluate if the action trace aligns with the assigned task, categorizing the trace as: 
1,completed: After the last action and based on the newest UI screen, the user's task is completed;
2,wrong: After the last action and based on the newest UI screen, the action trace goes into a wrong branch and need to be corrected;
3,go on: After the last action and based on the newest UI screen, the action trace is on the right track but not completed yet. Further actions are needed to complete the task.
You can refer to some completed examples similar to user's intent. But don't follow the examples exactly, though; they serve only as hints.
"Task" stands for user's intent; "Action Trace" stands for the user's current action traces on the mobile; "Last Page" stands for UI structure after the last action.
You should comprehensively analyze the above three fields or refer to similar examples to make a synthesis conclusion.
Use the following steps to respond to user inputs. Fully restate each step before proceeding. i.e. "Step 1: Reason...".
Step 1:Reason step-by-step about the relationship of the action trace  and UI task.
Step 2:Reason step-by-step about whether the newest UI screen is consistent with the UI task result.
Step 3:Output a JSON object structured like: {"status": "completed" or "wrong" or "go on", "reason": reason for the decision}."""
        },
            {
            "role": "user",
            "content": """
Task: Add a new contact called Steven
Action Trace: [Page]: Main interface of WhatsApp => [Action]: click on <button id=1 class='com.whatsapp:id/fab' description='New chat'>  </button> => [Page]: Adding new chat and invite friends
Last Page:
<button id=1 class='' > INVITE </button>
<button id=3 class='' description='Yellow'> Yellow </button>
<button id=7 class='' description='Wang Bowen'> Wang Bowen </button>
<button id=9 class='' > Contacts on WhatsApp </button>
<button id=10 class='' > New community </button>
<p id=11 class='com.whatsapp:id/contactpicker_button_two' description='Scan, share QR code'>  </p>
<button id=12 class='' > New group </button>
<button id=13 class='com.whatsapp:id/menuitem_overflow' description='More options'>  </button>
<p id=14 class='com.whatsapp:id/menuitem_search' description='Search'>  </p>
<p id=15 class='' description='Navigate up'>  </p>
            """
        },
            {
            "role": "assistant",
            "content": """
Step 1: Reason step-by-step about the relationship of the action trace and UI task.
Given UI Task: Add a new chat with Steven.
The user starts on the main interface of WhatsApp.
The user clicks on the 'New chat' button.
The user lands on the "Adding new chat and invite friends" page.
Based on this action trace, the user seems to be on the correct path to adding a new chat since they've navigated to the 'Adding new chat and invite friends' page from the main interface. However, the task specifically mentioned adding a chat with "Steven", and it's important to check if this action has been completed.
Step 2: Reason step-by-step about whether the newest UI screen is consistent with the UI task result.
Upon observing the provided 'Last Page' UI elements:
There are multiple buttons present, with some indicating individual contacts (like '余捷', 'Yellow', 'f', '助教', 'Wang Bowen', and '老婆子 (You)') and others with different functionalities (like 'INVITE', 'Invite to WhatsApp', 'Contacts on WhatsApp', 'New community', 'New group', etc.).
There's no button or contact labeled "Steven".
As per the task, we are looking for an action or a button related to starting a chat with "Steven", which is not present.
Given this information, while the user is in the appropriate section to start a new chat, they have not yet started a chat with Steven.
Step 3: Output a JSON object structured like:
{
  "status": "go on",
  "reason": "The user has navigated to the 'Adding new chat and invite friends' section, which is consistent with the task of starting a new chat. However, there is no indication that a chat with 'Steven' has been started or is available in the current UI screen. Further actions are needed."
}
Based on the provided information, the user should continue their actions to search or scroll for "Steven" in the contacts list to complete the task.





"""
        },
            {
            "role": "user",
            "content": """
Task:{}
Action trace:{}
Last Page:{}
Completed Examples from Library:
{}
            """.format(self.model.task, self.model.current_path_str, new_screen.semantic_info, [j+":"+"=>".join(k) for j, k in zip(self.model.similar_tasks, self.model.similar_traces)])
        }]
        response = openai.ChatCompletion.create(
            model = "gpt-4",
            messages = self.prompt,
            temperature=1,
        )
        self.model.log_json["@Similar_task"] = [j+":"+"=>".join(k) for j, k in zip(self.model.similar_tasks, self.model.similar_traces)]
        # 提取回答当中的json部分
        answer = response.choices[0]["message"]["content"]
        answer = json.loads(answer[answer.find("{"):answer.find("}")+1])

        log_info = {
            "Name":"Decide",
            "Description":"This module is a decision module, deciding the final action based on the evaluation result, whether complete or wrong or go on",
            "Output":answer
        }
        self.model.log_json["@Module"].append(log_info)
        self.model.log_json["@Successive_Page"]=self.model.next_model.screen.semantic_info_str
        with open("logs/log{}.json".format(self.model.index), "w") as f:
            print("· log{} generated".format(self.model.index))
            print(self.model.log_json)
            json.dump(self.model.log_json, f, indent=4)
        if answer["status"] == "wrong":
            with open("./src/KB/errors.csv", "w") as f:
                f.write("{},{},{},{}".format(str(self.model.task), self.model.current_path_str.replace("\n","").replace(",","::"), new_screen.semantic_info_str.replace("\n","").replace(",","::"),answer["reason"].replace("\n","").replace(","," ")))
        if answer["status"] == "completed":
            # task.json
            with open("./src/KB/task.json", "r") as f:
                task_json = json.load(f)
                task_json[self.model.task] = self.model.current_path_str
        return answer["status"]

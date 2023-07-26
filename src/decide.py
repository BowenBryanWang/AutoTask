import json
import openai


class Decide:
    def __init__(self, model) -> None:
        """
        Initializes a Decide object with a given OpenAI model.

        Args:
            model (str): The name of the OpenAI model to use.
        """
        self.model = model
        

    def decide(self):
        """
        Uses the OpenAI model to generate a response to the prompt.

        Returns:
            str: The status of the decision made by the model.
        """
        self.prompt = [{
            "role": "system",
            "content": """You are a professor with in-depth knowledge of User Interface (UI) tasks and their action traces. You are assigned a specific UI task along with an action trace. Your task is to evaluate if the action trace aligns with the assigned task, categorizing the trace as: completion, exception, or not completed yet. Several examples of similar UI tasks are provided for your reference.
                Use the following steps to respond to user inputs. Fully restate each step before proceeding. i.e. "Step 1: Reason...".
                Step 1:Reason step-by-step about the relationship of  the action trace  and UI task either: partly completed, fully completed, a superset.
                Step 2:Reason step-by-step about whether the final action(s) in the trace deviate from the correct execution path for the given task ,which means if the trace goes on it will never complete the task anymore, described as "wrong".
                Step 3:Output a JSON object structured like: {"status": "completed" or "wrong" or "partly completed", "reason": reason for the decision}."""
        },
        {
            "role": "user",
            "content": """
            Task: Add a new contact called Steven
            Action Trace: ["Homepage of Whatsapp","Click on <Add>"]
            """
        },
        {
            "role": "assistant",
            "content": """
            Step 1: Reason about the relationship of the action trace and UI task:
Based on the provided UI task and action trace, we can evaluate their relationship as follows:
The UI task is to "Add a new contact called Steven." The action trace provided includes two steps: first, the user is on the "Homepage of WhatsApp," and second, the user "Clicks on <Add>."
Step 2: Reason about whether the final action(s) in the trace deviate from the correct execution path for the given task:
In the given action trace, we can see that the user has navigated to the "Homepage of WhatsApp." However, the trace does not include the remaining steps required to complete the task, such as entering the contact details and saving the new contact named "Steven." Therefore, the final action (clicking on "Add") is not sufficient to complete the task.
Step 3: Output a JSON object:
Based on the evaluation, the JSON object would be:
{"status": "partly completed", "reason": "The action trace only shows the user reaching the 'Homepage of WhatsApp' and clicking on 'Add.' However, it does not include the subsequent actions required to enter the contact details and save the new contact called 'Steven.' Thus, the task is only partly completed in the action trace."}
"""
        },
            {
            "role": "user",
            "content": """
            Task:{}
            Action trace:{}
            """.format(self.model.task, self.model.current_path_str)
        }]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.prompt,
            temperature=0.5,
        )
        # 提取回答当中的json部分
        answer = response["choices"][0]["message"]["content"]
        print(answer)
        answer = json.loads(answer[answer.find("{"):answer.find("}")+1])
        print(answer)
        print(answer["status"])
        print(answer["reason"])
        return answer["status"]

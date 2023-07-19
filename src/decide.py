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
            Examples:
            []
            Task:{}
            Action trace:{}
            """.format(self.model.task, self.model.current_path_str)
        }]

    def decide(self):
        """
        Uses the OpenAI model to generate a response to the prompt.

        Returns:
            str: The status of the decision made by the model.
        """
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=self.prompt,
            temperature=0.5,
        )
        # 提取回答当中的json部分
        answer = response["choices"][0]["message"]["content"]
        print(answer)
        answer = json.loads(answer[answer.find("{"):answer.find("}")+1])
        print(answer.status)
        print(answer.reason)
        return answer.status

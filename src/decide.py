import json
import openai
import os

from src.utility import GPT, decide_prompt

openai.api_key = os.getenv('OPENAI_API_KEY')


class Decide:
    def __init__(self, model) -> None:
        self.model = model

    def log_decorator(func):
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)  # 调用原始函数
            # 在原始函数执行完毕后执行以下代码
            self.model.log_json["@Module"].append({
                "Name": "Decide",
                "Description": "This module is a decision module, deciding the final action based on the evaluation result, whether complete or wrong or go on",
                "Output": self.answer
            })
            self.model.log_json["@Successive_Page"] = self.model.next_model.screen.semantic_info_str
            if not os.path.exists("logs/log{}.json".format(self.model.index)):
                os.mkdir("logs/log{}.json".format(self.model.index))
                with open("logs/log{}.json".format(self.model.index), "w") as f:
                    json.dump(self.model.log_json, f, indent=4)
            return result  # 返回原始函数的结果（如果有的话）
        return wrapper

    @log_decorator
    def decide(self, new_screen, ACTION_TRACE):
        print("___________________________decide___________________________")

        self.answer = GPT(decide_prompt(
            self.model.task, ACTION_TRACE, new_screen.semantic_info))
        self.model.wrong_reason = self.answer["reason"]
        if self.answer["status"] == "completed":

            with open("./src/KB/task.json", "r") as f:
                task_json = json.load(f)
                task_json[self.model.task] = self.model.current_path_str
        return self.answer["status"]

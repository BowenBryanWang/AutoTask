import csv
import json
import openai
import os

from src.utility import GPT, Knowledge_prompt, decide_prompt
from page.init import Screen

openai.api_key = os.getenv('OPENAI_API_KEY')


class Decide:
    def __init__(self, model) -> None:
        self.model = model

    def log_decorator(func):
        print("___________________________decide___________________________")

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
        prompt = decide_prompt(
            self.model.task, self.model.prev_model.current_action if self.model.prev_model else "", ACTION_TRACE, new_screen.semantic_info_all_warp, self.model.decision_knowledge)
        if flag == "debug":
            prompt.append({"role": "user",
                           "content": """请注意以下特殊的额外信息：
现在你处于回溯纠错阶段，这意味着在ACTION_TRACE当中最后若干步骤执行后因不符合任务要求导致被回溯才到达此页面，作为决策模块，你需要判断是否继续在当前UI上进行探索，如果是，请输出status为“go on”；如果不是（即无法继续，需要继续往前回溯），请输出“wrong”。
为此，请仔细分析ACTION_TRACE中的每步操作，和每步操作进入的新页面的信息，特别是回溯导致的信息，判断在该页面上是否继续探索。
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

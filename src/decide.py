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
        task, knowledge = self.model.Decision_KB.find_experiences(
            query=[self.model.task, self.model.screen.page_description])
        prompt = decide_prompt(
            self.model.task, self.model.prev_model.current_action if self.model.prev_model else "", ACTION_TRACE, new_screen.semantic_info_all_warp, knowledge)
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
                if self.model.load:
                    self.extract_knowledge(ACTION_TRACE=ACTION_TRACE)
            return self.answer["status"]

    def extract_knowledge(self, ACTION_TRACE=None):
        with open("./src/KB/task/task.csv", "a", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow([self.model.task, [ACTION_TRACE[key]
                            for key in ACTION_TRACE.keys() if "Action_" in key]])
        response = GPT(Knowledge_prompt(
            TASK=self.model.task, ACTION_TRACE=ACTION_TRACE), tag="knowledge")
        selection_knowledge, decision_knowledge, error_knowledge = response.get(
            "selection"), response.get("decision"), response.get("error-handling")
        selection_path = os.path.join(os.path.dirname(
            __file__), "KB/selection/selection.csv")
        decision_path = os.path.join(os.path.dirname(
            __file__), "KB/decision/decision.csv")
        error_path = os.path.join(
            os.path.dirname(__file__), "KB/error/error.csv")

        self.write_knowledge_to_csv(selection_path, selection_knowledge)
        self.write_knowledge_to_csv(decision_path, decision_knowledge)
        self.write_knowledge_to_csv(error_path, error_knowledge)

    def write_knowledge_to_csv(self, file_path, knowledge_list):
        with open(file_path, "a", newline='', encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=',')
            for knowledge in knowledge_list:
                writer.writerow([self.model.task, knowledge])

import csv
import json
import openai
import os

from src.utility import GPT, Knowledge_prompt, decide_prompt

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
            self.model.log_json["@Successive_Page"] = self.model.next_model.screen.semantic_info_str

            with open("logs/log{}.json".format(self.model.index), "w", encoding="utf-8") as f:
                json.dump(self.model.log_json, f, indent=4)
            return result
        return wrapper

    @log_decorator
    def decide(self, new_screen, ACTION_TRACE):
        self.answer = GPT(decide_prompt(
            self.model.task, ACTION_TRACE, new_screen.semantic_info))
        self.model.wrong_reason = self.answer["reason"]
        if self.answer["status"] == "completed":
            self.extract_knowledge(
                ACTION_TRACE=ACTION_TRACE)
        return self.answer["status"]

    def extract_knowledge(self, ACTION_TRACE=None):
        with open("./src/KB/task.json", "r", encoding="utf-8") as f:
            task_json = json.load(f)
            task_json[self.model.task] = ACTION_TRACE.get("ACTION")
        response = GPT(Knowledge_prompt(
            TASK=self.model.task_description, ACTION_TRACE=ACTION_TRACE))
        selection_knowledge, decision_knowledge, error_knowledge = response.get(
            "selection"), response.get("decision"), response.get("error-handling")
        with open("./KB/selection.csv", "a", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            for knowledge in selection_knowledge:
                writer.writerow([
                    self.model.task_description,
                    knowledge
                ])
        with open("./KB/decision.csv", "a", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            for knowledge in decision_knowledge:
                writer.writerow([
                    self.model.task_description,
                    knowledge
                ])
        with open("./KB/error.csv", "a", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            for knowledge in error_knowledge:
                writer.writerow([
                    self.model.task_description,
                    knowledge
                ])

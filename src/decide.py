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
            self.model.log_json["@Successive_Page"] = self.model.next_model.screen.semantic_info_str

            with open("logs/log{}.json".format(self.model.index), "w", encoding="utf-8") as f:
                json.dump(self.model.log_json, f, indent=4)
            return result
        return wrapper

    @log_decorator
    def decide(self, new_screen: Screen, ACTION_TRACE: dict, flag: str):
        task, knowledge = self.model.Decision_KB.find_experiences(
            query=[self.model.task, self.model.screen.page_description])
        prompt = decide_prompt(
            self.model.task, ACTION_TRACE, new_screen.semantic_info, knowledge)
        if flag == "debug":
            prompt[0] = {"role": "system",
                         "content": """
You are a professor with in-depth knowledge of User Interface (UI) tasks. You are assigned a specific UI task, a history operation sequence, and the current UI (which is the result of the operation sequence).
You are now in a BACKTRACKING process, so you obtained additional information from subsequent operation steps and then backtrack to locate errors in History Operation Sequence.
Follow steps below and think step by step:
1, Pay attention to 'BACK' operation in the sequence and analyze each related screen information in "PAGES". Try to reproduce the sequence and locate key-error in the History Operation Sequence.
2, Think step by step on the ACTION_TRACE, If you believe the execution error actually happens on the Current UI and previous steps leading to Current UI do not have problems, and others options on Current UI can be explored to try to fulfill the task,output "Yes" finally in the JSON;
3, Think step by step on the ACTION_TRACE, If you think the EXPLORATIONs on Current UI are not going to fulfill the task and even no more better options on Current UI can be further explored, which means the error may lie in previous steps (Before Current UI) in the operation sequence, output "No" finally in the JSON;
(NOTE: as a error judger, you shouldn't be too strict to output "No", be tolerant about possible options on Current UI to be explored. Unless there are multiple tries or no better options to try then you should output "No")
Finally change original ouput JSON to:
{
    "status":"No" or "Yes"
    "reason":"...."(reason)
}"""}
        self.answer = GPT(prompt)
        if flag == "debug":
            self.model.wrong_reason = self.answer["reason"]
            return self.answer["status"]
        else:
            self.model.wrong_reason = self.answer["reason"]
            if self.answer["status"] == "completed":
                self.extract_knowledge(
                    ACTION_TRACE=ACTION_TRACE)
            return self.answer["status"]

    def extract_knowledge(self, ACTION_TRACE=None):
        with open("./src/KB/task/task.csv", "a", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow([self.model.task, ACTION_TRACE["ACTION"]])
        response = GPT(Knowledge_prompt(
            TASK=self.model.task, ACTION_TRACE=ACTION_TRACE))
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

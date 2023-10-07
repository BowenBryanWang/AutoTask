import json
import os
import numpy as np
import openai
from src.utility import GPT, Task_UI_grounding_prompt, plan_prompt, process_action_info
openai.api_key = os.getenv('OPENAI_API_KEY')


class Evaluate():

    def __init__(self, model):
        self.model = model
        self.score = []
        self.reason = []
        self.weights = []

    @staticmethod
    def log_decorator(func):
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)  # 调用原始函数
            # 在原始函数执行完毕后执行以下代码
            self.model.log_json["@Previous_Step"] = self.model.current_path_str
            self.model.log_json["@Action"] = self.model.current_action
            self.model.log_json["@Module"].append({
                "Name": "Evaluate",
                "Description": "This module is an evaluation module, evaluating the selected components of their contribution to fulfilling the user's intent",
                "Output": {key: item for key, item in zip(self.model.screen.semantic_info_list, self.score)},
            })
            if not os.path.exists("logs"):
                os.mkdir("logs")
                with open("logs/log{}.json".format(self.model.index), "w", encoding="utf-8") as f:
                    json.dump(self.model.log_json, f, indent=4)
            print("node_selected", self.model.node_selected)
            print("node_selected_id", self.model.node_selected_id)
            print(self.model.final_node.generate_all_semantic_info())
            return result  # 返回原始函数的结果（如果有的话）
        return wrapper

    @log_decorator
    def evaluate(self):
        self.score_comp()
        self.select_top_one()
        return self.score

    def score_comp(self):
        resp = GPT(Task_UI_grounding_prompt(self.model.task, self.model.current_path_str, self.model.similar_tasks,
                   self.model.similar_traces, self.model.predicted_step, self.model.screen.semantic_info_list, self.model.predict_module.next_comp))
        self.score, self.reason = np.array(resp["score"])/10, resp["reason"]
        if self.weights == []:
            self.weights = [1] * len(self.score)
        self.score = np.exp(self.score) / np.sum(np.exp(self.score))
        print(self.score)
        print(self.weights)
        self.score = (self.score * np.array(self.weights)
                      ).tolist() if self.weights != [] else self.score
        print(self.score)

    def select_top_one(self):
        self.model.node_selected = self.model.screen.semantic_info_list[np.argmax(
            self.score)]
        response = GPT(plan_prompt(self.model.task,
                       self.model.page_description, self.model.node_selected))
        self.model.node_selected_action, self.model.node_selected_text = response.get(
            "action"), response.get("text")
        self.model.node_selected_id = int(
            self.model.node_selected.split("id=")[1].split(" ")[0])
        self.model.current_action = process_action_info(
            self.model.node_selected_action, self.model.node_selected_text, self.model.node_selected)
        self.model.current_path.append(self.model.current_action)
        self.model.final_node = self.model.screen.semantic_nodes[
            "nodes"][self.model.node_selected_id - 1]

    def update_weights(self, weights):
        w = [0]*len(self.model.screen.semantic_info_list)
        for key, item in weights.items():
            if key.startswith("id_"):
                index = int(key.split("_")[1]) - 1
                w[index] = int(item)
        self.weights = (np.array(self.weights) *
                        np.array([(10-i)/10 for i in w])).tolist()

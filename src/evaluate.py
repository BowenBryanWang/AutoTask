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

    def log_decorator(self, func):
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
            print("node_selected", self.model.node_selected)
            print("node_selected_id", self.model.node_selected_id)
            return result  # 返回原始函数的结果（如果有的话）
        return wrapper
    
    @log_decorator
    def evaluate(self):
        resp = GPT(Task_UI_grounding_prompt(self.model.task, self.model.current_path_str, self.model.similar_tasks,self.model.similar_traces, self.model.predicted_step, self.model.screen.semantic_info_list, self.model.predict_module.next_comp))
        self.score, self.reason = resp["score"], resp["reason"]
        self.score = self.score * self.weights if self.weights else self.score
        self.model.node_selected = self.model.screen.semantic_info_list[np.argmax(self.score)]
        response = GPT(plan_prompt(self.model.task,self.model.page_description, self.model.node_selected))
        self.model.node_selected_action, self.model.node_selected_text = response.get("action"), response.get("text")
        self.model.node_selected_id = int(self.model.node_selected.split("id=")[1].split(" ")[0])
        self.model.current_action = process_action_info(self.model.node_selected_action, self.model.node_selected_text, self.model.node_selected)
        self.model.current_path.append(self.model.current_action)
        return self.score

    def update_weights(self, weights):
        self.update_weights = [(10-i)/10 for i in weights]




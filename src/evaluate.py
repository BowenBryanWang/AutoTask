import copy
import json
import os
import numpy as np
import openai
from src.embedding import sort_by_similarity
from src.utility import GPT, Task_UI_grounding_prompt, get_top_combined_similarities, plan_prompt, process_action_info
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
            result = func(self, *args, **kwargs)
            self.model.log_json["@Previous_Step"] = self.model.current_path_str
            self.model.log_json["@Action"] = self.model.current_action
            self.model.log_json["@Module"].append({
                "Name": "Evaluate",
                "Description": "This module is an evaluation module, evaluating the selected components of their contribution to fulfilling the user's intent",
                "Output": {key: item for key, item in zip(list(
                    filter(lambda x: "id=" in x, self.model.screen.semantic_info_list)), self.original_score)},
            })

            with open("logs/log{}.json".format(self.model.index), "w", encoding="utf-8") as f:
                json.dump(self.model.log_json, f, indent=4)
            print("node_selected", self.model.node_selected)
            print("node_selected_id", self.model.node_selected_id)
            print(self.model.final_node.generate_all_semantic_info())
            return result
        return wrapper

    @log_decorator
    def evaluate(self, ACTION_TRACE):
        if self.score_comp(ACTION_TRACE) == "wrong":
            self.model.currecnt_action = "Back"
            return "wrong"
        self.select_top_one()
        return self.score

    def score_comp(self, ACTION_TRACE):
        task, knowledge = self.model.Selection_KB.find_experiences(
            query=[self.model.task, self.model.screen.page_description])
        prompt = Task_UI_grounding_prompt(self.model.task, [ACTION_TRACE[key]
                                                            for key in ACTION_TRACE.keys() if "Action" in key], self.model.similar_tasks,
                                          self.model.similar_traces, self.model.predicted_step, self.model.screen.semantic_info_list, self.model.predict_module.comp_json_simplified, knowledge)
        similarity = sort_by_similarity(
            """You are a mobile UI expert acting as a "Judger". Your specialized role focuses on guiding the user to complete the user task on specific UI screen.
Your job is to choose the next UI element to be operated considering the user task, the history operation sequence, and the current UI. You should rate the available UI elements on the current page.

Task: "enable phone call & SMS for the user named Alice".
History operation sequence: {}.
Current UI:{}
Please output the next element to be operated.""".format([ACTION_TRACE[key] for key in ACTION_TRACE.keys() if "Action" in key],list(
                filter(lambda x: "id=" in x, self.model.screen.semantic_info_list))), list(
                filter(lambda x: "id=" in x, self.model.screen.semantic_info_list)))
        similarity = np.array([x[1] for x in similarity])
        resp = GPT(prompt)

        # self.score, self.reason = np.array(resp["score"])/10, resp["reason"]
        self.next_step = resp.get("next_steps")
        scores = [1.0 for x in self.model.screen.semantic_info_list if 'id=' in x]
        for key, rating in resp.items():
            if key.startswith('id_'):
                idx = int(key[len('id_'):]) - 1
                scores[idx] = rating
        # if not isinstance(self.score, list) and self.score.size > 0:
        #     indices = [index for index, value in enumerate(
        #         self.weights) if value != 1.0]
        #     if indices:
        #         for i, s in enumerate(scores):
        #             if i not in indices:
        #                 self.score[i] = s
        #     else:
        #         self.score = np.array(scores) / 10
        # else:
        self.score = (np.array(scores)+similarity) / 10

        self.score = (self.score * np.array(self.weights)
                      ).tolist() if self.weights != [] else self.score
        self.original_score = copy.deepcopy(self.score)
        if all(value < 0.2 for value in self.score) and self.model.prev_model:
            return "wrong"
        if self.weights == []:
            self.weights = [1.0] * len(self.score)
        self.score = np.exp(self.score) / np.sum(np.exp(self.score))
        print(self.score)
        print(self.weights)

        print(self.score)

    def select_top_one(self):
        top_index = np.argmax(self.score)
        self.model.node_selected = list(filter(
            lambda x: "id="+str(top_index+1) in x, self.model.screen.semantic_info_list))[0]
        if 'editable' in self.model.node_selected and 'ineditable' not in self.model.node_selected:
            response = GPT(plan_prompt(self.model.task,
                                       self.model.page_description, self.model.node_selected, self.next_step))
            self.model.node_selected_action, self.model.node_selected_text = response.get(
                "action"), response.get("text")
        else:
            self.model.node_selected_action, self.model.node_selected_text = (
                'click', None)
        self.model.node_selected_id = int(
            self.model.node_selected.split("id=")[1].split(" ")[0])
        self.model.current_action = process_action_info(
            self.model.node_selected_action, self.model.node_selected_text, self.model.node_selected)
        self.model.current_path.append(self.model.current_action)
        self.model.final_node = self.model.screen.semantic_nodes["nodes"][self.model.screen.semantic_info_list.index(
            self.model.node_selected)]

    def update_weights(self, weights):
        w = [0]*len(list(
            filter(lambda x: "id=" in x, self.model.screen.semantic_info_list)))
        for key, item in weights.items():
            if key.startswith("id_"):
                index = int(key.split("_")[1]) - 1
                w[index] = int(item)
        self.weights = (np.array(self.weights) *
                        np.array([(10-i)/10 for i in w])).tolist()

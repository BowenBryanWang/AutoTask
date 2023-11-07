
import copy
import csv
import json
import os
import pickle
from typing import Optional

import pandas as pd
from Graph import Edge, Node


from src.utility import generate_perform, process_string, simplify_ui_element

from .knowledge import Decision_KB, Error_KB, Selection_KB, Task_KB, retrivel_knowledge
from src.decide import Decide
from src.evaluate import Evaluate
from src.feedback import Feedback
from page.init import Screen
from src.predict import Predict


class Model:

    def update_infos(self, s):
        for k in self.screen.semantic_info_all_warp:
            if s in k:
                k = k.replace(s, s+" --New")

    def cal_diff(self):
        if self.prev_model is None:
            return
        else:
            new_elements = list(
                filter(lambda x: x not in self.prev_model.screen.semantic_info_half_warp, self.screen.semantic_info_half_warp))
            old_elements = list(
                filter(lambda x: x in self.prev_model.screen.semantic_info_half_warp, self.screen.semantic_info_half_warp))
            if len(new_elements) / len(self.screen.semantic_info_half_warp) > 0.8:
                return
            new_elements_index = [self.screen.semantic_info_half_warp.index(
                x) for x in new_elements]
            for i in new_elements_index:
                self.update_infos(self.screen.semantic_info_half_warp[i])
            self.screen.semantic_diff = new_elements_index

    def __init__(self, screen: Screen = None, description: str = "", prev_model=None, index: int = 0, LOAD=False):
        self.load: bool = LOAD
        self.index: int = index  # Index of current Model
        if screen is not None:
            self.screen: Screen = screen  # Current Screen

        self.task: str = description  # User's Task
        self.node_selected: str = None  # HTML format of the top UI element selected
        self.node_selected_id: int = 0  # id of the top UI element selected
        self.current_action: str = ""  # the lastest action of this model
        self.log_json: dict = {}

        self.prev_model = prev_model
        if prev_model is not None:
            prev_model.next_model = self
            self.current_path: list[str] = copy.deepcopy(
                self.prev_model.current_path)
        else:
            self.current_path: list[str] = [self.screen.page_description]

        self.next_model = None

        self.Task_KB = Task_KB()
        self.Error_KB = Error_KB()
        self.Decision_KB = Decision_KB()
        self.Selection_KB = Selection_KB()
        self.similar_tasks, self.similar_traces = self.Task_KB.find_most_similar_tasks(
            self.task)
        self.predict_module = Predict(self)
        self.evaluate_module = Evaluate(self)
        self.decide_module = Decide(self)
        self.feedback_module = Feedback(self)
        self.long_term_UI_knowledge = None
        self.simplified_semantic_info_no_warp = list(
            map(lambda x: simplify_ui_element(x), self.screen.semantic_info_no_warp))
        self.cal_diff()
        self.node_in_graph: Node = Node(self.screen)
        self.edge_in_graph: Edge = None
        self.wrong_reason: str = ""
        print("________________INITIAL_DONE________________")

    @property
    def current_path_str(self):
        return " -> ".join(self.current_path)

    def decide_before_and_log(func):
        def wrapper(self, *args, **kwargs):
            print("ACTION_TRACE", kwargs.get("ACTION_TRACE"))
            print("flag", kwargs.get("flag"))
            if self.load:
                self.prediction_knowledge = retrivel_knowledge(self.model.task, "prediction", list(
                    map(simplify_ui_element, self.model.screen.semantic_info_half_warp)))
                self.evaluation_knowledge = retrivel_knowledge(self.model.task, "selection", list(
                    map(simplify_ui_element, self.model.screen.semantic_info_half_warp)))
                self.decision_knowledge = retrivel_knowledge(self.model.task, "decision", list(
                    map(simplify_ui_element, self.model.screen.semantic_info_half_warp)))
            else:
                self.prediction_knowledge = None
                self.evaluation_knowledge = None
                self.decision_knowledge = None
            if self.prev_model is not None and kwargs.get("flag") != "debug":
                status = self.prev_model.decide_module.decide(
                    new_screen=self.screen, ACTION_TRACE=kwargs.get("ACTION_TRACE"), flag="normal")
                if status == "wrong":
                    print("wrong: feedback started")
                    if self.prev_model.node_selected_action == "scroll_forward":
                        return generate_perform("scroll_backward", absolute_id=self.prev_model.final_node.absolute_id), "wrong"
                    return {"node_id": 1, "trail": "[0,0]", "action_type": "back"}, "wrong"
                elif status == "completed":
                    return None, "completed"
            if self.prev_model is not None and kwargs.get("flag") == "debug":
                status = self.prev_model.decide_module.decide(
                    new_screen=self.screen, ACTION_TRACE=kwargs.get("ACTION_TRACE"), flag="debug")
                if status == "wrong":
                    print("wrong: feedback started")
                    if self.prev_model.node_selected_action == "scroll_forward":
                        return generate_perform("scroll_backward", absolute_id=self.prev_model.final_node.absolute_id), "wrong"
                    return {"node_id": 1, "trail": "[0,0]", "action_type": "back"}, "wrong"
            self.log_json["@User_intent"] = self.task
            self.log_json["@Page_components"] = self.screen.semantic_info_all_warp
            self.log_json["@Module"] = []
            return func(self, *args, **kwargs)
        return wrapper

    @decide_before_and_log
    def work(self, ACTION_TRACE=None, flag="normal"):

        self.predict_module.predict(ACTION_TRACE)
        eval_res = self.evaluate_module.evaluate(ACTION_TRACE)
        if isinstance(eval_res, str) and eval_res == "wrong":
            print("wrong: feedback started")
            return {"node_id": 1, "trail": "[0,0]", "action_type": "back"}, "wrong"
        return self.execute()

    def execute(self):
        node = self.final_node
        if self.node_selected_action == "click":
            center_x = (node.bound[0] + node.bound[2]) // 2
            center_y = (node.bound[1] + node.bound[3]) // 2
            perform = generate_perform("click", center_x, center_y)
            print(perform)
            return perform, "Execute"
        elif self.node_selected_action == "edit":
            perform = generate_perform(
                "text", text=self.node_selected_text, absolute_id=node.absolute_id)
            print(perform)
            return perform, "Execute"
        elif self.node_selected_action == "scroll_forward":
            perform = generate_perform(
                "scroll_forward", absolute_id=node.absolute_id)
            print(perform)
            return perform, "Execute"

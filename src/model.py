
import copy
import csv
import json
import os
from typing import Optional

import pandas as pd
from Graph import Node


from src.utility import generate_perform, process_string, simplify_ui_element

from .knowledge import Decision_KB, Error_KB, PageJump_KB, Selection_KB, Task_KB
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
            # if len(new_elements) / len(self.screen.semantic_info_half_warp) > 0.8:
            #     return
            new_elements_index = [self.screen.semantic_info_half_warp.index(
                x) for x in new_elements]
            for i in new_elements_index:
                self.update_infos(self.screen.semantic_info_half_warp[i])
            self.screen.semantic_diff = new_elements_index

    def __init__(self, screen: Optional[Screen] = None, description: str = "", prev_model=None, index=0):
        self.index: int = index  # Index of current Model
        if screen is not None:
            self.screen: Screen = screen  # Current Screen

        self.task: str = description  # User's Task
        self.candidate: list[int] = []
        self.candidate_str: list[str] = []
        self.candidate_action: list[str] = [None]*5
        self.candidate_text: list[str | None] = [None]*5
        self.node_selected = None
        self.node_selected_id: int = 0
        self.current_path: list[str] = []
        self.log_json: dict = {}

        self.prev_model = prev_model
        if prev_model is not None:
            self.prev_model = prev_model
            prev_model.next_model = self
            self.current_path = copy.deepcopy(self.prev_model.current_path)
        else:
            self.current_path = [self.screen.page_description]

        self.next_model = None

        self.PageJump_KB = PageJump_KB(None)
        self.Task_KB = Task_KB()
        self.Error_KB = Error_KB()
        self.Decision_KB = Decision_KB()
        self.Selection_KB = Selection_KB()
        self.similar_tasks, self.similar_traces = self.Task_KB.find_most_similar_tasks(
            self.task)
        self.predict_module = Predict(self, self.PageJump_KB)
        self.evaluate_module = Evaluate(self)
        self.decide_module = Decide(self)
        self.feedback_module = Feedback(self)
        self.long_term_UI_knowledge = None
        self.simplified_semantic_info_no_warp = list(
            map(lambda x: simplify_ui_element(x), self.screen.semantic_info_no_warp))
        self.cal_diff()
        self.node_in_graph: Node = Node(self.screen)
        self.wrong_reason: str = ""
        print("________________INITIAL_DONE________________")

    @property
    def current_path_str(self):
        return " -> ".join(self.current_path)

    def save_short_term_UI_knowledge(self):
        with open("./src/KB/pagejump/pagejump.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=',')
            prev_info = process_string(
                self.prev_model.screen.page_root.generate_all_text())
            prev_path = process_string(self.prev_model.node_selected_warp)
            prev_act = process_string(
                self.prev_model.node_selected_action)
            prev_para = process_string(
                self.prev_model.node_selected_text)
            current_info = process_string(
                self.screen.page_root.generate_all_text()),
            flag = any(row[0] == prev_info and row[1]
                       == prev_path for row in reader)
        if not flag:
            with open("./src/KB/pagejump/pagejump.csv", "a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=',')
                writer.writerow([
                    prev_info,
                    prev_path,
                    prev_act,
                    prev_para,
                    current_info,
                ])

    def save_long_term_UI_knowledge(self):
        node_list = []
        m = self.prev_model
        while m:
            node_list.append(m.node_selected)
            m = m.prev_model
        node_list = node_list[::-1]
        if not os.path.exists(os.path.join(os.path.dirname(__file__), "KB/pagejump/pagejump_long.json")):
            os.mkdir(os.path.join(os.path.dirname(__file__),
                     "KB/pagejump/pagejump_long.json"))
        with open(os.path.join(os.path.dirname(__file__), "KB/pagejump/pagejump_long.json"), 'r+', encoding="utf-8") as f:
            js = json.loads(f.read())
        with open(os.path.join(os.path.dirname(__file__), "KB/pagejump/pagejump_long.json"), 'w', encoding="utf-8") as f:
            for node in self.screen.semantic_info_no_warp:
                js[node] = node_list + [node]
            json.dump(js, f, indent=4)

    def decide_before_and_log(func):
        def wrapper(self, *args, **kwargs):
            print("ACTION_TRACE", kwargs.get("ACTION_TRACE"))
            print("flag", kwargs.get("flag"))
            if self.prev_model is not None and kwargs.get("flag") != "debug":
                self.save_short_term_UI_knowledge()
                self.save_long_term_UI_knowledge()
                status = self.prev_model.decide_module.decide(
                    new_screen=self.screen, ACTION_TRACE=kwargs.get("ACTION_TRACE"), flag="normal")
                if status == "wrong":
                    print("wrong: feedback started")
                    if self.prev_model.node_selected_action == "scroll_forward":
                        return generate_perform("scroll_backward", absolute_id=self.prev_model.final_node.absolute_id)
                    return {"node_id": 1, "trail": "[0,0]", "action_type": "back"}, "wrong"
                elif status == "completed":
                    return None, "completed"
            if self.prev_model is not None and kwargs.get("flag") == "debug":
                status = self.prev_model.decide_module.decide(
                    new_screen=self.screen, ACTION_TRACE=kwargs.get("ACTION_TRACE"), flag="debug")
                if status == "wrong":
                    print("wrong: feedback started")
                    return {"node_id": 1, "trail": "[0,0]", "action_type": "back"}, "wrong"
            self.log_json["@User_intent"] = self.task
            self.log_json["@Page_components"] = self.screen.semantic_info_no_warp
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


import copy
import time
from typing import Optional

import tqdm

from .knowledge import Error_KB, PageJump_KB, Task_KB
from src.decide import Decide
from src.evaluate import Evaluate
from src.feedback import Feedback
from page.init import Screen
from src.predict import Predict
import json


class Model:

    def __init__(self, screen: Optional[Screen] = None, description: str = "", prev_model=None, index=0):
        """
        Initializes a Model object with the given screen and description.

        Args:
        - screen: A Screen object representing the current screen information.
        - description: A string representing the task description.
        - prev_model: A Model object representing the previous model.

        Returns:
        None
        """
        #####################################################
        # 1. Common variables
        self.index: int = index  # 当前model的索引
        if screen is not None:
            self.screen = screen  # Screen类，用于存储界面信息
        self.task: str = description  # 任务描述
        self.candidate: list[int] = []  # 用于存储候选的控件,首次应该在suggest中初始化
        self.candidate_str: list[str] = []  # 用于存储候选的控件的字符串表示
        self.candidate_action: list[str] = [None]*5  # plan模块当中对于候选控件的动作
        self.candidate_text: list[str | None] = [None]*5  # plan模块当中对于候选控件的动作参数
        self.node_selected = None  # 用于存储被选择的控件
        self.node_selected_id: int = 0  # 用于存储被选择的控件的id
        self.current_path: list[str] = []  # 用于存储当前的路径
        self.log_json: dict = {}  # 用于存储日志信息
        #####################################################

        #####################################################
        # 2. Take Model as Node for Computational Graph
        self.prev_model = prev_model
        if prev_model is not None:
            self.prev_model = prev_model
            prev_model.next_model = self
            self.current_path = copy.deepcopy(self.prev_model.current_path)
            self.current_path_str = copy.deepcopy(
                self.prev_model.current_path_str)
        else:
            self.current_path = [self.screen.page_description]
            self.current_path_str = self.screen.page_description
        self.next_model = None
        #####################################################

        #####################################################
        # 3. Submodules
        # self.database = Database(
        #     user="root", password="wbw12138zy,.", host="127.0.0.1", database="GUI_LLM")
        print("· database connected")
        self.PageJump_KB = PageJump_KB(None)

        print("· pagejump_kb initialized")
        self.Task_KB = Task_KB()
        self.Error_KB = Error_KB()
        self.similar_tasks, self.similar_traces = self.Task_KB.find_most_similar_tasks(
            self.task)
        self.error_experiences = self.Error_KB.find_experiences(self.task)
        print("· task_kb initialized")
        self.predict_module = Predict(self, self.PageJump_KB)
        print("· predict module initialized")
        self.evaluate_module = Evaluate(self)
        print("· evaluate module initialized")
        self.decide_module = Decide(self)
        print("· decide module initialized")
        self.feedback_module = Feedback(self)
        print("· modules initialized")
        #####################################################
        
    @property
    def current_path_str(self):
        return " -> ".join(self.current_path)
    

    def work(self,ACTION_TRACE = None):
        if self.prev_model is not None:
            status = self.prev_model.decide_module.decide(self.screen,ACTION_TRACE)
            if status == "wrong":
                print("wrong: feedback started")
                return {"node_id": 1, "trail": "[0,0]", "action_type": "back"}, "wrong"
            elif status == "completed":
                return None,"completed"

        self.log_json["@User_intent"] = self.task
        self.log_json["@Page_components"] = self.screen.semantic_info_list
        self.log_json["@Module"] = []

        self.predict_module.predict()
        if self.prev_model is not None:
            with open("./src/KB/pagejump.csv", "a") as f:
                f.write("{},{},{},{}\n".format(self.prev_model.screen.semantic_info_str.replace('\n', '').replace(",", ";;"), self.prev_model.current_path[-1].replace(
                    '\n', '').replace(",", ";;"), self.screen.semantic_info_str.replace('\n', '').replace(",", ";;"), self.page_description))
        self.evaluate_module.evaluate()


        nodes = self.screen.semantic_nodes["nodes"]
        if self.node_selected_id > 0 and self.node_selected_id <= len(nodes):
            node = nodes[self.node_selected_id - 1]
            print(self.node_selected_id - 1)
            print(node.generate_all_semantic_info())
            if self.node_selected_action == "click":
                center = {"x": (
                    node.bound[0] + node.bound[2]) // 2, "y": (node.bound[1] + node.bound[3]) // 2}
                perform = {"node_id": 1, "trail": "[" + str(center["x"]) + "," + str(
                    center["y"]) + "]", "action_type": "click"}
                print(perform)
                return perform, "Execute"
            elif self.node_selected_action == "edit":
                perform = {"node_id": 1, "trail": "[0,0]", "action_type": "text",
                            "text": self.node_selected_text, "ori_absolute_id": node.absolute_id}
                print(perform)
                return perform, "Execute"
        else:
            raise Exception("Invalid node_selected_id")


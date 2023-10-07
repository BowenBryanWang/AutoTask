
import copy
import csv
from typing import Optional


from src.utility import generate_perform, process_string

from .knowledge import Error_KB, PageJump_KB, Task_KB
from src.decide import Decide
from src.evaluate import Evaluate
from src.feedback import Feedback
from page.init import Screen
from src.predict import Predict


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
        else:
            self.current_path = [self.screen.page_description]

        self.next_model = None
        #####################################################

        #####################################################

        self.PageJump_KB = PageJump_KB(None)
        self.Task_KB = Task_KB()
        self.Error_KB = Error_KB()
        self.similar_tasks, self.similar_traces = self.Task_KB.find_most_similar_tasks(
            self.task)
        self.error_experiences = self.Error_KB.find_experiences(self.task)
        self.predict_module = Predict(self, self.PageJump_KB)
        self.evaluate_module = Evaluate(self)
        self.decide_module = Decide(self)
        self.feedback_module = Feedback(self)
        print("________________INITIAL_DONE________________")
        #####################################################

    @property
    def current_path_str(self):
        return " -> ".join(self.current_path)

    def decide_before_and_log(func):
        def wrapper(self, *args, **kwargs):
            if self.prev_model is not None:
                with open("./src/KB/pagejump.csv", "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    prev_info = process_string(
                        self.prev_model.screen.semantic_info_str)
                    prev_path = process_string(
                        self.prev_model.current_path[-1])
                    flag = any(row[0] == prev_info and row[1]
                               == prev_path for row in reader)

                if not flag:
                    with open("./src/KB/pagejump.csv", "a", newline='', encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            prev_info,
                            prev_path,
                            process_string(self.screen.semantic_info_str),
                            self.page_description
                        ])
                status = self.prev_model.decide_module.decide(
                    self.screen, kwargs.get("ACTION_TRACE"))
                if status == "wrong":
                    print("wrong: feedback started")
                    return {"node_id": 1, "trail": "[0,0]", "action_type": "back"}, "wrong"
                elif status == "completed":
                    return None, "completed"
            self.log_json["@User_intent"] = self.task
            self.log_json["@Page_components"] = self.screen.semantic_info_list
            self.log_json["@Module"] = []
            result = func(self, *args, **kwargs)
            return result
        return wrapper

    @decide_before_and_log
    def work(self, ACTION_TRACE=None):
        self.predict_module.predict()
        self.evaluate_module.evaluate()
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

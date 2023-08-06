
import copy
from typing import Optional
from .database import Database
from .knowledge import PageJump_KB, Task_KB
from src.decide import Decide
from src.evaluate import Evaluate
from src.feedback import Feedback
from page.init import Screen
from src.predict import Predict
from src.suggest import Suggest


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
        self.current_path_str: str = ""  # 用于存储当前的路径的字符串表示
        #####################################################

        #####################################################
        # 2. Take Model as Node for Computational Graph
        if prev_model is not None:
            self.prev_model = prev_model
            prev_model.next_model = self
            self.current_path = copy.deepcopy(self.prev_model.current_path)
            self.current_path_str = copy.deepcopy(self.prev_model.current_path_str)
        else:
            self.current_path = [self.screen.page_description]
            self.current_path_str = self.screen.page_description
        self.next_model = None
        #####################################################

        #####################################################
        # 3. Submodules
        self.database = Database(
            user="root", password="wbw12138zy,.", host="127.0.0.1", database="GUI_LLM")
        print("· database connected")
        self.PageJump_KB = PageJump_KB(None)
        
        print("· pagejump_kb initialized")
        self.Task_KB = Task_KB()
        self.similar_tasks,self.similar_traces = self.Task_KB.find_most_similar_tasks(self.task)
        print("· task_kb initialized")
        self.predict_module = Predict(self, self.PageJump_KB)
        print("· predict module initialized")
        self.suggest_module = Suggest(self)
        print("· suggest module initialized")
        self.evaluate_module = Evaluate(self)
        print("· evaluate module initialized")
        self.decide_module = Decide(self)
        print("· decide module initialized")
        self.feedback_module = Feedback(self)
        print("· modules initialized")
        #####################################################

    def work(self):
        """
        This method represents the main loop of the model.

        @description:
        This function works as follows:
        - Call the predict method of the predict module to predict the next screen.
        - Call the suggest method of the suggest module to suggest candidate items.
        - Call the evaluate method of the evaluate module to evaluate the candidate items.
        - Call the decide method of the decide module to decide the next screen.
        - Call the feedback method of the feedback module to provide feedback to the model.
        """
        if self.prev_model:
            status = self.prev_model.decide_module.decide(self.screen)
            if status == "completed":
                return "completed"
            elif status == "wrong":
                # self.prev_model.feedback_module.feedback()
                print("wrong: feedback started")
                return "wrong"
        if self.screen is None:
            raise Exception("No Screen input")
        if self.task == "":
            raise Exception("No task description input")
        self.predict_module.predict()
        self.suggest_module.suggest()
        self.suggest_module.plan()
        self.evaluate_module.evaluate()
        node = self.screen.semantic_nodes["nodes"][self.node_selected_id-1]
        print(self.node_selected_id-1)
        print(node.generate_all_semantic_info())
        center = {"x": (node.bound[0]+node.bound[2]) //
                    2, "y": (node.bound[1]+node.bound[3])//2}
        perform = {
            "node_id": 1, "trail": "["+str(center["x"])+","+str(center["y"])+"]", "action_type": "click"}
        print(perform)
        return perform
        

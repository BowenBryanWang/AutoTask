
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

    def __init__(self, screen: Optional[Screen] = None, description: str = "", prev_model=None):
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
        if screen is not None:
            self.screen = screen  # Screen类，用于存储界面信息
        self.task = description  # 任务描述
        self.candidate = []  # 用于存储候选的控件,首次应该在suggest中初始化
        self.node_selected = None  # 用于存储用户选择的控件
        self.node_selected_id: int = 0  # 用于存储用户选择的控件的id
        #####################################################

        #####################################################
        # 2. Take Model as Node for Computational Graph
        if prev_model is not None:
            self.prev_model = prev_model
            prev_model.next_model = self
            self.current_path = self.prev_model.current_path.copy().append(
                self.screen.page_description)
            self.current_path_str = self.prev_model.current_path_str + \
                self.screen.page_description
            self.index = self.prev_model.index + 1
        else:
            self.index = 0
            self.current_path = [self.screen.page_description]
            self.current_path_str = self.screen.page_description
        self.next_model = None
        #####################################################

        #####################################################
        # 3. Submodules
        self.database = Database(
            user="root", password="wbw12138zy,.", host="127.0.0.1", database="GUI_LLM")
        self.PageJump_KB = PageJump_KB(self.database)
        self.Task_KB = Task_KB(self.database)
        self.predict_module = Predict(self, self.PageJump_KB)
        self.predict_module.predict()
        self.suggest_module = Suggest(self)
        self.evaluate_module = Evaluate(self)
        self.decide_module = Decide(self)
        self.feedback_module = Feedback(self)
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
        if self.screen is None:
            raise Exception("No Screen input")
        if self.task == "":
            raise Exception("No task description input")
        self.suggest_module.suggest()
        self.suggest_module.plan()
        self.evaluate_module.evaluate()
        s = self.decide_module.decide()
        if s == "completed":
            return "completed"
        elif s == "wrong":
            # self.feedback_module.feedback()
            return "wrong"
        elif s == "partly completed":
            node = self.screen.semantic_nodes["nodes"][self.node_selected_id-1]
            center = {"x": (node.bound[0]+node.bound[2]) //
                      2, "y": (node.bound[1]+node.bound[3])//2}
            perform = {
                "node_id": 1, "trail": "["+str(center["x"])+","+str(center["y"])+"]", "action_type": "click"}
            print(perform)
            return perform

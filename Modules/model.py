
import copy

from Graph import Edge, Node
from Modules.utility import generate_perform, simplify_ui_element
from .knowledge import Decision_KB, Error_KB, Selection_KB, Task_KB, retrivel_knowledge
from Modules.decide import Decide
from Modules.evaluate import Evaluate
from Modules.feedback import Feedback
from UI.init import Screen
from Modules.predict import Predict


class Model:
    """
    Model class for the AutoTask application.

    Attributes:
        load (bool): Indicates if the model is loaded with knowledge.
        index (int): The index of the current model in the workflow.
        screen (Screen): The current UI screen being processed.
        task (str): Description of the user's task.
        node_selected (str): HTML format of the top UI element selected.
        node_selected_id (int): ID of the top UI element selected.
        current_action (str): The latest action performed by this model.
        log_json (dict): Log data for the current model.
        prev_model (Model): Reference to the previous model.
        next_model (Model): Reference to the next model.
        Task_KB (Task_KB): Knowledge base for tasks.
        Error_KB (Error_KB): Knowledge base for errors.
        Decision_KB (Decision_KB): Knowledge base for decisions.
        Selection_KB (Selection_KB): Knowledge base for selections.
        similar_tasks (list): List of similar tasks.
        similar_traces (list): List of similar action traces.
        predict_module (Predict): Prediction module instance.
        evaluate_module (Evaluate): Evaluation module instance.
        decide_module (Decide): Decision module instance.
        feedback_module (Feedback): Feedback module instance.
        long_term_UI_knowledge: Long-term knowledge about the UI.
        simplified_semantic_info_no_warp (list): Simplified semantic information.
        node_in_graph (Node): Current node in the UI graph.
        edge_in_graph (Edge): Current edge in the UI graph.
        wrong_reason (str): Description of any error or wrong action.
        PER (float): Percentage of knowledge loaded.
    """

    def __init__(self, screen: Screen = None, description: str = "", prev_model=None, index: int = 0, LOAD=False, Graph=None, PER=0):
        self.load: bool = LOAD
        self.index: int = index
        if screen is not None:
            self.screen: Screen = screen

        self.task: str = description
        self.node_selected: str = None
        self.node_selected_id: int = 0
        self.current_action: str = ""
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
        self.node_in_graph: Node = Node(self.screen, Graph)
        self.edge_in_graph: Edge = None
        self.wrong_reason: str = ""
        self.PER = PER
        print("________________INITIAL_DONE________________")

    def update_infos(self, s):
        """Updates the semantic information with a new suffix."""
        for k in self.screen.semantic_info_all_warp:
            if s in k:
                k = k.replace(s, s + " --New")

    def cal_diff(self):
        """Calculates the difference in semantic elements between the current and previous model."""
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

    @property
    def current_path_str(self):
        """Returns the current path as a string."""
        return " -> ".join(self.current_path)

    def decide_before_and_log(func):
        # Decorator for logging and decision making before work execution
        def wrapper(self, *args, **kwargs):
            if self.load:
                self.prediction_knowledge = retrivel_knowledge(self.task, "prediction", list(
                    map(simplify_ui_element, self.screen.semantic_info_half_warp)), PER=self.PER)
                self.evaluation_knowledge = retrivel_knowledge(self.task, "selection", list(
                    map(simplify_ui_element, self.screen.semantic_info_half_warp)), PER=self.PER)
                self.decision_knowledge = retrivel_knowledge(self.task, "decision", list(
                    map(simplify_ui_element, self.screen.semantic_info_half_warp)), PER=self.PER)
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
        """Main work function of the model."""
        self.predict_module.predict(ACTION_TRACE)
        eval_res = self.evaluate_module.evaluate(ACTION_TRACE)
        if isinstance(eval_res, str) and eval_res == "wrong":
            print("wrong: feedback started")
            return {"node_id": 1, "trail": "[0,0]", "action_type": "back"}, "wrong"
        return self.execute()

    def execute(self):
        """Executes the selected action."""
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

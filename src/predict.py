import json

from src.utility import simplify_ui_element
import os

import openai


openai.api_key = os.getenv('OPENAI_API_KEY')


class Predict():

    def __init__(self, model):
        self.model = model
        self.modified_result = None
        self.insert_prompt = None

    def log_decorator(func):
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            self.model.log_json["@Module"].append({
                "Name": "Predict",
                "Description": "This module is a prediction model, predicting what will appear after clicking each components on current screen",
                "One-step UI knowledge": self.comp_json_simplified,
                "Multi-step UI knowledge": self.model.long_term_UI_knowledge if self.model.load else ""
            })
            if not os.path.exists("logs"):
                os.mkdir("logs")
                with open("logs/log{}.json".format(self.model.index), "w", encoding="utf-8") as f:
                    json.dump(self.model.log_json, f, indent=4)
            return result
        return wrapper

    def one_step_UI_grounding(self):
        SEMANTIC_INFO = list(
            filter(lambda x: "id=" in x, self.model.screen.semantic_info_no_warp))
        self.current_comp = SEMANTIC_INFO
        self.next_comp = [""]*len(SEMANTIC_INFO)
        self.comp_json = dict.fromkeys(SEMANTIC_INFO, "Unknown")

        node = self.model.refer_node
        graph = node.graph
        edges = graph.find_neighbour_edges(node)
        edges_node = list(map(lambda x: x.node, edges))
        for i, e in enumerate(SEMANTIC_INFO):
            if simplify_ui_element(e) in edges_node:
                index = edges_node.index(simplify_ui_element(e))
                target_node = edges[index]._to
                self.comp_json[SEMANTIC_INFO[i]] = target_node.elements
        self.comp_json_simplified = {
            "id="+str(index+1): item
            for index, (key, item) in enumerate(self.comp_json.items())
            if item != "Unknown"
        }

    def multi_step_UI_grounding(self):
        node = self.model.refer_node
        graph = node.graph
        target_UI, target_content = graph.find_target_UI(
            query=self.model.task)
        if target_UI != [] and target_content != []:
            target_UI_path = [graph.find_shortest_road_to(
                node, target) for target in target_UI]
            self.model.long_term_UI_knowledge = dict(
                zip([" ".join(sublist) for sublist in target_content], target_UI_path))
        else:
            self.model.long_term_UI_knowledge = None

    def UI_grounding(self):
        self.one_step_UI_grounding()
        if self.model.load:
            self.multi_step_UI_grounding()

    @ log_decorator
    def predict(self, ACTION_TRACE=None):
        self.UI_grounding()

import json
from src.knowledge import retrivel_knowledge

from src.utility import cal_similarity, cal_similarity_one, simplify_ui_element, simplify_ui_element_id, sort_by_similarity, sort_by_similarity_score, sort_by_similarity_with_index
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
                with open("logs/log{}.json".format(self.model.index+1), "w", encoding="utf-8") as f:
                    json.dump(self.model.log_json, f, indent=4)
            return result
        return wrapper

    def one_step_UI_grounding(self):
        SEMANTIC_INFO = list(
            filter(lambda x: "id=" in x, self.model.screen.semantic_info_no_warp))
        self.current_comp = SEMANTIC_INFO
        self.next_comp = ["Unknown"]*len(SEMANTIC_INFO)

        node = self.model.refer_node
        graph = node.graph
        edges = graph.find_neighbour_edges(node)
        edges_node = list(map(lambda x: x.node, edges))
        for i, e in enumerate(SEMANTIC_INFO):
            sims = sort_by_similarity_score(e, edges_node)
            if sims and max(sims) > 0.97:
                index = sims.index(max(sims))
                target_node = edges[index]._to
                self.next_comp[i] = target_node.elements
            else:
                continue
        self.next_comp = [(index, item) for index, item in enumerate(
            self.next_comp) if item != "Unknown"]
        sims = sort_by_similarity_with_index(
            self.model.task, [" ".join(x[1]) for x in self.next_comp], [x[0] for x in self.next_comp])
        sims = sorted(sims, key=lambda x: x[2], reverse=True)[:3]
        sims = sorted(sims, key=lambda x: x[0])
        self.comp_json_simplified = {
            "id="+str(index): item
            for index, item, score in sims
            if item != "Unknown"
        }

    def multi_step_UI_grounding(self):
        node = self.model.refer_node
        graph = node.graph
        target_UI, target_content = graph.find_target_UI(
            query="Which component may be relevant to this UI task? :"+self.model.task, refer_node=self.model.refer_node)
        if target_UI != [] and target_content != []:
            target_UI_path = []
            for target in target_UI:
                path = graph.find_shortest_road_to(node, target)
                if path is not None:
                    target_UI_path.append(path)
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

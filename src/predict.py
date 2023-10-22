import json
from src.utility import UI_grounding_prompt_only_summary, add_son_to_father, add_value_to_html_tag, get_top_combined_similarities_group, process_string
import copy
import random
import os
import re
import openai
import tqdm

from src.utility import GPT, UI_grounding_prompt, task_grounding_prompt

openai.api_key = os.getenv('OPENAI_API_KEY')


class Predict():

    def __init__(self, model, pagejump):
        self.pagejump_KB = pagejump
        self.model = model
        self.modified_result = None
        self.insert_prompt = None

    def log_decorator(func):
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            self.model.log_json["@Page_description"] = self.model.page_description
            self.model.log_json["@Similar_tasks"] = [j+":"+"=>".join(
                k) for j, k in zip(self.model.similar_tasks, self.model.similar_traces)]
            self.model.log_json["@Module"].append({
                "Name": "Predict",
                "Description": "This module is a prediction model, predicting what will appear after clicking each components on current screen",
                "Output": self.comp_json
            })
            if not os.path.exists("logs"):
                os.mkdir("logs")
                with open("logs/log{}.json".format(self.model.index), "w", encoding="utf-8") as f:
                    json.dump(self.model.log_json, f, indent=4)
            return result
        return wrapper

    def Task_grounding(self, ACTION_TRACE=None):
        self.model.predicted_step = 'unknown'
        # result = GPT(task_grounding_prompt(self.model.task,
        #              self.model.similar_tasks, self.model.similar_traces, ACTION_TRACE, self.model.screen.semantic_info_list))
        # self.model.predicted_step = result["result"]
        # print("predicted_step", self.model.predicted_step)

    def UI_grounding(self):
        SEMANTIC_INFO = list(
            filter(lambda x: "id=" in x, self.model.screen.semantic_info_list))
        SEMANTIC_STR = process_string(self.model.screen.semantic_info_str)
        self.current_comp = SEMANTIC_INFO
        self.next_comp = [""]*len(SEMANTIC_INFO)
        self.comp_json = dict.fromkeys(
            SEMANTIC_INFO, [])
        predict_node = copy.deepcopy(
            SEMANTIC_INFO)
        queries = [[SEMANTIC_STR, SEMANTIC_INFO[i]]
                   for i in range(len(SEMANTIC_INFO))]
        results = get_top_combined_similarities_group(queries=queries, csv_file=os.path.join(
            os.path.dirname(__file__), 'KB/pagejump/pagejump.csv'), k=1, fields=["Origin", "Edge"])
        for index, r in enumerate(results):
            if r != "Not found":
                self.next_comp[index] = {
                    "description": r["Description"], "comp": r["Destination"]}
                self.comp_json[SEMANTIC_INFO[index]] = {
                    "description": r["Description"], "comp": r["Destination"]}
                predict_node[index] = "None"
        indexs = [i for i, x in enumerate(predict_node) if x == "None"]
        predict_prompt = list(filter(lambda x: not any(
            [str(index+1) in x for index in indexs]), self.model.screen.semantic_info_list))
        response_text = GPT(UI_grounding_prompt_only_summary(predict_prompt))
        self.model.page_description = response_text["Page"]
        self.model.current_path.append("Page:"+self.model.page_description)
        for key, value in response_text.items():
            if key.startswith("id_"):
                index = SEMANTIC_INFO.index(
                    list(filter(lambda x: "id="+key.split("_")[1] in x, SEMANTIC_INFO))[0])
                self.next_comp[index] = value
                self.comp_json[SEMANTIC_INFO[index]] = value

        sem_list = copy.deepcopy(self.model.screen.semantic_info_list)
        temp = [add_value_to_html_tag(key, value["description"]) if value != [
        ] else key for key, value in self.comp_json.items()]
        for i in range(len(sem_list)):
            if "id=" in sem_list[i]:
                sem_list[i] = temp[int(
                    sem_list[i].split("id=")[1].split(" ")[0])-1]
        self.model.extended_info = add_son_to_father(
            sem_list, self.model.screen.trans_relation)

    @ log_decorator
    def predict(self, ACTION_TRACE=None):
        self.Task_grounding(ACTION_TRACE)
        self.UI_grounding()

    def query(self, page, node):
        res = self.pagejump_KB.find_next_page(page, node)
        if res != []:
            res = res[0].split("\\n")
            res = [re.sub(r'id=\d+', '', s) for s in res]
            return res
        else:
            return None

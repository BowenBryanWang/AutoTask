import copy
import random
import os
import re
import openai
import json
import tqdm

from src.utility import GPT, UI_grounding_prompt, task_grounding_prompt

openai.api_key = os.getenv('OPENAI_API_KEY')
openai.organization = 'org-veTDIexYdGbOKcYt8GW4SNOH'


def add_value_to_html_tag(key: str, value: str) -> str:
    index = key.find(">")
    key = key[:index] + " next=\"" + \
        value.replace("\n", "") + "\" " + key[index:]
    return key


def add_son_to_father(l: list, relation: list[tuple]) -> list:
    for index_father, index_son in relation:
        last_index = l[index_father].rfind(" </")
        if last_index != -1:
            l[index_father] = l[index_father][:last_index] + "\n    " + \
                l[index_son] + " </" + \
                l[index_father][last_index + 3:]
    return l


class Predict():

    def __init__(self, model, pagejump):
        self.pagejump_KB = pagejump
        self.model = model
        self.modified_result = None
        self.insert_prompt = None

    def log_decorator(func):
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)  # 调用原始函数
            # 在原始函数执行完毕后执行以下代码
            self.model.log_json["@Page_description"] = self.model.page_description
            self.model.log_json["@Similar_tasks"] = [j+":"+"=>".join(k) for j, k in zip(self.model.similar_tasks, self.model.similar_traces)]
            self.model.log_json["@Module"].append({
                "Name": "Predict",
                "Description": "This module is a prediction model, predicting what will appear after clicking each components on current screen",
                "Output": self.comp_json
            })
            return result  # 返回原始函数的结果（如果有的话）
        return wrapper

    @log_decorator
    def predict(self):
        self.current_comp = self.model.screen.semantic_info_list
        self.next_comp = [""]*len(self.model.screen.semantic_info_list)
        self.comp_json = dict.fromkeys(
            self.model.screen.semantic_info_list, [])

        predict_node = copy.deepcopy(
            self.model.screen.semantic_info_list)
        print("beforequery", self.model.screen.semantic_info_list)
        for i in tqdm.tqdm(range(len(self.model.screen.semantic_info_list))):
            res = self.query(self.model.screen.semantic_info_str,
                             self.model.screen.semantic_info_list[i])#TODO：这里开始逐个query
            if res:
                res = res[0].split("\\n")
                print(len(res))
                if len(res) >= 4:
                    res = random.sample(res, 5)
                res = [re.sub(r'id=\d+', '', s) for s in res]
                self.next_comp[i] = {"description": "",
                                     "comp": res}  # TODO：加入description
                self.comp_json[self.model.screen.semantic_info_list[i]] = {
                    "description": "", "comp": res}
                predict_node[i] = "None"
        print("afterquery", self.comp_json)
        result = GPT(task_grounding_prompt(self.model.task, self.model.similar_tasks,self.model.similar_traces))
        self.model.predicted_step = result["result"]
        print("predicted_step", self.model.predicted_step)
        print(predict_node)
        response_text = GPT(UI_grounding_prompt(predict_node.remove("None") if ("None" in predict_node) else predict_node))
        self.model.page_description = response_text["Page"]
        self.model.current_path.append("Page:"+self.model.page_description)
        for key, value in response_text.items():
            if key.startswith("id_"):
                index = int(key.split("_")[1]) - 1
                self.next_comp[index] = value
                self.comp_json[self.model.screen.semantic_info_list[index]] = value

        print("next_comp: ", self.next_comp)

        self.model.extended_info = add_son_to_father(
            [add_value_to_html_tag(
                key, value["description"]) for key, value in self.comp_json.items()], self.model.screen.trans_relation)
        print("augmented_info: ", self.model.extended_info)

    def query(self, page, node):
        """
        #TODO：Queries the knowledge from KB
        """
        answer = self.pagejump_KB.find_next_page(page, node)
        return answer if answer != [] else None

import copy
import random
import os
import re
import openai
import json
import tqdm

openai.api_key = os.getenv('OPENAI_API_KEY')


def add_value_to_html_tag(key: str, value: str) -> str:
    # last_index = key.rfind(" </")
    # if last_index != -1:
    #     key = key[:last_index] + "\n/* Below are predicted after-click components */\n    " + \
    #         value + " </" + \
    #         key[last_index + 3:]
    # return key
    index = key.find(">")
    key = key[:index] + " next=\"" + value.replace("\n","") + "\" " + key[index:]
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
    """
    A class for predicting the possible UI components that appear when a specific UI element is clicked.

    Attributes:
    -----------
    prompts : list
        A list of prompts for the prediction module.
    current_comp : list
        A list of the current page's components.
    next_comp : list
        A list of the next page's components, where each item is a list that corresponds to current_comp.
    comp_json : dict
        A dictionary of the prediction module's JSON, where each item is a component and its corresponding next page's components.
    """

    def __init__(self, model, pagejump):
        """
        Initializes a Predict object.

        Parameters:
        -----------
        node : str
            The HTML attributes of the UI element being clicked.
        """
        self.pagejump_KB = pagejump
        self.model = model
        self.modified_result = None
        self.insert_prompt = None

    def predict(self):
        """
        Predicts the possible UI components that appear when a specific UI element is clicked.
        """
        self.current_comp = self.model.screen.semantic_info_list
        if len(self.model.screen.semantic_info_list) > 25:
            self.model.extended_info = self.model.screen.semantic_info_list
            self.model.page_description = "Too many components"
            self.model.log_json["@Page_description"] = self.model.page_description
            self.model.current_path.append("Page:"+self.model.page_description)
            self.model.current_path_str = " -> ".join(self.model.current_path)
            log_info = {
                "Name": "Predict",
                "Description": "This module is a prediction model, predicting what will appear after clicking each components on current screen",
                "Output": "Step over due to too many components"
            }
            self.model.log_json["@Module"].append(log_info)
        else:
            self.next_comp = [""]*len(self.model.screen.semantic_info_list)
            self.comp_json = dict.fromkeys(
                self.model.screen.semantic_info_list, [])
            # with open("logs/predict_log{}.log".format(self.model.index), "a") as f:
            #     f.write("--------------------Predict--------------------\n")
            # log_file = logger.add(
            #     "logs/predict_log{}.log".format(self.model.index), rotation="500 MB")
            # logger.debug("Predict for Model {}".format(self.model.index))

            # logger.info("Current Path: {}".format(self.model.current_path_str))
            # logger.info("Task: {}".format(self.model.task))
            if self.modified_result:
                self.comp_json = json.loads(self.modified_result[self.modified_result.find("{"):self.modified_result.find("}")+1])
                self.next_comp = [self.comp_json[key] for key in self.model.screen.semantic_info_list]
                self.model.extended_info = [add_value_to_html_tag(
                    key, "\n".join(value)) for key, value in self.comp_json.items()]
                self.model.extended_info = add_son_to_father(
                    self.model.extended_info, self.model.screen.trans_relation)
            else:
                predict_node = copy.deepcopy(self.model.screen.semantic_info_list)
                print("beforequery", self.model.screen.semantic_info_list)
                for i in tqdm.tqdm(range(len(self.model.screen.semantic_info_list))):
                    res = self.query(self.model.screen.semantic_info_str,
                                    self.model.screen.semantic_info_list[i])
                    if res:
                        res = res[0].split("\\n")
                        print(len(res))
                        if len(res) >= 4:
                            res = random.sample(res, 5)
                        res = [re.sub(r'id=\d+', '', s) for s in res]
                        self.next_comp[i] = res
                        self.comp_json[self.model.screen.semantic_info_list[i]] = res
                        predict_node[i] += "/* Don't predict this, output [] */"
                print("afterquery", self.comp_json)

                self.prompt = [
                    {
                        "role": "system",
                        "content": """
You are an expert in User Interface (UI) automation. Your task is to predict the potential UI components that will be displayed after interacting with elements on the UI.
You are given a list of UI components and their attributes. Based on all the UI components on the current page and the relationship between them, reasonably deduce, predict, and synthesize the overall information of the page and the details of each UI component.

1. Reason step-by-step about the short one-sentence description of the current page.
2. Think step-by-step about what the successive page might be like and how about it's UI components. Summarize the prediction results in short sentence.
i.e. (<div> Voice Search</div>:" a voice input page for searching").
3. Output the predictions in a JSON formated like:
{
  "Page": "..."(One-sentence description of the current page),
  "id_x": "..."(Predicted description for the successive UI page with id=x),
  ......(x is the id of the current UI component,you should iterate over all the UI components)
}
        """
                    },
                    {
                        "role": "user",
                        "content": """
<button id=1 class='com.whatsapp:id/home_tab_layout' description='Status'> Status </button>
<button id=2 class='com.whatsapp:id/button'> Add Status </button>
<button id=3 class='com.whatsapp:id/home_tab_layout' description='Community'>  </button>
                            """
                    },
                    {
                        "role": "assistant",
                        "content": """
{
    "Page": "Main interface of the WhatsApp application",
    "id_1": "Display a new page where you can view the status updates of contacts",
    "id_2": "Mean to add a new status update",
    "id_3": "Lead to a page with group chats or a community forum.",
}
                            """
                    },
                    {
                        "role": "user",
                        "content": """
                            {}
                            """.format(predict_node)
                    }
                ]
                if self.insert_prompt:
                    self.prompt.append(self.insert_prompt)
                print(self.prompt[-1])
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=self.prompt,
                    temperature=0,
                )
                response_text = response["choices"][0]["message"]["content"]
                self.resp = response_text
                print(response_text)
                response_text = json.loads(
                    response_text[response_text.find("{"):response_text.find("}")+1])
                print("JSON:----", response_text)
                self.model.page_description = response_text["Page"]
                self.model.log_json["@Page_description"] = self.model.page_description
                self.model.current_path.append("Page:"+self.model.page_description)
                self.model.current_path_str = " -> ".join(self.model.current_path)
                for key in response_text.keys():
                    if "id_" in key:
                        index = int(key.split("_")[1])-1
                        if response_text[key] != []:
                            self.next_comp[index] = response_text[key]
                            self.comp_json[self.model.screen.semantic_info_list[index]
                                        ] = response_text[key]
                        else:
                            if self.next_comp[index] == "":
                                self.next_comp[index] = []
                                self.comp_json[self.model.screen.semantic_info_list[index]] = [
                                ]
                            else:
                                continue
                    else:
                        continue

                print("next_comp: ", self.next_comp)

                self.model.extended_info = [add_value_to_html_tag(
                    key, "\n".join(value)) for key, value in self.comp_json.items()]
                print("extended_info: ", self.model.extended_info)
                self.model.extended_info = add_son_to_father(
                    self.model.extended_info, self.model.screen.trans_relation)
                print("augmented_info: ", self.model.extended_info)

            log_info = {
                "Name": "Predict",
                "Description": "This module is a prediction model, predicting what will appear after clicking each components on current screen",
                "Output": self.comp_json
            }
            self.model.log_json["@Module"].append(log_info)

    def query(self, page, node):
        """
        Queries the knowledge from KB
        """
        answer = self.pagejump_KB.find_next_page(page, node)
        return answer if answer != [] else None

    def update(self, advice: dict):
        self.update_prompt = [
            {
                "role": "system",
                "content": """
You are an intelligent [Predict Module] updater. A [Predict Module]'s task is to predict the potential UI components that will be displayed after clicking  button on the UI.
Now, the [End Human User](represents ground-truth) has provided feedback (criticisms) regarding the prediction result from this intelligent agent that generated before.
You need to optimize the current [Predict Module] based on this feedback and analyze how to utilize the feedback to this agent.
You are given the feedback from end-user and description of [Predict Module], you have 2 strategies to update the [Predict Module]:
1, [Insert]: Insert a slice prompt to the end of the original prompt of [Predict Module]'s LLM based on the feedback, augmenting the decision process of it.
2, [Modify]: Step over the LLM decision process of [Predict Module] and directly modify the original output result based on the feedback.
Think step-by-step about the process of updating the [Predict Module] and output a json object structured like: {"strategy": Insert or Modify, "prompt": your inserted slice prompt, "output": your direct modified output based on the original output. Don't break the json format}
"""
            }
        ]
        self.update_prompt.append({
            "role": "user",
            "content": """
                Feedback from end-user(ground-truth):{}
                """.format(advice)
        })
        self.update_prompt.append({
            "role": "user",
            "content": """
                Original Output of [Predict Module]:{}
                """.format(self.comp_json)
        })
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.update_prompt,
            temperature=1,
        )
        response_text = response["choices"][0]["message"]["content"]
        print(response_text)
        resp = json.loads(
            response_text[response_text.find("{"):response_text.find("}")+1])
        
        strategy = resp["strategy"]
        prompt = resp["prompt"]
        output = resp["output"]
        if strategy == "Insert":
            self.insert_prompt = {
                "role": "user",
                "content": prompt,
            }
        else:
            self.modified_result = output

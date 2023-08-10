import copy
import random
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
import csv
import os
import openai
from loguru import logger
import json
from langchain.document_loaders.csv_loader import CSVLoader
import tqdm

openai.api_key = os.getenv("OPENAI_API_KEY")


def add_value_to_html_tag(key: str, value: str) -> str:
    last_index = key.rfind(" </")
    if last_index != -1:
        key = key[:last_index] + "\n/* Below are predicted after-click components */\n    " + \
            value + " </" + \
            key[last_index + 3:]
    return key

def add_son_to_father(l:list,relation:list[tuple])-> list:
    for index_father, index_son in relation:
        last_index = l[index_father].rfind(" </")
        if last_index != -1:
            l[index_father] = l[index_father][:last_index] + "\n    " + \
                l[index_son] + " </" + \
                l[index_father][last_index + 3:]
    return l

class Predict():
    """
    A class for predicting the possible controls that appear when a specific UI element is clicked.

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
        
        

    def predict(self):
        """
        Predicts the possible controls that appear when a specific UI element is clicked.
        """
        self.current_comp = self.model.screen.semantic_info_list
        self.next_comp = [""]*len(self.model.screen.semantic_info_list)
        self.comp_json = dict.fromkeys(self.model.screen.semantic_info_list,[])
        # with open("logs/predict_log{}.log".format(self.model.index), "a") as f:
        #     f.write("--------------------Predict--------------------\n")
        # log_file = logger.add(
        #     "logs/predict_log{}.log".format(self.model.index), rotation="500 MB")
        # logger.debug("Predict for Model {}".format(self.model.index))

        # logger.info("Current Path: {}".format(self.model.current_path_str))
        # logger.info("Task: {}".format(self.model.task))

        self.model

        predict_node=copy.deepcopy(self.model.screen.semantic_info_list)
        print("beforequery",self.model.screen.semantic_info_list)
        for i in tqdm.tqdm(range(len(self.model.screen.semantic_info_list))):
            res = self.query(self.model.screen.semantic_info_str, self.model.screen.semantic_info_list[i])
            if res: 
                res = res[0].split("\\n")
                print(len(res))
                if len(res) >= 4:
                    res = random.sample(res, 4)
                self.next_comp[i] = res
                self.comp_json[self.model.screen.semantic_info_list[i]] = res
                predict_node[i]+="/* Don't predict this, output [] */"
        print("afterquery",self.comp_json)
                
        self.prompt = [
            {
                "role": "system",
                "content": """You are an expert in User Interface (UI) automation. Your task is to predict the potential controls that will be displayed after clicking  button on the UI.
You are given a list of UI components and their attributes. Based on all the controls on the current page and the relationship between them, reasonably deduce, predict, and synthesize the overall information of the page and the details of each control.
Step 1: Reason step-by-step about the one sentence description of the current page.
Step 2: Reason step-by-step about the prediction of list of controls after clicking each control.
Step 3: Output a JSON object structured like:{"Page": short description of current page, "id=x": [(Prediction Results for Control which id is x)]}.
"""
            },
            {
                "role": "user",
                "content": """
<button id=1 class='com.whatsapp:id/home_tab_layout' description='Calls'> Calls </button>/* Don't predict this, output [] */
<button id=2 class='com.whatsapp:id/home_tab_layout' description='Status'> Status </button>
<button id=3 class='com.whatsapp:id/button'> Add Status </button>
<button id=4 class='com.whatsapp:id/home_tab_layout' description='Community'>  </button>
<button id=5 class='com.whatsapp:id/menuitem_overflow' description='More options'>  </button>
                    """
            },
            {
                "role": "assistant",
                "content": """
                    Step 1: Reason step-by-step about the one-sentence description of the current page.
From the controls and their classes, this page seems to be the main interface of the WhatsApp application where the user can navigate to different functionalities such as Calls, Status, Community, and so on. There are also other options like a search function and a camera function, which are commonly seen on the WhatsApp main page.

Step 2: Reason step-by-step about the prediction of list of controls after clicking each control.
1, Don't predict this component so just output [].
2, Button "Status": This should display a new page where you can view the status updates of contacts.
3, Button "Add Status" is meant to add a new status update.
4, Button "Community": This might be a custom feature, maybe leading to a page with group chats or a community forum.
5, Button "More options": This should display a dropdown or popup menu with more options, like Settings, WhatsApp Web, etc.

Step 3: Output a JSON object structured.
{
    "Page": "Main interface of the WhatsApp application",
    "id=1": [],
    "id=2": ["<p description='My Status'> </p>","<button description='Add Status'> </button>"],
    "id=3": ["<button description='Selector'> </p>","<button description='New Status'> </button>"],
    "id=4": ["<button description='Members'> </button>","<button description='Add new Member'> </button>","<p description='Connect'> </p>"],
    "id=5": ["<button description='Settings'> </button>","<button description='WhatsApp Web'> </button>"]
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
        print(self.prompt[-1])
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.prompt,
            temperature=0.3,
            max_tokens=1024,
        )
        response_text = response["choices"][0]["message"]["content"]
        print(response_text)
        response_text = json.loads(
            response_text[response_text.find("{"):response_text.find("}")+1])
        print("JSON:----", response_text)
        self.model.page_description = response_text["Page"]
        self.model.current_path.append("Page:"+self.model.page_description)
        self.model.current_path_str = " -> ".join(self.model.current_path)
        # for i in range(len(self.model.screen.semantic_info_list)):
        #     if response_text["id="+str(i+1)] == []:
        #         if self.next_comp[i] == "":
        #             self.next_comp[i] = []
        #             self.comp_json[self.model.screen.semantic_info_list[i]] = []
        #         else:
        #             continue
        #     else:
        #         self.next_comp[i]=response_text["id="+str(i+1)]
        #         self.comp_json[self.model.screen.semantic_info_list[i]
        #                     ] = response_text["id="+str(i+1)]
        for key in response_text.keys():
            if "id=" in key:
                index = int(key.split("=")[1])-1
                if response_text[key] !=[]:
                    self.next_comp[index] = response_text[key]
                    self.comp_json[self.model.screen.semantic_info_list[index]] = response_text[key]
                else:
                    if self.next_comp[index] == "":
                        self.next_comp[index] = []
                        self.comp_json[self.model.screen.semantic_info_list[index]] = []
                    else:
                        continue
            else:
                continue
                
        print("next_comp: ", self.next_comp)
        # logger.info("Response: {}".format(response_text))
        self.model.extended_info = [add_value_to_html_tag(key, "\n".join(value)) for key, value in self.comp_json.items()]
        print("extended_info: ", self.model.extended_info)
        self.model.extended_info = add_son_to_father(self.model.extended_info, self.model.screen.trans_relation)
        print("augmented_info: ", self.model.extended_info)
        # logger.warning("Components: {}".format(json.dumps(self.comp_json)))
        # logger.debug("Predict for Model {} Done".format(self.model.index))
        # logger.remove(log_file)
        log_info = {
            "Name":"Predict",
            "Description":"This module is a prediction model, predicting what will appear after clicking each components on current screen",
            "Input":predict_node,
            "Output":response_text
        }
        self.model.log_json["@Module"].append(log_info)

    def query(self, page, node):
        """
        Queries the knowledge from KB
        """
        answer = self.pagejump_KB.find_next_page(page, node)
        return answer if answer!=[] else None



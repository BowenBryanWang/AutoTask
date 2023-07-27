import os
from langchain import FAISS
import openai
from loguru import logger
import json

openai.api_key = os.getenv("OPENAI_API_KEY")
# from reliablegpt import reliableGPT

# openai.ChatCompletion.create = reliableGPT(
#     openai.ChatCompletion.create,
#     user_email= "saltyp0rridge20@gmail.com",
#     queue_requests=True,
#     fallback_strategy=['gpt-3.5-turbo', 'text-davinci-003', 'gpt-3.5-turbo'],
#     model_limits_dir = {"gpt-4": {"max_token_capacity": 90000, "max_request_capacity": 3500	}}
# ) # type: ignore


def add_value_to_html_tag(key: str, value: str) -> str:
    start_tag_index = key.find('>') + 1
    end_tag_index = key.rfind('</')
    wrapped_content = key[start_tag_index:end_tag_index]
    wrapped_content_with_value = wrapped_content.strip() + str(value)
    modified_key = key[:start_tag_index] + '/* Below are after-click components */\n' + \
        wrapped_content_with_value + key[end_tag_index:]
    return modified_key


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
        self.prompts = []
        self.current_comp = []
        self.next_comp = []
        self.comp_json = {}
        self.prompt = [
            {
                "role": "system",
                "content": """You are an expert in User Interface (UI) automation. Your task is to predict the potential controls that will be displayed after clicking  button on the UI.
                                You are given a list of UI components and their attributes. Based on all the controls on the current page and the relationship between them, reasonably deduce, predict, and synthesize the overall information of the page and the details of each control.
                                Step 1: Reason step-by-step about the one sentence description of the current page.
                                Step 2: Reason step-by-step about the prediction of list of controls after clicking each control. Be simple but accurate.
                                Step 3: Output a JSON object structured like:{"Page": short description of current page, "id=x": [](Prediction Results for Control which id is x)}.
                                """
            },
            {
                "role": "user",
                "content": """
                    <button id=1 class='com.whatsapp:id/home_tab_layout' description='Calls'> Calls </button>
                    <button id=2 class='com.whatsapp:id/home_tab_layout' description='Status'> Status </button>
                    <button id=3 class='com.whatsapp:id/home_tab_layout' description='Community'>  </button>
                    <button id=4 class='com.whatsapp:id/menuitem_overflow' description='More options'>  </button>
                    """
            },
            {
                "role": "assistant",
                "content": """
                    Step 1: Reason step-by-step about the one-sentence description of the current page.
                    From the controls and their classes, this page seems to be the main interface of the WhatsApp application where the user can navigate to different functionalities such as Calls, Status, Community, and so on. There are also other options like a search function and a camera function, which are commonly seen on the WhatsApp main page.

                    Step 2: Reason step-by-step about the prediction of list of controls after clicking each control.
                    1, Button "Calls": This will probably open a new page listing the recent calls.
                    2, Button "Status": This should display a new page where you can view the status updates of contacts.
                    3, Button "Community": This might be a custom feature, maybe leading to a page with group chats or a community forum.
                    4, Button "More options": This should display a dropdown or popup menu with more options, like Settings, WhatsApp Web, etc.
                    
                    Step 3: Output a JSON object structured.
                    {
                        "Page": "Main interface of the WhatsApp application",
                        "id=1": ["<button description='Bowen'> </button>","<button description='Yellow'> </button>"],
                        "id=2": ["<p description='My Status'> </p>","<button description='Add Status'> </button>"],
                        "id=3": ["<button description='Members'> </button>","<button description='Add new Member'> </button>","<p description='Connect'> </p>"],
                        "id=4": ["<button description='Settings'> </button>","<button description='WhatsApp Web'> </button>"]
                    }
                    """
            },
            {
                "role": "user",
                "content": """
                    {}
                    """.format(self.model.screen.semantic_info_str)
            }
        ]

    def predict(self):
        """
        Predicts the possible controls that appear when a specific UI element is clicked.
        """
        log_file = logger.add("logs/predict.log", rotation="500 MB")
        logger.debug("Predict for Model {}".format(self.model.index))

        logger.info("Current Path: {}".format(self.model.current_path_str))
        logger.info("Task: {}".format(self.model.task))

        # for (node, prompt) in zip(self.model.screen.semantic_info, self.prompts):

        #     logger.info("Prompt: {}".format(json.dumps(prompt[-1])))
        #     next_page = self.query(self.model.screen.semantic_info_str, node)
        #     if next_page is not None:
        #         self.next_comp.append(next_page)
        #         continue
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.prompt,
            temperature=0.5,
        )
        response_text = response["choices"][0]["message"]["content"]
        print(response_text)
        response_text = json.loads(response_text[response_text.find("{"):response_text.find("}")+1])
        print("JSON:----",response_text)
        self.model.screen.description = response_text["Page"]
        for i in range(len(self.model.screen.semantic_info)):
            self.next_comp.append(response_text["id="+str(i+1)])
            self.comp_json[self.model.screen.semantic_info[i]] = response_text["id="+str(i+1)]
        logger.info("Response: {}".format(response_text))
        self.model.extended_info = "\n".join([add_value_to_html_tag(
            key, "\n".join(value)) for key, value in self.comp_json.items()])

        logger.warning("Components: {}".format(json.dumps(self.comp_json)))
        logger.debug("Predict for Model {} Done".format(self.model.index))
        logger.remove(log_file)

    def query(self, page, node):
        """
        Queries the knowledge from KB
        """
        self.pagejump_KB.find_next_page(page, node)

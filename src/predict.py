from langchain import FAISS
import openai
from loguru import logger
import json


# from reliablegpt import reliableGPT

# openai.ChatCompletion.create = reliableGPT(
#     openai.ChatCompletion.create,
#     user_email= "saltyp0rridge20@gmail.com",
#     queue_requests=True,
#     fallback_strategy=['gpt-3.5-turbo', 'text-davinci-003', 'gpt-3.5-turbo'],
#     model_limits_dir = {"gpt-4": {"max_token_capacity": 90000, "max_request_capacity": 3500	}}
# ) # type: ignore


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
    
    def __init__(self, model,pagejump):
        """
        Initializes a Predict object.

        Parameters:
        -----------
        node : str
            The HTML attributes of the UI element being clicked.
        """
        self.pagejump = pagejump
        self.prompts = []
        self.current_comp = []
        self.next_comp = []
        self.comp_json = {}
        self.model = model
        for node in self.model.screen.semantic_nodes:
            self.current_comp.append(node)
            self.prompts.append([
                {
                    "role": "system",
                    "content": "You are an intelligent UI automation assistant that can predict the possible controls that appear when a specific UI element is clicked. Your task is to predict the potential controls that will be displayed after clicking a particular button on the UI."
                },
                {
                    "role": "user",
                    "content": """
                    The current scenario is "Whatsapp application's home screen".
                    The UI element is a button with the following attributes:
                    ```HTML
                    <button id=10 class='contact_photo' description='Wang Bowen'>  </button>
                    ```
                    Think step by step. give the predicted UI component as a simple list warped with ```HTML```.Be short,simple and accurate..
                    """
                },
                {
                    "role": "assistant",
                    "content": """
                    This appears to be a button that's typically found in a list of contacts on WhatsApp's home screen, representing the contact photo of "Wang Bowen". When this button is clicked, it should open the chat screen for that contact.
                    ```HTML
                    <p id=1 class='camera_btn' description='Camera'>  </p>
                    <p id=2 class='input_attach_button' description='Attach'>  </p>
                    <p id=3 class='entry' > Message </p>
                    <p id=4 class='emoji_picker_btn' description='Emoji'>  </p>
                    <p id=5 class='info' >   Messages and calls are end-to-end encrypted. No one outside of this chat, not even WhatsApp, can read or listen to them. Tap to learn more. </p>
                    <button id=6 class='menuitem_overflow' description='More options'>  </button>
                    <p id=7 class='' description='Voice call'>  </p>
                    <p id=8 class='back' description='Navigate up'>  </p>w
                    ```
                    """
                },
                {
                    "role": "user",
                    "content": """
                    The current scenario is {}.
                    The UI element is a button with the following attributes:
                    ```HTML
                    {}
                    ```
                    Think step by step. give the predicted UI component as a simple list warped with ```HTML```.Be short,simple and accurate..
                    """.format(self.model.screen.page_description, node)
                }
            ])
    
    def predict(self):
        """
        Predicts the possible controls that appear when a specific UI element is clicked.
        """
        log_file = logger.add("log/predict.log", rotation="500 MB")
        logger.debug("Predict for Model {}".format(self.model.index))
        logger.info("Current Page: {}".format(self.model.screen.page_description))
        logger.info("Current Path: {}".format(self.model.current_path_str))
        logger.info("Task: {}".format(self.model.task))

        for (node,prompt) in zip(self.model.screen.semantic_nodes,self.prompts):

            logger.info("Prompt: {}".format(json.dumps(prompt[-1])))

            if self.query(node):
                self.next_comp.append(self.query(node))
                continue
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=prompt,
                temperature=0.5,
            )
            print(response["choices"][0]["message"]["content"])
            response_text = response["choices"][0]["message"]["content"]
            response_text = response_text[response_text.find("```HTML")+7:response_text.find("```")].split("\n")
            print(response_text)
            self.next_comp.append(response_text)

            logger.info("Response: {}".format(response_text))
            
        for i in range(len(self.current_comp)):
            self.comp_json[self.current_comp[i]] = self.next_comp[i]

        logger.warning("Components: {}".format(json.dumps(self.comp_json)))
        logger.debug("Predict for Model {} Done".format(self.model.index))
        logger.remove(log_file)
            
         
    
    def query(self,page,node):
        """
        TODO:Queries the knowledge from KB
        """
        self.pagejump.find_next_page(page,node)


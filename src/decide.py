import json
import openai
from loguru import logger



class Decide:
    def __init__(self, model) -> None:
        """
        Initializes a Decide object with a given OpenAI model.

        Args:
            model (str): The name of the OpenAI model to use.
        """
        self.model = model
        

    def decide(self,new_screen):
        """
        Uses the OpenAI model to generate a response to the prompt.

        Returns:
            str: The status of the decision made by the model.
        """
        self.prompt = [{
            "role": "system",
            "content": """You are a professor with in-depth knowledge of User Interface (UI) tasks and their action traces. You are assigned a specific UI task along with an action trace. Your task is to evaluate if the action trace aligns with the assigned task, categorizing the trace as: completion(Till now after the final action, task completed), wrong(Till now the trace goes into a wrong branch), or partly completed(Till now nothing wrong and could go on).
You can refer to some completed examples similar to user's intent. But don't follow the examples exactly, though; they serve only as hints.
"Task" stands for user's intent; "Action Trace" stands for the user's current action traces on the mobile; "Last Page" stands for UI structure after the last action.
You should comprehensively analyze the above three fields or refer to similar examples to make a synthesis conclusion.
Use the following steps to respond to user inputs. Fully restate each step before proceeding. i.e. "Step 1: Reason...".
Step 1:Reason step-by-step about the relationship of the action trace  and UI task either: partly completed and need to go on, fully completed(done), a superset(More).
Step 2:Reason step-by-step about whether the final action(s) in the trace deviate from the correct answer for the given task, described as "wrong".You can assess by analyzing the last step and the last page information.
Step 3:Output a JSON object structured like: {"status": "completed" or "wrong" or "go on", "reason": reason for the decision}."""
        },
        {
            "role": "user",
            "content": """
Task: Add a new contact called Steven
Action Trace: [Page]: Main interface of WhatsApp => [Action]: click on <button id=1 class='com.whatsapp:id/fab' description='New chat'>  </button> => [Page]: Adding new chat and invite friends
Last Page:
<button id=1 class='' > INVITE </button>
<button id=2 class='' description='余捷'> 余捷 </button>
<button id=3 class='' description='Yellow'> Yellow </button>
<button id=4 class='' description='f'> f </button>
<button id=5 class='' > Invite to WhatsApp </button>
<button id=6 class='' description='助教'> 助教 </button>
<button id=7 class='' description='Wang Bowen'> Wang Bowen </button>
<button id=8 class='' description='+86 19805565778'> 老婆子 (You) </button>
<button id=9 class='' > Contacts on WhatsApp </button>
<button id=10 class='' > New community </button>
<p id=11 class='com.whatsapp:id/contactpicker_button_two' description='Scan, share QR code'>  </p>
<button id=12 class='' > New group </button>
<button id=13 class='com.whatsapp:id/menuitem_overflow' description='More options'>  </button>
<p id=14 class='com.whatsapp:id/menuitem_search' description='Search'>  </p>
<p id=15 class='' description='Navigate up'>  </p>
            """
        },
        {
            "role": "assistant",
            "content": """
Step 1: Reason about the relationship of the action trace and UI task:
The provided action trace is not fully completed since it stops at the "Adding new chat and invite friends" page after clicking on the button to create a new chat. The task requires adding a new contact called "Steven," but the trace only shows the user navigating to the "Adding new chat and invite friends" page without performing any further actions related to adding a contact. Therefore, the action trace is partly completed and needs to go on.
Step 2: Reason about whether the final action(s) in the trace deviate from the correct execution path for the given task:
The last action in the action trace is to navigate to the "Adding new chat and invite friends" page, which opens a new page of "adding page".The presence of buttons like "Invite to WhatsApp" and "Contacts on WhatsApp" suggests that the user still needs to go on and find Steven after clicking on the button to create a new chat. Therefore,the final action didn' deviate and is on the right way.
Step 3: Output a JSON object:
Based on the evaluation, the JSON object would be:
{"status": "go on", "reason": "The action trace shows the user reaching the 'Homepage of WhatsApp' and clicking on 'Add.'. Until now nothing wrong and could go on to find Steven."}
"""
        },
            {
            "role": "user",
            "content": """
Task:{}
Action trace:{}
Last Page:{}
Completed Examples from Library:
{}
            """.format(self.model.task, self.model.current_path_str,new_screen.semantic_info,[j+":"+"=>".join(k) for j,k in zip(self.model.similar_tasks,self.model.similar_traces)])
        }]


        with open("logs/log{}.log".format(self.model.index), "a") as f:
            f.write("--------------------Decide--------------------\n")
        log_file = logger.add("logs/log{}.log".format(self.model.index), rotation="500 MB")
        logger.debug("Decide for Model {}".format(self.model.index))
        logger.info("Current Page: {}".format(self.model.page_description))
        logger.info("Current Path: {}".format(self.model.current_path_str))
        logger.info("Task: {}".format(self.model.task))
        logger.info("Prompt: {}".format(json.dumps(self.prompt[-1])))

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.prompt,
            temperature=0.5,
        )
        # 提取回答当中的json部分
        answer = response["choices"][0]["message"]["content"]
        answer = json.loads(answer[answer.find("{"):answer.find("}")+1])

        logger.warning("Response: {}".format(json.dumps(answer)))
        logger.debug("Decide for Model {} Done".format(self.model.index))
        logger.remove(log_file)
        
        return answer["status"]

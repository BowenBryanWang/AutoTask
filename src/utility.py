import openai

import json
import pickle
import os
import time


def persist_to_file(file_name, use_cache=True):
    def decorator(original_func):
        try:
            cache = pickle.load(open(file_name, 'rb'))
        except (IOError, ValueError):
            cache = {}

        def new_func(*argv, **args):
            arg_s = json.dumps({
                'argv': argv,
                'args': args
            })
            cache_used = True
            if use_cache and arg_s in cache:
                res = cache[arg_s]
                if res is None or len(res) == 0:
                    del cache[arg_s]
            if arg_s not in cache or not use_cache:
                cache[arg_s] = original_func(*argv, **args)
                cache_used = False
                pickle.dump(cache, open(file_name, 'wb'))

            if 'prompt' in args:
                store_path = os.path.join(os.path.dirname(__file__), 'gpt_res')
                if not os.path.exists(store_path):
                    os.makedirs(store_path)

                store_path = os.path.join(
                    store_path, f"{int(time.time() * 1000)}{'cache' if cache_used else ''}.txt")
                with open(store_path, 'w') as f:
                    f.write(
                        '\n'.join([f'{x["role"]}:\n{x["content"]}\n' for x in args['prompt']]))
                    f.write('\n')
                    f.write('===response===\n')
                    f.write(cache[arg_s])
            return cache[arg_s]
        return new_func
    return decorator


@persist_to_file("Cache.pickle")
def chat(prompt):
    print('connecting to gpt')
    response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=prompt,
        temperature=0.5,
        stream=True  # this time, we set stream=True
    )
    collected_messages = ""
    print('start streaming...')
    for chunk in response:
        chunk_message = chunk['choices'][0]['delta'].get('content', '')
        print(chunk_message, end="")
        collected_messages += chunk_message

    return collected_messages


def GPT(prompt):
    while True:
        try:
            result = chat(prompt=prompt)
            result_json = json.loads(
                result[result.find("{"):result.rfind("}")+1])
            return result_json
        except Exception as e:
            print(e)
            continue


def process_action_info(action, params, node):
    if action == "click":
        return "Action: Click on {}".format(node)
    elif action == "edit":
        return "Action: Edit {} with {}".format(node, params)


def task_grounding_prompt(task, similar_tasks, similar_traces):
    return [
        {
            "role": "system",
            "content": """
You are an expert in User Interface (UI) automation. Your task is to predict the actual execution steps of user's intent based on your knowledge.
You are given the original user's intent and a list of ground-truth of similar task-executions on UI. 
Based on your knowledge, reasonably predict, and synthesize the step-by-step execution tutorials of the user's intent.
You are also given some examples of similar tasks and their executions, which you can refer to and help you figure out the tutorial of user's execution


Think step by step and then output the predictions in a JSON formated like:
{
"result": "..."(detailed step-by-by tutorial of how to implement the task),
}
"""
        },
        {
            "role": "user",
            "content": """
                    User task: {}
                    Similar examples: {}
                    """.format(task, [j+":"+"=>".join(k) for j, k in zip(similar_tasks, similar_traces)])
        }
    ]


def UI_grounding_prompt(predict_node):
    return [
        {
            "role": "system",
            "content": """You are an expert in User Interface (UI) automation. Your task is to predict the potential UI components that will be displayed after interacting with elements on the UI.
You are given a list of UI components and their attributes. Based on all the UI components on the current page and the relationship between them, reasonably deduce, predict, and synthesize the overall information of the page and the details of each UI component.

1. Reason step-by-step about the short one-sentence description of the current page.
2. Think step-by-step about what the successive page might be like. Summarize the prediction results in short sentence.
3. Think step-by-step about how the UI components in the successive page would be like. List them in the final answer as short as possible.
i.e. (<div> Voice Search</div>:{"description":a voice input page for searching","comps":["<div>Voice Input</div>","<button>Enter</button>"]}).
4. Output the predictions in a JSON formated like:
{
"Page": "..."(One-sentence description of the current page),
"id_x": {"description":"..."(Predicted description for the successive UI page with id=x),"comps:[](Predicted components as a list for the successive UI page with id=x)},
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
"id_1": {"description":"Display a new page where you can view the status updates of contacts","comps":["<div>My Status</div>","<button>Update Status</button>"]},
"id_2": {"description":"Mean to add a new status update","comps":["<div>New Status</div>","<div>Enter</div>"]},
"id_3": {"description":"Lead to a page with group chats or a community forum.","comps":["<div>Community Member</div>","<div>Add Member</div>"]}
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


def Task_UI_grounding_prompt(task, current_path_str, similar_tasks, similar_traces, predicted_step, semantic_info_list, next_comp):
    return [
        {
            "role": "system",
            "content": """You are a mobile UI expert acting as a "Judger". Your specialized role focuses on guiding the user to complete the user task on specific UI screen.
Only guiding by your knowledge is irreliable , so you are give two kinds of ground-truths, they are:
1, the tutorial of how to fulfill the task, estimated through retriving the knowledge libraray and learned from similar tasks.
2, current extended UI screen, which contains the components of current UI screen and their corresponding interaction results.
Basically the tutorial represents how to do the task conceptually without grounding and the UI screen represents the UI ground-truth. You need to conbine them, thus build a connection between them.
Finnaly, your job is to rate the available options on the current page based on your grounding. For each option, provide a confidence rating from 0-10, where 0 indicates 'unlikely' and 10 indicates 'highly likely'

For each available option on the screen:

Step 1: Think step by step about how there two kinds of knowlegde lead you to score each UI element.
Step 2: Output a JSON object with scores and reasoning. The structure should be: {"score": [], "reason": []}
Example:
{
"score": [10, 8, 4, 1, 2],
"reason": [
"...","...","...","...","..."
]
"""
        },
        {
            "role": "user",
            "content": """Task: "{}".
Current path: {}.
Examples:{}
Estimated tutorial: {}
Current UI:
'''HTML
{}
'''
Successive results of current UI:
{}
""".format(
                    task,
                    current_path_str,
                    [j+":"+"=>".join(k) for j, k in zip(
                        similar_tasks, similar_traces)],
                    predicted_step,
                    "".join(semantic_info_list),
                    next_comp)
        }]


def plan_prompt(task, page_description, node_selected):
    return [
        {
            "role": "system",
            "content":
                """You are an AI assistant specialized in UI Automation. Now you have successfully obtained the top UI component that are most likely to operate with based on user's intent. Now, you need to determine the action to be performed on it. 
There are two main types of actions: 
    1,clicking on a component (no text parameter needed) 
    2,editing a component (you should also determine the text parameter).
For the top component, analyze the possible action to be taken and, if it involves an editing action, provide the corresponding text parameter as well. 
Reason step by step to provide the actions and text parameters for it based on the user's intent and the context of the current screen.
Output a JSON object structured like 
{
    "action": the action to be taken, either "click" or "edit", 
    "text": the text parameter for the action if any (Optional),
    "reason": the reason,
},
"""
        },
        {
            "role": "user",
            "content": """
                Task: {},
Current Page : {}:
Top Candidate:{}""".format(task, page_description, node_selected)
        }
    ]


def decide_prompt(task, ACTION_TRACE, semantic_info):
    return [{
            "role": "system",
            "content": """You are a professor with in-depth knowledge of User Interface (UI) tasks and their action traces. You are assigned a specific UI task along with an action trace. Your task is to evaluate if the action trace aligns with the assigned task, categorizing the trace as: 
1,completed: After the last action and based on the newest UI screen, the user's task is completed;
2,wrong: After the last action and based on the newest UI screen, the action trace goes into a wrong branch and need to be corrected;
3,go on: After the last action and based on the newest UI screen, the action trace is on the right track but not completed yet.
Use the following steps to respond to user inputs. Fully restate each step before proceeding. i.e. "Step 1: Reason...".
Step 1:Reason step-by-step about the relationship of the action trace  and UI task.
Step 2:Reason step-by-step about whether the newest action leading to the newest UI screen is consistent with the UI task result.Decide whether the lastest action leads to a wrong branch and needs navigate back.
Step 3:Output a JSON object structured like: {"status": "completed" or "wrong" or "go on", "reason": reason for the decision}."""
            },
            {
            "role": "user",
            "content": """
Task: Add a new contact called Steven
Action Trace: [Page]: Main interface of WhatsApp => [Action]: click on <button id=1 class='com.whatsapp:id/fab' description='New chat'>  </button> => [Page]: Adding new chat and invite friends
Latest Page:
<button id=1 class='' > INVITE </button>
<button id=3 class='' description='Yellow'> Yellow </button>
<button id=7 class='' description='Wang Bowen'> Wang Bowen </button>
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
Step 1: Reason step-by-step about the relationship of the action trace and UI task.
Given UI Task: Add a new chat with Steven.
The user starts on the main interface of WhatsApp.
The user clicks on the 'New chat' button.
The user lands on the "Adding new chat and invite friends" page.
Based on this action trace, the user seems to be on the correct path to adding a new chat since they've navigated to the 'Adding new chat and invite friends' page from the main interface. However, the task specifically mentioned adding a chat with "Steven", and it's important to check if this action has been completed.
Step 2: Reason step-by-step about whether the newest UI screen is consistent with the UI task result.
Upon observing the provided 'Last Page' UI elements:
There are multiple buttons present, with some indicating individual contacts (like '余捷', 'Yellow', 'f', '助教', 'Wang Bowen', and '老婆子 (You)') and others with different functionalities (like 'INVITE', 'Invite to WhatsApp', 'Contacts on WhatsApp', 'New community', 'New group', etc.).
There's no button or contact labeled "Steven".
As per the task, we are looking for an action or a button related to starting a chat with "Steven", which is not present.
Given this information, while the user is in the appropriate section to start a new chat, they have not yet started a chat with Steven.
Step 3: Output a JSON object structured like:
{
  "status": "go on",
  "reason": "The user has navigated to the 'Adding new chat and invite friends' section, which is consistent with the task of starting a new chat. However, there is no indication that a chat with 'Steven' has been started or is available in the current UI screen. Further actions are needed."
}
Based on the provided information, the user should continue their actions to search or scroll for "Steven" in the contacts list to complete the task.
"""
            },
            {
            "role": "user",
            "content": """Task:{}
Action trace:{}
Latest Page:{}
""".format(task,ACTION_TRACE,semantic_info)
    }]

def process_action_info(action, params, node):
    if action == "click":
        return "Action: Click on {}".format(node)
    elif action == "edit":
        return "Action: Edit {} with {}".format(node, params)
import openai

import json
import pickle
import os
import time
import spacy
import pandas as pd
import pickle
import os
import numpy as np
from typing import List, Tuple, Any


nlp = spacy.load("en_core_web_md")


def cache_decorator(function):
    def wrapped_function(*args, **kwargs):
        cache_file = kwargs['cache_file']

        if not os.path.exists(cache_file):
            result = function(*args, **kwargs)
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
            return result
        else:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
    return wrapped_function


@cache_decorator
def get_vectors_from_csv(csv_file: str, cache_file: str, field: str) -> Tuple[Any, List[Any]]:
    df = pd.read_csv(csv_file)
    database_texts = df[field].tolist()
    vectors = [nlp(text).vector for text in database_texts]
    return df, vectors  # Return the entire DataFrame


def get_top_similarities(s: str, csv_file: str, k: int, field: str) -> List[Any]:
    cache_file = csv_file.replace(".csv", "_"+field+".pickle")
    df, database_vectors = get_vectors_from_csv(
        csv_file=csv_file, cache_file=cache_file, field=field)
    database_texts = df[field].tolist()
    s_vector = nlp(s).vector
    similarities = [(row, np.dot(s_vector, vector) / (np.linalg.norm(s_vector) * np.linalg.norm(vector)))
                    for row, vector in zip(df.to_dict(orient='records'), database_vectors)]
    sorted_rows = [row for row, _ in sorted(
        similarities, key=lambda x: x[1], reverse=True)[:k]]
    return sorted_rows  # Returns top-k rows with all fields


def get_top_combined_similarities(queries, csv_file, k, fields):
    if len(queries) != len(fields):
        raise ValueError(
            "The length of 'queries' and 'fields' must be the same.")

    database_vectors_list = []
    for field in fields:
        cache_file = csv_file.replace(".csv", "_" + field + ".pickle")
        df, database_vectors = get_vectors_from_csv(
            csv_file=csv_file, cache_file=cache_file, field=field)
        database_vectors_list.append(database_vectors)

    # Calculate similarity vectors for each query
    similarity_vectors = [nlp(query).vector for query in queries]

    combined_similarities = []
    for index, row in enumerate(df.to_dict(orient='records')):
        product_similarity = 1
        for sim_vector, db_vectors in zip(similarity_vectors, database_vectors_list):
            product_similarity *= sim_vector.dot(db_vectors[index]) / (
                np.linalg.norm(sim_vector) * np.linalg.norm(db_vectors[index]))
        combined_similarities.append((row, product_similarity))

    sorted_rows = [row for row, _ in sorted(
        combined_similarities, key=lambda x: x[1], reverse=True)[:k]]

    return sorted_rows  # Returns top-k rows with all fields based on combined similarity


def get_top_combined_similarities_group(queries, csv_file, k, fields):

    database_vectors_list = []
    for field in fields:
        cache_file = csv_file.replace(".csv", "_" + field + ".pickle")
        df, database_vectors = get_vectors_from_csv(
            csv_file=csv_file, cache_file=cache_file, field=field)
        database_vectors_list.append(database_vectors)

    # Calculate similarity vectors for each query
    similarity_vectors = [[nlp(query[0]).vector, nlp(
        query[1]).vector] for query in queries]

    top_results = []

    for query_set in similarity_vectors:
        if len(query_set) != len(fields):
            raise ValueError(
                "Each query set must have the same length as 'fields'.")
        # Calculate similarity vectors for each query in the set
        combined_similarities = []
        for index, row in enumerate(df.to_dict(orient='records')):
            product_similarity = 1
            for sim_vector, db_vectors in zip(query_set, database_vectors_list):
                product_similarity *= sim_vector.dot(db_vectors[index]) / (
                    np.linalg.norm(sim_vector) * np.linalg.norm(db_vectors[index]))
            combined_similarities.append((row, product_similarity))

        sorted_rows = sorted(
            combined_similarities, key=lambda x: x[1], reverse=True)[:1]
        if sorted_rows[0][1] > 0.999:
            top_results.append(sorted_rows[0][0])
        else:
            top_results.append("Not found")
    return top_results


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
                with open(store_path, 'w', encoding="utf-8") as f:
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
            json_res = result[result.find("{"):result.rfind("}")+1]
            json_res = json_res.replace('\\', '\\\\')
            result_json = json.loads(json_res)
            return result_json
        except Exception as e:
            print(e)
            continue


def process_action_info(action, params, node):
    if action == "click":
        return "Action: Click on {}".format(node)
    elif action == "edit":
        return "Action: Edit {} with {}".format(node, params)


def task_grounding_prompt(task, similar_tasks, similar_traces, previous_action, current_ui):
    return [
        {
            "role": "system",
            "content": """
You are an expert in User Interface (UI) automation. Your task is to predict the actual execution steps of user's intent based on your knowledge.
You are given the original user's intent and a list of ground-truth of similar task-executions on UI.
Based on your knowledge, reasonably predict, and synthesize the step-by-step execution tutorials of the user's intent.
You are also given some examples of similar tasks and their executions, which you can refer to and help you figure out the tutorial of user's execution
The output of each step of the tutorial should clearly seperate each step to a function and with parameters (if have), such as Click("My contact"), Edit("Name", "Steven").

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
        },
        {
            "role": "user",
            "content": """Additionally,you are also given the [previous Action Trace] and the [current UI screen], which you can refer to and help you adjust the tutorial based on the real circumstance on UI.
Previous Action:{}
Current UI:{}
Attention: you should pay attention to the ACTION_TRACE["ACTION"] and more, it conveys the user's actions till now,where some BACK action may occur indicating possible error, you should adjust your tutorial based on it.
                    """.format(previous_action, current_ui)
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


def Task_UI_grounding_prompt(task, current_path_str, similar_tasks, similar_traces, predicted_step, semantic_info_list, next_comp, Knowledge):
    # Follow steps below:
    # Step 1: Think step by step about how there two kinds of knowlegde lead you to score the UI elements.
    # Step 2: Output a JSON object with scores and reasoning. 
    
    return [
        {
            "role": "system",
            "content": """You are a mobile UI expert acting as a "Judger". Your specialized role focuses on guiding the user to complete the user task on specific UI screen.
Only guiding by your knowledge is irreliable , so you are give two kinds of ground-truths, they are:
1, the tutorial of how to fulfill the task, estimated through retriving the knowledge libraray and learned from similar tasks.
2, current extended UI screen, which contains the components of current UI screen and their corresponding interaction results.
Basically the tutorial represents how to do the task conceptually without grounding and the UI screen represents the ground-truth. You need to conbine them, thus build a connection between them.
Finnaly, your job is to rate the available options on the current page based on your grounding. For each option, provide a confidence rating from 1.0-10.0, where 1.0 indicates 'definitely no' and 5.0 indicates 'normal' and 10.0 indicates 'most likely'
Note that you should only output elements with ratings >= 3.
The structure of the output should be: {"id_x": <rating>, ...}, where "id_x" is the id of an operational element (you should replace "x" with an actual value), and "<rating>" denotes its rating. If the rating of an element is less than 3.0, you should not display it in the final result.
Example:
{
    "id_2": 9.5, "id_5": 9.0, "id_11": 3.5
}
"""
        },
        {
            "role": "user",
            "content": """Task: "{}".
Current path: {}.
Examples:{}
Estimated tutorial: {}
These tutorials serve as hints, they are not absolutely right and may be subjective so do not score all by them.
Current UI:
'''HTML
{}
'''
Successive results of current UI:
{}
REMEMBER always give Back buttons like "Navigate up" the score of 1.0, they are not allowed to perform.
NOTE that your scoring should be diverse between all of them, avoid giving same scores to some of them in case of identication.
""".format(
                task,
                current_path_str,
                [j+":"+"=>".join(k) for j, k in zip(
                    similar_tasks, similar_traces)],
                predicted_step,
                "".join(semantic_info_list),
                next_comp
            )
        }, {
            "role": "user",
            "content": """Knowledge:
{}
These are knowledge accumulated form previous task execution iterations, you should think step by step about how these would guide you to score each components.
""".format(Knowledge)
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


def decide_prompt(task, ACTION_TRACE, semantic_info, Knowledge):
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
Especially, [] means it's empty in the latest page and cannot go on.
""".format(task, ACTION_TRACE, semantic_info)
    },
        {
        "role": "user",
            "content": """Knowledge:
{}
These are knowledge accumulated form previous task execution iterations, you should think step by step about how these would guide you to score each components.
""".format(Knowledge)
    }]


def Knowledge_prompt(TASK, ACTION_TRACE):
    return [
        {
            "role": "system",
            "content": """You are an active learner in User Interface (UI) automation. Your task is to learn and summarize UI automation pieces of knowledge from completed User Task and Action Trace.
You are given the User's Task and an actual action trace of it. Use the following steps to think:
1, Try to reproduce the ACTION_TRACE while keeping an eye on each page and analyzing each steps' insights provided. Reason step by step on the insights of the relationship between TASK and ACTION-TRACE from a higher level and generate SOFT knowledge of connecting them, it could be hints, experiences, or shortcuts.
    1.1, Specificly, think step by step on what kind of SOFT knowledge can be extracted from them to guide better action-selection, which means how an AI agent choose correct next-step when exploring in the UI.(i.e. "In settings page, network functions would be more related to 'Newwork' button"......)
    1.2, Then think step by step on what kind of SOFT knowledge can be extracted from them to guide better status-decision, which means how an AI agent decide the status of task execution, either finished or in-the-process or wrong. (i.e. "If a switch button is clicked from off to on, that would imply that the completion of 'Turn on XXX' task")
2, Follow the action trace to reproduce the execution process, focusing on the error backtracking process (that is, when the traces go wrong and then navigate back to correct). Think step by step about each backtrack, analyze if they are essential, and summarize error knowledge from them; it could be notices, traps, or other formats. ("i.e. ,"XXX means a possible wrong exection when YYY, you should be aware of ZZZ")
"""
        }, {
            "role": "user",
            "content": """TASK:{}
ACTION TRACE:{}
Be smart and insightful, think step by step, finally,summarize them into a json format:""".format(TASK, ACTION_TRACE)
        },
        {
            "role": "user",
            "content": """'''HTML
{
    "selection":[](organize as a list if have)
    "decision"[](organize as a list if have)
    "error-handling":[](organize as a list if have)
}'''"""
        }
    ]


def process_action_info(action, params, node):
    if action == "click":
        return "Action: Click on {}".format(node)
    elif action == "edit":
        return "Action: Edit {} with {}".format(node, params)


def process_string(s):
    return s.replace('\n', '').replace(',', ';;')


def generate_perform(action_type, x=0, y=0, text="", absolute_id=""):
    return {
        "node_id": 1,
        "trail": f"[{x},{y}]",
        "action_type": action_type,
        "text": text,
        "ori_absolute_id": absolute_id
    }


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
                l[index_son] + " </" + l[index_father][last_index + 3:]
        l[index_son] = ""
    return list(filter(lambda x: x != "", l))

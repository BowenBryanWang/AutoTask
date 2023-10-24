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
    df = pd.read_csv(csv_file, delimiter=',')
    database_texts = df[field].tolist()
    vectors = [nlp(text).vector for text in database_texts]
    return df, vectors  # Return the entire DataFrame


def get_top_similarities(s: str, csv_file: str, k: int, field: str) -> List[Any]:
    cache_file = csv_file.replace(".csv", "_"+field+".pickle")
    if os.path.exists(cache_file):
        os.remove(cache_file)
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
        if os.path.exists(cache_file):
            os.remove(cache_file)
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
            for iindex, (sim_vector, db_vectors) in enumerate(zip(query_set, database_vectors_list)):
                s = sim_vector.dot(db_vectors[index]) / (
                    np.linalg.norm(sim_vector) * np.linalg.norm(db_vectors[index]))
                if iindex == 1 and s < 0.99:
                    product_similarity *= 0
                else:
                    product_similarity *= s
            combined_similarities.append((row, product_similarity))

        sorted_rows = sorted(
            combined_similarities, key=lambda x: x[1], reverse=True)[:1]
        if sorted_rows and sorted_rows[0][1] > 0.9:
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


def extract_json(input_string):
    stack = []
    json_start_positions = []

    json_strings = []

    for pos, char in enumerate(input_string):
        if char in '{[':
            stack.append(char)
            if len(stack) == 1:
                json_start_positions.append(pos)
        elif char in '}]':
            if len(stack) == 0:
                raise ValueError(
                    "unexpected {} at position {}".format(pos, char))
            last_open = stack.pop()
            if (last_open == '{' and char != '}') or (last_open == '[' and char != ']'):
                raise ValueError(
                    "mismatched brackets {} and {} at position {}".format(last_open, char, pos))
            if len(stack) == 0:
                json_strings.append(
                    input_string[json_start_positions.pop():pos+1])
    return json_strings


def GPT(prompt, auto_correct_when_json_error=True):
    while True:
        try:
            result = chat(prompt=prompt)
            jsons = extract_json(result)
            json_res = jsons[-1]  # 只处理最后一个json
            if not auto_correct_when_json_error:
                result_json = eval(
                    json_res, {'true': True, 'false': False, 'null': None})
            else:
                try:
                    result_json = eval(
                        json_res, {'true': True, 'false': False, 'null': None})
                except Exception as e:
                    result_json = correct_json_format(
                        json_str=json_res, error=e)
            return result_json
        except Exception as e:
            print(e)
            continue


def correct_json_format(json_str, error):
    prompt = [{
        'role': 'system',
        'content': f'the following string cannot be parsed to a dict (or list) by the built-in function eval (in Python) due to the error: {str(error)}.\n\n{json_str}\n\nPlease correct its format error and output the correct string. Do not output anything else.'
    }]

    return GPT(prompt, auto_correct_when_json_error=False)


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
                    """.format(task, [j+":"+k for j, k in zip(similar_tasks, similar_traces)])
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


def UI_grounding_prompt_only_summary(predict_node):
    return [
        {
            "role": "system",
            "content": """You are an expert in User Interface (UI) automation. Your task is to describe the current page. You are given a list of UI components and their attributes. 
1. Reason step-by-step about the short one-sentence description of the current page.
2. Output the predictions in a JSON formated like:
{
"Page": "..."(One-sentence description of the current page),
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

    return [
        {
            "role": "system",
            "content": """You are a mobile UI expert acting as a "Judger". Your specialized role focuses on guiding the user to complete the user task on specific UI screen.
Your job is to
(1) summary what has been done according to the History Operation Sequecnce;
(2) decide what general direction should we go next according to the relationship of elements on the CURRENT UI and USER TASK. 
(3) think step by step on the Succesive Results of each UI options, which represents the subsequent items after operating on them. They can indicate the ground-truth operation results which is rather important to fulfilling User Task
(4) choose the next UI element to be operated considering the user task, the history operation sequence, and the current UI. You should rate the available UI elements on the current page. 
    (4.1) The element with the largest rating will be choosen as the next element to be operated.
    (4.2) Your score should be accurate to two decimal places.
    (4.3) If you think none of the elements can be the next to be operated, you can try to explore the UI to gather more information and rating the elements according to their semantic simialrities with the user task.
For each option, provide a confidence rating from 1.00-10.00, based on the relation of each option to the task, where 1.00 is the lowest tier indicating complete irrelevance and may lead to errors, 3.00 is the second tier indicating minor relevance, 5.00 is the medium tier indicating neutrality, 7.00 indicates higher relevance, possibly a candidate, and 10.00 indicates the most likely to be chosen and executed.
The structure of the output should be: {
    "finished_steps": [...],
    "next_steps": [...],
    "id_x": <rating>, ...}, where "id_x" is the id of an operational element (you should replace "x" with an actual value and iterate over all possible values), and "<rating>" denotes its rating.
Example:
{
    "finished_steps": ["Click('Alice')"]
    "next_steps": ["Edit('hi')", "Click('Send')"]
    "id_1": 5.53, "id_2": 9.71, "id_3": 3.20
}
Think step by step and output your reasoning process: 
Step 1: what has been done,especially pay attention to those steps which is wrong and caused navigate back if any;
Step 2: think step by step on the Succesive Results of each UI options (if the results exist. Note that sometimes the UI is not fully explored and the results are unknown. However, the element may still be the next to be operated), which represents the subsequent items after operating on them. They can indicate the ground-truth operation results which is rather important to fulfilling User Task
Step 3: decide what should be done next. Possible operations: click, edit (text input); "scroll" is NOT supported. Pay attention to those steps which is wrong and caused navigate back if any;
Step 4: Synthesize the above output a conclusion and output a JSON object with scores. 
"""
        },
        {
            "role": "user",
            "content": """Task: "{}".
History operation sequence: {}.
Examples:{}
Current UI:
'''HTML
{}
'''
Successive results of current UI:
{}
REMEMBER always assign Back buttons like "Navigate up" the score of 1.0, they are not allowed to perform.
""".format(
                task,
                current_path_str,
                [j+":"+k for j, k in zip(
                    similar_tasks, similar_traces)],
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


def plan_prompt(task, page_description, node_selected, next_step):
    action_names = ['click']
    action_desc = ['clicking on a component (no text parameter needed)']
    if 'editable' in node_selected and 'ineditable' not in node_selected:
        action_names.append('edit')
        action_desc.append(
            'editing a component (you should also determine the text parameter)')

    newline = '\n'
    return [
        {
            "role": "system",
            "content":
                f"""You are an AI assistant specialized in UI Automation. Now you have successfully obtained the top UI component that are most likely to operate with based on user's intent. Now, you need to determine the action to be performed on it.
There {'are' if len(action_desc) > 1 else 'is'} {len(action_desc)} main type{'s' if len(action_desc) > 1 else ''} of action{'s' if len(action_desc) > 1 else ''}:
{newline.join([f'{idx+1}. {content}' for idx, content in enumerate(action_desc)])}
For the top component, analyze the possible action to be taken and, if it involves an editing action, provide the corresponding text parameter as well.
Reason step by step to provide the actions and text parameters for it based on the user's intent and the context of the current screen.
Output a JSON object structured like
{{
    "action": the action to be taken, {' or '.join(action_names)},
    "text": the text parameter for the action if any (Optional),
}},
"""
        },
        {
            "role": "user",
            "content": """
                Task: {},
Current Page : {}:
Top Candidate:{}
Estimated next step:{} (Note, this is generated by the Evaluation Module who selected the Top candidate, so you can refer to)
,""".format(task, page_description, node_selected, next_step)
        }
    ]


def decide_prompt(task, last_action, ACTION_TRACE, semantic_info, Knowledge):
    prompt = [{
        "role": "system",
        "content": """You are a professor with in-depth knowledge of User Interface (UI) tasks. You are assigned a specific UI task, a history operation sequence, and the current UI (which is the result of the last action).
Your task is to evaluate if the operation sequence and the current UI can further lead to the user task fulfillment. You should categorize the STATUS as:
1,completed: After the Latest action and the subsequent newest UI screen, the user's task is completed;
2,wrong: After the Latest action and the subsequent newest UI screen, the Last Action is not correct and the current UI cannot further lead to the UI task anymore (You should choose "wrong" if you think navigating back is necessary to finish the task).
3,go on: After the Latest action and the subsequent newest UI screen, the Last Action is on the correct track, which means the agent can continue to perform further operations (excluding navigating back) to complete the task. Further Actions should be taken on the current (may also be the subsequent pages) UI page.
Use the following steps to respond. Fully restate each step number before proceeding. i.e. "Step 1".
Step 1:Reason step-by-step about the the history ACTIONs (especially the last action leading to the Current UI)and UI TASK. Whether Last Action can contribute to fulfill the user's task IN THE LONG RUN?
Step 2:Reason step-by-step about whether LATEST UI PAGE can further lead to the UI task fulfillment IN THE LONG RUN. Can any element on screen be operated next to lead to the fulfillment of the task?
Step 3:Synthesize the above thoughts and output a conclusion on the STATUS as a JSON object structured like: 
{
    "next ui element": if the value of the status is "go on", please also output the next ui element to be operated. The status should not be "go on" if none element in the UI page can be the next.
    "status": "completed" or "wrong" or "go on". Attention that only when "next ui element" refers to a valid element on the screen can you choose "go on"
    "reason": reason for the decision,
}."""
    },
        {
        "role": "user",
            "content": """Task:{}
Last Action:{}
NOTE in this History Pages and Action Dict format:
1, Here "Page_X"  means each page UI elements that the user has gone through.
2, Here "Action_x_to_y"  means the action which operated on x and leads to y.
History Pages and Action Dict:{}

Latest UI Page:{}
([] means it's empty in the latest page and cannot go on)
""".format(task, last_action, ACTION_TRACE, semantic_info)
    }]
    if Knowledge:
        prompt.append({
            "role": "user",
            "content": """Knowledge:
{}
These are knowledge accumulated form previous task execution iterations, you should think step by step about how these would guide you to the correct answer.
""".format(Knowledge)
        })
    return prompt


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
        return "Click on {}".format(node)
    elif action == "edit":
        return "Edit {} with {}".format(node, params)


def process_string(s):
    if s:
        return s.replace('\n', '').replace(',', ';')
    else:
        return ""


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


def decouple_HTML(h: str) -> str:
    l = h.split(" ")[1:]


def process_ACTION_TRACE(ACTION_TRACE):
    actions = ACTION_TRACE["ACTION"]
    pages = ACTION_TRACE["PAGES"]
    result_dict = {}

    for i in range(len(pages)):
        result_dict[f'Page_{i}'] = pages[i]
        if i < len(actions):  # Ensure we don't go out of bounds
            result_dict[f'Action_{i}_to_{i + 1}'] = actions[i]

    return result_dict

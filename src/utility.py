from typing import List
import traceback
import re
import copy
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


if os.path.exists('./cache/ebd.pickle'):
    with open('./cache/ebd.pickle', 'rb') as f:
        cache = pickle.load(f)
else:
    cache = {}


def cal_embedding(text, model_name='text-embedding-ada-002'):
    if type(text) == str:
        return cal_embedding([text], model_name)[0]
    to_call_text = [x for x in text if x not in cache]
    if len(to_call_text) > 0:
        while True:
            try:
                result = openai.Embedding.create(
                    model=model_name,
                    input=to_call_text
                )
                break
            except Exception as e:
                traceback.print_exc()
                time.sleep(2)

        for idx, d in enumerate(result['data']):
            cache[to_call_text[idx]] = d['embedding']
        with open('./cache/ebd.pickle', 'wb') as f:
            pickle.dump(cache, f)
    return [cache[x] for x in text]


def cal_similarity(v1, v2):
    vec1 = np.array(v1)
    vec2 = np.array(v2)
    return vec1.dot(vec2)  # / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def sort_by_similarity(q: str, a_list: List[str]):
    q_ebd = cal_embedding(q)
    a_ebds = cal_embedding(a_list)

    extend_a = [(a, cal_similarity(q_ebd, a_ebd))
                for a, a_ebd in zip(a_list, a_ebds)]
    return extend_a


def sort_by_similarity_with_index(q: str, a_list: List[str], index_list: List[int]):
    q_ebd = cal_embedding(q)
    a_ebds = cal_embedding(a_list)

    extend_a = [(index+1, a, cal_similarity(q_ebd, a_ebd))
                for index, a, a_ebd in zip(index_list, a_list, a_ebds)]
    return extend_a


def sort_by_similarity_score(q: str, a_list: List[str]):
    q_ebd = cal_embedding(q)
    a_ebds = cal_embedding(a_list)

    extend_a = [cal_similarity(q_ebd, a_ebd)
                for a_ebd in a_ebds]
    return extend_a


def cal_similarity_one(q: str, a: str):
    q_ebd = cal_embedding(q)
    a_ebd = cal_embedding(a)
    return cal_similarity(q_ebd, a_ebd)


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
                    store_path, f"{int(time.time() * 1000)}{args.get('tag')}{'cache' if cache_used else ''}.txt")
                with open(store_path, 'w', encoding="utf-8") as f:
                    f.write(
                        '\n'.join([f'{x["role"]}:\n{x["content"]}\n' for x in args['prompt']]))
                    f.write('\n')
                    f.write('===response===\n')
                    f.write(cache[arg_s])
            return cache[arg_s]
        return new_func
    return decorator


@persist_to_file("./cache/gpt_cache.pickle")
def chat(prompt, tag):
    print('connecting to gpt')
    response = openai.ChatCompletion.create(
        model='gpt-4-1106-preview',
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


def GPT(prompt, auto_correct_when_json_error=True, tag=None):
    while True:
        try:
            result = chat(prompt=prompt, tag=tag)
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
    elif action == "scroll_forward":
        return "Action: Scroll forward"
    elif action == "scroll_backward":
        return "Action: Scroll backward"


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


def Task_UI_grounding_prompt(task, current_path_str, semantic_info_list, next_comp, Knowledge, UI_long_term_knowledge, hint):
    content = {}
    content["Task"] = task
    content["History operation sequence"] = current_path_str
    content["Current UI screen"] = "".join(semantic_info_list)
    content["Successive results"] = next_comp
    if hint is not None and hint["status"] == "go on":
        content["Hint"] = "Below is a hint and suggestion from another model" + \
            json.dumps(hint)
    if Knowledge:
        content["Knowledge"] = Knowledge
    if UI_long_term_knowledge:
        content["possible paths to UI target"] = UI_long_term_knowledge

    p = [
        {
            "role": "system",
            "content": """You are a mobile UI expert acting as a "Judger". Your specialized role focuses on guiding the user to complete the user task on specific UI screen.
Your job is to rate the available UI elements on the current page.
Note that:
    (1) The element with the highest score will be choosen as the next element to be operated. If you have more than one top scoring option in your scoring, it's a good idea to highlight the score of one of the most likely candidates to avoid confusion.
    (2) Your score should be accurate to two decimal places.
    (3) If you think none of the elements can be the next to be operated, you can try to explore the UI to gather more information and rating the elements according to their semantic simialrities with the user task.
    (4) <scroll /> element means there is a list and you can interact with it by scrolling forward. If you want to explore more, you can also try giving <scroll/> a relatively high scorat. The score of the <scroll /> should always be higher than that of those appearantly unrelated with the task.
For each option, provide a confidence rating from 1.00-10.00, based on the relation of each option to the task, where 1.00 is the lowest tier indicating complete irrelevance and may lead to errors, 2.00-4.00 is the second tier indicating minor relevance, 4.00-6.00 is the medium tier indicating neutrality, 6.00-8.00 indicates higher relevance, possibly a candidate, and 10.00 indicates the most likely to be chosen and executed.
The structure of the output should be: {
    "id_x": <rating>, ...}, where "id_x" is the id of an operational element (you should replace "x" with an actual value and iterate over all possible values), and "<rating>" denotes its rating.
Example:
{
    "id_1": 5.53, "id_2": 9.71, "id_3": 3.20
}
Think step by step and output your reasoning process:
Step 1: think about ["History operation sequence"],what has been done,especially pay attention to those steps which is wrong and caused navigate back if any;
Step 2: think step by step on the ["Succesive Results"] of each UI options GIVEN by user, which represents the subsequent items after operating on them, and the ["possible paths to UI target"] GIVEN by user, which was suggested by expert knowledge;
Step 3: decide what should be done next. Possible operations: click, edit (text input), scroll. Pay attention to those steps which is wrong and caused navigate back if any;
Step 4: Synthesize the above output to output a JSON object with scores.

Strictly output a format like "id_1": 3.00, do not tamper with it to make it look like "scroll_1": 3.00, etc., it must start with id_.
"""
        },
        {
            "role": "user",
            "content": json.dumps(content, indent=4)
        }]
    return p


def plan_prompt(task,  page, node_selected, suggestion):
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
{newline.join([f'{idx+1}. {content}' for idx,
              content in enumerate(action_desc)])}
For the top component and the overall page, analyze the possible action to be taken and, if it involves an editing action, provide the corresponding text parameter as well.
Reason step by step to provide the actions and text parameters for it based on the user's intent and the context of the current screen.
Consider the suggestion from the selector
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
Page Components:{}
Top Candidate:{}
Suggestion from selector:{}
,""".format(task, page, node_selected, suggestion)
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
Step 3:Reason step-by-step about whether there are any elements with GENERAL proposes that are worthy being explored. If any, you should also choose "go on" and explore them. A kind note: if you find <scroll /> elements, it means that you can try to scroll forward to explore more elements on the screen. so you can also choose "go on" if you think there are elements worthy being explored.
Step 4:Synthesize the above thoughts and output a conclusion on the STATUS as a JSON object structured like:
Hint:
1, if the history operation sequence actually indicates the completion, should consider "completed", i.e. Last step clicking OK may lead to completion
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


def Knowledge_prompt(TASK, ACTION_TRACE, log, l):
    content = {}
    content["TASK"] = TASK
    content["ACTION_TRACE"] = ACTION_TRACE
    content["Log"] = log
    content["Error_pieces"] = []
    for Page, Action in l:
        content["Error_pieces"].append(
            [i for j in zip(Page, Action) for i in j])
    return [
        {
            "role": "system",
            "content": """You are an active learner in User Interface (UI) automation. Your task is to learn and summarize UI automation pieces of knowledge from completed User Task and Action Trace.
You are given the User's Task and a log of ACTION_TRACE generated by another AI agent. 
The other AI agent is an intelligent AI for UI task execution, which has a workflow of [predict-evaluate-decide], i.e., it first calculates the follow-up of each page according to the UI Pagejump database, then scores the elements on the page related to the user's task, and finally decides the status of task completion. Eventually the task is completed successfully.
The accuracy of this AI agent needs to be improved, so your task is to analyse the work log of this AI agent to help it summarise and analyse the illuminating knowledge that may be present in each step of the process, which will be subsequently injected into the AI agent to aid better task execution!
You are given:
{
    "TASK": "..."(User's Task),
    "ACTION_TRACE": "..."(ACTION_TRACE),
    "Log":[](Detailed LOG from the other AI agent),
    "Error_pieces": [Page1,Action1-2.Page2,...](Error_pieces extracted from ACTION_TRACE, which you should deeply analyse and summarize knowledge from),
}
Use the following steps to think:
1, Observe the correct part of the UI execution path of the task as described in TASK and ACTION_TRACE (excluding the error branches such as navigate back), to provide ground-truth for the subsequent analysis.
2, Analyse the extracted Error_pieces, they are the error branches that appeared when the AI agent explored the task execution on the UI, fortunately these errors were successfully recovered by the agent's error correction session, which led to the final completion of the task. But these errors also indicate that the Agent's understanding of the task was off during execution, you need to analyse these errors and summarise the knowledge for subsequent error correction. You need:
    2,1: Replicate Error_pieces and observe each new page that is accessed by incorrect operation due to selection, and analyse the gap with the ground-truth summarised in the first step;
    2,2: Summarise the reasons why this part of Error_pieces is wrong, is it due to the lack of relevant UI experience in the [Prediction] phase? Or is it due to an error in the scoring or reasoning of the AI agent during [Selection]? Or is it due to a simple [decision-making] error?
        2.2.1: If an error is caused by the lack of UI knowledge, it means that the error in this step is caused by the AI agent's lack of UI knowledge in the [Prediction] stage, i.e., it doesn't know what will be caused by clicking this button; if the error is caused by the error in selection, it means that there is a problem with the AI agent's analysis and scoring, and it is that the agent itself is not competent enough If the error is due to an error in [Decision], it means that the agent don't know how to decide the task status as wrong or right.
    2.3: After thinking about the reasons for the mistakes, summarise the inspiring knowledge contained therein, noting that this part of the knowledge will be injected into the other AI agent for the subsequent execution of the UI task.
    2.4: Bind the knowledge to the page, i.e., the page on which this knowledge is found, so that it can help the other AI agent to better choose the correct action in the subsequent execution of the task. Bind the type of knowledge, is it the knowledge of [Prediction], [Execution] or [Decision] stage?
3, if you feel that there is valuable knowledge throughout the execution of the task, you can also summarise it;
4, summarise and output as a json file in the following format:
'''HTML
{
    "prediction":[{"knowledge":"","index":"Page_x"}](organize as a list if have,remove x in Page_x to indicate the page index in ACTION_TRACE["PAGES"] starting from Page_0 )
    "selection":[{"knowledge":"","index":"Page_x"}](organize as a list if have,remove x in Page_x to indicate the page index in ACTION_TRACE["PAGES"] starting from Page_0)
    "decision"[{"knowledge":"","index":"Page_x"}](organize as a list if have,remove x in Page_x to indicate the page index in ACTION_TRACE["PAGES"] starting from Page_0)
}'''
NOTE:
a, You should generate inspiring and high-level and concrete knowledge that is relevant to the task exection and valuable for the agent to follow, don't just copy the error or generate simple and meaningless knowledge that is common knowledge or generate ambiguous knowledge that is not helpful for the agent to follow.
    a.1:Good example: "When the user wants to add a new contact, the agent should not click the "Add" button on the main page, but should click the "Add" button on the contact page."
                "when the user enter into a form page, it should input all the necceary information first and then click the "Submit" button to submit the form."
    a.2:Bad example: "The agent should optimize the scoring process"(too abstract)
                "Scroll forward to explore more elements"(already known common knowledge)
                "if agent enters into a page with no relevant pages, should recognize wrong and navigate back"(already known by the agent)
                "When the task is to change an application setting such as a theme, prioritize selecting the 'Settings' option from the menu."(too meaningless and not valuable, the agent already known)
                "When task is XXX, A should be clicked rather than B" (too specific and not valuable, not generalizable)
"""}, {
            "role": "user",
            "content": json.dumps(content, indent=4)
        },
    ]


def process_action_info(action, params, node):
    if action == "click":
        return "Click on {}".format(node)
    elif action == "scroll_forward":
        return "Scroll forward on {}".format(node)
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
    result_dict = copy.deepcopy(ACTION_TRACE)

    for i in range(len(pages)):
        result_dict[f'Page_{i}'] = pages[i]
        if i < len(actions):  # Ensure we don't go out of bounds
            result_dict[f'Action_{i}_to_{i + 1}'] = actions[i]

    return result_dict


def coverage(text1, text2):
    if isinstance(text1, str) and isinstance(text2, str):
        words1 = set(text1.split())
        words2 = set(text2.split())
    elif isinstance(text1, list) and isinstance(text2, list):
        words1 = set(text1)
        words2 = set(text2)

    common_words = words1.intersection(words2)

    return len(common_words) / max(len(words1), len(words2))


def simplify_ui_element(html_str):
    # 移除id属性
    html_str = re.sub(r'\sid=[\'"]?\w+[\'"]?', '', html_str)

    # 移除空属性
    html_str = re.sub(r'\s\w+=(\'\'|\"\")', '', html_str)

    # 移除HTML标签
    html_str = re.sub(r'</?\w+\s*', '', html_str)

    # 提取属性值
    html_str = re.sub(r'\w+=', '', html_str)

    # 移除结尾的 '>'
    html_str = re.sub(r'>', '', html_str)

    # 压缩多余空格
    html_str = re.sub(r'\s+', ' ', html_str).strip()

    return html_str if html_str != "" else " "


def simplify_ui_element_id(html_str):
    # 移除id属性
    html_str = re.sub(r'\sid=[\'"]?\w+[\'"]?', '', html_str)

    return html_str if html_str != "" else " "

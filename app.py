import pickle
import pandas as pd
from openai.embeddings_utils import (
    get_embedding,
    cosine_similarity,
    distances_from_embeddings,
    tsne_components_from_embeddings,
    chart_from_components,
    indices_of_nearest_neighbors_from_distances,
)
import os

import openai
import re
from flask import Flask, redirect, render_template, request, url_for
import cv2
from flask import Flask
from flask import request
import os
import base64
from page.init import Screen
from page.WindowStructure import *
import time
from page.NodeDescriberManager import *
import json
import numpy as np
from flask_socketio import SocketIO
from flask import Flask
from flask_sockets import Sockets
import datetime

from src.model import Model


app = Flask(__name__)

openai.api_key = "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"
layout = None
screenshot = None
imgdata = None
cnt = 0
semantic_nodes = []
describermanagers = {}

i = 0
prompt_now = ""
intention = ""
intent_embedding = None
html_detect = False
agenda_detect = False
upload_time = None
time_between_upload = 1
all_text = ""  # 当前页面的所有文本
describermanagers_init = False
page_root = None
semantic_info = []
chart_data = {
    'labels': [],
    'datasets': [
        {
            'data': [],
            'backgroundColor': [
                'rgb(255, 99, 132)',
                'rgb(54, 162, 235)',
                'rgb(255, 205, 86)',
                'rgb(75, 192, 192)',
                'rgb(153, 102, 255)'
            ],
            'hoverOffset': 4
        }
    ]
}
line_data = {
    "labels": [],
    "datasets": [
        {
            "label": 'Similarity',
            "data": [],
            "pointStyle": 'circle',
            "pointRadius": 10,
            "pointHoverRadius": 15
        }
    ]
}
result = ""
img_id = 1
GLOBAL_STATE = "Not Started"
center = {"x": 0, "y": 0}


current_path = ["Homepage"]
current_path_str = "Homepage"
anchors = []
stepbacks = -1
probs = []
EMBEDDING_MODEL = "text-embedding-ada-002"

embedding_cache_path = "embeddings_cache.pkl"

# load the cache if it exists, and save a copy to disk
try:
    embedding_cache = pd.read_pickle(embedding_cache_path)
except FileNotFoundError:
    embedding_cache = {}
with open(embedding_cache_path, "wb") as embedding_cache_file:
    pickle.dump(embedding_cache, embedding_cache_file)

# define a function to retrieve embeddings from the cache if present, and otherwise request via the API
sims = []


def embedding_from_string(
    string: str,
    model: str = EMBEDDING_MODEL,
    embedding_cache=embedding_cache
) -> list:
    """Return embedding of given string, using a cache to avoid recomputing."""
    if (string, model) not in embedding_cache.keys():
        embedding_cache[(string, model)] = get_embedding(string, model)
        with open(embedding_cache_path, "wb") as embedding_cache_file:
            pickle.dump(embedding_cache, embedding_cache_file)
    return embedding_cache[(string, model)]


def expand_seq(inst_seq: list) -> list:
    inst_seq_str = str(inst_seq)
    q = [
        {"role": "system",
         "content": """You are an assistant translating user's instruction sequence to more detailed, longer, clearer and more precise description.One sentence only!"""},
        {"role": "user",
         "content": """['Homepage', 'Bowen', 'Chat Info','Bowen','Moments]"""},
        {"role": "assistant",
         "content": """['Go to the homepage','Navigate to Bowen's profile from the homepage','Click on “Chat info” while on Bowen's profile page','From the “Chat info” page, select Bowen's profile.','Once on Bowen's profile, click on “Moments”']"""},
        {"role": "user",
         "content": """['Homepahe','Me','Settings','General','Dark Mode']"""},
        {"role": "assistant",
         "content": """['Go to the homepage of the website or application.','Once on the homepage, click on “Me” to access your user profile or account settings.','From there, navigate to the “Settings” section.','In the “Settings” section, select “General”.','Finally, click on “Dark Mode” to activate it and switch your interface to the dark mode.']"""},
        {"role": "user",
         "content": inst_seq_str},
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=q,
        temperature=0.5,
    )
    inst_seq_str = response["choices"][0]["message"]["content"]
    print(inst_seq_str)
    inst_seq = inst_seq_str.split("','")
    inst_seq = [inst.replace("['", "").replace("']", "") for inst in inst_seq]
    return inst_seq


def init_describer():
    print("loadmodel")
    global relation_dict
    with open('./static/data'+'/manager_structure.json', 'r', encoding='utf-8') as file:
        describermanagers_str = json.load(file)
        global describermanagers
        for key, value in describermanagers_str.items():
            value = json.loads(value)
            print("loading", key)
            if key == "Root Object;":
                describermanagers[key] = NodeDescriberManager(
                    "Root", None, "Root Object;")
            if key.count(";") > 1:
                p_last = key.split(";")[-2]
                model_fa_id = key.replace(p_last+";", "")
                describermanagers[key] = NodeDescriberManager(
                    value["type"], describermanagers[model_fa_id], key)
                describermanagers[model_fa_id].update_children(
                    describermanagers[key])
                tmp_positive_ref_nodes = []
                tmp_negative_ref_nodes = []
                tmp_positive_nodes = []
                for node_info in value["positive_ref"]:
                    with open('static/data/'+'page' + str(node_info["page_id"]) + '.json', 'r')as fp:
                        tmp_layout = json.loads(fp.read())
                    tmp_page_instance = PageInstance()
                    if isinstance(tmp_layout, list):
                        tmp_layout = tmp_layout[0]
                    tmp_page_instance.load_from_dict("", tmp_layout)
                    tmp_page_root = tmp_page_instance.ui_root
                    tmp_node = tmp_page_root.get_node_by_relative_id(
                        node_info["index"])
                    tmp_node.update_page_id(node_info["page_id"])
                    tmp_positive_ref_nodes.append(
                        (tmp_node.findBlockNode(), tmp_node))
                for node_info in value["negative_ref"]:
                    print("node_info", node_info)
                    with open('static/data/'+'page' + str(node_info["page_id"]) + '.json', 'r')as fp:
                        tmp_layout = json.loads(fp.read())
                    tmp_page_instance = PageInstance()
                    if isinstance(tmp_layout, list):
                        tmp_layout = tmp_layout[0]
                    tmp_page_instance.load_from_dict("", tmp_layout)
                    tmp_page_root = tmp_page_instance.ui_root
                    print(node_info["page_id"],
                          tmp_page_root.generate_all_text())
                    tmp_node = tmp_page_root.get_node_by_relative_id(
                        node_info["index"])
                    tmp_node.update_page_id(node_info["page_id"])
                    tmp_negative_ref_nodes.append(
                        (tmp_node.findBlockNode(), tmp_node))
                for node_info in value["positive"]:
                    with open('static/data/'+'page' + str(node_info["page_id"]) + '.json', 'r')as fp:
                        tmp_layout = json.loads(fp.read())
                    tmp_page_instance = PageInstance()
                    if isinstance(tmp_layout, list):
                        tmp_layout = tmp_layout[0]
                    tmp_page_instance.load_from_dict("", tmp_layout)
                    tmp_page_root = tmp_page_instance.ui_root
                    tmp_node = tmp_page_root.get_node_by_relative_id(
                        node_info["index"])
                    tmp_node.update_page_id(node_info["page_id"])
                    tmp_positive_nodes.append(
                        (tmp_node.findBlockNode(), tmp_node))
                describermanagers[key].update(
                    tmp_positive_ref_nodes, tmp_negative_ref_nodes, tmp_positive_nodes)
    global describermanagers_init
    describermanagers_init = True


@app.route('/demo', methods=['POST'])
def demo():
    screen = Screen()
    screen.update(request=request.form)
    # llm = LLM(screen, "test")
    # llm.decision()
    # llm.evaluate()
    # candidate, score = llm.get_result()


def detect_error(sims, probs):
    mark = 1
    entropy = sum([-i*math.log(i) for i in probs.values()])
    if entropy > 0.5:
        mark *= (1.0+entropy)
    else:
        mark *= 0.9
    if len(sims) > 1:
        if sims[-1] < sims[-2]:
            delta = (sims[-2] - sims[-1])/sims[-2]
            mark *= (1+delta)
            if sims[-1] < 0.75:
                mark *= 1.2

    print("error", mark)
    if mark > 0:
        return mark, True
    else:
        return mark, False


def error_handler():
    global result, img_id, i, seq, ins_seq,  prompt_now, intention, semantic_info, chart_data, current_path, current_path_str, intent_embedding, sims, line_data, GLOBAL_STATE, center, anchors, stepbacks
    GLOBAL_STATE = "ERROR Handling"
    max_score = 0
    if anchors:
        for i in range(len(anchors)):
            if anchors[i][1] > max_score:
                max_score = anchors[i][1]
                center = anchors[i][0]
        prompt_now += "Warning : After and exploration, the step selected in step " + \
            str(center)+" is False. So we step back to that page , select again.\n"
        stepbacks = len(current_path)-center

        print("stepbacks", stepbacks)
    return False


def step_back():
    global result, img_id, i, seq, ins_seq,  prompt_now, intention, semantic_info, chart_data, current_path, current_path_str, intent_embedding, sims, line_data, GLOBAL_STATE, center, anchors, stepbacks
    tmp_num = -1
    for info in semantic_info:
        if "{返回}" in info or "{Back}" in info or "{back}" in info:
            tmp_num = info.split("{")[0]
            print("step back", tmp_num)
    if tmp_num != -1:
        node_selected = semantic_nodes["nodes"][int(tmp_num)-1]
        center = {"x": (node_selected.bound[0]+node_selected.bound[2])//2,
                  "y": (node_selected.bound[1]+node_selected.bound[3])//2}
        perform = {
            "node_id": 1, "trail": "["+str(center["x"])+","+str(center["y"])+"]", "action_type": "click"}
        return perform
    if tmp_num == -1:
        return "0"


def update_knowledge(item, page):
    with open("./static/knowledge.json", "r") as f:
        knowledge = json.load(f)
    knowledge[item] = page
    with open("./static/knowledge.json", "w") as f:
        json.dump(knowledge, f)


def find_from_knowledge(semantic_info: str):
    # 打开/static/knowledge.json
    with open("./static/knowledge.json", "r") as f:
        knowledge = json.load(f)
    for key in knowledge.keys():
        if semantic_info in key:
            return knowledge[key]
    return None


def expand_semantic(semantic_info: list):
    hist = semantic_info.copy()
    for item in range(len(semantic_info)):
        if find_from_knowledge(semantic_info[item]) is not None:
            semantic_info[item] = semantic_info[item] + ":" + \
                str(find_from_knowledge(semantic_info[item]))
            print("-----------", semantic_info[item])
        else:
            intention = [
                {"role": "system",
                    "content": """You are a highly intelligent assistant capable of deriving and predicting GUI interface information. You are a highly intelligent assistant capable of deriving and predicting GUI interface information. You would be given a page and the selected components, you should predict the after-page."""},
                {"role": "user",
                    "content": """The page:['1{}-{}-{More function buttons}-{Tab}', '2{}-{}-{Search}-{Tab}', '3{Me}-{Me}-{}-{Tab}', '4{Discover}-{Discover}-{}-{Tab}', '5{Contacts}-{Contacts}-{}-{Tab}', '6{Chats}-{Chats}-{}-{Tab}', '7{Bowen}-{Bowen,3/22/23,398178}-{}-{}', '8{Weixin Team}-{Weixin Team,3/22/23,Welcome back! Feel free to tell…}-{}-{}', '9{Subscriptions}-{Subscriptions,4:04 PM,[10 message(s)] 清华大学:“00后”清华女…}-{}-{}', '10{OOVTest}-{OOVTest,3/22/23}-{}-{}'].The component selected:['3{Me}-{Me}-{}-{Tab}',]."""},
                {"role": "assistant",
                    "content": """After-page:['{Me}-{Me}-{}-{Tab}', '{Discover}-{Discover}-{}-{Tab}', '{Contacts}-{Contacts}-{}-{Tab}', '{Chats}-{Chats}-{}-{Tab}', '{Settings}-{Settings}-{}-{}', '{Sticker Gallery}-{Sticker Gallery}-{}-{}', '{My Posts}-{My Posts}-{}-{}', '{Favorites}-{Favorites}-{}-{}', '{Services}-{Services}-{}-{}', "{}-{}-{Friends' Status}-{}", '{Status}-{Status}-{Add Status}-{}', '{}-{}-{My QR Code}-{Tab}', '{Weixin ID: saltyp0}-{Weixin ID: saltyp0}-{}-{Title}']"""},
                {"role": "user",
                    "content": """The page:['1{Plus}-{Plus}-{}-{}', '2{Help & Feedback}-{Help & Feedback}-{}-{}', '3{About}-{About}-{}-{}', '4{Information Shared with Third Parties}-{Information Shared with Third Parties}-{}-{}', '5{Collected Personal Information}-{Collected Personal Information}-{}-{}', '6{My Information & Authorizations}-{My Information & Authorizations}-{}-{}', "7{Friends' Permissions}-{Friends' Permissions}-{}-{}", '8{Privacy}-{Privacy}-{}-{}', '9{General}-{General}-{}-{}', '10{Chats}-{Chats}-{}-{}', '11{Message Notifications}-{Message Notifications}-{}-{}', '12{Easy Mode}-{Easy Mode}-{}-{}', '13{Parental Control Mode}-{Parental Control Mode}-{}-{}', '14{Account Security}-{Account Security}-{}-{}', '15{}-{}-{Back}-{}'].The component selected:'9{General}-{General}-{}-{}'."""},
                {"role": "assistant",
                    "content": """After-page:['{Storage}-{Storage}-{}-{}', '{Tools}-{Tools}-{}-{}', '{Manage Discover}-{Manage Discover}-{}-{}', '{Photos, Videos, Files & Calls}-{Photos, Videos, Files & Calls}-{}-{}', '{Text Size}-{Text Size}-{}-{}', '6{Language}-{Language,Auto}-{}-{}', '{Auto-Update Weixin}-{Auto-Update Weixin,Wi-Fi Only}-{}-{}', '{Dark Mode}-{Dark Mode,Auto}-{}-{}', '{}-{}-{Back}-{}']"""},
                {"role": "user",
                    "content": "The page:"+str(hist)+".The component selected:"+str(semantic_info[item])+"."},
            ]
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=intention,
                temperature=0.7,
            )
            print(response)
            update_knowledge(semantic_info[item], response["choices"]
                             [0]["message"]["content"].split("After-page:")[1])
            semantic_info[item] = semantic_info[item]+":" + \
                response["choices"][0]["message"]["content"].split(
                    "After-page:")[1]
            print("+++++++++", semantic_info[item])

    print("semantic_info", semantic_info)
    return semantic_info


def perform_one_step():
    global result, img_id, i, seq, ins_seq,  prompt_now, intention, semantic_info, chart_data, current_path, current_path_str, intent_embedding, sims, line_data, GLOBAL_STATE, center, anchors, stepbacks, probs

    if prompt_now.count("[Begin]") == 1 and "[End]" not in prompt_now:
        return False
    if probs != []:
        score, error = detect_error(sims, probs)
        if error:
            anchor = current_path[-1]
            anchor_index = len(current_path)-1
            anchors.append((anchor_index, score))
            print("!!!!!!!!!!!!!!!!anchor!!!!!!!!!!!!!!!!!!!!!!!!", anchor)
            print(anchors)
            # 如果在这里判断应该进入错误处理流程
            if len(sims) >= 3:
                # 计算sim倒数三项的方差
                var = np.var(sims[-3:])
                print("var", var)
                if var < 0.1:
                    return error_handler()
                if np.mean(sims[-3:]) < 73:
                    return error_handler()
                if len(sims) >= 5:
                    if sims[-1] < 80:
                        return error_handler()

    img_id = str(cnt)
    print(semantic_info)
    print("semantic_info", semantic_info)
    if "[Begin]" in prompt_now and "[End]" in prompt_now:
        prompt_now = prompt_now.split(
            "[Begin]")[0]+prompt_now.split("[End]")[-1]

    print("prompt_now_len", len(prompt_now))
    print("==================================================")
    # semantic_info = expand_semantic(semantic_info)
    print("semantic_info", semantic_info)
    print("==================================================")
    generate_prompt(semantic_info=str(semantic_info))
    print("prompt_now_len", len(prompt_now))
    print("prompt_now", prompt_now)
    if len(prompt_now) > 7500:
        return False
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt_now,
        temperature=0,
        max_tokens=512,
        logprobs=5,
        stop="<EOC>",
    )
    tokens = response["choices"][0]["logprobs"]["tokens"]
    # 判断"S","OC"是否连续出现在tokens中
    index_i = 0
    if "S" in tokens and "OC" in tokens:
        index_S, index_OC = tokens.index("S"), tokens.index("OC")
        if index_S == index_OC-1:
            index_i = index_OC+2
    print(tokens[index_i])
    probs = response["choices"][0]["logprobs"]["top_logprobs"][index_i]
    for key, value in probs.items():
        probs[key] = math.exp(value)
    print(probs)

    chart_data = {
        'labels': list(probs.keys()),
        'datasets': [
            {
                'data': list(probs.values()),
                'backgroundColor': [
                    'rgb(255, 99, 132)',
                    'rgb(54, 162, 235)',
                    'rgb(255, 205, 86)',
                    'rgb(75, 192, 192)',
                    'rgb(153, 102, 255)'
                ],
                'hoverOffset': 4
            }
        ]
    }
    print(chart_data)
    result = response.choices[0].text
    result = result.replace("choose one component",
                            "[End]choose one component")
    result += "<EOC>].\n"
    if "DONE" in result:
        GLOBAL_STATE = "Finished"
        return False
    prompt_now = prompt_now+result
    comp_selected = result[result.find("<SOC>")+5:result.find("<EOC>")]
    current_path.append(comp_selected.split(",")[-1])
    # current_path = expand_seq(current_path)
    current_path_str = ";".join(current_path)
    similarity = cosine_similarity(intent_embedding, embedding_from_string(
        current_path_str))*0.8+0.2*cosine_similarity(intent_embedding, embedding_from_string(comp_selected))
    sims.append(100*similarity)

    line_data = {
        "labels": current_path,
        "datasets": [
            {
                "label": 'Similarity',
                "data": sims,
                "pointStyle": 'circle',
                "pointRadius": 10,
                "pointHoverRadius": 15
            }
        ]
    }
    print("current_path", current_path)
    print("sims", sims)

    if "choose one component" in result:
        result = result.split("choose one component")[-1]
    print(result)
    pattern = re.compile(r"\d+")
    number = re.findall(pattern, result)[0]
    node_selected = semantic_nodes["nodes"][int(number)-1]
    center = {"x": (node_selected.bound[0]+node_selected.bound[2])//2,
              "y": (node_selected.bound[1]+node_selected.bound[3])//2}
    print("center", center)
    return True


@app.route("/", methods=("GET", "POST"))
def index():
    print(request.form)
    global result, img_id, i, seq, ins_seq,  prompt_now, intention, semantic_info, chart_data, current_path, current_path_str, intent_embedding, sims, line_data, GLOBAL_STATE, center
    if request.method == "POST" and "intention" in request.form:

        intention = request.form["intention"]
        intention = [
            {"role": "system",
             "content": """You are an assistant translating user's intention to more detailed, longer, clearer and more precise description.One sentence only!"""},
            {"role": "user",
             "content": """Don't allow others to friending me by 'search phone number' in WeChat"""},
            {"role": "assistant",
             "content": """Prevent people from finding and adding them as a friend on the WeChat app using their phone number"""},
            {"role": "user",
             "content": """Check Wallet Transactions"""},
            {"role": "assistant",
                "content": """Viewing the transaction history of their WeChat wallet"""},
            {"role": "user",
                "content": """Enter Bowen's Moments"""},
            {"role": "assistant",
                "content": """Accessing the social media feed or posts of the user named Bowen on WeChat, which is commonly referred to as 'Moments'"""},
            {"role": "user",
                "content": intention+". Note that do not show app name in the description."},
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=intention,
            temperature=0.5,
        )
        print(response)
        intention = response["choices"][0]["message"]["content"]
        print(intention)
        intent_embedding = embedding_from_string(intention)
        sims.append(100*cosine_similarity(intent_embedding,
                    embedding_from_string("Homepage")))
        initialize_prompt(intention)
        GLOBAL_STATE = "Not Started"
    elif request.method == "POST" and "start" in request.form:
        GLOBAL_STATE = "Started"
    elif request.method == "POST" and "reset" in request.form:
        if intention != "":
            initialize_prompt(intention)
            current_path = ["Homepage"]
            current_path_str = "Homepage"
            intent_embedding = None
            sims = []
            chart_data = {
                'labels': [],
                'datasets': [
                    {
                        'data': [],
                        'backgroundColor': [
                            'rgb(255, 99, 132)',
                            'rgb(54, 162, 235)',
                            'rgb(255, 205, 86)',
                            'rgb(75, 192, 192)',
                            'rgb(153, 102, 255)'
                        ],
                        'hoverOffset': 4
                    }
                ]
            }
            line_data = {
                "labels": [],
                "datasets": [
                    {
                        "label": 'Similarity',
                        "data": [],
                        "pointStyle": 'circle',
                        "pointRadius": 10,
                        "pointHoverRadius": 15
                    }
                ]
            }
            i = 0
            GLOBAL_STATE = "Not Started"

    return render_template("index.html", elements=json.dumps({"result": result, "image_id": img_id}), chart_data=json.dumps(chart_data), line_data=json.dumps(line_data))


@app.route('/test_data', methods=['GET'])
def test_data():
    global result, img_id, i, seq, ins_seq, intention, semantic_info, chart_data, current_path, current_path_str, intent_embedding, sims, line_data, GLOBAL_STATE, center
    if result != "" and img_id != 0:
        return json.dumps({"result": result, "image_id": img_id, "semantic_info": semantic_info, "chart_data": chart_data, "line_data": line_data})
    return json.dumps({"result": "", "image_id": 1, "semantic_info": semantic_info, "chart_data": chart_data, "line_data": line_data})


def generate_prompt(semantic_info: str) -> str:
    global prompt_now, i
    print(type(semantic_info))
    prompt_now = prompt_now+"""{},[Begin]Current page components:"[{}]".
""".format(
        str(i+1), semantic_info
    )
    i += 1
    return prompt_now


def initialize_prompt(init):
    global prompt_now
    prompt_now = """A user's intention is to 'Turn off Dark mode in WeChat'.
1,Current page components:"['1,{}-{}-{More function buttons}-{RelativeLayout}', '2,{}-{}-{Search}-{RelativeLayout}', '3,{Me}-{Me}-{}-{RelativeLayout}', '4,{Discover}-{Discover}-{}-{RelativeLayout}', '5,{Contacts}-{Contacts}-{}-{RelativeLayout}', '6,{Chats}-{Chats}-{}-{RelativeLayout}']".The current page is:"Homepage".Expecting the next page to appear :['{Settings}-{}-{}-{LinearLayout}'].Currently choose one component :[Click on <SOC>3,Me<EOC> ].
2,Current page components:"['1,{Settings}-{}-{}-{LinearLayout}', '2,{Sticker Gallery}-{}-{}-{LinearLayout}', '3,{My Posts}-{}-{}-{LinearLayout}', '4,{Favorites}-{}-{}-{LinearLayout}', '5,{Services}-{}-{}-{LinearLayout}']".The current page is:"Me page".Expecting the next page to appear :['{General}-{}-{}-{LinearLayout}'].Currently choose one component :[Click on <SOC>1,Settings<EOC> ].
3,Current page components:"['1,{My Information & Authorizations}-{}-{}-{LinearLayout}', "2,{Friends' Permissions}-{}-{}-{LinearLayout}", '3,{Privacy}-{}-{}-{LinearLayout}', '4,{General}-{}-{}-{LinearLayout}', '5,{Chats}-{}-{}-{LinearLayout}', '6,{}-{}-{Back}-{LinearLayout}']".The current page is:"Settings page".Expecting the next page to appear :['{Dark Mode}-{}-{}-{LinearLayout}'].Currently choose one component :[Click on <SOC>4,General<EOC> ].
4,Current page components:"['1,{Manage Discover}-{}-{}-{LinearLayout}', '2,{Photos, Videos, Files & Calls}-{}-{}-{LinearLayout}', '3,{Text Size}-{}-{}-{LinearLayout}','4,{Dark Mode}-{Auto}-{}-{LinearLayout}', '5,{}-{}-{Back}-{LinearLayout}']".The current page is:"Settings-General subpage".Expecting the next page to appear :["DONE!"].Currently choose one component :[Click on <SOC>4,Dark Mode, The Task is DONE!<EOC> ].

Rules:
1,UI components are organized as {major text}-{all text}-{description}-{android class}.
2,Please strictly follow the answer format:"Expecting...Currently".
3,Only one short instruction is allowed to be generated per step.
4,Each instruction can only choose from the current components.Indicate the serial number!
A user's intention is to """ + "["+init+"]\n"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

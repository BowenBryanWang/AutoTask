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
from WindowStructure import *
import time
from NodeDescriberManager import *
import json
import numpy as np
from flask_socketio import SocketIO
from flask import Flask
from flask_sockets import Sockets
import datetime


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
    # with open('./static/data/'+'/relation_dict.json', 'r', encoding='utf-8') as file:
    #     relation_dict = json.loads(file.read())
    # with open('./static/data/'+'/model_structure.json', 'r', encoding='utf-8') as file:
    #     model_data = json.loads(file.read())
    #     print(model_data)
    #     return model_data


@app.route('/demo', methods=['POST'])
def demo():
    if not describermanagers_init:
        init_describer()
    global cnt
    cnt += 1
    global layout,  screenshot, imgdata, img_np, page_instance, pageindex, page_id_now, page_root, semantic_nodes, semantic_info, center,GLOBAL_STATE,stepbacks,anchors
    start_time = time.time()
    page_id_now = cnt
    screenshot = request.form["screenshot"]
    print("depredict", request.form["layout"] == layout)
    if request.form["layout"] == layout:
        print("depredict")
        return "0"
    layout = request.form['layout']
    # pageindex = request.form['pageindex']
    imgdata = base64.b64decode(screenshot)
    nparr = np.frombuffer(imgdata, np.uint8)
    img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    fp = open('static/data/imagedata' + str(cnt) +
              ".jpg", 'wb')  # 'wb'表示写二进制文件
    fp.write(imgdata)
    fp.close()
    fp = open('static/data/page' + str(cnt) + ".json", 'w')
    fp.write(layout)
    fp.close()
    page_instance = PageInstance()
    page_instance.load_from_dict("", json.loads(layout))
    print("page loaded")
    page_root = page_instance.ui_root
    if len(page_root.children[0].children[0].children) == 2:
        print("FUCK")
        page_root.children[0].children[0].children = [
            page_root.children[0].children[0].children[0]]
    global all_text, semantic_info, describermanagers
    ll = page_root.generate_all_text()
    if ll == all_text:
        return "0"
    all_text = ll
    print("all_text", all_text)
    semantic_nodes = page_root.get_all_semantic_nodes()

    # 创建与semantic_nodes["nodes"]等长的type列表，用于存放每个节点的类型
    semantic_nodes["type"] = ["" for ii in range(len(semantic_nodes["nodes"]))]
    for i in range(len(semantic_nodes["nodes"])):
        semantic_nodes["nodes"][i].update_page_id(page_id_now)
        dis = 99.0
        for key, value in describermanagers.items():
            if key == "Root Object;":
                continue
            tmp_dis = value.calculate(semantic_nodes["nodes"][i])
            if tmp_dis < dis:
                dis = tmp_dis
                semantic_nodes["type"][i] = key.split(";")[-2]
    print("semantic_nodes", semantic_nodes["type"])

    semantic_info = [node.generate_all_semantic_info()
                     for node in semantic_nodes["nodes"]]

    for i in range(len(semantic_info)):
        semantic_info[i] = str(i+1)+"{"+",".join([str(i) for i in semantic_info[i]["Major_text"]])+"}-{"+",".join([str(i) for i in semantic_info[i]["text"]])+"}-{"+",".join(
            [str(i) for i in semantic_info[i]["content-desc"]])+"}-{"+semantic_nodes["type"][i]+"}"
    print("semantic info,", semantic_info)
    print("semantic_nodes", len(semantic_nodes))
    end_time = time.time()
    global upload_time  # 上一次上传的时间
    upload_time = end_time  # 记录本次上传的时间
    print("upload_time", upload_time)
    inprocessing = False
    print("time:", end_time-start_time, flush=True)
    if GLOBAL_STATE == "Not Started":
        return "Not Started"
    elif GLOBAL_STATE == "Started" and not inprocessing:
        inprocessing = True
        if perform_one_step():
            perform = {
                "node_id": 1, "trail": "["+str(center["x"])+","+str(center["y"])+"]", "action_type": "click"}
            print(perform)
            time.sleep(2)
            inprocessing = False
            return json.dumps(perform)
    elif GLOBAL_STATE == "Finished":
        return "Finished"
    if GLOBAL_STATE == "ERROR Handling":
        perform_back = step_back()
        stepbacks -=1
        print("stepbacks", stepbacks)
        current_path.pop(-1)
        print("current_path", current_path)
        sims.pop(-1)
        print("sims", sims)
        anchors.pop(-1)
        print("anchors", anchors)
        if stepbacks == 0:
            GLOBAL_STATE = "Started"
        time.sleep(2)
        return json.dumps(perform_back)
    return "0"


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
    if mark >0:
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
        prompt_now += "After verification and exploration, the components selected in step "+str(center)+" are not very credible.So we step back to that page , please select again.\n"
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
        perform = {"node_id": 1, "trail": "["+str(center["x"])+","+str(center["y"])+"]", "action_type": "click"}
        return perform
    if tmp_num == -1:
        return "0"


def perform_one_step():
    global result, img_id, i, seq, ins_seq,  prompt_now, intention, semantic_info, chart_data, current_path, current_path_str, intent_embedding, sims, line_data, GLOBAL_STATE, center, anchors, stepbacks,probs
    
    if prompt_now.count("[Begin]") == 1 and "[End]" not in prompt_now:
        return False
    if probs != []:
        score, error = detect_error(sims, probs)
        if error:
            anchor = current_path[-1]
            anchor_index = len(current_path)-1
            anchors.append((anchor_index, score))
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!anchor", anchor)
            print(anchors)
            #如果在这里判断应该进入错误处理流程
            if len(sims)>=3:
                #计算sim倒数三项的方差
                var = np.var(sims[-3:])
                print("var", var)
                # if var < 0.01:
                #     return error_handler()
                if np.mean(sims[-3:]) < 72:
                    return error_handler()
                if len(sims) >= 5:
                    if sims[-1]<82:
                        return error_handler()
                
    img_id = str(cnt)
    print(semantic_info)
    print("semantic_info", semantic_info)
    if "[Begin]" in prompt_now and "[End]" in prompt_now:
        prompt_now = prompt_now.split(
            "[Begin]")[0]+prompt_now.split("[End]")[-1]
    print("prompt_now", prompt_now)
    print("prompt_now_len", len(prompt_now))
    generate_prompt(semantic_info=str(semantic_info))
    print("prompt_now_len", len(prompt_now))
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
    current_path.append(comp_selected)
    current_path_str = "->".join(current_path)
    similarity = cosine_similarity(intent_embedding, embedding_from_string(
        current_path_str))*0.7+0.3*cosine_similarity(intent_embedding, embedding_from_string(comp_selected))
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
                "content": intention},
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
A user's intention is to """ + init


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

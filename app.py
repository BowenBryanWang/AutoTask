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
seq = ["8", "50", "141", "146", "167"]
seq_semantic_info = [[
    {"text": ["微信(20)"], "content-desc": ["更多功能按钮", "搜索"], "type":"标题"},
    {"text": [], "content-desc": ["更多功能按钮"], "type":"按钮"},
    {"text": [], "content-desc": ["搜索"], "type":"按钮"},
    {"text": ["微信(20)"], "content-desc": [], "type":"文字"},
    {"text": ["我"], "content-desc": [], "type":"按钮"},
    {"text": ["发现"], "content-desc": [], "type":"按钮"},
    {"text": ["通讯录"], "content-desc": [], "type":"按钮"},
    {"text": ["微信", "20"], "content-desc": [], "type":"文字"},
    {"text": ["安全登录提醒", "凌晨2:43", "微信团队", "1"],
        "content-desc": [], "type":"消息"},
    {
        "text": ["微视频丨为谁辛苦为谁忙", "凌晨5:57", "腾讯新闻", "19"],
        "content-desc": [], "type":"消息"
    },
    {"text": ["微信(20)", "小程序"], "content-desc": [], "type":"标题"}
], [{'text': [], 'content-desc': ['发送视频动态']}, {'text': [], 'content-desc': ['发送视频动态']}, {'text': ['我'], 'content-desc': []}, {'text': ['发现'], 'content-desc': []}, {'text': ['通讯录'], 'content-desc': []}, {'text': ['微信'], 'content-desc': []}, {'text': ['设置'], 'content-desc': []}, {'text': [], 'content-desc': ['分隔栏']}, {'text': ['表情'], 'content-desc': []}, {'text': ['朋友圈'], 'content-desc': []}, {'text': ['收藏'], 'content-desc': []}, {'text': [], 'content-desc': ['分隔栏']}, {'text': ['支付'], 'content-desc': []}, {'text': [], 'content-desc': ['分隔栏']}, {'text': ['微信号：wxid_ziqw5ovbzej012', 'aa'], 'content-desc': []}, {'text': ['微信号：wxid_ziqw5ovbzej012', 'aa'], 'content-desc': []}, {'text': ['微信号：wxid_ziqw5ovbzej012'], 'content-desc': []}],
    [{'text': ['退出'], 'content-desc': []}, {'text': [], 'content-desc': ['分隔栏']}, {'text': ['切换帐号'], 'content-desc': []}, {'text': [], 'content-desc': ['分隔栏']}, {'text': ['插件'], 'content-desc': []}, {'text': [], 'content-desc': ['分隔栏']}, {'text': ['帮助与反馈'], 'content-desc': []}, {'text': ['关于微信'], 'content-desc': []}, {'text': [], 'content-desc': ['分隔栏']},
        {'text': ['通用'], 'content-desc': []}, {'text': ['隐私'], 'content-desc': []}, {'text': ['聊天'], 'content-desc': []}, {'text': ['勿扰模式'], 'content-desc': []}, {'text': ['新消息提醒'], 'content-desc': []}, {'text': [], 'content-desc': ['分隔栏']}, {'text': ['未开启', '青少年模式'], 'content-desc': []}, {'text': ['帐号与安全'], 'content-desc': []}, {'text': [], 'content-desc': ['返回']}],
    [{'text': ['关闭后，视频号有新内容更新时，微信发现页不再出现红点提示。', '视频号'], 'content-desc': ['已开启']}, {'text': ['关闭后，有朋友发表朋友圈时，微信发现页不再出现红点提示。', '朋友圈'], 'content-desc': ['已开启']}, {'text': ['更新提醒'], 'content-desc': []}, {'text': ['收到语音和视频通话邀请的声音与振动', '语音和视频通话邀请'], 'content-desc': []},
        {'text': ['声音与振动'], 'content-desc': []}, {'text': [], 'content-desc': ['分隔栏']}, {'text': ['接收语音和视频通话邀请通知'], 'content-desc': ['已开启']}, {'text': ['接收新消息通知'], 'content-desc': ['已关闭']}, {'text': ['通知开关'], 'content-desc': []}, {'text': [], 'content-desc': ['返回']}],
    [
    {"text": ["Default"], "content-desc": []},
    {"text": ["Toys"], "content-desc": []},
    {"text": ["Cupid"], "content-desc": []},
    {"text": ["Celestial"], "content-desc": []},
    {"text": ["Delight"], "content-desc": []},
    {"text": ["Crystals"], "content-desc": []},
    {"text": ["Fairy"], "content-desc": []},
    {"text": ["Elegance"], "content-desc": []},
]
]
ins_seq = ["Click 'Me'", "Click 'Settings'",
           "Click'Message Notifications'", "Click 'Alert Sound'", "Click 'Toys'"]
i = 0
prompt_now = ""
intention = ""
html_detect = False
agenda_detect = False
upload_time = None
time_between_upload = 1
all_text = ""  # 当前页面的所有文本
describermanagers_init = False
page_root = None
semantic_info=[]


@app.route('/detect', methods=['GET'])
def detect():
    global html_detect, all_text
    print("detect")
    detect_money()
    while True:
        if time.time()-upload_time <= time_between_upload:
            continue
        else:
            html = detect_html(all_text)
            if html:
                return {"type": "html", "html": str(html)}
            else:
                continue


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
                    with open('data/'+'/page' + str(node_info["page_id"]) + '.json', 'r')as fp:
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
                    with open('data/'+'/page' + str(node_info["page_id"]) + '.json', 'r')as fp:
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
                    with open('data/'+'/page' + str(node_info["page_id"]) + '.json', 'r')as fp:
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
    global html_detect
    html_detect = True
    global cnt
    cnt += 1
    global layout,  screenshot, imgdata, img_np, page_instance, pageindex, page_id_now, page_root, semantic_nodes, semantic_info
    start_time = time.time()
    page_id_now = cnt
    screenshot = request.form["screenshot"]
    layout = request.form['layout']
    # pageindex = request.form['pageindex']
    imgdata = base64.b64decode(screenshot)
    nparr = np.frombuffer(imgdata, np.uint8)
    img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    result_json = {"state": "ok"}
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
    global all_text,semantic_info
    all_text = page_root.generate_all_text()
    print("all_text", all_text)
    semantic_nodes = page_root.get_all_semantic_nodes()
    semantic_info = [node.generate_all_semantic_info()
                     for node in semantic_nodes["nodes"]]
    print("semantic info,", semantic_info)
    print("semantic_nodes", len(semantic_nodes))
    end_time = time.time()
    global upload_time  # 上一次上传的时间
    upload_time = end_time  # 记录本次上传的时间
    print("upload_time", upload_time)
    print("time:", end_time-start_time, flush=True)
    result_json["time"] = (end_time-start_time)*1000
    return json.dumps(result_json)


def detect_html(str):
    # 该函数检测str中是否有网址，如果有，返回网址字符串，否则返回空
    # 网址的正则表达式
    reg = r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'
    # 匹配网址
    url = re.findall(reg, str)
    if url:
        print("url:", url[0])
        return url[0]
    else:
        return None


def detect_money():
    global describermanagers_init
    if not describermanagers_init:
        init_describer()
        return None
    else:
        global describermanagers, page_root
        count = 0
        for key, value in describermanagers.items():
            if value.find_node(page_root):
                count += 1
        print(count)
        return count


def detect_agenda(str):
    # 构造若干规则判断该str里面是否包含日程信息

    # time_mark=["今天","明天","后天","上午","下午","晚上","周一","周二","周三","周四","周五","周六","周日","星期一","星期二","星期三","星期四","星期五","星期六","星期日","年","月","日","点","时","分","秒","周","星期","年","月","日","点","时","分","秒","周","星期"]
    time_mark = {
        "今天": 5,
        "明天": 5,
        "后天": 5,
        "上午": 5,
        "下午": 5,
        "晚上": 5,
        "周一": 2,
        "周二": 2,
        "周三": 2,
        "周四": 2,
        "周五": 2,
        "周六": 2,
        "周日": 2,
        "星期一": 2,
        "星期二": 2,
        "星期三": 2,
        "星期四": 2,
        "星期五": 2,
        "星期六": 2,
        "星期日": 2,
        "年": 4,
        "月": 4,
        "日": 4,
        "点": 4,
        "时": 4,
        "分": 4,
        "秒": 4,
        "周": 4,
        "星期": 4,
    }
    # deadline_mark = ["之前","之后","前","后","截止","截止时间","ddl","due","转发","回复","@所有人"]
    deadline_mark = {
        "之前": 10,
        "之后": 5,
        "前": 1,
        "后": 1,
        "截止": 10,
        "截止时间": 10,
        "ddl": 10,
        "转发": 1,
        "回复": 5,
        "@所有人": 10,
    }

    # 正则匹配时间,比如2:00
    reg = r'([0-9]{1,2}:[0-9]{1,2})'
    time = re.findall(reg, str)
    # 计算time_mark和deaddline_mark在str中命中的分数
    all = 0
    time_mark_cnt = 0
    deadline_mark_cnt = 0
    for key in time_mark:
        if key in str:
            time_mark_cnt += time_mark[key]
    for key in deadline_mark:
        if key in str:
            deadline_mark_cnt += deadline_mark[key]

    all = time_mark_cnt + deadline_mark_cnt+len(time)*10
    # 如果命中次数大于等于3，那么就认为这个str里面包含日程信息
    print("time_mark_cnt", time_mark_cnt, "deadline_mark_cnt",
          deadline_mark_cnt, "time", len(time)*10)
    if all >= 10:
        return True
    return False

# def detect_money():


@app.route("/", methods=("GET", "POST"))
def index():
    global i, seq, ins_seq,  prompt_now, intention
    print(request.form)
    global semantic_info
    if request.method == "POST" and "intention" in request.form:
        
        intention = request.form["intention"]
        initialize_prompt(intention)
        print(prompt_now)
        print(semantic_info)
    elif request.method == "POST" and "next" in request.form:
        
        img_id = str(cnt)
        print(semantic_info)
        semantic_info = str(semantic_info)[2:-2].replace(r"}, {", "\n")
        print(semantic_info)
        print(generate_prompt(semantic_info=str(semantic_info)))
        response = openai.Completion.create(
            model="text-davinci-002",
            prompt=prompt_now,
            temperature=0,
            max_tokens=20,
        )
        print(response)
        result = response.choices[0].text
        # #正则匹配result中的每句以.结尾的句子,并只保留该句子当中的单词或者数字或者标点符号，拼接起来以\n分割成一个新的字符串
        # result=re.sub(r'[^a-zA-Z0-9,.?! ]', '', result)
        # #将每一句话后接上一个换行符
        # result=re.sub(r'([.?!])', r'\1\n', result)
        
        # 正则匹配到类似于"3,"的字符串，数字加一个逗号，做一个split
        if "The page now has" in result:
            result = result.split('The page now has')[0]
        # if "\n" in result:
        #     result = result.split("\n")[-2]
        print(result)
        prompt_now = prompt_now+result+"\n"

        return render_template("index.html", result=result, img_id=img_id, semantic_info=semantic_info)

    # result = request.args.get("result")
    # img_id = request.args.get("img_id")
    # semantic_info = request.args.get("semantic_info")
    return render_template("index.html")


def generate_prompt(semantic_info):
    global prompt_now, i
    prompt_now = prompt_now+"""{},The page now has the following components:"{}".The instruction is :
""".format(
        str(i+1), semantic_info
    )
    return prompt_now


def initialize_prompt(init):
    global prompt_now
    prompt_now = """A user's intention is to "Open Meituan  app to see how long it is to deliver my takeaway".
1, The page now has following components: "Wechat","Meituan","Tiktok","Home","Settings". The instruction is : Click "Meituan".
2, The page now has the following components: "Messages", "Shopping cart", "Me". The instruction is : Click "Me".
3, The page now has the following components: "My orders", "My wallet", "My coupons". The instruction is : Click "My orders".
4, The page now has the following components: "All orders", "To be paid", "To be delivered", "To be commented". The instruction is : Click "To be delivered".
5, The page now has a list of orders. The user's intention is to find the order just placed, so he looks for the order with the latest order time.

A user's intention is to "{}".
""".format(
        init.capitalize()
    )


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

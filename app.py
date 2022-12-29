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
# from NodeDescriberManager import *
import json
import numpy as np
from flask_socketio import SocketIO
from flask import Flask
from flask_sockets import Sockets
import datetime

app = Flask(__name__)
# sockets = Sockets(app)
socketio = SocketIO(app)

from flask_cors import *
CORS(app, supports_credentials=True)

openai.api_key = "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"
layout = None
screenshot = None
imgdata = None
cnt = 0
semantic_nodes = []
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


@app.route('/demo', methods=['POST'])
def demo():
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
    fp = open('runtime_data/imagedata' + str(cnt) +
              ".jpg", 'wb')  # 'wb'表示写二进制文件
    fp.write(imgdata)
    fp.close()
    fp = open('runtime_data/page' + str(cnt) + ".json", 'w')
    fp.write(layout)
    fp.close()
    page_instance = PageInstance()
    page_instance.load_from_dict("", json.loads(layout))
    print("page loaded")
    page_root = page_instance.ui_root
    semantic_nodes = page_root.get_all_semantic_nodes()
    semantic_info = [node.generate_all_semantic_info()
                     for node in semantic_nodes]
    print("semantic info,", semantic_info)
    print("semantic_nodes", len(semantic_nodes))
    end_time = time.time()
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
        return url[0]
    else:
        return ""


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


@app.route("/", methods=("GET", "POST"))
def index():
    global i, seq, ins_seq, seq_semantic_info, prompt_now, intention
    print(request.form)
    if request.method == "POST" and "intention" in request.form:

        intention = request.form["intention"]
        initialize_prompt(intention)
        print(prompt_now)
        img_id = seq[i]
        seq_semantic_info[i] = str(seq_semantic_info[i])
        semantic_info = seq_semantic_info[i][2:-2].replace(r"}, {", "\n")
        return redirect(url_for("index", img_id=img_id, semantic_info=semantic_info))
    if request.method == "POST" and "next" in request.form:
        print(generate_prompt(semantic_info=str(seq_semantic_info[i])))
        response = openai.Completion.create(
            model="text-davinci-002",
            prompt=prompt_now,
            temperature=0,
            max_tokens=50,
        )
        print(response)
        result = response.choices[0].text
        # #正则匹配result中的每句以.结尾的句子,并只保留该句子当中的单词或者数字或者标点符号，拼接起来以\n分割成一个新的字符串
        # result=re.sub(r'[^a-zA-Z0-9,.?! ]', '', result)
        # #将每一句话后接上一个换行符
        # result=re.sub(r'([.?!])', r'\1\n', result)
        print(result)
        # 正则匹配到类似于"3,"的字符串，数字加一个逗号，做一个split
        result = result.split('The page now has')[0]
        if "\n" in result:
            result = result.split("\n")[-2]
        img_id = seq[i]
        # 把seq_semantic_info的每一项都转化成一个长字符串
        seq_semantic_info[i] = str(seq_semantic_info[i])
        semantic_info = seq_semantic_info[i][2:-2].replace(r"}, {", "\n")
        i += 1
        prompt_now = prompt_now+result+"\n"

        return redirect(url_for("index", result=result, img_id=img_id, semantic_info=semantic_info))

    result = request.args.get("result")
    img_id = request.args.get("img_id")
    semantic_info = request.args.get("semantic_info")
    return render_template("index.html", result=result, img_id=img_id, semantic_info=semantic_info)


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


@socketio.on('message')
def handle_message(message):
    print('received message: ' + message)
    socketio.emit('my response', {'data': 'got it!'})


@socketio.on('connect')
def test_connect():
    print("connect")
    socketio.emit('my response', {'data': 'Connected'})

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')
    
@socketio.on('/echo')
def echo_socket(ws):
    print("connection start")
    while not ws.closed:
        msg = ws.receive() # 同步阻塞
        print(msg)
        ws.send("can you hear me?")  # 发送数据
        time.sleep(1)





# @sockets.route('/echo',methods=["GET","POST"])
# def echo_socket(ws):
#     print("hello")
#     while not ws.closed:
#         msg = ws.receive()
#         print(msg)
#         now = datetime.datetime.now().isoformat()
#         ws.send(now)  #发送数据

@app.route('/test')
def test():
    print("hello")


# if __name__ == "__main__":
#     from gevent import pywsgi
#     from geventwebsocket.handler import WebSocketHandler
#     server = pywsgi.WSGIServer(('0.0.0.0', 5000), app, handler_class=WebSocketHandler)
#     print('server start')
#     server.serve_forever()


if __name__ == "__main__":
    # #获取输入
    # test = input("请输入：")
    # print(detect_agenda(test))
    print("server started1")
    socketio.run(app, host='0.0.0.0', port=5000)
    print("server started2")
    # app.run(host='0.0.0.0', port=5000)
    print("server started3")

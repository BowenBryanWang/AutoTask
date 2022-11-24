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
import socket
import json
import numpy as np
app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")
layout = None
screenshot = None
imgdata = None
cnt = 0
semantic_nodes=[]
@app.route('/demo', methods=['POST'])
def demo():
    global cnt
    cnt += 1
    global layout,  screenshot, imgdata, img_np, page_instance, pageindex, page_id_now,page_root,semantic_nodes,semantic_info
    start_time = time.time()
    page_id_now = cnt
    screenshot = request.form["screenshot"]
    layout = request.form['layout']
    pageindex = request.form['pageindex']
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
    semantic_info = [node.generate_semantic_info() for node in semantic_nodes]
    print("semantic_nodes",len(semantic_nodes))
    end_time = time.time()
    print("time:", end_time-start_time, flush=True)
    result_json["time"] = (end_time-start_time)*1000
    return json.dumps(result_json)
    
    

@app.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":
        animal = request.form["animal"]
        response = openai.Completion.create(
            model="text-davinci-002",
            prompt=generate_prompt(animal),
            temperature=1,
            max_tokens=100,
        )
        print(response)
        result=response.choices[0].text
        #正则匹配result中的每句以.结尾的句子,并只保留该句子当中的单词或者数字或者标点符号，拼接起来以\n分割成一个新的字符串
        result=re.sub(r'[^a-zA-Z0-9,.?! ]', '', result)
        #将每一句话后接上一个换行符
        result=re.sub(r'([.?!])', r'\1\n', result)
        print(result)
        return redirect(url_for("index", result=result))

    result = request.args.get("result")
    return render_template("index.html", result=result)


def generate_prompt(animal):
    return """A user's intention is to "Search for information about Elon Musk on Twitter and to express his opinion about him".
He may do the following sequence:
1, user clicked the "Twitter" icon to enter the Twitter page.
2, user clicked on the search box and type in "Elon Musk".
3, user clicked on the Twitter user "Elon Musk" and enters his personal page.
4, the user liked Elon Musk's second tweet.
5, the user commented "You awful man!" to his third tweet.
A user's intention is "{}".
Let's think step by step, he may do the following sequence:
1,The user enters the app.
2,
""".format(
        animal.capitalize()
    )

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)
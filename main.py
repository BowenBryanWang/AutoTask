from pynput import keyboard
import argparse
import shutil
import threading
from flask import Response, jsonify
from typing import Union
from flask import Flask, request
from src.model import Model

from page.init import Screen
from page.WindowStructure import *
from page.NodeDescriberManager import *
from src.utility import generate_perform, GPT


app = Flask(__name__)

TASK = ""
MODE = ""
MODEL = ""
STATUS = "stop"
INDEX = 0
NEW_TASK = True
ACTION_TRACE = []

force_load_count = 0.0
auto_load = False
listener_global = None

@app.route('/heart_beat', methods=['POST'])
def heat_beat():
    global force_load_count, auto_load
    if auto_load:
        force_load_count += (2.0 / 10.0)  # 前端每1秒发送一次，预计等待10秒
    force_load = force_load_count >= 2
    if force_load:
        force_load_count = 0.0
        auto_load = False
    return jsonify({
        "state": 'success',
        "force_load": force_load
    })

def wait_and_load_decorator(function):
    global auto_load

    def wrapped_function(*args, **kwargs):
        global auto_load
        result = function(*args, **kwargs)
        if isinstance(result, dict) and "action_type" in result:
            auto_load = True
        return result
    return wrapped_function

@app.route('/demo', methods=['POST'])
@wait_and_load_decorator
def demo() -> Union[str, Response]:
    global TASK, STATUS, ACTION_TRACE, NEW_TASK, listener_global

    if listener_global is not None:
        listener_global.stop()

    screen = Screen(INDEX)
    screen.update(request=request.form)

    # 每次前端传来数据，都会创建一个screen类，这个类就是处理前端传来的数据，已经写好，内部实现复杂，如果感兴趣可以debug模式下查看其成员变量
    # TODO：实现你的ChatGPT调用仍然在此保留了我的实现，当然你的实现版本更简单，可以参考，不用这样复杂
    # 以下是你可能用到的成员变量
    print("Screen UI semantic elements:", screen.semantic_info)
    print("Screen UI semantic list 形式:", screen.semantic_info_list)

    if STATUS == "start":
        NEW_TASK = True
        ACTION_TRACE = []
        STATUS = "running"
    
    if STATUS == "running":
        model = Model(screen=screen, description=TASK)

        query_history = read_history()

        if MODEL == "LLM-0":
            prompt = paper_provided_prompt_1(model.task, model.screen.semantic_info_list)
        elif MODEL == "LLM-hist-5-CoT":
            prompt = paper_provided_prompt_2(model.task, model.screen.semantic_info_list)

        result = GPT(prompt)
        
        print(result)

        save_history(query_history, model.screen.semantic_info_list, model.task, result)

        ACTION_TRACE.append(result)

        if result["action_type"] == "text":
            STATUS = "finish"
            #TODO: load next task
            return generate_perform(action_type="text", text=result["text"])
        else:
            node = screen.semantic_nodes["nodes"][find_node_idx(result["idx"], screen.semantic_info_list)]
            return generate_perform(action_type=result["action_type"], x=node.center[0], y=node.center[1], absolute_id=node.absolute_id)
    else:
        return Response("0")

def find_node_idx(id, info_list):
    for index, node_info in enumerate(info_list):
        if "id={}".format(id) in node_info:
            return index
    return -1


def paper_provided_prompt_1(task, current_ui):
    return [
        {
            "role": "system",
            "content": 
"""
Given a mobile screen and a question, provide the action based on the screen
information.

Available Actions:
{"action_type": "click", "idx": <element_idx>}
{"action_type": "type", "text": <text>}
{"action_type": "navigate_home"}
{"action_type": "navigate_back"}
{"action_type": "scroll", "direction": "up"}
{"action_type": "scroll", "direction": "down"}
{"action_type": "scroll", "direction": "left"}
{"action_type": "scroll", "direction": "right"}
{"action_type": "text", "text": <answer_to_the_instruction>}
"""
        },
        {
            "role": "user",
            "content": 
"""
Screen: {}
Instruction: {}
Think step by step, and output JSON format with property name enclosed in double quotes. 
When found the answer or finished the task, use "text" to report the answer or to end the task.
Answer:
""".format(current_ui, task)
        }
    ]

def paper_provided_prompt_2(task, current_ui):
    global ACTION_TRACE
    prompt = []
    prompt.append({
            "role": "system",
            "content": 
"""
Given a mobile screen and a question, provide the action based on the screen
information.

Available Actions:
{"action_type": "click", "idx": <element_idx>}
{"action_type": "type", "text": <text>}
{"action_type": "navigate_home"}
{"action_type": "navigate_back"}
{"action_type": "scroll", "direction": "up"}
{"action_type": "scroll", "direction": "down"}
{"action_type": "scroll", "direction": "left"}
{"action_type": "scroll", "direction": "right"}
{"action_type": "text", "text": <answer_to_the_instruction>}
"""
    })
    
    prompt.append({
        "role": "user",
        "content": 
"""
Previous Actions:
{"step_idx": 0, "action_description": "press [HOME key]"}
{"step_idx": 2, "action_description": "click [Google Icon]"}
{"step_idx": 3, "action_description": "click [search for hotels]"}

Screen:
<img id=0 class="IconGoogle" alt="Google Icon"> </img>
<img id=1 class="IconX" alt="Close Icon"> </img>
<p id=2 class="text" alt="search for hotels"> search for hotels </p>
<p id=3 class="text" alt="in"> in </p>
<p id=4 class="text" alt="mexico city mexico"> mexico city mexico </p>
<img id=5 class="IconMagnifyingGlass" alt="Search Icon"> </img>
<p id=6 class="text" alt="Share"> Share </p>
<p id=7 class="text" alt="Select alI"> Select alI </p>
<p id=8 class="text" alt="Cut"> Cut </p>
<p id=9 class="text" alt="Copy"> Copy </p>
<p id=10 class="text" alt="hotel in mex"> hotel in mex </p>
<img id=11 class="IconMagnifyingGlass" alt="Search Icon"> </img>
<p id=12 class="text" alt="best hotel"> best hotel </p>
<p id=13 class="text" alt="mexico city"> mexico city </p>
<p id=14 class="text" alt="in"> in </p>
<img id=15 class="IconMagnifyingGlass" alt="Search Icon"> </img>
<p id=16 class="text" alt="K"> K </p>
<p id=17 class="text" alt="hotel ciudad"> hotel ciudad </p>
<p id=18 class="text" alt="de mexico"> de mexico </p>
<p id=19 class="text" alt="gran"> gran </p>
<img id=20 class="IconVBackward" alt="Left Icon"> </img>
<img id=21 class="IconNavBarCircle" alt="Home Icon"> </img>
<img id=22 class="IconNavBarRect" alt="Overview Icon"> </img>

Instruction: What time is it in Berlin?
Answer: Let's think step by step. I see unrelated search results in the Google app,
I must clear the search bar, so the action is {"action_type": "click", "idx": 1}

Previous Actions:
{"step_idx": 0, "action_description": "click [DISMISS]"}

Screen:
<p id=0 class="text" alt="Update your"> Update your </p>
<p id=1 class="text" alt="Gmail app"> Gmail app </p>
<p id=2 class="text" alt="attach files from"> attach files from </p>
<p id=3 class="text" alt="To"> To </p>
<p id=4 class="text" alt="download the"> download the </p>
<p id=5 class="text" alt="Drive,"> Drive, </p>
<p id=6 class="text" alt="latest"> latest </p>
<p id=7 class="text" alt="version"> version </p>
<p id=8 class="text" alt="of"> of </p>
<p id=9 class="text" alt="Gmail"> Gmail </p>
<p id=10 class="text" alt="UPDATE"> UPDATE </p>
<p id=11 class="text" alt="DISMISS"> DISMISS </p>
<p id=12 class="text" alt="Got"> Got </p>
<p id=13 class="text" alt="it"> it </p>
<img id=14 class="IconVBackward" alt="Left Icon"> </img>

Instruction: see creations saved in the google photos
Answer: Let's think step by step. I see a popup, I need to open Google Photos, so
the action is {"action_type": "click", "idx": 11}

Previous Actions:

Screen:
<p id=0 class="text" alt="M"> M </p>
<p id=1 class="text" alt="New in Gmail"> New in Gmail </p>
<p id=2 class="text" alt="All the features you"> All the features you </p>
<p id=3 class="text" alt="love with"> love with </p>
<p id=4 class="text" alt="a fresh"> a fresh </p>
<p id=5 class="text" alt="look"> look </p>
<p id=6 class="text" alt="new"> new </p>
<p id=7 class="text" alt="GOT IT"> GOT IT </p>

Instruction: open app "Google Play services"
Answer: Let's think step by step. I see the GMail app, I need to open the app
drawer, so the action is {"action_type": "navigate_home"}

Previous Actions:

Screen:
<p id=0 class="text" alt="Tuesday, Aug"> Tuesday, Aug </p>
<p id=1 class="text" alt="9"> 9 </p>
<img id=2 class="IconChat" alt="Chat Icon"> </img>
<img id=3 class="IconGoogle" alt="Google Icon"> </img>

Instruction: open app "Messenger Lite" (install if not already installed)
Answer: Let's think step by step. I see the home screen, I need to open the app
drawer, I should swipe up, so the action is {"action_type": "scroll", "direction":
"down"}

Previous Actions:
{"step_idx": 0, "action_description": "scroll down"}

Screen:
<img id=0 class="IconThreeDots" alt="More Icon"> </img>
<p id=1 class="text" alt="Search your phone and more"> Search your phone and more </p>
<p id=2 class="text" alt="M"> M </p>
<p id=3 class="text" alt="O"> O </p>
<img id=4 class="IconPlay" alt="Play Icon"> </img>
<p id=5 class="text" alt="Clock"> Clock </p>
<p id=6 class="text" alt="YouTube"> YouTube </p>
<p id=7 class="text" alt="Photos"> Photos </p>
<p id=8 class="text" alt="Gmail"> Gmail </p>
<p id=9 class="text" alt="All apps"> All apps </p>
<p id=10 class="text" alt="g"> g </p>
<p id=11 class="text" alt="O"> O </p>
<img id=12 class="IconTakePhoto" alt="Camera Icon"> </img>
<p id=13 class="text" alt="10"> 10 </p>
<p id=14 class="text" alt="Calendar"> Calendar </p>
<p id=15 class="text" alt="Camera"> Camera </p>
<p id=16 class="text" alt="Chrome"> Chrome </p>
<p id=17 class="text" alt="Clock"> Clock </p>
<p id=18 class="text" alt="0"> 0 </p>
<p id=19 class="text" alt="M"> M </p>
<p id=20 class="text" alt="B"> B </p>
<img id=21 class="IconPerson" alt="Person Icon"> </img>
<p id=22 class="text" alt="Gmail"> Gmail </p>
<p id=23 class="text" alt="Drive"> Drive </p>
<p id=24 class="text" alt="Files"> Files </p>
<p id=25 class="text" alt="Contacts"> Contacts </p>
<p id=26 class="text" alt="G OO"> G OO </p>
<img id=27 class="IconGoogle" alt="Google Icon"> </img>
<img id=28 class="IconLocation" alt="Location Icon"> </img>
<img id=29 class="IconCall" alt="Phone Icon"> </img>
<img id=30 class="IconChat" alt="Chat Icon"> </img>
<p id=31 class="text" alt="Google"> Google </p>
<p id=32 class="text" alt="Maps"> Maps </p>

Instruction: Search for hotels in Chicago.
Answer: Let's think step by step. I see the app drawer, I need to search, so the
action is {"action_type": "click", "idx": 27}

"""
    })
    prompt.append({
            "role": "user",
            "content": 
"""
Previous Action: 
{}
Screen:
{}
Instruction: {}
""".format(ACTION_TRACE[-5:], current_ui, task)
    })
    prompt.append({
        "role": "assistant",
        "content":
"""
Answer: Let's think step by step. I see
"""
    })
    return prompt

def read_history():
    with open("./src/KB/history.json", "r") as f:
        history = json.load(f)
    return history

def save_history(query_history, screen, instruction, answer):
    global ACTION_TRACE, NEW_TASK
    history = {
        "Previous Actions": ACTION_TRACE,
        "Screen": screen,
        "Instruction": instruction,
        "Answer": answer
    }
    if NEW_TASK:
        query_history.append(history)
        NEW_TASK = False
    else:
        query_history[-1] = history
    with open("./src/KB/history.json", "w") as f:
        json.dump(query_history, f, indent=4)


def save_to_file(task_name):
    task_name = task_name.replace(" ", "_")
    # 在同级目录./Shots下创建一个名为task_name的文件夹
    if not os.path.exists("./Shots/{}".format(task_name)):
        os.makedirs("./Shots/{}".format(task_name))
        # 将./logs文件夹和./Page/static/data文件夹移到其下
        shutil.move("./logs", "./Shots/{}".format(task_name))
        shutil.move("./Page/static/data", "./Shots/{}".format(task_name))


def on_key_release(key):
    global STATUS, force_load_count
    if key == keyboard.Key.enter:
        STATUS = "start"
        print("Task execution started!")
    elif 'char' in key.__dict__ and key.char == 'l':
        if key.char == 'l':
            force_load_count += 1
        else:
            force_load_count = 0


def keyboard_listener():
    global listener_global
    with keyboard.Listener(on_release=on_key_release) as listener:
        listener_global = listener
        listener.join()
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Flask app with argparse integration")
    parser.add_argument("--task", type=str, help="Specify the TASK parameter",
                        default="View data usage of 'T-mobile' on this phone")
    parser.add_argument("--mode", type=str, choices=["normal", "preserve"],
                        default="normal", help="Specify the mode: 'normal' or 'preserve'")
    parser.add_argument("--model", type=str, choices=["LLM-0", "LLM-hist-5-CoT"],
                        default="LLM-0", help="Specify the model: 'LLM-0' or 'LLM-hist-5-CoT'")
    args = parser.parse_args()

    TASK = args.task
    MODE = args.mode
    MODEL = args.model

    keyboard_thread = threading.Thread(target=keyboard_listener)
    keyboard_thread.daemon = True
    keyboard_thread.start()

    app.run(host='localhost', port=5002)

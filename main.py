import csv
import json
from pynput import keyboard
import argparse
import shutil
import threading
import time
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
TASK_START_LINE = 236
TASK_END_LINE = 236
TASK_INDEX = 0
TASK_LIST = []
ACTION_TRACE = []

force_load_count = 0.0
auto_load = False
listener_global = None
previous_time = 0

@app.route('/heart_beat', methods=['POST'])
def heart_beat():
    global force_load_count, auto_load, previous_time, STATUS
    if auto_load:
        force_load_count += (2.0 / 8.0)  # 前端每1秒发送一次，预计等待10秒
    force_load = force_load_count >= 2

    current_time = time.time()
    if STATUS == "running" and current_time - previous_time > 30:
        force_load = True

    if force_load:
        previous_time = current_time
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
    global TASK, STATUS, ACTION_TRACE, TASK_LIST, TASK_INDEX, TASK_START_LINE, listener_global

    if listener_global is not None:
        listener_global.stop()

    

    if STATUS == "start":
        STATUS = "running"
        # TASK_LIST = read_task_from_csv("pixeltasks.csv")
        TASK_LIST = read_task_from_jsonl("new_ugif_tasks_.jsonl")
        TASK = TASK_LIST[TASK_INDEX]

    screen = Screen(INDEX)
    screen.update(request=request.form)

    if STATUS == "running":
        model = Model(screen=screen, description=TASK)

        if MODEL == "LLM-0":
            prompt = paper_provided_prompt_1(model.task, model.screen.semantic_info_all_warp)
        elif MODEL == "LLM-hist-5-CoT":
            prompt = paper_provided_prompt_2(model.task, model.screen.semantic_info_all_warp)

        send_req_time = time.time()
        result = GPT(prompt)
        receive_req_time = time.time()
        
        print(result)

        save_log(model.screen.semantic_info_all_warp, model.task, result, send_req_time, receive_req_time)

        ACTION_TRACE.append(result)

        if result["action_type"] == "report_answer":
            end_old_start_new(result["success"], None)
            return generate_perform(action_type="")
        elif len(ACTION_TRACE) > 20:
            end_old_start_new(False, None)
            return generate_perform(action_type="")
        elif result["action_type"] == "navigate_back":
            return generate_perform(action_type="back")
        elif result["action_type"] == "type":
            node = screen.semantic_nodes["nodes"][find_node_idx(result["idx"], screen.semantic_info_no_warp)]
            return generate_perform(action_type="text", x=node.center[0], y=node.center[1], absolute_id=node.absolute_id, text=result["text"])
        else:
            if result["action_type"] == "scroll_down":
                result["action_type"] = "scroll_forward"
            elif result["action_type"] == "scroll_up":
                result["action_type"] = "scroll_backward"
            try:
                node = screen.semantic_nodes["nodes"][find_node_idx(result["idx"], screen.semantic_info_no_warp)]
            except Exception as e:
                end_old_start_new(False, str(type(e)))
                return generate_perform(action_type="")
            else:
                return generate_perform(action_type=result["action_type"], x=node.center[0], y=node.center[1], absolute_id=node.absolute_id)


def find_node_idx(id, info_list):
    for index, node_info in enumerate(info_list):
        if "id={}".format(id) in node_info:
            return index
    return -1

def read_task_from_csv(file_path):
    global TASK_START_LINE, TASK_END_LINE
    task_list = []

    with open(file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
    
        for _ in range(TASK_START_LINE - 1):
            next(csv_reader)

        task_list = [row[0] for row in csv_reader]

        task_list = task_list[:TASK_END_LINE - TASK_START_LINE + 1]
        print(task_list)
    return task_list

def read_task_from_jsonl(file_path):
    global TASK_START_LINE, TASK_END_LINE
    task_list = []

    with open(file_path, 'r', encoding="utf-8") as jsonl_file:
        for line_number, line in enumerate(jsonl_file, 1):
            if TASK_START_LINE <= line_number <= TASK_END_LINE:
                json_data = json.loads(line)

                task_value = json_data.get('task', None)

                if task_value is not None:
                    task_list.append(task_value)

    return task_list


def end_old_start_new(completed, error):
    global TASK, TASK_INDEX, TASK_START_LINE, TASK_LIST, ACTION_TRACE

    # os.system("adb shell am force-stop com.google.android.gm")
    # os.system("adb shell am start -n com.google.android.gm/.GmailActivity")

    os.system("adb shell am force-stop com.android.settings")
    os.system("adb shell am start -n com.android.settings/.Settings")

    # os.system("adb shell am force-stop com.android.chrome")
    # os.system("adb shell am start -n com.android.chrome/com.google.android.apps.chrome.Main")

    # with open('pixel_results.txt', 'r') as file:
    #     data = json.load(file)
    # insert = False
    # for result in data:
    #     if result["id"] == TASK_INDEX + TASK_START_LINE:
    #         result = {
    #                     "task": TASK,
    #                     "id": TASK_INDEX + TASK_START_LINE,
    #                     "completed": completed,
    #                     "error": error
    #                 }
    #         insert = True
    #         break
    # if not insert:
    #     data.append({"task": TASK,
    #              "id": TASK_INDEX + TASK_START_LINE,
    #              "completed": completed,
    #              "error": error})
    # with open('pixel_results.txt', 'w') as file:
    #     json.dump(data, file, indent=4)

    with open('results.txt', 'r') as file:
        data = json.load(file)
    insert = False
    for result in data:
        if result["id"] == TASK_INDEX + TASK_START_LINE:
            result = {
                        "task": TASK,
                        "id": TASK_INDEX + TASK_START_LINE,
                        "completed": completed,
                        "error": error
                    }
            insert = True
            break
    if not insert:
        data.append({"task": TASK,
                 "id": TASK_INDEX + TASK_START_LINE,
                 "completed": completed,
                 "error": error})
    with open('results.txt', 'w') as file:
        json.dump(data, file, indent=4)

    TASK_INDEX += 1
    TASK = TASK_LIST[TASK_INDEX]
    ACTION_TRACE = []

def save_log(screen, instruction, answer, send_time, receive_time):
    global ACTION_TRACE, TASK_INDEX, TASK, TASK_START_LINE
    history = {
        "Previous Actions": ACTION_TRACE,
        "Screen": screen,
        "Instruction": instruction,
        "Send Time": send_time,
        "Receive Time": receive_time,
        "Answer": answer
    }

    task_name = str(TASK_INDEX + TASK_START_LINE) + "_" + TASK.replace(" ", "_")
    task_name = ''.join(e for e in task_name if (e.isalnum() or e == '_'))

    # if not os.path.exists("./pixel_logs/{}".format(task_name)):
    #     os.mkdir("./pixel_logs/{}".format(task_name))

    # if not os.path.exists("./pixel_logs/{}/{}".format(task_name, len(ACTION_TRACE))):
    #     os.mkdir("./pixel_logs/{}/{}".format(task_name, len(ACTION_TRACE)))
    # shutil.move("./page/data", "./pixel_logs/{}/{}".format(task_name, len(ACTION_TRACE)))

    # with open("./pixel_logs/{}/log_{}.json".format(task_name, len(ACTION_TRACE)), "a") as f:
    #     json.dump(history, f, indent=4)
    
    if not os.path.exists("./logs/{}".format(task_name)):
        os.mkdir("./logs/{}".format(task_name))

    if not os.path.exists("./logs/{}/{}".format(task_name, len(ACTION_TRACE))):
        os.mkdir("./logs/{}/{}".format(task_name, len(ACTION_TRACE)))
    shutil.move("./page/data", "./logs/{}/{}".format(task_name, len(ACTION_TRACE)))

    with open("./logs/{}/log_{}.json".format(task_name, len(ACTION_TRACE)), "a") as f:
        json.dump(history, f, indent=4)


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
{"action_type": "type", "idx": <element_idx>, "text": <text>}
{"action_type": "navigate_back"}
{"action_type": "scroll_forward", "idx": <element_idx>}
{"action_type": "scroll_backward", "idx": <element_idx>}
{"action_type": "report_answer", "text": "task_completed" / <answer_to_the_query>}
"""
        },
        {
            "role": "user",
            "content": 
"""
Screen: {}
Instruction: {}
Think step by step, and output JSON format with property name enclosed in double quotes. 
When found the answer or finished the task, use "report_answer" to report the answer or to end the task.
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
{"action_type": "type", "idx": <element_idx>, "text": <text>}
{"action_type": "navigate_back"}
{"action_type": "scroll_down", "idx": <element_idx>}
{"action_type": "scroll_up", "idx": <element_idx>}
{"action_type": "report_answer", "success": <True_or_False>, "text": <answer_to_the_instruction>}
"""
    })
    
    prompt.append({
        "role": "user",
        "content": 
"""
Here are examples of different actions.

Example_1:
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

Example_2:
    Previous Actions:

    Screen:
    <scroll id=0 class="android.widget.ScrollView"> </scroll>
    <p id=1 class="text" alt="Tuesday, Aug"> Tuesday, Aug </p>
    <p id=2 class="text" alt="9"> 9 </p>
    <img id=3 class="IconChat" alt="Chat Icon"> </img>
    <img id=4 class="IconGoogle" alt="Google Icon"> </img>

    Instruction: open app "Messenger Lite" (install if not already installed)
    Answer: Let's think step by step. I see the home screen, but I don't see the app
    drawer, I should swipe up, so the action is {"action_type": "scroll_down", "idx": 0}

Example_3:
    Previous Actions:
        {"step_idx": 0, "action_type": "click"}
        {"step_idx": 1, "action_type": "click"}
        {"step_idx": 2, "action_type": "scroll_down"}
        {"step_idx": 3, "action_type": "click"}

    Screen:
    <p class=''> Set a schedule </p>
    <div id=1 class=''> </div>
    <div id=2 class='android:id/checkbox'  enabled not_checked >  </div>
    <p class='android:id/title'  > No schedule </p>
    <div id=3 class=''> </div>
    <div id=4 class='android:id/checkbox'  enabled not_checked >  </div>
    <p class='android:id/title'  > Based on your routine </p>
    <p class='android:id/summary'  > Battery Saver turns on if your battery is likely to run out before your next typical charge </p>
    <div id=5 class=''> </div>
    <div id=6 class='android:id/checkbox'  enabled checked >  </div>
    <p class='android:id/title'  > Based on percentage </p>

    Instruction: Set the schedule for the battery saver mode to "Based on percentage" on the phone.,
    Answer: Let's think step by step. I see the 'Based on percentage' option, 
    and the checkbox is checked, so the schedule is already set to 'Based on percentage'.
    I need to report the task completed, so the action is {"action_type": "report_answer", "success": true, "text": "Successfully set the schedule for the battery saver mode to "Based on percentage" on the phone."}


Example_4:
    Previous Actions:
    {"step_idx": 0, "action_description": "click"}
    {"step_idx": 1, "action_description": "click"}

    Screen:
    <div id=1 class='' description='Back'>  </div>
    <p class='' > Accounts </p>
    <p class='android:id/title' > ACCOUNTS FOR OWNER </p>
    <div id=2 class='' > Add account </div>
    <div id=3 class='' > Automatically sync app data </div>
    <p> Let apps refresh data automatically </p>
    <switch id=4 class='android:id/switch_widget' clickable> On </switch>
    

    Instruction: Turn 'Automatically sync my app data' on.
    Answer: Let's think step by step. I see the 'Automatically sync app data' option, 
    and the switch widget status is 'On', so the 'Automatically sync my app data' function is already on.
    I need to report the task completed, so the action is {"action_type": "report_answer", "success": true, "text": "Successfully turned 'Automatically sync my app data' on."


Example_5:
    Previous Actions:
    {"step_idx": 0, "action_description": "scroll_down"}
    {"step_idx": 1, "action_description": "click"}

    Screen:
    <div id=1 class='' description='Back'>  </div>
    <p class='' > Storage </p>
    <scroll id=2 class=androidx.recyclerview.widget.RecyclerView > </scroll>
    <div id=3 class='com.android.settings:id/deletion_helper_button' > MANAGE STORAGE </div>
    <div id=4 class='' description='Storage manager'> Storage manager </div>
    <switch id=5 class='com.android.settings:id/switchWidget' clickable> Off </switch>
    <div id=6 class='' > Photos & videos </div>
    <p> 1.30 GB </p>
    <div id=7 class='' > Music & audio </div>
    <p> 0.00 GB </p>
    <div id=8 class='' > Games </div>
    <p> 0.00 GB </p>
    <div id=9 class='' > Movie & TV apps </div>
    <p> 0.00 GB </p>
    <div id=10 class='' > Other apps </div>
    <p> 0.08 GB </p>

    Instruction: Check the storage usage of photos on the phone.
    Answer: Let's think step by step. I see the Storage page, there is the storage usage of Photos & videos, 
    so I need to report the answer to the query, so the action is {"action_type": "report_answer", "success": true, "text": "The storage usage of photos on the phone is 1.30 GB."}
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
Additional Requirements:
1. Output your action in JSON format, you can only choose an action in "Available Actions" as we mentioned above.
2. You can find your latest actions in the "Previous Action" list right above, and you should NOT scroll_down three times in a row!!! Try something new!
3. When you completed the task or found the answer, use "report_answer" to report that the task is already completed and start a new one.
""".format(ACTION_TRACE, current_ui, task)
    })
    prompt.append({
        "role": "assistant",
        "content":
"""
Answer: Let's think step by step. I see
"""
    })
    return prompt


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
                        default="Enable 'Find My Device'")
    parser.add_argument("--mode", type=str, choices=["normal", "preserve"],
                        default="normal", help="Specify the mode: 'normal' or 'preserve'")
    parser.add_argument("--model", type=str, choices=["LLM-0", "LLM-hist-5-CoT"],
                        default="LLM-hist-5-CoT", help="Specify the model: 'LLM-0' or 'LLM-hist-5-CoT'")
    args = parser.parse_args()

    TASK = args.task
    MODE = args.mode
    MODEL = args.model


    keyboard_thread = threading.Thread(target=keyboard_listener)
    keyboard_thread.daemon = True
    keyboard_thread.start()

    app.run(host='localhost', port=5002)

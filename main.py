import json
from pynput import keyboard
import argparse
import shutil
import threading
from flask import Response, jsonify
from typing import Any, Union
from flask import Flask, request
from src.model import Model

from page.init import Screen
from page.WindowStructure import *

import logging

import click

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


def secho(text, file=None, nl=None, err=None, color=None, **styles):
    pass


def echo(text, file=None, nl=None, err=None, color=None, **styles):
    pass


click.echo = echo
click.secho = secho


app = Flask(__name__)

TASK = ""
MODE = ""
STATUS = "stop"
INDEX = 0
COMPUTATIONAL_GRAPH: List[Any] = []
GRAPH_ACTION: List[Any] = []
ACTION_TRACE = {
    "ACTION": [],
    "ACTION_DESC": [],
    "PAGES": [],
}

force_load_count = 0
auto_load = False
listener_global = None


@app.route('/heart_beat', methods=['POST'])
def heat_beat():
    global force_load_count, auto_load
    if auto_load:
        force_load_count += (2.0 / 10.0)  # 前端每1秒发送一次，预计等待10秒
    force_load = force_load_count >= 2
    if force_load:
        force_load_count = 0
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
        if isinstance(result, dict) and 'action_type' in result:
            auto_load = True
        return result
    return wrapped_function


def coverage(text1, text2):
    words1 = set(text1.split())
    words2 = set(text2.split())

    common_words = words1.intersection(words2)

    return len(common_words) / max(len(words1), len(words2))


@app.route('/demo', methods=['POST'])
@wait_and_load_decorator
def demo() -> Union[str, Response]:
    global TASK, STATUS, INDEX, COMPUTATIONAL_GRAPH, GRAPH_ACTION
    if listener_global is not None:
        listener_global.stop()
    screen = Screen(INDEX)
    screen.update(request=request.form)
    while screen.semantic_info_list == []:
        return Response("0")
    print("INDEX", INDEX)
    # return {'node_id': 1, 'trail': '[0,0]', 'action_type': 'text', 'text': 'tsinghua', 'ori_absolute_id': 'android.widget.FrameLayout|0;android.widget.LinearLayout|0;android.widget.FrameLayout|0;android.widget.LinearLayout|0;android.widget.FrameLayout|0;android.view.ViewGroup|0;android.view.ViewGroup|1;android.widget.FrameLayout|0;android.widget.FrameLayout|0;android.widget.LinearLayout|0;android.widget.FrameLayout|0;android.widget.LinearLayout|0;android.widget.FrameLayout|0;android.widget.LinearLayout|0;android.widget.EditText'}
    if STATUS == "start":
        STATUS = "running"
        model = Model(screen=screen, description=TASK,
                      prev_model=COMPUTATIONAL_GRAPH[-1] if COMPUTATIONAL_GRAPH != [] else None, index=INDEX)
        COMPUTATIONAL_GRAPH.append(model)
        print("work")
        result, work_status = model.work(ACTION_TRACE=ACTION_TRACE)
        model.final_result = result
        if work_status == "wrong":
            if MODE == "normal":
                STATUS = "backtracking"
            elif MODE == "preserve":
                STATUS = "running"
            return result
        elif work_status == "Execute":
            ACTION_TRACE["ACTION"].append(model.log_json["@Action"])
            ACTION_TRACE["ACTION_DESC"].append("NEXT")
            ACTION_TRACE["PAGES"].append(
                model.screen.page_root.generate_all_text())
            if MODE == "normal":
                STATUS = "start"
            elif MODE == "preserve":
                STATUS = "running"
            INDEX += 1
            return result
        elif work_status == "completed":
            save_to_file(TASK)
            STATUS = "stop"
            return Response("Task completed successfully!")
        else:
            return Response("Task failed.")
    if STATUS == "backtracking":
        all_text_uploaded = screen.page_root.generate_all_text()
        for index, step in [x for x in enumerate(COMPUTATIONAL_GRAPH[:-1])][::-1]:
            if coverage(step.screen.page_root.generate_all_text(), all_text_uploaded) >= 0.98:
                if index == INDEX-1:
                    break
                else:
                    return step.final_result
        INDEX -= 1
        res, act = COMPUTATIONAL_GRAPH[INDEX].feedback_module.feedback(
            COMPUTATIONAL_GRAPH[INDEX].wrong_reason)
        ACTION_TRACE["ACTION"].append("Click on navigate back due to error")
        ACTION_TRACE["ACTION_DESC"].append("BACK")
        ACTION_TRACE["PAGES"].append(
            COMPUTATIONAL_GRAPH[INDEX].screen.page_root.generate_all_text())
        if res is not None:
            COMPUTATIONAL_GRAPH = COMPUTATIONAL_GRAPH[:INDEX+1]
            result, work_status = COMPUTATIONAL_GRAPH[INDEX].work(
                ACTION_TRACE=ACTION_TRACE, flag="debug")
            COMPUTATIONAL_GRAPH[INDEX].final_result = result
            if work_status == "wrong":
                if MODE == "normal":
                    STATUS = "backtracking"
                elif MODE == "preserve":
                    STATUS = "running"
                return result
            elif work_status == "Execute":
                ACTION_TRACE["ACTION"].append(
                    COMPUTATIONAL_GRAPH[INDEX].log_json["@Action"])
                ACTION_TRACE["ACTION_DESC"].append(
                    "Retry after error detection")
                ACTION_TRACE["PAGES"].append(
                    COMPUTATIONAL_GRAPH[INDEX].screen.page_root.generate_all_text())
                if MODE == "normal":
                    STATUS = "start"
                elif MODE == "preserve":
                    STATUS = "running"
                INDEX += 1
                return result
            elif work_status == "completed":
                save_to_file(TASK)
                STATUS = "stop"
                return Response("Task completed successfully!")
            else:
                return Response("Task failed.")
        else:

            print("------------------------back--------------------------")
            return {"node_id": 1, "trail": "[0,0]", "action_type": "back"}
    return Response("0")


def save_to_file(task_name):
    global ACTION_TRACE
    with open(os.path.join(os.path.dirname(__file__), "logs/final.json"), 'w', encoding="utf-8") as f:
        json.dump(ACTION_TRACE, f, ensure_ascii=False, indent=4)
    task_name = task_name.replace(" ", "_").replace(":", '_')
    if not os.path.exists("./Shots/{}".format(task_name)):
        os.makedirs("./Shots/{}".format(task_name))
        shutil.move("./logs", "./Shots/{}".format(task_name))
        shutil.move("./Page/data", "./Shots/{}".format(task_name))


def on_key_release(key):
    global STATUS, force_load_count
    if key == keyboard.Key.enter:
        STATUS = "start"
        print("Task execution started!")
    # elif key == keyboard.Key.delete:
    #    STATUS = "backtracking"
    #    print("Backtracking started!")
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
    default_cmd = 'turn on Web & App Activity in Google'

    parser = argparse.ArgumentParser(
        description="Flask app with argparse integration")
    parser.add_argument("--task", type=str, help="Specify the TASK parameter",
                        default=default_cmd)
    parser.add_argument("--mode", type=str, choices=["normal", "preserve"],
                        default="normal", help="Specify the mode: 'normal' or 'preserve'")
    args = parser.parse_args()

    TASK = args.task
    MODE = args.mode

    keyboard_thread = threading.Thread(target=keyboard_listener)
    keyboard_thread.daemon = True
    keyboard_thread.start()
    app.run(host='localhost', port=5002)

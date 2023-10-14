from pynput import keyboard
import argparse
import shutil
import threading
from flask import Response
from typing import Union
from flask import Flask, request
from src.model import Model

from page.init import Screen
from page.WindowStructure import *


app = Flask(__name__)

TASK = ""
MODE = ""
STATUS = "stop"
INDEX = 0
COMPUTATIONAL_GRAPH = []
GRAPH_ACTION = []
ACTION_TRACE = {
    "ACTION": [],
    "ACTION_DESC": [],
    "TRACE": [],
    "TRACE_DESC": [],
}


@app.route('/demo', methods=['POST'])
def demo() -> Union[str, Response]:
    global TASK, STATUS, INDEX, COMPUTATIONAL_GRAPH, GRAPH_ACTION
    screen = Screen(INDEX)
    screen.update(request=request.form)
    print("INDEX", INDEX)
    if STATUS == "start":
        STATUS = "running"
        model = Model(screen=screen, description=TASK,
                      prev_model=COMPUTATIONAL_GRAPH[-1] if COMPUTATIONAL_GRAPH != [] else None, index=INDEX)
        COMPUTATIONAL_GRAPH.append(model)
        print("work")
        result, work_status = model.work(ACTION_TRACE=ACTION_TRACE)

        if work_status == "wrong":
            if MODE == "normal":
                STATUS = "backtracking"
            elif MODE == "preserve":
                STATUS = "running"
            return result
        elif work_status == "Execute":
            ACTION_TRACE["ACTION"].append(model.log_json["@Action"])
            ACTION_TRACE["ACTION_DESC"].append("NEXT")
            ACTION_TRACE["TRACE"].append(model.candidate_str)
            ACTION_TRACE["TRACE_DESC"].append(model.page_description)
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
        INDEX -= 1
        res, act = COMPUTATIONAL_GRAPH[INDEX].feedback_module.feedback(
            COMPUTATIONAL_GRAPH[INDEX].wrong_reason)
        ACTION_TRACE["ACTION"].append("Click on navigate back due to error")
        ACTION_TRACE["ACTION_DESC"].append("BACK")
        ACTION_TRACE["TRACE"].append(COMPUTATIONAL_GRAPH[INDEX].candidate_str)
        ACTION_TRACE["TRACE_DESC"].append(
            COMPUTATIONAL_GRAPH[INDEX].page_description)
        if res is not None:
            COMPUTATIONAL_GRAPH = COMPUTATIONAL_GRAPH[:INDEX+1]
            result, work_status = COMPUTATIONAL_GRAPH[INDEX].work(
                ACTION_TRACE=ACTION_TRACE)
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
                ACTION_TRACE["TRACE"].append(
                    COMPUTATIONAL_GRAPH[INDEX].candidate_str)
                ACTION_TRACE["TRACE_DESC"].append(
                    COMPUTATIONAL_GRAPH[INDEX].page_description)
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
    task_name = task_name.replace(" ", "_")
    if not os.path.exists("./Shots/{}".format(task_name)):
        os.makedirs("./Shots/{}".format(task_name))
        shutil.move("./logs", "./Shots/{}".format(task_name))
        shutil.move("./Page/data", "./Shots/{}".format(task_name))


def on_key_release(key):
    global STATUS
    if key == keyboard.Key.enter:
        STATUS = "start"
        print("Task execution started!")
    elif key == keyboard.Key.delete:
        STATUS = "backtracking"
        print("Backtracking started!")


def keyboard_listener():
    with keyboard.Listener(on_release=on_key_release) as listener:
        listener.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Flask app with argparse integration")
    parser.add_argument("--task", type=str, help="Specify the TASK parameter",
                        default="View data usage of 'T-mobile' on this phone")
    parser.add_argument("--mode", type=str, choices=["normal", "preserve"],
                        default="normal", help="Specify the mode: 'normal' or 'preserve'")
    args = parser.parse_args()

    TASK = args.task
    MODE = args.mode

    keyboard_thread = threading.Thread(target=keyboard_listener)
    keyboard_thread.daemon = True
    keyboard_thread.start()
    app.run(host='localhost', port=5002)

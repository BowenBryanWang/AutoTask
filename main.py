import json
import pickle
from pynput import keyboard
import argparse
import shutil
import threading
from flask import Response, jsonify
from typing import Any, Union
from flask import Flask, request
from Graph import UINavigationGraph
from src.utility import sort_by_similarity
from src.model import Model

from page.init import Screen
from page.WindowStructure import *

import logging

import click

from src.utility import process_ACTION_TRACE, coverage, simplify_ui_element_id, simplify_ui_element

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
PER = 0
STATUS = "stop"
STATUS_SAME = False
INDEX = 0
COMPUTATIONAL_GRAPH: List[Any] = []
GRAPH_ACTION: List[Any] = []
ACTION_TRACE = {
    "ACTION": [],
    "ACTION_DESC": [],
    "PAGES": [],
}
Graph = None

force_load_count = 0
auto_load = False
listener_global = None


@app.route('/heart_beat', methods=['POST'])
def heat_beat():
    global force_load_count, auto_load
    if auto_load:
        force_load_count += (2.0 / 5.0)  # 前端每1秒发送一次，预计等待10秒
    force_load = force_load_count >= 2
    if force_load:
        force_load_count = 0
        auto_load = False
        print("send force_load")
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
        else:
            print("not auto load")
        return result
    return wrapped_function


@app.route('/demo', methods=['POST'])
@wait_and_load_decorator
def demo() -> Union[str, Response]:
    global TASK, STATUS, INDEX, COMPUTATIONAL_GRAPH, GRAPH_ACTION, force_load_count, auto_load, Graph, STATUS_SAME
    if listener_global is not None:
        listener_global.stop()
    screen = Screen(INDEX)
    screen.update(request=request.form)
    force_load_count = 0
    auto_load = False

    while screen.semantic_info_no_warp == []:
        return Response("0")
    print("INDEX", INDEX)
    if STATUS == "start":
        STATUS = "running"
        model = Model(screen=screen, description=TASK,
                      prev_model=COMPUTATIONAL_GRAPH[-1] if COMPUTATIONAL_GRAPH != [] else None, index=INDEX, LOAD=LOAD, Graph=Graph, PER=PER)
        model.refer_node = Graph.add_node(model.node_in_graph)
        COMPUTATIONAL_GRAPH.append(model)
        if len(COMPUTATIONAL_GRAPH) > 10:
            print("_____________THE TASK FAILED_____________")
            save_to_file(TASK)
            STATUS = "stop"
            return Response("Task Failed")
        if model.prev_model is not None:
            if ACTION_TRACE["ACTION_DESC"][-1] != "BACK":
                Graph.add_edge(model.prev_model.node_in_graph,
                               model.node_in_graph, model.prev_model.edge_in_graph)
        ACTION_TRACE["PAGES"].append(
            list(
                map(simplify_ui_element, model.screen.semantic_info_half_warp)))
        if len(COMPUTATIONAL_GRAPH) > 1 and model.screen.semantic_info_all_warp == COMPUTATIONAL_GRAPH[-2].screen.semantic_info_all_warp:
            if MODE == "normal":
                STATUS_SAME = True
                STATUS = "backtracking"
            elif MODE == "preserve":
                STATUS = "running"
            return {"node_id": 1, "trail": "[0,0]", "action_type": ""}
        result, work_status = model.work(
            ACTION_TRACE=process_ACTION_TRACE(ACTION_TRACE))
        model.final_result = result
        if work_status == "wrong":
            if MODE == "normal":
                STATUS = "backtracking"
            elif MODE == "preserve":
                STATUS = "running"
            return result
        elif work_status == "Execute":
            ACTION_TRACE["ACTION"].append(model.log_json["@Current_Action"])
            ACTION_TRACE["ACTION_DESC"].append("NEXT")
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
        if STATUS_SAME:
            ACTION_TRACE["PAGES"].append(
                ["SAME page as last one"])
            ACTION_TRACE["ACTION"].append("上步操作没有响应，因此是错误的")
            ACTION_TRACE["ACTION_DESC"].append("BACK")
            STATUS_SAME = False
        else:
            ACTION_TRACE["PAGES"].append(list(map(
                simplify_ui_element, COMPUTATIONAL_GRAPH[INDEX].screen.semantic_info_half_warp)))
            ACTION_TRACE["ACTION"].append("Navigate back due to error")
            ACTION_TRACE["ACTION_DESC"].append("BACK")

        if res is not None:
            COMPUTATIONAL_GRAPH = COMPUTATIONAL_GRAPH[:INDEX+1]
            result, work_status = COMPUTATIONAL_GRAPH[INDEX].work(
                ACTION_TRACE=process_ACTION_TRACE(ACTION_TRACE), flag="debug")
            COMPUTATIONAL_GRAPH[INDEX].final_result = result
            if work_status == "wrong":
                if MODE == "normal":
                    STATUS = "backtracking"
                elif MODE == "preserve":
                    STATUS = "running"
                return result
            elif work_status == "Execute":
                ACTION_TRACE["ACTION"].append(
                    COMPUTATIONAL_GRAPH[INDEX].log_json["@Current_Action"])
                ACTION_TRACE["ACTION_DESC"].append(
                    "Retry after error detection")
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
        shutil.move("./src/gpt_res", "./Shots/{}".format(task_name))


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
    default_cmd = "Enable Wifi hotspot"

    parser = argparse.ArgumentParser(
        description="Flask app with argparse integration")
    parser.add_argument("--task", type=str, help="Specify the TASK parameter",
                        default=default_cmd)
    parser.add_argument("--mode", type=str, choices=["normal", "preserve"],
                        default="normal", help="Specify the mode: 'normal' or 'preserve'")
    parser.add_argument("--load", type=bool, choices=[True, False],
                        default=False, help="determine whether to load UI graph")
    parser.add_argument("--percentage", type=float, default=0, choices=[0.25, 0.5, 0.75, 1],
                        help="determine the percentage to load knowledge")
    args = parser.parse_args()

    TASK = args.task
    MODE = args.mode
    LOAD = args.load
    PER = args.percentage
    if LOAD:
        Graph = UINavigationGraph("cache/random/Graph_"+str(PER)+".pkl")
        Graph.merge_from_random(k=PER)
    else:
        Graph = UINavigationGraph(
            "./cache/Graph_"+TASK.replace(" ", "_")+".pkl")

    keyboard_thread = threading.Thread(target=keyboard_listener)
    keyboard_thread.daemon = True
    keyboard_thread.start()
    app.run(host='localhost', port=5002)

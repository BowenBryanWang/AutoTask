import json
from pynput import keyboard
import argparse
import shutil
import threading
from flask import Response, jsonify
from typing import Any, Union
from flask import Flask, request
from Graph import UINavigationGraph
from src.embedding import sort_by_similarity
from src.model import Model

from page.init import Screen
from page.WindowStructure import *

import logging

import click

from src.utility import process_ACTION_TRACE, coverage

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
Graph = UINavigationGraph("Graph.pkl")

force_load_count = 0
auto_load = False
listener_global = None
long_term_UI_knowledge = []


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


@app.route('/demo', methods=['POST'])
@wait_and_load_decorator
def demo() -> Union[str, Response]:
    global TASK, STATUS, INDEX, COMPUTATIONAL_GRAPH, GRAPH_ACTION, force_load_count, auto_load, long_term_UI_knowledge, Graph
    if listener_global is not None:
        listener_global.stop()
    screen = Screen(INDEX)
    screen.update(request=request.form)
    force_load_count = 0
    auto_load = False

    while screen.semantic_info_list == []:
        return Response("0")
    print("INDEX", INDEX)
    if STATUS == "start":
        STATUS = "running"
        model = Model(screen=screen, description=TASK,
                      prev_model=COMPUTATIONAL_GRAPH[-1] if COMPUTATIONAL_GRAPH != [] else None, index=INDEX, long_term_UI_knowledge=long_term_UI_knowledge)
        model.refer_node = Graph.add_node(model.node_in_graph)

        if len(COMPUTATIONAL_GRAPH) >= 1 and model.screen.page_root.generate_all_text() == COMPUTATIONAL_GRAPH[-1].screen.page_root.generate_all_text():
            if MODE == "normal":
                STATUS = "backtracking"
            elif MODE == "preserve":
                STATUS = "running"
            return COMPUTATIONAL_GRAPH[-1].final_result
        COMPUTATIONAL_GRAPH.append(model)
        if model.prev_model is not None:
            if ACTION_TRACE["ACTION_DESC"][-1] != "BACK":
                Graph.add_edge(model.prev_model.node_in_graph,
                               model.node_in_graph, model.prev_model.edge_in_graph)
        ACTION_TRACE["PAGES"].append(
            model.screen.page_root.generate_all_text().split("-"))
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
            ACTION_TRACE["ACTION"].append(model.log_json["@Action"])
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
        ACTION_TRACE["PAGES"].append(
            COMPUTATIONAL_GRAPH[INDEX].screen.page_root.generate_all_text().split("-"))
        ACTION_TRACE["ACTION"].append("Click on navigate back due to error")
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
                    COMPUTATIONAL_GRAPH[INDEX].log_json["@Action"])
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


def retrivel_long_term_UI_knowledge(Task):
    global long_term_UI_knowledge
    with open(os.path.join(os.path.dirname(__file__), "src/KB/pagejump/pagejump_long.json"), 'r', encoding="utf-8") as f:
        js = json.loads(f.read())
        key_components = js.keys()
        query = "The user's task is to "+Task + \
            ". Which componnets is most relevant?"
        result = sort_by_similarity(query, key_components)
        result = sorted(result, key=lambda x: x[1], reverse=True)
        result = list(filter(lambda x: x[1] > 0.80, result))
        keys = list(map(lambda x: x[0], result))
        answer = list(map(lambda x: js[x], keys))
        long_term_UI_knowledge = answer


if __name__ == "__main__":
    default_cmd = "Find my phone's MAC address"

    parser = argparse.ArgumentParser(
        description="Flask app with argparse integration")
    parser.add_argument("--task", type=str, help="Specify the TASK parameter",
                        default=default_cmd)
    parser.add_argument("--mode", type=str, choices=["normal", "preserve"],
                        default="normal", help="Specify the mode: 'normal' or 'preserve'")
    args = parser.parse_args()

    TASK = args.task
    retrivel_long_term_UI_knowledge(TASK)
    MODE = args.mode
    Graph.load_from_pickle("Graph.pkl")

    keyboard_thread = threading.Thread(target=keyboard_listener)
    keyboard_thread.daemon = True
    keyboard_thread.start()
    app.run(host='localhost', port=5002)

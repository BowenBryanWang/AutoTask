import argparse
import threading
import time
from flask import jsonify
from flask import Response
from typing import List, Dict, Any, Union
from flask import Flask, render_template, request
from src.model import Model

from page.init import Screen
from page.WindowStructure import *
from page.NodeDescriberManager import *


app = Flask(__name__)

TASK = ""
STATUS = "stop"
INDEX = 0
COMPUTATIONAL_GRAPH = []
GRAPH_ACTION=[]


@app.route('/demo', methods=['POST'])
def demo_route() -> Union[str, Response]:
    """
    This function handles the '/demo' route for the Flask app. It receives POST requests and updates the screen
    based on the request form. It then creates a new Model object and appends it to the computational graph. Finally,
    it calls the work() method of the Model object and returns the result as a JSON object or a Response object.

    Returns:
        Union[str, Response]: A JSON object or a Response object.
    """
    global TASK, STATUS, INDEX, COMPUTATIONAL_GRAPH,GRAPH_ACTION
    # return {'node_id': 1, 'trail': '[0,0]', 'action_type': 'text', 'text': "Lowe's", 'ori_absolute_id': 'android.widget.FrameLayout|0;android.widget.LinearLayout|0;android.widget.FrameLayout|0;android.widget.FrameLayout|0;android.widget.FrameLayout|0;android.view.ViewGroup|0;android.widget.FrameLayout|0;android.widget.FrameLayout|0;android.view.ViewGroup|0;android.widget.ScrollView|0;android.widget.LinearLayout|1;android.widget.LinearLayout|0;android.widget.EditText'}
    screen = Screen(INDEX)
    screen.update(request=request.form)
    if STATUS == "start":
        STATUS = "running"
        if COMPUTATIONAL_GRAPH != []:
            if INDEX < len(COMPUTATIONAL_GRAPH):
                if screen.all_text.overlap(COMPUTATIONAL_GRAPH[INDEX].screen.all_text) > 0.9:
                    model = Model(screen=screen, description=TASK,
                            prev_model=COMPUTATIONAL_GRAPH[INDEX-1], index=INDEX)
                    model.predict_module = COMPUTATIONAL_GRAPH[INDEX].predict_module
                    model.suggest_module = COMPUTATIONAL_GRAPH[INDEX].suggest_module
                    model.evaluate_module = COMPUTATIONAL_GRAPH[INDEX].evaluate_module
                    model.decide_module = COMPUTATIONAL_GRAPH[INDEX].decide_module
                    COMPUTATIONAL_GRAPH[INDEX] = model
                else:
                    model = Model(screen=screen, description=TASK,
                            prev_model=COMPUTATIONAL_GRAPH[INDEX-1], index=INDEX)
                    COMPUTATIONAL_GRAPH[INDEX] = model
                    COMPUTATIONAL_GRAPH = COMPUTATIONAL_GRAPH[:INDEX+1]
            else:
                model = Model(screen=screen, description=TASK,
                            prev_model=COMPUTATIONAL_GRAPH[-1], index=INDEX)
                COMPUTATIONAL_GRAPH.append(model)
        else:
            model = Model(screen=screen, description=TASK,
                          prev_model=None, index=INDEX)
            COMPUTATIONAL_GRAPH.append(model)
        print("work")
        result,work_status = model.work()
        if work_status == "Wrong":
            STATUS = "backtracking"
            return result
        if work_status == "Execute":
            STATUS = "start"
            INDEX += 1
            GRAPH_ACTION.append(result)
            return result
        elif result == "completed":
            STATUS = "stop"
            return Response("Task completed successfully!")
        else:
            return Response("Task failed.")
    if STATUS=="backtracking":
        INDEX-=1
        if COMPUTATIONAL_GRAPH[INDEX].feedback():
            STATUS="start"
            INDEX+=1
            return GRAPH_ACTION[INDEX-1]
        else:
            return {"node_id": 1, "trail": "[0,0]", "action_type": "back"}
    return Response("0")


@app.route("/", methods=("GET", "POST"))
def index() -> Union[str, Response]:
    return render_template("index.html", elements=json.dumps({"result": "", "image_id": 1, "semantic_info": "", "chart_data": "", "line_data": ""}))

def keyboard_listener():
    global STATUS
    while True:  # 添加无限循环
        input("Press Enter to start the task execution...")
        STATUS = "start"
        print("Task execution started!")

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask app with argparse integration")
    parser.add_argument("--task", type=str, required=True, help="Specify the TASK parameter")
    args = parser.parse_args()

    TASK = args.task
    
    # Start the keyboard listener in a separate thread
    keyboard_thread = threading.Thread(target=keyboard_listener)
    keyboard_thread.daemon = True
    keyboard_thread.start()

    app.run(host='0.0.0.0', port=5000)

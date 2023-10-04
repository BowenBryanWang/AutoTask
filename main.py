import argparse
import threading
from flask import Response
from typing import Union
from flask import Flask, request
from src.model import Model

from page.init import Screen
from page.WindowStructure import *
from page.NodeDescriberManager import *


app = Flask(__name__)

TASK = ""
STATUS = "stop"
INDEX = 0
COMPUTATIONAL_GRAPH = []
GRAPH_ACTION = []
ACTION_TRACE = {
    "ACTION": [],
    "ACTION_DESC" : [],
    "TRACE": [],
    "TRACE_DESC": [],
}


@app.route('/demo', methods=['POST'])
def demo() -> Union[str, Response]:
    """
    This function handles the '/demo' route for the Flask app. It receives POST requests and updates the screen
    based on the request form. It then creates a new Model object and appends it to the computational graph. Finally,
    it calls the work() method of the Model object and returns the result as a JSON object or a Response object.

    Returns:
        Union[str, Response]: A JSON object or a Response object.
    """
    global TASK, STATUS, INDEX, COMPUTATIONAL_GRAPH, GRAPH_ACTION
    # return {'node_id': 1, 'trail': '[0,0]', 'action_type': 'text', 'text': "Lowe's", 'ori_absolute_id': 'android.widget.FrameLayout|0;android.widget.LinearLayout|0;android.widget.FrameLayout|0;android.widget.FrameLayout|0;android.widget.FrameLayout|0;android.view.ViewGroup|0;android.widget.FrameLayout|0;android.widget.FrameLayout|0;android.view.ViewGroup|0;android.widget.ScrollView|0;android.widget.LinearLayout|1;android.widget.LinearLayout|0;android.widget.EditText'}
    screen = Screen(INDEX)
    screen.update(request=request.form)
    print("INDEX", INDEX)
    if STATUS == "start":
        STATUS = "running"
        model = Model(screen=screen, description=TASK,
                      prev_model=COMPUTATIONAL_GRAPH[-1] if COMPUTATIONAL_GRAPH != [] else None, index=INDEX)
        COMPUTATIONAL_GRAPH.append(model)
        print("work")
        result, work_status = model.work(ACTION_TRACE)
        
        if work_status == "wrong":
            STATUS = "backtracking"
            return result
        elif work_status == "Execute":
            ACTION_TRACE["ACTION"].append(model.log_json["@Action"])
            ACTION_TRACE["ACTION_DESC"].append("NEXT")
            ACTION_TRACE["TRACE"].append(model.candidate_str)
            ACTION_TRACE["TRACE_DESC"].append(model.page_description)
            STATUS = "start"
            INDEX += 1
            return result
        elif work_status == "completed":
            STATUS = "stop"
            return Response("Task completed successfully!")
        else:
            return Response("Task failed.")
    if STATUS == "backtracking":
        INDEX -= 1
        res, act = COMPUTATIONAL_GRAPH[INDEX].feedback_module.feedback(COMPUTATIONAL_GRAPH[INDEX].wrong_reason)
        if res is not None:
            COMPUTATIONAL_GRAPH = COMPUTATIONAL_GRAPH[:INDEX+1]
            result, work_status = COMPUTATIONAL_GRAPH[INDEX].work(ACTION_TRACE)
            if work_status == "wrong":
                STATUS = "backtracking"
                return result
            elif work_status == "Execute":
                ACTION_TRACE["ACTION"].append(COMPUTATIONAL_GRAPH[INDEX].log_json["@Action"])
                ACTION_TRACE["ACTION_DESC"].append("Error Recovery")
                ACTION_TRACE["TRACE"].append(COMPUTATIONAL_GRAPH[INDEX].candidate_str)
                ACTION_TRACE["TRACE_DESC"].append(COMPUTATIONAL_GRAPH[INDEX].page_description)
                STATUS = "start"
                INDEX += 1
                return result
            elif work_status == "completed":
                STATUS = "stop"
                return Response("Task completed successfully!")
            else:
                return Response("Task failed.")
        else:
            ACTION_TRACE["ACTION"].append("Backtrack")
            ACTION_TRACE["ACTION_DESC"].append("BACK")
            ACTION_TRACE["TRACE"].append(COMPUTATIONAL_GRAPH[INDEX].candidate_str)
            ACTION_TRACE["TRACE_DESC"].append(COMPUTATIONAL_GRAPH[INDEX].page_description)
            print("------------------------back--------------------------")
            return {"node_id": 1, "trail": "[0,0]", "action_type": "back"}
    return Response("0")



def keyboard_listener():
    global STATUS
    while True:
        input("Press Enter to start the task execution...")
        STATUS = "start"
        print("Task execution started!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Flask app with argparse integration")
    parser.add_argument("--task", type=str, help="Specify the TASK parameter",
                        default="increase text size one step in settings app")
    args = parser.parse_args()

    TASK = args.task

    # Start the keyboard listener in a separate thread
    keyboard_thread = threading.Thread(target=keyboard_listener)
    keyboard_thread.daemon = True
    keyboard_thread.start()

    app.run(host='localhost', port=5002)

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


@app.route('/demo', methods=['POST'])
def demo_route() -> Union[str, Response]:
    """
    This function handles the '/demo' route for the Flask app. It receives POST requests and updates the screen
    based on the request form. It then creates a new Model object and appends it to the computational graph. Finally,
    it calls the work() method of the Model object and returns the result as a JSON object or a Response object.

    Returns:
        Union[str, Response]: A JSON object or a Response object.
    """
    global TASK, STATUS, INDEX, COMPUTATIONAL_GRAPH
    print("demo")
    screen = Screen(INDEX)
    screen.update(request=request.form)
    if STATUS == "start":
        STATUS = "running"
        if COMPUTATIONAL_GRAPH != []:
            model = Model(screen=screen, description=TASK,
                          prev_model=COMPUTATIONAL_GRAPH[-1], index=INDEX)
        else:
            model = Model(screen=screen, description=TASK,
                          prev_model=None, index=INDEX)
        COMPUTATIONAL_GRAPH.append(model)
        print("work")
        result = model.work()
        
        if isinstance(result, dict):
            STATUS="start"
            INDEX += 1
            print(jsonify(result))
            return result
        elif result == "completed":
            STATUS = "stop"
            return Response("Task completed successfully!")
        
        else:
            return Response("Task failed.")
    return Response("0")


@app.route("/", methods=("GET", "POST"))
def index() -> Union[str, Response]:
    """
    This function handles the '/' route for the Flask app. It receives GET and POST requests and updates the global
    variables TASK and STATUS based on the request form. It then renders the 'index.html' template and returns it as
    a string or a Response object.

    Returns:
        Union[str, Response]: A string or a Response object.
    """
    global TASK, STATUS
    print("index")
    if request.method == "POST" and "intention" in request.form:
        TASK = request.form["intention"]
        STATUS = "start"
    else:
        STATUS = "stop"
    return render_template("index.html", elements=json.dumps({"result": "", "image_id": 1, "semantic_info": "", "chart_data": "", "line_data": ""}))


if __name__ == "__main__":

    app.run(host='0.0.0.0', port=5000)

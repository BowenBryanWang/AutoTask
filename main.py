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

from flask import jsonify

@app.route('/demo', methods=['POST'])
def demo_route() -> Union[str, Response]:
    global TASK, STATUS
    if STATUS == "start":
        screen = Screen()
        screen.update(request=request.form)
        model = Model(screen=screen, description=TASK)
        result = model.work()
        if isinstance(result, dict):
            return jsonify(result)
        elif result == "completed":
            return Response("Task completed successfully!")
        else:
            return Response("Task failed.")
    return Response("0")


@app.route("/", methods=("GET", "POST"))
def index() -> Union[str, Response]:
    global TASK,STATUS
    print("index")
    if request.method == "POST" and "intention" in request.form:
        TASK = request.form["intention"]
        STATUS = "start"
    else:
        STATUS = "stop"
    return render_template("index.html", elements=json.dumps({"result": "", "image_id": 1, "semantic_info": "", "chart_data": "", "line_data": ""}))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

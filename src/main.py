from flask import Flask, render_template, request

from page.init import Screen
from page.WindowStructure import *

from page.NodeDescriberManager import *

from flask import Flask




app = Flask(__name__)

# class Step:
#     """
#     用于记录Agent操作的每一步中的信息
#     """
#     index = -1
#     candidate = []
#     decision_result = []
#     evaluate_result = []
#     gamma = []
#     llm = Model()

#     def __init__(self, index, llm: Model):
#         self.index = index
#         self.llm = llm
#         try:
#             self.candidate = llm.candidate
#             self.decision_result = llm.decision_result
#             self.evaluate_result = llm.evaluate_result
#         except:
#             raise Exception("LLM not defined!")
#         self.gamma = [0 for _ in range(len(self.candidate))]

from typing import List, Dict, Any, Union
from flask import Response, jsonify



@app.route('/demo', methods=['POST'])
def demo_route() -> Union[str, Response]:
    screen = Screen()
    screen.update(request=request.form)
    return "Hello, World!"
    

@app.route("/", methods=("GET", "POST"))
def index() -> Union[str, Response]:
    print("index")
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
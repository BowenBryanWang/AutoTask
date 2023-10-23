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
from page.NodeDescriberManager import *
from src.utility import GPT


app = Flask(__name__)

TASK = ""
MODE = ""
MODEL = ""
STATUS = "stop"
INDEX = 0
NEW_TASK = True
ACTION_TRACE = []

@app.route('/demo', methods=['POST'])
def demo() -> Union[str, Response]:
    global TASK, STATUS, ACTION_TRACE, NEW_TASK
    screen = Screen(INDEX)
    screen.update(request=request.form)

    # 每次前端传来数据，都会创建一个screen类，这个类就是处理前端传来的数据，已经写好，内部实现复杂，如果感兴趣可以debug模式下查看其成员变量
    # TODO：实现你的ChatGPT调用仍然在此保留了我的实现，当然你的实现版本更简单，可以参考，不用这样复杂
    # 以下是你可能用到的成员变量
    print("Screen UI semantic elements:", screen.semantic_info)
    print("Screen UI semantic list 形式:", screen.semantic_info_list)

    if STATUS == "start":
        NEW_TASK = True
        ACTION_TRACE = []
        STATUS = "running"
    
    if STATUS == "running":
        model = Model(screen=screen, description=TASK)

        query_history = read_history()

        if MODEL == "LLM-0":
            prompt = paper_provided_prompt_1(model.task, model.screen.semantic_info_list)
        elif MODEL == "LLM-hist-5-CoT":
            prompt = paper_provided_prompt_2(model.task, query_history, model.screen.semantic_info_list)

        result = GPT(prompt)
        
        print(result)

        save_history(query_history, model.screen.semantic_info_list, model.task, result)

        if result["action_type"] == "report_answer":
            STATUS = "end"
            ACTION_TRACE = []
        else:
            ACTION_TRACE.append(result)

        return result
    return None

    # i.e.
    # result = GPT(task_grounding_prompt(self.model.task,self.model.similar_tasks, self.model.similar_traces, ACTION_TRACE, self.model.screen.semantic_info_list))
    # self.model.predicted_step = result["result"]
    # print("predicted_step", self.model.predicted_step)

    # if STATUS == "start":
    #     STATUS = "running"
    #     model = Model(screen=screen, description=TASK,
    #                   prev_model=COMPUTATIONAL_GRAPH[-1] if COMPUTATIONAL_GRAPH != [] else None, index=INDEX)
    #     COMPUTATIONAL_GRAPH.append(model)
    #     print("work")
    #     result, work_status = model.work(ACTION_TRACE=ACTION_TRACE)

    #     if work_status == "wrong":
    #         if MODE == "normal":
    #             STATUS = "backtracking"
    #         elif MODE == "preserve":
    #             STATUS = "running"
    #         return result
    #     elif work_status == "Execute":
    #         ACTION_TRACE["ACTION"].append(model.log_json["@Action"])
    #         ACTION_TRACE["ACTION_DESC"].append("NEXT")
    #         ACTION_TRACE["TRACE"].append(model.candidate_str)
    #         ACTION_TRACE["TRACE_DESC"].append(model.page_description)
    #         if MODE == "normal":
    #             STATUS = "start"
    #         elif MODE == "preserve":
    #             STATUS = "running"
    #         INDEX += 1
    #         return result
    #     elif work_status == "completed":
    #         save_to_file(TASK)
    #         STATUS = "stop"
    #         return Response("Task completed successfully!")
    #     else:
    #         return Response("Task failed.")
    # if STATUS == "backtracking":
    #     INDEX -= 1
    #     res, act = COMPUTATIONAL_GRAPH[INDEX].feedback_module.feedback(
    #         COMPUTATIONAL_GRAPH[INDEX].wrong_reason)
    #     ACTION_TRACE["ACTION"].append("Click on navigate back due to error")
    #     ACTION_TRACE["ACTION_DESC"].append("BACK")
    #     ACTION_TRACE["TRACE"].append(COMPUTATIONAL_GRAPH[INDEX].candidate_str)
    #     ACTION_TRACE["TRACE_DESC"].append(
    #         COMPUTATIONAL_GRAPH[INDEX].page_description)
    #     if res is not None:
    #         COMPUTATIONAL_GRAPH = COMPUTATIONAL_GRAPH[:INDEX+1]
    #         result, work_status = COMPUTATIONAL_GRAPH[INDEX].work(
    #             ACTION_TRACE=ACTION_TRACE)
    #         if work_status == "wrong":
    #             if MODE == "normal":
    #                 STATUS = "backtracking"
    #             elif MODE == "preserve":
    #                 STATUS = "running"
    #             return result
    #         elif work_status == "Execute":
    #             ACTION_TRACE["ACTION"].append(
    #                 COMPUTATIONAL_GRAPH[INDEX].log_json["@Action"])
    #             ACTION_TRACE["ACTION_DESC"].append(
    #                 "Retry after error detection")
    #             ACTION_TRACE["TRACE"].append(
    #                 COMPUTATIONAL_GRAPH[INDEX].candidate_str)
    #             ACTION_TRACE["TRACE_DESC"].append(
    #                 COMPUTATIONAL_GRAPH[INDEX].page_description)
    #             if MODE == "normal":
    #                 STATUS = "start"
    #             elif MODE == "preserve":
    #                 STATUS = "running"
    #             INDEX += 1
    #             return result
    #         elif work_status == "completed":
    #             save_to_file(TASK)
    #             STATUS = "stop"
    #             return Response("Task completed successfully!")
    #         else:
    #             return Response("Task failed.")
    #     else:

    #         print("------------------------back--------------------------")
    #         return {"node_id": 1, "trail": "[0,0]", "action_type": "back"}

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
{"action_type": "type", "text": <text>}
{"action_type": "navigate_home"}
{"action_type": "navigate_back"}
{"action_type": "scroll", "direction": "up"}
{"action_type": "scroll", "direction": "down"}
{"action_type": "scroll", "direction": "left"}
{"action_type": "scroll", "direction": "right"}
{"action_type": "report_answer", "text": <answer_to_the_instruction>}
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

def paper_provided_prompt_2(task, query_history, current_ui):
    prompt = []
    prompt.append({
            "role": "system",
            "content": 
"""
Given a mobile screen and a question, provide the action based on the screen
information.

Available Actions:
{"action_type": "click", "idx": <element_idx>}
{"action_type": "type", "text": <text>}
{"action_type": "navigate_home"}
{"action_type": "navigate_back"}
{"action_type": "scroll", "direction": "up"}
{"action_type": "scroll", "direction": "down"}
{"action_type": "scroll", "direction": "left"}
{"action_type": "scroll", "direction": "right"}
{"action_type": "report_answer", "text": <answer_to_the_instruction>}
"""
        })
    
    for query in query_history:
        prompt.append({
            "role": "user",
            "content": 
"""
Previous Actions: {}
Screen: {}
Instruction: {}
Answer: {}
""".format(query["Previous Actions"], query["Screen"], query["Instruction"], query["Answer"])
        })

    prompt.append({
            "role": "user",
            "content": 
"""
Screen: {}
Instruction: {}
Think step by step, and output JSON format with property name enclosed in double quotes. When found the answer or finished the task, use "report_answer" to report the answer or to end the task.
Answer:
""".format(current_ui, task)
        })
    return prompt

def read_history():
    with open("./src/KB/history.json", "r") as f:
        history = json.load(f)
    return history

def save_history(query_history, screen, instruction, answer):
    global ACTION_TRACE, NEW_TASK
    history = {
        "Previous Actions": ACTION_TRACE,
        "Screen": screen,
        "Instruction": instruction,
        "Answer": answer
    }
    if NEW_TASK:
        while len(query_history) >= 5:
            query_history.pop()
        query_history.insert(0, history)
        NEW_TASK = False
    else:
        query_history[0] = history
    with open("./src/KB/history.json", "w") as f:
        json.dump(query_history, f, indent=4)

def save_to_file(task_name):
    task_name = task_name.replace(" ", "_")
    # 在同级目录./Shots下创建一个名为task_name的文件夹
    if not os.path.exists("./Shots/{}".format(task_name)):
        os.makedirs("./Shots/{}".format(task_name))
        # 将./logs文件夹和./Page/static/data文件夹移到其下
        shutil.move("./logs", "./Shots/{}".format(task_name))
        shutil.move("./Page/static/data", "./Shots/{}".format(task_name))


def on_key_release(key):
    global STATUS
    if key == keyboard.Key.enter:
        STATUS = "start"
        print("Task execution started!")
    elif key == keyboard.Key.delete:
        STATUS = "end"
        print("Task ended!")


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
    parser.add_argument("--model", type=str, choices=["LLM-0", "LLM-hist-5-CoT"],
                        default="LLM-0", help="Specify the model: 'LLM-0' or 'LLM-hist-5-CoT'")
    args = parser.parse_args()

    TASK = args.task
    MODE = args.mode
    MODEL = args.model

    keyboard_thread = threading.Thread(target=keyboard_listener)
    keyboard_thread.daemon = True
    keyboard_thread.start()

    app.run(host='localhost', port=5002)

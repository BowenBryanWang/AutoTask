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


app = Flask(__name__)

TASK = ""
MODE = ""
STATUS = "stop"
INDEX = 0


@app.route('/demo', methods=['POST'])
def demo() -> Union[str, Response]:
    global TASK, STATUS
    screen = Screen(INDEX)
    screen.update(request=request.form)

    # 每次前端传来数据，都会创建一个screen类，这个类就是处理前端传来的数据，已经写好，内部实现复杂，如果感兴趣可以debug模式下查看其成员变量
    # TODO：实现你的ChatGPT调用仍然在此保留了我的实现，当然你的实现版本更简单，可以参考，不用这样复杂
    # 以下是你可能用到的成员变量
    print("Screen UI semantic elements:", screen.semantic_info)
    print("Screen UI semantic list 形式:", screen.semantic_info_list)
    # TODO：任务
    # 照抄论文中的prompt，然后把刚刚这些变量和用户任务TASK输入到GPT调用里面，得到返回结果后处理好，然后return掉即可。
    # GPT如何调用？已经写好接口，参考./src/Utility.py中的GPT函数，和./src/Utility.py中的GPT调用示例 Task_grounding()函数
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
    return Response("0")


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

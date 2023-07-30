import base64
import json
import time

import numpy as np
import cv2
from page.NodeDescriberManager import NodeDescriberManager

from page.WindowStructure import PageInstance
from page.process import transfer_2_html


class Screen:

    cnt = 0
    describermanagers_init = False
    describermanagers = {}
    all_text = ""  # 当前页面的所有文本
    current_path = []
    current_path_str = "Begin"
    page_id_now = 0
    screenshot = None
    layout = None
    imgdata = None
    page_instance = None
    page_root = None
    semantic_nodes = []
    semantic_info = []
    upload_time = 0
    page_description = ""

    def __init__(self,cnt=0) -> None:
        self.cnt = cnt

    def update(self, request):
        # if not self.describermanagers_init:
        #     self.init_describer()  # 全局第一次初始化discribermanagers
        self.cnt += 1  # 将数据存储时候页面的编号
        start_time = time.time()  # 记录开始时间
        self.page_id_now = self.cnt
        self.screenshot = request["screenshot"]
        if request['layout'] == self.layout:
            print("Layout depredicted")
            return "error:"
        self.layout = request['layout']
        self.imgdata = base64.b64decode(self.screenshot)
        self.page_instance = PageInstance()
        self.page_instance.load_from_dict("", json.loads(self.layout))
        self.page_root = self.page_instance.ui_root
        if len(self.page_root.children[0].children[0].children) == 2:
            print("FUCK")
            self.page_root.children[0].children[0].children = [
                self.page_root.children[0].children[0].children[0]]
        print("all_text", self.page_root.generate_all_text())
        self.semantic_nodes = self.page_root.get_all_semantic_nodes()

        # 创建与semantic_nodes["nodes"]等长的type列表，用于存放每个节点的类型
        self.semantic_nodes["type"] = [
            "" for ii in range(len(self.semantic_nodes["nodes"]))]
        for i in range(len(self.semantic_nodes["nodes"])):
            self.semantic_nodes["nodes"][i].update_page_id(self.page_id_now)
            dis = 99.0
            for key, value in self.describermanagers.items():
                if key == "Root Object;":
                    continue
                tmp_dis = value.calculate(self.semantic_nodes["nodes"][i])
                if tmp_dis < dis:
                    dis = tmp_dis
                    self.semantic_nodes["type"][i] = key.split(";")[-2]
        print("semantic_nodes", self.semantic_nodes["type"])

        self.semantic_info = transfer_2_html(self.semantic_nodes["nodes"])
        self.semantic_info_str = "".join(self.semantic_info)
        with open('./page/static/data/page{}.txt'.format(self.cnt), 'w') as fp:
            fp.write("".join(self.semantic_info))
        print("semantic_info", self.semantic_info)
        print("semantic_nodes", len(self.semantic_nodes))
        end_time = time.time()
        self.upload_time = end_time  # 记录本次上传的时间
        print("upload_time", self.upload_time)
        print("time:", end_time-start_time, flush=True)
        with open('./page/static/data/imagedata{}.jpg'.format(self.cnt), 'wb') as fp:
            fp.write(self.imgdata)
        with open('./page/static/data/page{}.json'.format(self.cnt), 'w') as fp:
            fp.write(self.layout)
        return "OK"

    def init_describer(self):
        print("loadmodel")
        global relation_dict
        with open('./page/static/data'+'/manager_structure.json', 'r', encoding='utf-8') as file:
            describermanagers_str = json.load(file)
            global describermanagers
            for key, value in describermanagers_str.items():
                value = json.loads(value)
                print("loading", key)
                if key == "Root Object;":
                    self.describermanagers[key] = NodeDescriberManager(
                        "Root", None, "Root Object;")
                if key.count(";") > 1:
                    p_last = key.split(";")[-2]
                    model_fa_id = key.replace(p_last+";", "")
                    self.describermanagers[key] = NodeDescriberManager(
                        value["type"], self.describermanagers[model_fa_id], key)
                    self.describermanagers[model_fa_id].update_children(
                        self.describermanagers[key])
                    tmp_positive_ref_nodes = []
                    tmp_negative_ref_nodes = []
                    tmp_positive_nodes = []
                    for node_info in value["positive_ref"]:
                        with open('./page/static/data/'+'page' + str(node_info["page_id"]) + '.json', 'r')as fp:
                            tmp_layout = json.loads(fp.read())
                        tmp_page_instance = PageInstance()
                        if isinstance(tmp_layout, list):
                            tmp_layout = tmp_layout[0]
                        tmp_page_instance.load_from_dict("", tmp_layout)
                        tmp_page_root = tmp_page_instance.ui_root
                        tmp_node = tmp_page_root.get_node_by_relative_id(
                            node_info["index"])
                        tmp_node.update_page_id(node_info["page_id"])
                        tmp_positive_ref_nodes.append(
                            (tmp_node.findBlockNode(), tmp_node))
                    for node_info in value["negative_ref"]:
                        print("node_info", node_info)
                        with open('./page/static/data/'+'page' + str(node_info["page_id"]) + '.json', 'r')as fp:
                            tmp_layout = json.loads(fp.read())
                        tmp_page_instance = PageInstance()
                        if isinstance(tmp_layout, list):
                            tmp_layout = tmp_layout[0]
                        tmp_page_instance.load_from_dict("", tmp_layout)
                        tmp_page_root = tmp_page_instance.ui_root
                        print(node_info["page_id"],
                              tmp_page_root.generate_all_text())
                        tmp_node = tmp_page_root.get_node_by_relative_id(
                            node_info["index"])
                        tmp_node.update_page_id(node_info["page_id"])
                        tmp_negative_ref_nodes.append(
                            (tmp_node.findBlockNode(), tmp_node))
                    for node_info in value["positive"]:
                        with open('./page/static/data/'+'page' + str(node_info["page_id"]) + '.json', 'r')as fp:
                            tmp_layout = json.loads(fp.read())
                        tmp_page_instance = PageInstance()
                        if isinstance(tmp_layout, list):
                            tmp_layout = tmp_layout[0]
                        tmp_page_instance.load_from_dict("", tmp_layout)
                        tmp_page_root = tmp_page_instance.ui_root
                        tmp_node = tmp_page_root.get_node_by_relative_id(
                            node_info["index"])
                        tmp_node.update_page_id(node_info["page_id"])
                        tmp_positive_nodes.append(
                            (tmp_node.findBlockNode(), tmp_node))
                    self.describermanagers[key].update(
                        tmp_positive_ref_nodes, tmp_negative_ref_nodes, tmp_positive_nodes)
        global describermanagers_init
        describermanagers_init = True

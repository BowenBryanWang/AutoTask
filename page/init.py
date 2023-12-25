"""
Description: This module contains the Screen class for UI analysis.
Author: Your Name
Date: Creation Date
License: Appropriate License (e.g., MIT License)
"""

import base64
import json
import os
import time

from page.WindowStructure import PageInstance
from page.process import transfer_2_html


class Screen:
    """
    Represents a screen for UI analysis.
    """

    @staticmethod
    def process_layout(root):
        # 删除所有不可见的子元素
        # 删除visible属性为false的子元素
        if 'node' in root:
            if isinstance(root['node'], dict):
                root['node'] = [root['node']]
            root['node'] = [Screen.process_layout(x) for x in root['node'] if (
                '@visible' not in x or x['@visible'])]

        return root

    @staticmethod
    def process_frag_overlap(node, rect_exist=None):
        overlapped = False
        bound = eval(node['@bounds'].replace('][', '],['))
        x0, y0, x1, y1 = bound[0][0], bound[0][1], bound[1][0], bound[1][1]
        if rect_exist is not None:
            for x_min, y_min, x_max, y_max in rect_exist:
                if x_min <= x0 <= x_max and y_min <= y0 <= y_max and x_min <= x1 <= x_max and y_min <= y1 <= y_max:
                    overlapped = True
        if overlapped:
            node['@visible'] = False

        if 'node' not in node:
            node['node'] = []
        if isinstance(node['node'], dict):
            node['node'] = [node['node']]

        if 'FrameLayout' in node['@class']:
            crt_rect_exist = set()
            if rect_exist is not None:
                crt_rect_exist.update(rect_exist)

            for sub_node in node['node'][::-1]:
                crt_rect_exist.add(Screen.process_frag_overlap(
                    sub_node, crt_rect_exist))
        else:
            for sub_node in node['node']:
                Screen.process_frag_overlap(sub_node, rect_exist)
        return (x0, y0, x1, y1)

    def __init__(self, cnt=0) -> None:
        """
        Initializes a Screen object.

        Args:
            cnt (int, optional): The number of the screen. Defaults to 0.
        Returns:
            None
        """
        self.cnt = cnt
        self.all_text = ""
        self.page_id_now = 0
        self.screenshot = None
        self.layout = None
        self.imgdata = None
        self.page_instance = None
        self.page_root = None
        self.semantic_nodes = []
        self.semantic_info = []
        self.upload_time = 0
        self.page_description = ""

    def update(self, request):
        if not os.path.exists("./page/data"):
            os.makedirs("./page/data")
        self.cnt += 1
        start_time = time.time()
        self.page_id_now = self.cnt
        self.screenshot = request["screenshot"] if 'screenshot' in request else None
        if request['layout'] == self.layout:
            print("Layout depredicted")
            return "error:"
        self.layout = request['layout']
        self.imgdata = base64.b64decode(
            self.screenshot) if self.screenshot is not None else None
        self.page_instance = PageInstance()
        layout_json = json.loads(self.layout)
        # Screen.process_frag_overlap(layout_json)
        layout_json = Screen.process_layout(layout_json)
        self.page_instance.load_from_dict("", layout_json)
        self.page_root = self.page_instance.ui_root
        print("all_text", self.page_root.generate_all_text())
        self.semantic_nodes, relation = self.page_root.get_all_semantic_nodes()

        self.semantic_info_all_warp, self.semantic_info_half_warp, self.semantic_info_no_warp, self.trans_relation = transfer_2_html(
            self.semantic_nodes["nodes"], relation)
        self.semantic_info_no_warp_with_id = list(
            filter(lambda x: "id=" in x, self.semantic_info_no_warp))

        self.semantic_info_str = "".join(self.semantic_info)

        with open('./page/data/page{}.txt'.format(self.cnt), 'w', encoding="utf-8") as fp:
            fp.write("".join(self.semantic_info_all_warp))
        print("semantic_info", self.semantic_info_all_warp)
        end_time = time.time()
        self.upload_time = end_time
        print("upload_time", self.upload_time)
        print("time:", end_time-start_time, flush=True)
        if self.imgdata is not None:
            with open('./page/data/imagedata{}.jpg'.format(self.cnt), 'wb') as fp:
                fp.write(self.imgdata)
        with open('./page/data/page{}.json'.format(self.cnt), 'w', encoding="utf-8") as fp:
            fp.write(self.layout)
        return "OK"

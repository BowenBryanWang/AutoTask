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
        print("all_text", self.page_root.generate_all_text())
        self.semantic_nodes, relation = self.page_root.get_all_semantic_nodes()

        self.semantic_info, self.semantic_info_list, self.trans_relation = transfer_2_html(
            self.semantic_nodes["nodes"], relation)

        self.semantic_info_str = "".join(self.semantic_info)

        with open('./page/data/page{}.txt'.format(self.cnt), 'w', encoding="utf-8") as fp:
            fp.write("".join(self.semantic_info))
        print("semantic_info", self.semantic_info_str)
        end_time = time.time()
        self.upload_time = end_time  # 记录本次上传的时间
        print("upload_time", self.upload_time)
        print("time:", end_time-start_time, flush=True)
        with open('./page/data/imagedata{}.jpg'.format(self.cnt), 'wb') as fp:
            fp.write(self.imgdata)
        with open('./page/data/page{}.json'.format(self.cnt), 'w', encoding="utf-8") as fp:
            fp.write(self.layout)
        return "OK"

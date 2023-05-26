# coding=utf-8
#  这个文件强调的是一个应用爬虫结果的组织形式

import os.path
import Screen.Utility
import json
from queue import Queue, deque
import cv2


try:
    from typing import List, Optional, Dict, Callable, Tuple, Any, Deque, Set
except ImportError:
    pass


class UINode:

    STOP_NODE_LIST = []

    MAX_SCROLL_STEP = 1

    def __init__(self, crt_layout, parent, instance):
        if crt_layout is None:
            return
        self.page_instance = instance  # type: PageInstance
        self.depth = 0 if parent is None else parent.depth + 1
        self.parent = parent  # type: UINode
        self.index = int(crt_layout['@index'])
        self.page_id = instance.page_cnt
        if '@text' in crt_layout:
            self.text = crt_layout['@text']  # type: str
        else:
            self.text = ""
        if '@resource-id' in crt_layout:
            self.resource_id = crt_layout['@resource-id']  # type: str
        else:
            self.resource_id = ""
        self.node_class = crt_layout['@class']  # type: str
        if '@package' in crt_layout:
            self.package = crt_layout['@package']  # type: str
        else:
            self.package = ""
        if '@content-desc' in crt_layout:
            self.content_desc = crt_layout['@content-desc']  # type: str
        else:
            self.content_desc = ""
        self.checkable = (crt_layout['@checkable'] ==
                          'true') or (crt_layout['@checkable'] == True)
        self.checked = (crt_layout['@checked'] ==
                        'true') or (crt_layout['@checked'] == True)
        self.clickable = (crt_layout['@clickable'] ==
                          'true') or (crt_layout['@clickable'] == True)
        if '@enabled' in crt_layout:
            self.enabled = (crt_layout['@enabled'] ==
                            'true') or (crt_layout['@enabled'] == True)
        else:
            self.enabled = True
        if '@focusable' in crt_layout:
            self.focusable = (
                crt_layout['@focusable'] == 'true') or (crt_layout['@focusable'] == True)
        else:
            self.focusable = True
        if '@focused' in crt_layout:
            self.focused = (crt_layout['@focused'] ==
                            'true') or (crt_layout['@focused'] == True)
        else:
            self.focused = False
        if '@scrollable' in crt_layout:
            self.scrollable = (
                crt_layout['@scrollable'] == 'true') or (crt_layout['@scrollable'] == True)
        else:
            self.scrollable = False
        self.long_clickable = (
            crt_layout['@long-clickable'] == 'true') or (crt_layout['@long-clickable'] == True)
        # self.password = (crt_layout['@password'] == 'true')
        if '@selected' in crt_layout:
            self.selected = (
                crt_layout['@selected'] == 'true') or (crt_layout['@selected'] == True)
        else:
            self.selected = False
        if '@nodeid' in crt_layout:
            self.ori_node_id = crt_layout['@nodeid']
        else:
            self.ori_node_id = None
        self.editable = (crt_layout['@editable'] ==
                         'true') or (crt_layout['@editable'] == True)
        # self.accessibilityFocused = (crt_layout['@accessibilityFocused'] == 'true')
        # self.dismissable = (crt_layout['@dismissable'] == 'true')  # todo 这个属性如何利用
        self.executable = self.clickable | self.long_clickable | self.editable | self.scrollable
        self.clone_source = None

        self.bound = [int(x) for x in crt_layout['@bounds'].replace('][', ',').replace(']', '').replace('[', '').split(
            ',')]  # type: List[int]  # 左上右下两个点四个坐标
        self.width = self.bound[2] - self.bound[0]
        self.height = self.bound[3] - self.bound[1]
        self.center = [(self.bound[0] + self.bound[2]) / 2,
                       (self.bound[1] + self.bound[3]) / 2]
        # 面积
        self.area = self.width * self.height
        self.isVisible = (self.bound[0] < self.bound[2]
                          and self.bound[1] < self.bound[3])

        self.absolute_id = self.node_class if self.parent is None else self.parent.absolute_id + '|%d;%s' % (
            self.index, self.node_class)  # type: str

        # self.absolute_id = None  # type: str
        # type: str # 需要在知道的 dynamic entrance 之后才能确定 在原来基础上，不对动态区域子节点 index 进行要求
        self.absolute_dynamic_id = None

        if 'node' not in crt_layout.keys():  # 不对 WebView 进行处理
            self.children = list()  # type: List[UINode]
        elif isinstance(crt_layout['node'], list):
            self.children = [UINode(x, self, instance)
                             for x in crt_layout['node']]  # type: List[UINode]
        else:
            # type: List[UINode]
            self.children = [UINode(crt_layout['node'], self, instance)]
        self.blockRoot = None

        # # 接下来的这些属性不是 UI 树中原有的属性,是为了处理方便加上去的
        # # 这些属性现在还仅仅是默认值
        # # self.action_result = None  # type: ActionResult
        # self.is_in_static_region = True
        # self.is_dynamic_entrance = False  # 意味着其每一个子节点都是某个动态区域的根节点 现在仅允许一级的动态

        # self.all_text = self.generate_all_text()  # type: str
        # self.all_content = self.generate_all_content()  # type: str

        # self.is_click_with_context = False

        # # type: Dict[Tuple[int, Optional[int, str, None]], List[Optional[ActionResult]]]  # 带参数的操作类型向实际操作结果的映射
        # self.action_type_to_action_result = dict()
        # # type: Dict[ActionResult, List[Tuple[Tuple[int, Any], str]]]
        # self.action_result_to_action_type = dict()
        # # type: List[Tuple[int, Optional[int, str, None]]]  # 存储了所有进行的操作
        # self.actions_to_act = list()

        # self.state_of_sons_skip_path = list()  # type: List[List[Tuple[int]]]

        # self.corresponding_merged_node = None

        # if self.parent is None:
        #     self.action_type_to_action_result[(Action.GLOBAL_BACK, None)] = []
        #     self.actions_to_act.append((Action.GLOBAL_BACK, None))

        # if self.editable:
        #     self.action_type_to_action_result[(Action.ENTER_TEXT, '的')] = [
        #     ]   # todo 如何根据上下文生成合法的文本
        #     self.actions_to_act.append((Action.ENTER_TEXT, '的'))
        #     self.action_type_to_action_result[(Action.ENTER_TEXT, '')] = [
        #     ]  # 同时支持添加文本和删除文本的操作
        #     self.actions_to_act.append((Action.ENTER_TEXT, ''))
        # if self.clickable:
        #     self.action_type_to_action_result[(Action.CLICK, None)] = []
        #     self.actions_to_act.append((Action.CLICK, None))
        # if self.scrollable:  # 即使这个节点不是一个动态入口，这个节点还是一个可以被滚动的节点。两者并不矛盾
        #     for i in range(- UINode.MAX_SCROLL_STEP, UINode.MAX_SCROLL_STEP + 1):
        #         if i == 0:
        #             continue
        #         self.action_type_to_action_result[(Action.SCROLL, i)] = []
        #         self.actions_to_act.append((Action.SCROLL, i))

        # '''
        # if self.long_clickable:
        #     self.action_type_to_action_result[(Action.LONG_CLICK, None)] = None
        #     self.actions_to_act.append((Action.LONG_CLICK, None))
        # '''

        # self.fit_result_region_inside = None  # type: StaticDynamicSplit.FitResultRegion
        # self.new_ui_node_in_fit_res = None  # type: WindowStructure.UINode
        # self.semantic_id = -1
        return

    '''def print_debug_info(self):
        print "depth: ",self.depth
        print "parent: ",self.parent
        print "index: ",self.index
        print "resource_id: ",self.resource_id
        print "text: ",self.text
        print "instance index: ",self.page_instance.index
        print "state index: ",self.page_instance.page_state.index
        print "page index: ",self.page_instance.page_instance.page.index'''

    def has_semantic_info(self):
        # 判断该节点以及它的所有子节点是否有语义信息
        # 语义信息指的是一个节点有没有text或者description或者content-desc
        def hasSemanticInfo(self):
            if self.text != '' or self.content_desc != '':
                return True
            else:
                return False
        if hasSemanticInfo(self):
            return True
        else:
            # 遍历所有后代
            all_children = [self]
            while all_children:
                current_node = all_children.pop()
                if hasSemanticInfo(current_node):
                    return True
                else:
                    all_children.extend(current_node.children)
            return False

    def generate_all_semantic_info(self):
        # 获得该节点和它的所有后代，所有的语义信息，以dict形式返回
        # {"text":[],"content-desc":[],"description":[]}
        res = {"text": [], "content-desc": [], "class": [], "Major_text": []}

        def generateAllSemanticInfo(self):
            semanticInfo = {}
            if self.text != '':
                semanticInfo['text'] = [self.text]
            if self.content_desc != '':
                semanticInfo['content-desc'] = [self.content_desc]
            if self.node_class != '':
                semanticInfo['class'] = [self.node_class.split('.')[-1]]
            return semanticInfo
        stack = [self]
        while stack:
            current_node = stack.pop()
            if current_node.children != [] and current_node.children is not None:
                stack.extend(current_node.children[::-1])
            tmp_info = generateAllSemanticInfo(current_node)
            if "text" in tmp_info:
                if res["Major_text"] == []:
                    res["Major_text"] = tmp_info["text"]
                res["text"].extend(tmp_info["text"])
            if "content-desc" in tmp_info:
                res["content-desc"].extend(tmp_info["content-desc"])
            if "class" in tmp_info:
                if res["class"] == []:
                    res["class"] = tmp_info["class"]
        # 从text中去除Major_text

        return res

    def has_similar_children(self):
        # 如果一个节点的子节点中有半数以上的子节点的宽度和高度都在一个范围内，那么就认为这个节点有相似的子节点
        # 这个函数用于判断一个节点是否有相似的子节点
        all = {"width": [], "height": []}
        if self.children != [] and len(self.children) > 1:
            for child in self.children:
                all["width"].append(child.width)
                all["height"].append(child.height)
            # 找到all中width和height的众数比例
            widthModeRatio = all["width"].count(
                max(set(all["width"]), key=all["width"].count))/len(all["width"])
            heightModeRatio = all["height"].count(
                max(set(all["height"]), key=all["height"].count))/len(all["height"])
            # print("area:",widthModeRatio,heightModeRatio)
            if widthModeRatio*heightModeRatio > 0.8:
                return True
        return False

    def is_selected(self):
        prob = 1
        # 如果节点的面积大于页面面积的0.4，给予惩罚
        if self.area > 1080*2310*0.4:
            # print("area too large")
            prob *= 0.3
        if self.clickable:
            # print("clickable")
            prob *= 1
        else:
            # print("not clickable")
            prob *= 0
        if self.executable:
            # print("executable")
            prob *= 1.5
        else:
            # print("not executable")
            prob *= 0.1
        if self.has_semantic_info():
            # print("has semantic info")
            prob *= 1.5
        else:
            # print("no semantic info")
            prob *= 0.5
        if self.has_similar_children():
            # print("has similar children")
            prob *= 0.2
        if self.editable:
            # print("editable")
            prob *= 2
        # print(prob)
        return prob

    def get_all_semantic_nodes(self):
        # 此函数的作用是获取当前页面中所有的有语义的节点
        # 从根节点开始

        stack = [self]
        res = {"nodes": []}
        while stack:
            node = stack.pop()
            if node.is_selected() >= 0.8:
                res["nodes"].append(node)
            for child in node.children:
                stack.append(child)
        # 对res进行剪枝，规则为：若res中一节点是另一节点的祖先，则删除祖先节点
        # print("before pruning:",len(res["nodes"]))
        for i in range(len(res["nodes"])):
            for j in range(len(res["nodes"])):
                if i != j and res["nodes"][i].is_ancestor(res["nodes"][j]):
                    res["nodes"][j] = None
        res["nodes"] = [node for node in res["nodes"] if node is not None]
        return res

    def common_ancestor(self, other1, other2):
        if other1 is None or other2 is None:
            return None
        if other1.depth == other2.depth:
            if other1 == other2:
                return other1
            else:
                return self.common_ancestor(other1.parent, other2)
        if other1.depth > other2.depth:
            return self.common_ancestor(other1.parent, other2)
        else:
            return self.common_ancestor(other1, other2.parent)

    def get_all_clickable_nodes(self):
        res = list()
        if self.clickable:
            res.append(self)
        for child in self.children:
            res.extend(child.get_all_clickable_nodes())
        return res

    def width(self):
        return self.bound[2]-self.bound[0]

    def height(self):
        return self.bound[3]-self.bound[1]

    def isListNode(self):
        return self.children != []

    def is_list_item_node(self):
        parent = self.parent
        if parent is None:
            return False
        if self.findBlockNode() is None:
            return False
        if self.findBlockNode() == self:
            return True
        return False

    def findBlockNode(self):
        if self.blockRoot != None:
            return self.blockRoot
        crtNode = self
        p = None
        while (crtNode != None) and (crtNode.parent != None):
            # if crtNode.parent and crtNode.parent.is_dynamic_entrance:
            #     p = crtNode
            #     break
            crtNode = crtNode.parent
        if p is not None:
            self.blockRoot = p
        else:
            self.blockRoot = self
        if self.blockRoot == None:
            print("??", p, self)
        return self.blockRoot

    def draw_the_tree(self, depth, file_name, screen_path):
        for i in range(depth):
            print("     ", end='')
        print(file_name, end=': ')
        '''if block_name == "VB1_0":
            print(self.children_block[4].bound, "ui_node:",end=' ')
            print(self.children_block[4].ui_node.node_class, self.children_block[4].ui_node.text)
            return'''
        print(self.bound, end=' ')
        print(self.node_class, self.text)
        if file_name == "ui_node2_0_0_2":
            for i in range(depth+1):
                print("     ", end='')
            print("......")
            return
        if file_name == "ui_node2_0_0_9":
            for i in range(depth+1):
                print("     ", end='')
            print("......")
            quit()
        if (len(self.children) != 0):
            # if img is None:
            img = cv2.imread(screen_path, 1)
            crt_bound = self.bound
            #cv2.rectangle(img, (crt_bound[0], crt_bound[1]), (crt_bound[2], crt_bound[3]), (255, 0, 0), 10)
            #mask = np.zeros((img.shape))
            for child in self.children:
                # if block.ui_node:
                bound = child.bound
                #mask = cv2.rectangle(mask, (bound[0], bound[1]), (bound[2], bound[3]), (0, 255, 0), thickness = -1)
                cv2.rectangle(img, (bound[0], bound[1]),
                              (bound[2], bound[3]), (0, 255, 0), 10)
            # cv2.imwrite("mask.jpg",mask)
            #zero_mask = cv2.imread("mask.jpg")
            #img = cv2.addWeighted(img,0.9,zero_mask,0.1,0)
            cutimg = img[crt_bound[1]:crt_bound[3], crt_bound[0]:crt_bound[2]]
            #crt_bound = self.root_block.node_bound
            #cutimg = img[crt_bound[1]:crt_bound[3],crt_bound[0]:crt_bound[2]]
            cv2.imwrite("./result/"+file_name+".jpg", cutimg)
        for i in range(len(self.children)):
            child = self.children[i]
            new_file_name = file_name
            if self.parent is None:
                new_file_name += str(i)
            else:
                new_file_name += "_"+str(i)
            child.draw_the_tree(depth+1, new_file_name, screen_path)

    def get_all_important_nodes(self):
        self.is_important = False
        self.is_valid = False
        for child in self.children:
            if child.get_all_important_nodes():
                self.is_valid = True
        if (self.is_text_node()) and ((self.bound[3] - self.bound[1]) >= 10):
            self.is_important = True
        area = (self.bound[2]-self.bound[0])*(self.bound[3]-self.bound[1])
        area_threshold = 350000
        # print(self.is_important)
        if ((self.clickable or self.checkable) and (area < area_threshold)) or \
                self.scrollable or self.long_clickable or self.selected or self.editable:
            self.is_important = True
        # print(self.is_important)
        if self.bound[0] < 0 or self.bound[1] < 0 or self.bound[2] < 0 or self.bound[3] < 0:
            self.is_important = False
        if self.bound[2]-self.bound[0] < 5:
            self.is_important = False
        if self.bound[3]-self.bound[1] < 5:
            self.is_important = False
        if not self.isVisible:
            self.is_important = False
        if self.is_important:
            self.is_valid = True
        '''if self.content_desc == "分隔栏":
            print(self.is_important, self.clickable, self.scrollable, self.long_clickable, self.selected, self.editable, self.bound)
            quit()'''
        return self.is_valid

    def is_text_node(self):
        # TODO: 判断是否包含文本信息，不一定就是text非空，要考虑图像信息
        '''if self.content_desc=="分隔栏":
            print(self.text=="",self.node_class.find("TextView"))
            quit()'''
        if self.node_class.find("TextView") != -1 and self.text == "":
            return False
        return ((self.text != "") or (self.content_desc != "")) and (self.node_class.find("Image") == -1)

    def is_virtual_text_node(self):
        for child in self.children:
            if (not child.is_text_node()) or (not child.is_virtual_text_node()):
                return False
        return True

    def only_have_text_important_node(self):
        for child in self.children:
            if not child.only_have_text_important_node():
                return False
        for child in self.children:
            if child.is_important and (not child.is_text_node()):
                return False
        return True

    def print_bound_tree(self):
        print(self.depth, "bound:", self.bound)
        if hasattr(self, "visual_bound"):
            print("visual_bound:", self.visual_bound)
        for child in self.children:
            child.print_bound_tree()

    def verify_validity(self):
        # TODO (UINode->boolean)
        # print(self.bound)
        if self.bound[0] < 0 or self.bound[1] < 0 or self.bound[2] < 0 or self.bound[3] < 0:
            #print(self.depth," HORIZONTAL")
            return False
        if self.bound[2]-self.bound[0] <= 0:
            #print(self.depth," HORIZONTAL")
            return False
        if self.bound[3]-self.bound[1] < 5:
            #print(self.depth," VERTICAL")
            return False
        if not self.isVisible:
            #print(self.depth,": IS NOT VISIBLE")
            return False
        '''if not self.is_valid:
            print(self.depth,": IS NOT VALID")
            return False'''
        if self.hasattr("visual_bound"):
            # print(self.visual_bound)
            if self.visual_bound[2]-self.visual_bound[0] < 0:
                #print(self.depth," HORIZONTAL")
                return False
            if self.visual_bound[3]-self.visual_bound[1] < 0:
                #print(self.depth," VERTICAL")
                return False
        return True

    def has_valid_children(self):
        for child in self.children:
            if child.verify_validity():
                return True
        return False

    def get_valid_children(self):
        res = []
        for child in self.children:
            if child.verify_validity():
                res.append(child)
        return res

    def get_valid_offspring(self):
        res = []
        for child in self.children:
            if child.verify_validity():
                res.append(child)
            res += child.get_valid_offspring()
        return res

    def is_ancestor(self, other_node):  # other_node是self的祖先
        crt_node = self
        while crt_node is not None:
            if crt_node is other_node:
                return True
            crt_node = crt_node.parent
        return False

    def is_brother(self, other_node):
        if self.parent == other_node.parent:
            return True
        return False

    def count_node_num(self):
        res = 1
        for n in self.children:
            res += n.count_node_num()
        return res

    def get_id_relative_to(self, related_root, is_root_index_important=True):
        # type: (UINode, UINode) -> str
        if not self.absolute_id.startswith(related_root.absolute_id):
            return None
        res = self.absolute_id[len(related_root.absolute_id):]
        res = related_root.node_class + res
        return res

    def get_ori_id_relative_to(self, related_root, is_root_index_important=True):
        # type: (UINode, UINode) -> str
        if self.ori_node_id is None:
            self.ori_node_id = self.absolute_id
        if related_root.ori_node_id is None:
            related_root.ori_node_id = related_root.absolute_id
        if not self.ori_node_id.startswith(related_root.ori_node_id):
            return None
        res = self.ori_node_id[len(related_root.ori_node_id):]
        res = related_root.node_class + res
        return res

    def color_dis(self, color1, color2):
        sum = 0
        for i in range(3):
            sum += (int(color1[i])-int(color2[i]))**2
        return sum**0.5

    def have_nodes_with_text(self):
        if self.text != "":
            return True
        for child in self.children:
            if child.have_nodes_with_text():
                return True
        return False

    def is_the_same_type(self, node_list):

        print(node_list[0].depth, node_list[0].node_type,
              node_list[0].generate_all_text())
        if node_list[0].node_class != self.node_class:
            return False
        if node_list[0].checkable != self.checkable:
            return False
        if node_list[0].clickable != self.clickable:
            return False
        if node_list[0].focusable != self.focusable:
            return False
        if node_list[0].scrollable != self.scrollable:
            return False
        if node_list[0].long_clickable != self.long_clickable:
            return False
        '''if node_list[0].node_type == 3:
            print(node_list[0].have_nodes_with_text(),self.have_nodes_with_text())'''
        if node_list[0].have_nodes_with_text():
            if not self.have_nodes_with_text():
                return False
        elif self.have_nodes_with_text():
            return False
        if self.resource_id != "":
            for other_node in node_list:
                if other_node.resource_id == self.resource_id:
                    print("resource-id")
                    return True
        # 考虑字体大小、颜色、内容语义
        if self.is_text_node() and hasattr(self, "font_size"):
            # TODO:
            value = 0
            size_threshold = 0.1
            color_threshold = 5
            for other_node in node_list:
                if other_node.is_text_node() and hasattr(other_node, "font_size"):
                    print(self.color_dis(other_node.font_color, self.font_color), abs(
                        other_node.font_size-self.font_size)/self.font_size)
                    if (abs(other_node.font_size-self.font_size)/self.font_size <= size_threshold) and \
                            (self.color_dis(other_node.font_color, self.font_color) <= color_threshold):
                        value += 1
                        print(other_node.font_size, self.font_size, other_node.font_color,
                              self.font_color, other_node.text, self.text)
                    elif (self.color_dis(other_node.font_color, self.font_color) == 0) and (abs(other_node.font_size-self.font_size)/self.font_size <= size_threshold*2):
                        value += 1
                    elif (abs(other_node.font_size-self.font_size)/self.font_size <= size_threshold*0.6):
                        value += 1
            value_threshold = 0.5
            if value/len(node_list) > value_threshold:
                print("text", value)
                return True
            else:
                print("text", value)
                return False
        area_w = self.bound[2]-self.bound[0]
        area_h = self.bound[3]-self.bound[1]
        for other_node in node_list:
            other_area_w = other_node.bound[2]-other_node.bound[0]
            other_area_h = other_node.bound[3]-other_node.bound[1]
            print(area_w, area_h, other_area_w, other_area_h)
            if (area_w == other_area_w) and (area_h == other_area_h):
                print("area")

                '''if other_node.depth==10 and other_node.node_type==3 and len(self.generate_all_text())==1:
                    print(other_node.have_nodes_with_text(), self.have_nodes_with_text(), self.generate_all_text())
                    quit()'''

                return True

        leaves_id = self.get_all_leaf_id()
        have_found = False
        for other_node in node_list:
            other_leaves_id = other_node.get_all_leaf_id()
            for leaf_id1 in leaves_id:
                for leaf_id2 in other_leaves_id:
                    if leaf_id1 == leaf_id2:
                        have_found = True
                        break
                if have_found:
                    break
            if have_found:
                break
        if not have_found:
            return False

        # 考虑儿子的种类
        # TODO:
        other_node_types = set()
        for other_node in node_list:
            for child in other_node.children:
                other_node_types.add(child.node_type)
        node_types = set()
        for child in self.children:
            node_types.add(child.node_type)
        if len(node_types) > 0:
            print(node_types, other_node_types)
            if len((node_types & other_node_types)) == 0:
                return False
            if (len((node_types - other_node_types)) != 0):
                return False
            if (len((other_node_types - node_types)) == 0):
                print("node types")
                return True
            '''for other_node in node_list:
                for child in other_node.children:
                    if (child.node_type in node_types):
                        if child.is_text_node:
                            return False'''
        print("final", len(self.children), self.is_text_node(), self.bound)
        return True
        '''
        # 有一个子树完全一样
        for child1 in self.children:
            for child2 in other_node.children:
                if child1.is_sub_tree_same(child2, True):
                    return True
        # 自己的子树node class 被包含
        flag = True
        for child1 in self.children:
            Found = False
            for child2 in other_node.children:
                if child1.node_class == child2.node_class:
                    Found = True
                    break
            if not Found:
                flag = False
                break
        # 别人的子树node class被包含
        for child1 in other_node.children:
            Found = False
            for child2 in self.children:
                if (child1.node_class == child2.node_class):
                    Found = True
                    break
            if not Found:
                flag = False
                break
        if not flag:
            return False
        if (not is_text_diff_allowed) and (not Utility.is_two_str_same_without_num(self.text, other_node.text)):
            return False
        return True'''

    def generate_all_text(self):
        res = ""
        q = Queue()
        q.put(self)
        while not q.empty():
            crt_node = q.get()
            for child_node in crt_node.children:
                q.put(child_node)
            if crt_node.text is not None and len(crt_node.text) > 0:
                res = res + crt_node.text
        return res

    def generate_all_text_with_list(self):
        res = []
        q = Queue()
        q.put(self)
        while not q.empty():
            crt_node = q.get()
            for child_node in crt_node.children:
                q.put(child_node)
            if crt_node.text is not None and len(crt_node.text) > 0:
                res.append(crt_node.text)
        return res

    def generate_all_content(self):
        # type: () -> str
        res = ""
        q = Queue()
        q.put(self)
        while not q.empty():
            crt_node = q.get()
            for child_node in crt_node.children:
                q.put(child_node)
            if crt_node.content_desc is not None and len(crt_node.content_desc) > 0:
                res = res + crt_node.content_desc
        return res

    def generate_all_content_with_list(self):
        res = []
        q = Queue()
        q.put(self)
        while not q.empty():
            crt_node = q.get()
            for child_node in crt_node.children:
                q.put(child_node)
            if crt_node.content_desc is not None and len(crt_node.content_desc) > 0:
                res.append(crt_node.content_desc)
        return res

    def generate_all_text_skip_too_long(self):
        # type: () -> str
        if self.parent is None:
            return "#NI#"

        res = ""
        q = Queue()
        q.put(self)
        while not q.empty():
            crt_node = q.get()
            for child_node in crt_node.children:
                q.put(child_node)
            if crt_node.text is not None and len(crt_node.text) > 0:
                if len(crt_node.text) <= 10:
                    res = res + crt_node.text
                else:
                    res = res + "#TL#"
        return res

    def generate_all_content_skip_too_long(self):
        # type: () -> str
        if self.parent is None:
            return "NI"

        res = ""
        q = Queue()
        q.put(self)
        while not q.empty():
            crt_node = q.get()
            for child_node in crt_node.children:
                q.put(child_node)
            if crt_node.content_desc is not None and len(crt_node.content_desc) > 0:
                if len(crt_node.content_desc) <= 10:
                    res = res + crt_node.content_desc
                else:
                    res = res + "#TL#"
        return res

    def has_same_type_as_child(self, other_node):
        for n1, n2 in zip(self.children, other_node.children):
            if n1.is_sub_tree_same(n2, is_text_diff_allowed=True, is_important_interaction_diff_allowed=False):
                return True
        return False

    def is_sub_tree_same(self, other_node, is_text_diff_allowed, stop_situation=None, allow_if_id_not_influenced=False,
                         is_important_interaction_diff_allowed=True):
        # type: (UINode, bool, Optional[Callable[[UINode, UINode], bool]], bool, bool) -> bool
        #  在这里的判断始终不考虑 content 的内容的比较
        #  比较 type 和 子节点的数量  (可能需要比较 text
        if self.page_instance.activity_name is not None and other_node.page_instance.activity_name is not None \
                and not Utility.is_two_str_same_without_num(self.page_instance.activity_name, other_node.page_instance.activity_name):
            return False

        if self.node_class != other_node.node_class:
            return False
        if self.resource_id != other_node.resource_id:
            return False
        if stop_situation is not None and stop_situation(self, other_node):
            return True
        if not is_important_interaction_diff_allowed:
            if self.clickable != other_node.clickable:
                return False

        if (not is_text_diff_allowed) \
                and (not Utility.is_two_str_same_without_num(self.text, other_node.text)
                     or (not Utility.is_two_str_same_without_num(self.content_desc, other_node.content_desc)
                         and not (self.editable and other_node.editable))):
            return False

        if not allow_if_id_not_influenced:
            if len(self.children) != len(other_node.children):
                return False
            for i in range(len(self.children)):
                if self.children[i].index != other_node.children[i].index:
                    return False
            if self.is_dynamic_entrance != other_node.is_dynamic_entrance:
                return False

            for nodes in zip(self.children, other_node.children):
                if not nodes[0].is_sub_tree_same(nodes[1], is_text_diff_allowed, stop_situation,
                                                 allow_if_id_not_influenced):
                    return False
        else:
            min_children_length = min(
                len(self.children), len(other_node.children))
            for i in range(min_children_length):
                if self.children[i].index != other_node.children[i].index:
                    return False

            if self.is_dynamic_entrance != other_node.is_dynamic_entrance:
                return False

            for nodes in zip(self.children[0: min_children_length], other_node.children[0: min_children_length]):
                if not nodes[0].is_sub_tree_same(nodes[1], is_text_diff_allowed, stop_situation,
                                                 allow_if_id_not_influenced):
                    return False
        return True

    def debug_print_info(self, depth):
        # type: (int) -> str
        result = '\t' * depth
        result = '%sresource-id=\'%s\' classname=\'%s\' index=\'%d\' text=\'%s\' content=\'%s\' bound=\'[%d, %d, %d, %d]\' dismissable=\'%s\' clickable=\'%s\'  scrollable=\'%s\' selected=\'%s\' \n' \
                 % (result, 'None' if self.resource_id is None else self.resource_id, self.node_class, self.index, self.text, self.content_desc, self.bound[0], self.bound[1],
                    self.bound[2], self.bound[3], 'True' if self.dismissable else 'False', 'True' if self.clickable else 'False', 'True' if self.scrollable else 'False', 'True' if self.selected else 'False')
        for index, child_node in enumerate(self.children):
            result += child_node.debug_print_info(depth + 1)
        return result

    def refresh_absolute_id(self):
        # type: () -> None
        #  当自己的 index 发生改变,或者父节点的 id 发生改变的时候
        self.absolute_id = self.node_class if self.parent is None else self.parent.absolute_id + '|%d;%s' % (
            self.index, self.node_class)
        for child in self.children:
            child.refresh_absolute_id()

    def generate_all_text_not_clickable(self):
        # type: () -> str
        res = self.text if len(self.text) > 0 else self.content_desc
        for child_node in self.children:
            if not child_node.clickable:
                res = res + child_node.generate_all_text()
        return res

    def clone(self, parent):
        # type: (Optional[UINode]) -> UINode
        #  返回自己的克隆
        res = UINode(None, None, None)
        res.parent = parent
        res.depth = self.depth
        res.index = self.index
        res.text = self.text
        res.resource_id = self.resource_id
        res.node_class = self.node_class
        res.package = self.package
        res.content_desc = self.content_desc
        res.checkable = self.checkable
        res.checked = self.checked
        res.clickable = self.clickable
        res.enabled = self.enabled
        res.focusable = self.focusable
        res.focused = self.focused
        res.scrollable = self.scrollable
        res.long_clickable = self.long_clickable
        res.password = self.password
        res.selected = self.selected
        res.editable = self.editable
        res.accessibilityFocused = self.accessibilityFocused
        res.dismissable = self.dismissable
        res.bound = self.bound[:]
        res.isVisible = self.isVisible
        #res.page_instance = self.page_instance

        # 不直接进行节点 ID 的复制是考虑到可能仅仅对一个子树进行了复制
        res.absolute_id = res.node_class if res.parent is None else res.parent.absolute_id + '|%d;%s' % (
            res.index, res.node_class)

        res.is_in_static_region = self.is_in_static_region
        res.is_dynamic_entrance = self.is_dynamic_entrance
        res.all_content = self.all_content
        res.all_text = self.all_text
        res.actions_to_act = self.actions_to_act[:]
        res.action_type_to_action_result = dict()
        for action_type_and_attr, action_res_list in self.action_type_to_action_result.items():
            res.action_type_to_action_result[action_type_and_attr] = action_res_list[:]

        if res.parent is None or not res.parent.is_dynamic_entrance:
            res.absolute_dynamic_id = res.node_class if res.parent is None \
                else res.parent.absolute_dynamic_id + '|%d;%s' % (res.index, res.node_class)
        else:
            res.absolute_dynamic_id = res.parent.absolute_dynamic_id + '|*;%s' % res.node_class

        res.clone_source = self.get_original_node()
        res.page_instance = None  # instance 这个属性是不能克隆的！！

        res.children = [x.clone(res) for x in self.children]

        return res

    def get_original_node(self):
        return self.clone_source if hasattr(self, 'clone_source') and self.clone_source is not None \
            else self

    def hasattr(self, attr):
        # type: (str) -> bool
        return hasattr(self, attr)

    def get_dynamic_entrance_if_in_dynamic_region(self):
        # type: () -> Optional[UINode]
        crt_node = self
        while crt_node is not None:
            if crt_node.is_dynamic_entrance:
                break
            crt_node = crt_node.parent
        return crt_node

    def get_dynamic_root_if_in_dynamic_region(self):
        # type: () -> Optional[UINode]
        if self.is_in_static_region:
            return None
        crt_node = self
        while crt_node is not None:
            if crt_node.parent.is_dynamic_entrance:
                return crt_node
            crt_node = crt_node.parent
        return None

    def get_node_by_relative_id(self, relative_id):
        # type: (str) -> Optional[UINode]
        sub_id_list = relative_id.split(';')
        crt_node = self
        for sub_id in sub_id_list[:-1]:
            sub_id_split = sub_id.split('|')
            if crt_node.node_class != sub_id_split[0]:
                return None

            intended_index = int(sub_id_split[1])
            target_node = None
            for c in crt_node.children:
                if c.index == intended_index:
                    target_node = c
                    break
            if target_node is None:
                return None

            crt_node = target_node
        if crt_node.node_class != sub_id_list[-1]:
            return None
        return crt_node

    def get_node_by_xy(self, x, y):
        all_nodes = self.get_all_nodes_after()
        if len(all_nodes) == 0:
            return None
        res = []
        for node in all_nodes:
            if node.bound[0] <= x <= node.bound[2] and node.bound[1] <= y <= node.bound[3]:
                res.append(node)
        return res

    def get_all_nodes_after(self):
        # type: () -> List[UINode]
        # 获得该节点的所有子孙节点
        res = []
        for child in self.children:
            res += child.get_all_nodes_after()
        res.append(self)
        return res

    def has_node_satisfy(self, cond):
        # type: (Callable[[UINode], bool]) -> bool
        if cond(self):
            return True

        for child in self.children:
            if child.has_node_satisfy(cond):
                return True

        return False

    def find_all_clickable_id_to_node(self, id_2_node):
        # type: (Dict[str, UINode]) -> None
        if self.is_dynamic_entrance:
            return
        if self.clickable:
            id_2_node[self.absolute_id] = self
        for c in self.children:
            c.find_all_clickable_id_to_node(id_2_node)

    def get_node_by_cond(self, cond):
        # type: (Callable[[UINode], bool]) -> UINode
        if cond(self):
            return self
        for n in self.children:
            res = n.get_node_by_cond(cond)
            if res is not None:
                return res
        return None

    def get_all_interactive_node(self, res):
        # type: (List[UINode]) -> None
        if len(self.text) > 0 \
                or (len(self.children) == 0 and len(self.content_desc) > 0) \
                or (self.scrollable or self.clickable or self.checkable or self.editable or self.long_clickable or 'ListView' in self.node_class) \
                or ('WebView' in self.node_class):
            res.append(self)
        else:
            for child in self.children:
                child.get_all_interactive_node(res)

    def get_raw_area(self):
        return max(self.bound[2] - self.bound[0], 0) * max(self.bound[3] - self.bound[1], 0)

    def get_area(self):  # todo: 这里的面积计算还有很多值得商榷的地方！
        # bound 并不能体现出实际上显示的区域
        # 对用户来说，合理的显示区域实际上是和可交互节点相挂钩的
        all_interactive_node = []  # type: List[UINode]
        self.get_all_interactive_node(all_interactive_node)
        # res = 0
        # for node in all_interactive_node:
        #     res += node.get_raw_area()
        # return res
        if len(all_interactive_node) == 0:
            return 0
        # if len(all_interactive_node) == 0:  # 已经忘了这个为什么是这样的。。。
        #     return (self.bound[3] - self.bound[1]) * (self.bound[2] - self.bound[0])
        min_up = all_interactive_node[0].bound[0]
        min_left = all_interactive_node[0].bound[1]
        max_down = all_interactive_node[0].bound[2]
        max_right = all_interactive_node[0].bound[3]

        for node in all_interactive_node:
            min_up = min_up if node.bound[0] > min_up else node.bound[0]
            min_left = min_left if node.bound[1] > min_left else node.bound[1]
            max_down = max_down if node.bound[2] < max_down else node.bound[2]
            max_right = max_right if node.bound[3] < max_right else node.bound[3]

        return (max_right - min_left) * (max_down - min_up)

    def get_sum_area(self):
        res = self.get_raw_area()
        for child in self.children:
            res += child.get_sum_area()
        return res

    def get_overlap_area(self, other_node):
        if self.bound[0] >= other_node.bound[2] or other_node.bound[0] >= self.bound[2]:
            return 0
        if self.bound[1] >= other_node.bound[3] or other_node.bound[1] >= self.bound[3]:
            return 0
        up = max(self.bound[1], other_node.bound[1])
        down = min(self.bound[3], other_node.bound[3])
        left = max(self.bound[0], other_node.bound[0])
        right = min(self.bound[2], other_node.bound[2])
        return (down-up)*(right-left)

    def is_node_same(self, depth, other_node, is_text_diff_allowed, stop_situation=None):
        #  在这里的判断始终不考虑 content 的内容的比较
        #  比较 type 和 子节点的数量  (可能需要比较 text
        leaves_id1 = self.get_all_leaf_id()
        leaves_id2 = other_node.get_all_leaf_id()
        have_found = False
        for leaf_id1 in leaves_id1:
            for leaf_id2 in leaves_id2:
                if leaf_id1 == leaf_id2:
                    have_found = True
                    break
            if have_found:
                break
        if not have_found:
            return False
        if self.node_class != other_node.node_class:
            return False
        # if self.resource_id != other_node.resource_id:
        #     return False
        if self.checkable != other_node.checkable:
            return False
        if self.clickable != other_node.clickable:
            return False
        if self.focusable != other_node.focusable:
            return False
        if self.scrollable != other_node.scrollable:
            return False
        if self.long_clickable != other_node.long_clickable:
            return False
        '''
        self.checkable = (crt_layout['@checkable'] == 'true')
        self.checked = (crt_layout['@checked'] == 'true')
        self.clickable = (crt_layout['@clickable'] == 'true')
        self.enabled = (crt_layout['@enabled'] == 'true')
        self.focusable = (crt_layout['@focusable'] == 'true')
        self.focused = (crt_layout['@focused'] == 'true')
        self.scrollable = (crt_layout['@scrollable'] == 'true')
        self.long_clickable = (crt_layout['@long-clickable'] == 'true')
        '''

        if stop_situation is not None and stop_situation(self, other_node):
            return True
        for child1 in self.children:
            for child2 in other_node.children:
                if child1.is_sub_tree_same(child2, True):
                    return True
        flag = True
        for child1 in self.children:
            Found = False
            for child2 in other_node.children:
                if child1.node_class == child2.node_class:
                    Found = True
                    break
            if not Found:
                flag = False
                break
        for child1 in other_node.children:
            Found = False
            for child2 in self.children:
                if (child1.node_class == child2.node_class):
                    Found = True
                    break
            if not Found:
                flag = False
                break
        if not flag:
            return False
        if (not is_text_diff_allowed) and (not Utility.is_two_str_same_without_num(self.text, other_node.text)):
            return False
        return True

    def is_node_similar(self, depth, other_node, is_text_diff_allowed, stop_situation=None):
        pass

    def cal_diff_area_ratio(self):
        pass

    def cal_path_match_raito(self, node):
        if node is None:
            return 0
        st1 = self.absolute_id
        st2 = node.absolute_id
        if st1 == st2:
            return 1
        sub_id_list1 = st1.split(";")
        l1 = len(sub_id_list1)
        if sub_id_list1[0].find("fake") != -1:
            sub_id_list1 = sub_id_list1[1:]
            l1 -= 1
        sub_id_list2 = st2.split(";")
        l2 = len(sub_id_list2)
        if sub_id_list2[0].find("fake") != -1:
            sub_id_list2 = sub_id_list2[1:]
            l2 -= 1
        if l1 == 0 or l2 == 0:
            return 0
        F = []
        for i in range(l1):
            F.append([])
            for j in range(l2):
                F[i].append(0)
                if i != 0:
                    F[i][j] = max(F[i][j], F[i-1][j])
                if j != 0:
                    F[i][j] = max(F[i][j], F[i][j-1])
                tmp = 0
                if i != 0 and j != 0:
                    tmp = F[i-1][j-1]
                if sub_id_list1[i] == sub_id_list2[j]:
                    tmp += 1
                else:
                    sub_id_split1 = sub_id_list1[i].split("|")
                    sub_id_split2 = sub_id_list2[j].split("|")
                    if sub_id_split1[0] == sub_id_split2[0]:
                        tmp += 0.8
                    elif i == l1-1 and j == l2-1:
                        return 0
                F[i][j] = max(F[i][j], tmp)
        print(str(len(F)), str(len(F[0])), str(l1), str(l2))
        matched_ratio = 2.0*F[l1-1][l2-1]/(l1+l2)
        return matched_ratio

    def get_text_match_state(self, node):
        # 0: 完全相同 1：同时有文本 2：一个有文本一个没有文本
        if self.text == node.text:
            return 0
        if self.text != "" and node.text != "":
            return 1
        return 2

    def cal_text_match_raito(self, node):
        matched_cnt = 0.0
        ref_text = self.all_text
        if (ref_text is None) or (len(ref_text) == 0):
            return -1
        crt_texts = node.generate_all_text_with_list()
        for text in crt_texts:
            if ref_text.find(text) != -1:
                matched_cnt += 1
            else:
                matched_cnt += Utility.get_common_length(ref_text, text)
        return float(matched_cnt)*1.0/float(len(ref_text))

    def cal_content_match_state(self, node):
        # 0: 完全相同 1：同时有文本 2：一个有文本一个没有文本
        if self.content_desc == node.content_desc:
            return 0
        if self.content_desc != "" and node.content_desc != "":
            return 1
        return 2

    def cal_content_match_ratio(self, node):
        matched_cnt = 0.0
        ref_content = self.all_content
        if (ref_content is None) or (len(ref_content) == 0):
            return -1
        crt_contents = node.generate_all_content_with_list()
        for content in crt_contents:
            if ref_content.find(content) != -1:
                matched_cnt += 1
            else:
                matched_cnt += Utility.get_common_length(ref_content, content)
        return float(matched_cnt)*1.0/float(len(ref_content))

    def check_resource_id(self, node):
        if self.resource_id == node.resource_id:
            return 1
        return 0

    def cal_left(self, type):
        if type == 0:
            left_ratio = float(self.bound[0])*1.0 / \
                float(self.page_instance.ui_root.width())
        else:
            left_ratio = float(self.bound[0])*1.0 / \
                float(self.findBlockNode().width())
        return left_ratio

    def cal_left_diff(self, node, type):
        # type = 0, global; type = 1, block
        left_diff = float(node.bound[0]-self.bound[0])*1.0
        relative_left_diff = 0
        if type == 0:
            relative_left_diff = left_diff / \
                float(self.page_instance.ui_root.width())
        else:
            relative_left_diff = left_diff / \
                float(self.findBlockNode().width())
        return relative_left_diff

    def cal_right(self, type):
        if type == 0:
            right_ratio = float(self.bound[2])*1.0 / \
                float(self.page_instance.ui_root.width())
        else:
            right_ratio = float(self.bound[2])*1.0 / \
                float(self.findBlockNode().width())
        return right_ratio

    def cal_right_diff(self, node, type):
        # type = 0, global; type = 1, block
        right_diff = float(node.bound[2]-self.bound[2])*1.0
        relative_right_diff = 0
        if type == 0:
            relative_right_diff = right_diff / \
                float(self.page_instance.ui_root.width())
        else:
            relative_right_diff = right_diff / \
                float(self.findBlockNode().width())
        return relative_right_diff

    def cal_top(self, type):
        if type == 0:
            top_ratio = float(self.bound[1])*1.0 / \
                float(self.page_instance.ui_root.height())
        else:
            top_ratio = float(self.bound[1])*1.0 / \
                float(self.findBlockNode().height())
        return top_ratio

    def cal_top_diff(self, node, type):
        # type = 0, global; type = 1, block
        top_diff = float(node.bound[1]-self.bound[1])*1.0
        relative_top_diff = 0
        if type == 0:
            relative_top_diff = top_diff / \
                float(self.page_instance.ui_root.height())
        else:
            relative_top_diff = top_diff / float(self.findBlockNode().height())
        return relative_top_diff

    def cal_bottom(self, type):
        if type == 0:
            bottom_ratio = float(
                self.bound[3])*1.0 / float(self.page_instance.ui_root.height())
        else:
            bottom_ratio = float(
                self.bound[3])*1.0 / float(self.findBlockNode().height())
        return bottom_ratio

    def cal_bottom_diff(self, node, type):
        # type = 0, global; type = 1, block
        bottom_diff = float(node.bound[3]-self.bound[3])*1.0
        relative_bottom_diff = 0
        if type == 0:
            relative_bottom_diff = bottom_diff / \
                float(self.page_instance.ui_root.height())
        else:
            relative_bottom_diff = bottom_diff / \
                float(self.findBlockNode().height())
        return relative_bottom_diff

    def cal_mid_x(self, type):
        if type == 0:
            mid_x_ratio = float(
                self.bound[0]+self.bound[2])*1.0 / float(self.page_instance.ui_root.width())
        else:
            mid_x_ratio = float(
                self.bound[0]+self.bound[2])*1.0 / float(self.findBlockNode().width())
        return mid_x_ratio

    def cal_mid_x_diff(self, node, type):
        mid_x_diff = float(
            node.bound[0]+node.bound[2]-self.bound[0]-self.bound[2]) * 0.5
        relative_mid_x_diff = 0
        if type == 0:
            relative_mid_x_diff = mid_x_diff / \
                float(self.page_instance.ui_root.width())
        else:
            relative_mid_x_diff = mid_x_diff / \
                float(self.findBlockNode().width())
        return relative_mid_x_diff

    def cal_mid_y(self, type):
        if type == 0:
            mid_y_ratio = float(
                self.bound[1]+self.bound[3])*1.0 / float(self.page_instance.ui_root.height())
        else:
            mid_y_ratio = float(
                self.bound[1]+self.bound[3])*1.0 / float(self.findBlockNode().height())
        return mid_y_ratio

    def cal_mid_y_diff(self, node, type):
        mid_y_diff = float(
            node.bound[1]+node.bound[3]-self.bound[1]-self.bound[3]) * 0.5
        relative_mid_y_diff = 0
        if type == 0:
            relative_mid_y_diff = mid_y_diff / \
                float(self.page_instance.ui_root.height())
        else:
            relative_mid_y_diff = mid_y_diff / \
                float(self.findBlockNode().height())
        return relative_mid_y_diff

    def get_all_leaf_id(self):
        if (len(self.children) == 0):
            return [self.node_class]
        res = []
        for child_index, child in enumerate(self.children):
            tmp = child.get_all_leaf_id()
            for i in range(len(tmp)):
                tmp[i] = self.node_class+str(child_index)+"|"+tmp[i]
            res += tmp
        return res

    def has_clickable_parent(self):
        crt_node = self

        while crt_node is not None:
            if crt_node.clickable:
                return True
            crt_node = crt_node.parent
        return False

    def get_nearest_entrance_root(self):
        # type: () -> UINode
        if self.is_in_static_region:
            return None

        crt_node = self
        while crt_node.parent is not None:
            if crt_node.parent.is_dynamic_entrance:
                return crt_node
            crt_node = crt_node.parent
        return crt_node

    def is_action_type_will_be_tried(self, action_type):
        # type: (int) -> bool
        if action_type == Action.CLICK:
            return self.clickable
        if action_type == Action.ENTER_TEXT:
            return self.editable
        if action_type == Action.SCROLL:
            return self.is_dynamic_entrance
        return False

    def get_root(self):
        crt_node = self
        while True:
            if crt_node.parent is None:
                return crt_node
            crt_node = crt_node.parent

    def update_page_id(self, page_id):
        self.page_id = page_id

    def add_new_action_result(self, action_info, new_action_res):
        # 和直接进行 append 相比，这里主要的目的在于去重
        # 如果是 inferred 的 action res 的话，只要有重复就不会添加；否则，只有在列表中有重复的，不是 inferred 的时候才不会添加，如果已经有的是非 inferred 的话，就把原来的那个删掉，把这个加上去
        similar_action_res = None
        if action_info not in self.action_type_to_action_result:
            return  # 该节点不支持这个操作
        for crt_action_res in self.action_type_to_action_result[action_info]:
            if crt_action_res.action_target is new_action_res.action_target and crt_action_res.action_type == new_action_res.action_type and cmp(crt_action_res.attr, new_action_res.attr) == 0 and crt_action_res.is_pruned == new_action_res.is_pruned:
                similar_action_res = crt_action_res
                break
        if similar_action_res is None:
            self.action_type_to_action_result[action_info].append(
                new_action_res)
        else:
            if similar_action_res.is_inferred and not new_action_res.is_inferred:
                self.action_type_to_action_result[action_info].remove(
                    similar_action_res)
                self.action_type_to_action_result[action_info].append(
                    new_action_res)

    def detect_all_text_nodes(self):
        if self.text != "":
            print(self.text, self.bound)
        for child in self.children:
            child.detect_all_text_nodes()


class Action:
    # 指定在哪个页面进行操作了哪个节点
    NOT_IMPORTANT = -1
    INIT = 0
    CLICK = 1
    LONG_CLICK = 2
    SCROLL = 3
    ENTER_TEXT = 4
    GLOBAL_BACK = 5

    def __init__(self, page_instance, node, action_type, **kwargs):
        self.page_instance = page_instance  # type: Optional[PageInstance]
        self.node = node  # type: Optional[UINode]
        self.type = action_type  # type: int
        self.attr = kwargs  # type: Dict
        if not isinstance(self.type, int):
            print('error type of type!')
        if self.type == Action.GLOBAL_BACK and self.node.parent is not None:
            print(' only root can perform global back')

    def __eq__(self, other):
        # type: (Action)->bool
        return self.page_instance is other.page_instance \
            and self.node is other.node \
            and self.type == other.type \
            and cmp(self.attr, other.attr) == 0

    def genarate_action_info(self):
        if self.type == Action.SCROLL:
            return self.type, self.attr['step']
        elif self.type == Action.ENTER_TEXT:
            return self.type, self.attr['text']

        return self.type, None


class ActionResult:
    def __init__(self, page_instance, action_type, is_inferred, is_pruned=False, **kwargs):
        self.no_result = page_instance is None and action_type is None and len(
            kwargs) == 0
        self.action_type = action_type  # type: int
        self.action_target = page_instance  # type: PageInstance
        self.attr = kwargs
        self.is_inferred = is_inferred
        self.is_pruned = is_pruned
        if self.is_pruned:
            assert self.no_result

        self.is_click_with_context = False
        # type: Optional[Tuple[PageInstance, UINode]]
        self.context_template = None

    def get_result_as_inferred(self):
        if self.is_inferred:
            return self
        return ActionResult(self.action_target, self.action_type, True, **self.attr)


class PageInstance:
    # 被认为是同类的界面，这些页面之间必然静态区域是相同的或者非常相似的
    # 并且这些界面之间不能是直接的前后关系（需要对一阶的变化进行刻画）
    store_root = os.path.join(os.getcwd(), 'PageInfo/')
    tmp_root = os.path.join(store_root, 'tmp/')

    def __init__(self):
        self.time_stamp = -1
        self.page_state = None  # type: PageState
        self.index = -1

        self.screen_save_path = None  # type: str
        self.layout_json_path = None  # type: str

        # type: List[Action]  # 仅仅记录最后一步的操作，而且这里所记录的 全部都是 actual 的。
        self.last_actions_into = []
        # add new last action 只会在页面完全一致的时候添加

        self.ui_root = None  # type: UINode
        self.absolute_id_2_node = {}  # type: Dict[str, UINode]
        self.absolute_dynamic_id_2_node = {}  # type: Dict[str, List[UINode]]
        self.node_not_tried_to_action = []  # type: List[UINode]
        # self.node_acted = []  # type: List[UINode]  # todo 删除这个成员变量。这是考虑到现在一个节点支持多个操作，难以简单地描述 acted
        self.dynamic_entrance = []  # type: List[UINode]
        self.activity_name = None
        self.is_static_empty = True
        self.has_semantic_context = False
        # 在到达这个状态的路径中 具体是什么操作为这个页面赋予了语义信息
        # type: List[Action] # type: List[Tuple[Page, str, str, UINode]]  # 有可能一个节点是多次操作的语义信息的叠加
        self.semantic_source_action = []
        self.added_due_to_back = False

        # type: PageInstance  # 和到达这个页面的路径中的哪一个 instance 是相似的 更加细致的处理会在 post processing 中完成
        self.last_similar_instance = None

        self.ori_instance_id = (-1, -1, -1)  # 这里所说的是在最为原始的数据中的 instance id 是什么
        self.crt_instance_id = (-1, -1, -1)

        self.crt_time_stamp = -1

        self.ref_instance = None  # type: PageInstance
        self.state_id = None  # type: str

    def load_from_file(self, screen_save_path, layout_json_path, activity_name=None):
        self.screen_save_path = screen_save_path
        self.layout_json_path = layout_json_path
        self.activity_name = activity_name
        raw_layout = json.load(open(layout_json_path), encoding='utf-8')
        self.time_stamp = raw_layout["@timestamp"]
        self.ui_root = UINode(raw_layout, None, self)
        self.generate_dynamic_attr(self.ui_root, self.dynamic_entrance)
        self.is_static_empty = Utility.is_static_empty(self.ui_root)

    def load_from_dict(self, screen_save_path, raw_layout, activity_name=None):
        self.screen_save_path = screen_save_path
        self.activity_name = activity_name
        if "@timestamp" in raw_layout:
            self.time_stamp = raw_layout["@timestamp"]
        if "page_cnt" in raw_layout:
            self.page_cnt = raw_layout["page_cnt"]
        else:
            self.page_cnt = -1
        self.ui_root = UINode(raw_layout, None, self)
        self.generate_dynamic_attr(self.ui_root, self.dynamic_entrance)
        self.is_static_empty = Utility.is_static_empty(self.ui_root)

    def load_from_device(self, device, action=None, file_stored=True):
        # type: (Device, Action, bool) -> None
        self.crt_time_stamp = int(time.time() * 10e6)
        self.screen_save_path = os.path.join(
            self.tmp_root, '%d_screen.jpg' % self.crt_time_stamp)
        self.layout_json_path = os.path.join(
            self.tmp_root, '%d_layout.json' % self.crt_time_stamp)
        if file_stored:
            Utility.load_screen(self.screen_save_path)
        raw_layout = device.dump_layout(self.layout_json_path)
        self.ui_root = UINode(raw_layout, None, self)

        # 从 STOP_LIST 中删除对应的节点的子节点
        for node_id in UINode.STOP_NODE_LIST:
            node = self.ui_root.get_node_by_relative_id(node_id)
            if node is not None:
                node.children = []

        self.generate_dynamic_attr(self.ui_root, self.dynamic_entrance)
        if action is not None:
            self.last_actions_into.append(action)

        self.activity_name = device.get_activity_name()

        self.is_static_empty = Utility.is_static_empty(self.ui_root)
        for node_id in UINode.STOP_NODE_LIST:
            assert (node_id not in self.absolute_id_2_node) or len(
                self.absolute_id_2_node[node_id].children) == 0

    def generate_dynamic_attr(self, crt_node, dynamic_entrance_store_list, has_encounter_entrance=False):
        # type: (UINode, List, bool) -> None
        if not hasattr(crt_node, "scrollable"):
            crt_node.scrollable = False
        if crt_node.scrollable or 'ListView' in crt_node.node_class or 'RecyclerView' in crt_node.node_class or 'GridView' in crt_node.node_class:
            #  要求这个节点的子节点都是 至少部分可见的
            child_node_num_before = len(crt_node.children)
            all_popped_children = []
            for index in range(len(crt_node.children) - 1, -1, -1):
                if not crt_node.children[index].isVisible:
                    all_popped_children.append(crt_node.children.pop(index))

            # and 'pager' not in crt_node.node_class.lower():
            if (len(crt_node.children) > 1 or (child_node_num_before == 1)):
                # 如果的确存在多个子节点，但是一次就显示一个的话，那么不认为是一个动态区域入口
                # 那么反之，一次展示多个子节点，或者原本就只有一个子节点的话，就认为是一个动态区域的入口
                crt_node.is_dynamic_entrance = True
                dynamic_entrance_store_list.append(crt_node)
            # and 'pager' not in crt_node.node_class.lower():  # 字面上说，有 pager 的一般就是一次出现一个的那种
            elif len(crt_node.children) == 1:
                # 除非这些被删除掉的子节点和被保留下来的子节点非常相似
                left_child = crt_node.children[0]
                # is_diff_found = False
                # for popped_child in all_popped_children:
                #     if popped_child.node_class != left_child.node_class \
                #             or popped_child.resource_id != left_child.resource_id:
                #         is_diff_found = True
                #         break
                #
                # if not is_diff_found:
                #     crt_node.is_dynamic_entrance = True
                #     dynamic_entrance_store_list.append(crt_node)
                # else:
                is_y_overlapped = False
                # 之所以要这么"丧心病狂"地确定到底是不是页面整体左右滚动的原因在于，我们希望能够在这种话情况下尽量避免 dynamic entrance，从而能够实现对 page 和 page state 的更好的判断
                # 考虑到页面设计的规范，一般是左右滚动而不是上下滚动。左右滚动一般会出现 y 方向上有重叠的情况
                for popped_child in all_popped_children:
                    # 判断和 left child 和 popped_child 之间在 y 方向上有没有重叠
                    if not (popped_child.bound[1] >= left_child.bound[3]
                            or popped_child.bound[3] <= left_child.bound[1]):
                        is_y_overlapped = True
                    if is_y_overlapped:
                        break

                if not is_y_overlapped:
                    crt_node.is_dynamic_entrance = True
                    dynamic_entrance_store_list.append(crt_node)

        # 只有是认为真的 list 才会改 index （毕竟这个 index 也没有什么其他的用途
        for i in range(len(crt_node.children)):
            crt_node.children[i].index = i

        crt_node.is_in_static_region = not has_encounter_entrance

        if crt_node.parent is None or not crt_node.parent.is_dynamic_entrance:
            crt_node.absolute_dynamic_id = crt_node.node_class if crt_node.parent is None else crt_node.parent.absolute_dynamic_id + '|%d;%s' % (
                crt_node.index, crt_node.node_class)
        else:
            assert crt_node.parent.is_dynamic_entrance
            crt_node.absolute_dynamic_id = crt_node.node_class if crt_node.parent is None else crt_node.parent.absolute_dynamic_id + '|*;%s' % (
                crt_node.node_class)

        crt_node.absolute_id = crt_node.node_class if crt_node.parent is None else crt_node.parent.absolute_id + '|%d;%s' % (
            crt_node.index, crt_node.node_class)

        self.absolute_id_2_node[crt_node.absolute_id] = crt_node  # 准备数据
        if crt_node.absolute_dynamic_id not in self.absolute_dynamic_id_2_node:
            self.absolute_dynamic_id_2_node[crt_node.absolute_dynamic_id] = []
        self.absolute_dynamic_id_2_node[crt_node.absolute_dynamic_id].append(
            crt_node)

        # if len(crt_node.actions_to_act) > 0:
        #     self.node_not_tried_to_action.append(crt_node)

        # for index, child_node in enumerate(crt_node.children):
        #     self.generate_dynamic_attr(
        #         child_node, dynamic_entrance_store_list, has_encounter_entrance or crt_node.is_dynamic_entrance)

    def add_new_last_action(self, new_last_into_action):
        # type: (Action) -> None
        # 增加一个新的跳转到当前页面的路径
        # 由于现在仅仅对最后一步进行描述，没有对后续页面进行递归更新的必要
        # 所有出现的去重（环状？）只要在后面进行搜索的时候确定即可

        for action in self.last_actions_into:
            if new_last_into_action == action:
                return

        self.last_actions_into.append(new_last_into_action)

    def refresh_path(self):

        if self.index < 0 or self.page_state is None:
            return
        new_path = os.path.join(PageInstance.store_root, 'Page%d' % self.page_state.page.index,
                                'PageState%d' % self.page_state.index)
        if not os.path.exists(new_path):
            os.makedirs(new_path)
        png_path = os.path.join(new_path, 'PageInstance%d%s' % (
            self.index, os.path.splitext(self.screen_save_path)[1]))  # type: str
        json_path = os.path.join(
            new_path, 'PageInstance%d.json' % self.index)  # type: str

        # print self.screen_save_path
        # print json_path
        os.renames(self.screen_save_path, png_path)
        os.renames(self.layout_json_path, json_path)
        self.screen_save_path = png_path
        self.layout_json_path = json_path

    def is_static_id_same(self, other, is_text_diff_allowed):
        return self.ui_root.is_sub_tree_same(other.ui_root, is_text_diff_allowed,
                                             lambda node1, node2: node1.is_dynamic_entrance,
                                             allow_if_id_not_influenced=True)

    def is_same(self, other, is_text_diff_allowed):
        return self.ui_root.is_sub_tree_same(other.ui_root, is_text_diff_allowed)

    def get_all_dynamic_clickable_nodes_in_sub_tree(self, crt_node, dynamic_id_to_result_list):
        # type: (UINode, Dict[str, List[Tuple[UINode, PageInstance]]]) -> None
        if (not crt_node.is_in_static_region) \
                and (Action.CLICK, None) in crt_node.action_type_to_action_result \
                and len(crt_node.action_type_to_action_result[(Action.CLICK, None)]) > 0:
            assert '*' in crt_node.absolute_dynamic_id
            # result_list.append((crt_node, self))
            if crt_node.absolute_dynamic_id not in dynamic_id_to_result_list:
                dynamic_id_to_result_list[crt_node.absolute_dynamic_id] = []
            # 去重，去掉重复的点
            has_found = False
            for result in dynamic_id_to_result_list[crt_node.absolute_dynamic_id]:
                if result[0].is_sub_tree_same(crt_node, is_text_diff_allowed=False):
                    has_found = True
                    break
            if not has_found:
                dynamic_id_to_result_list[crt_node.absolute_dynamic_id].append(
                    (crt_node, self))

        for n in crt_node.children:
            self.get_all_dynamic_clickable_nodes_in_sub_tree(
                n, dynamic_id_to_result_list)

    MAX_STEP_NUM = 10

    def generate_jump_path_to_target(self, target_instance, target_node, used_jump_edge):

        #         # 返回值的意义是  是不是成功地找到路径 所找到的最短的路径

        # 使用深度优先搜索的方式确定具体的跳转路径
        # 上面所使用的方法明显不是深度优先搜索！！

        pages_belong_to, states_belong_to = Application.THIS.get_page_state_belong_to(
            self)
        if target_instance.page_state.page in pages_belong_to:  # 要求至少是同一个 page。否则就是两个页面上恰好有两个同样的按钮
            node_list_from_self = Utility.get_same_node_from_other_instance(
                target_node, self)
            if len(node_list_from_self) > 0:
                return True, []

        # type: Deque[Tuple[WindowStructure.PageInstance, List[Tuple[WindowStructure.Page, str, int, Optional[int, str]]]]]  # 存储了页面，和到达这个页面所使用的方法
        q = deque()
        # type: Set[WindowStructure.PageInstance]  # type: 用来剪枝
        reached_instance_set = set()
        q.append((self, list()))
        reached_instance_set.add(self)  # 在进入的时候记录，而不是在退出的时候记录！
        while len(q) > 0:
            crt_instance, actions_to_crt_instance = q.popleft()
            # used jump page 还是在实际跳转的时候再使用
            # 我们仅仅允许在寻路的最开始使用 global back，其他的情况不允许使用 global back
            is_all_back_action = True
            # for action_info in actions_to_crt_instance:  # 允许前面不是返回，后面返回
            #     if not Utility.is_action_info_back(action_info):
            #         is_all_back_action = False
            #         break

            # 只有 all back 的情况才能够继续使用 back 性质的操作
            all_possible_next_action, all_possible_next_instance = \
                Utility.get_all_possible_next_instance_with_action_from_one_instance(
                    crt_instance, used_jump_edge)

            if len(actions_to_crt_instance) >= PageInstance.MAX_STEP_NUM:
                continue  # 路径太长的话  就不进行搜索了

            for next_action, next_instance_set in all_possible_next_action.items():
                # 如果是返回操作，但是已经有的操作列表上出现了不是返回的操作了 就不能够再使用具有返回性质的了
                if Utility.is_action_info_back(next_action) and not is_all_back_action:
                    is_instance_only_back = True
                    for next_instance in next_instance_set:
                        for last_action in next_instance.last_actions_into:
                            if not Utility.is_action_info_back((last_action.page_instance.page_state.page, last_action.node.absolute_id, last_action.type, None)):
                                is_instance_only_back = False
                                break
                        if not is_instance_only_back:
                            break

                    if not is_instance_only_back:
                        continue

                actions_to_next_instance = actions_to_crt_instance[:]
                actions_to_next_instance.append(next_action)
                for next_instance in next_instance_set:  # 同一节点同一操作可能到达不同页面
                    if next_instance in reached_instance_set:
                        continue

                    pages_belong_to, states_belong_to = Application.THIS.get_page_state_belong_to(
                        next_instance)
                    if target_instance.page_state.page in pages_belong_to:
                        # node_list = Utility.get_same_node_from_other_instance(target_node, next_instance)
                        # if len(node_list) > 0:
                        #     return True, actions_to_next_instance
                        if next_instance is target_instance:  # 必须跳转到对应的节点
                            return True, actions_to_next_instance

                    q.append((next_instance, actions_to_next_instance))
                    reached_instance_set.add(next_instance)

        return False, []

    def get_all_merged_nodes(self, crt_node):
        # type: (WindowStructure.UINode)->List[StaticDynamicSplit.MergedNode]
        res = []  # type: List[StaticDynamicSplit.MergedNode]
        assert crt_node.corresponding_merged_node is not None
        res.append(crt_node.corresponding_merged_node)
        for child in crt_node.children:
            res.extend(self.get_all_merged_nodes(child))
        return res

    '''def print_debug_info(self, crt_node):
        print crt_node,"'s action_result_length: ", len(crt_node.action_type_to_action_result)
        print crt_node,"'s children size: ", len(crt_node.children)
        for child in crt_node.children:
            self.print_debug_info(child)'''

    def add_action_text_info(self, crt_node):
        # type: (WindowStructure.UINode)->None
        # type: Dict[ActionResult, List[Tuple[Tuple[int, Any], str]]]
        crt_node.action_result_to_action_type = dict()
        for action_type, action_results in crt_node.action_type_to_action_result.items():
            for action_result in action_results:
                #  todo 到底要怎么处理inferred
                if action_result.is_inferred:
                    continue
                if action_result not in crt_node.action_result_to_action_type:
                    crt_node.action_result_to_action_type[action_result] = []
                info = crt_node.generate_all_text_skip_too_long()
                crt_node.action_result_to_action_type[action_result].append(
                    (action_type, info))
        for child in crt_node.children:
            self.add_action_text_info(child)


class PageState:
    def __init__(self, index, page):
        self.page_instances = []  # type: List[PageInstance]
        self.index = index  # type: int
        self.page = page  # type: Page
        self.has_too_many_instance = False
        self.context_source = []  # type: List[ContextSource]

    def add_new_instance(self, new_instance):
        # type: (PageInstance) -> None
        self.page_instances.append(new_instance)
        new_instance.page_state = self
        new_instance.index = len(self.page_instances) - 1
        new_instance.refresh_path()


class Page:
    def __init__(self, index):
        self.page_states = []  # type: List[PageState]
        self.index = index  # type: int

    def get_diff_info_to_instance(self, new_page_instance, is_force_static, use_parent_when_count_num=True):
        min_diff = 100
        min_diff_instance = None
        max_diff = 0
        max_diff_instance = None

        min_node_diff = 100
        min_node_diff_instance = None
        max_node_diff = 0
        max_node_diff_instance = None

        for state in self.page_states:
            for instance in state.page_instances:
                diff_ratio, diff_num_ratio = Utility.cal_diff_area_ratio(
                    instance, new_page_instance, is_force_static, use_parent_when_count_num)
                if diff_ratio < min_diff:
                    min_diff = diff_ratio
                    min_diff_instance = instance
                if diff_ratio > max_diff:
                    max_diff = diff_ratio
                    max_diff_instance = instance

                if diff_num_ratio < min_node_diff:
                    min_node_diff = diff_num_ratio
                    min_node_diff_instance = instance
                if diff_num_ratio > max_node_diff:
                    max_node_diff = diff_num_ratio
                    max_node_diff_instance = instance

        return (min_diff, min_diff_instance), (max_diff, max_diff_instance),\
               (min_node_diff, min_node_diff_instance), (max_node_diff,
                                                         max_node_diff_instance)

    def refresh_action_res(self, instance_acted, node_acted, action_info):
        # 在已经知道一个节点的新的操作结果的情况下，对该页面中其他 state 的其他 instance 的同一个按钮进行处理。仅仅会涉及到这个 page
        # 如果是具有返回性质的，就不要迁移了。值得注意的是，这里遇到了 返回性质的节点是不能够直接 return 的，因为需要借助这里，将返回性质的节点从 not action 移除出去
        is_back_action_node = (
            node_acted.parent is None or Utility.is_backward_button(node_acted))
        assert self is instance_acted.page_state.page
        is_self_found = False
        if action_info not in node_acted.action_type_to_action_result:
            node_acted.action_type_to_action_result[action_info] = []
        if not node_acted.action_type_to_action_result[action_info]:
            last_action_result_marked_as_inferred = None  # 说明这个节点的点击是没有效果的！！
        else:
            last_action_result_marked_as_inferred = \
                node_acted.action_type_to_action_result[action_info][-1].get_result_as_inferred(
                )  # 因为是新加入的，必然是最后一个！

        if node_acted.is_in_static_region:
            for state in self.page_states:
                for instance in state.page_instances:
                    if is_back_action_node and instance is not instance_acted \
                            and not Utility.is_state_too_many_instances(state):  # 返回按钮仅对实际页面生效，不会再迁移到别的页面上去
                        # 只有在 last action 的列表中有相同的 page 存在的话，才能够迁移
                        is_same_last_page_find = False
                        for action1, action2 in [(x, y) for x in instance.last_actions_into for y in instance_acted.last_actions_into]:
                            if Application.THIS.get_page_state_belong_to(action1.page_instance) is Application.THIS.get_page_state_belong_to(action2.page_instance):
                                is_same_last_page_find = True
                                break
                        if not is_same_last_page_find:
                            # 两个 state 的 page instance 的数量都很少的话，就 continue
                            continue

                    node_in_crt = instance.absolute_id_2_node.get(
                        node_acted.absolute_id, None)
                    #  即使在静态区域也要求两个区域是完全一样的
                    if node_in_crt is None:
                        continue

                    # 为了使得存储在根节点上的 global back 不受到这里要求完全相同  的 影响
                    if node_in_crt.parent is not None and not node_in_crt.is_sub_tree_same(
                            node_acted,
                            is_text_diff_allowed=False,
                            stop_situation=lambda x, y: x.is_dynamic_entrance and y.is_dynamic_entrance):
                        continue  # 静态区域迁移的两个要求：id 相同、子树相同

                    is_self_found = is_self_found or node_in_crt is node_acted

                    if node_in_crt is not node_acted and last_action_result_marked_as_inferred is not None:
                        if instance is instance_acted or action_info[0] != Action.SCROLL:
                            node_in_crt.add_new_action_result(
                                action_info, last_action_result_marked_as_inferred)

                    if action_info in node_in_crt.actions_to_act \
                            and len(node_in_crt.action_type_to_action_result[action_info]) > 0:
                        node_in_crt.actions_to_act.remove(action_info)

                    if node_in_crt in instance.node_not_tried_to_action:
                        if len(node_in_crt.actions_to_act) == 0:
                            instance.node_not_tried_to_action.remove(
                                node_in_crt)
        else:
            actioned_dynamic_root = node_acted.get_dynamic_root_if_in_dynamic_region()
            id_relative_to_root = node_acted.get_id_relative_to(
                actioned_dynamic_root)
            for state in self.page_states:
                for instance in state.page_instances:
                    if is_back_action_node and instance is not instance_acted:  # 返回按钮仅对实际页面生效，不会再迁移到别的页面上去
                        is_same_last_page_find = False
                        for action1, action2 in [(x, y) for x in instance.last_actions_into for y in
                                                 instance_acted.last_actions_into]:
                            if Application.THIS.get_page_state_belong_to(
                                    action1.page_instance) is Application.THIS.get_page_state_belong_to(
                                    action2.page_instance):
                                is_same_last_page_find = True
                                break
                        if not is_same_last_page_find:
                            continue

                    dynamic_roots_in_crt = instance.absolute_dynamic_id_2_node.get(
                        actioned_dynamic_root.absolute_dynamic_id, None)
                    if dynamic_roots_in_crt is None:
                        continue
                    for dynamic_root_crt in dynamic_roots_in_crt:
                        # 这里当 state 数量过多的时候放宽对 text 的要求
                        if dynamic_root_crt.is_sub_tree_same(actioned_dynamic_root, is_text_diff_allowed=Utility.is_state_too_many_instances(state),
                                                             stop_situation=lambda x, y: x.is_dynamic_entrance or y.is_dynamic_entrance) or len(state.page_instances) > 20:
                            correspond_node = dynamic_root_crt.get_node_by_relative_id(
                                id_relative_to_root)  # type: UINode
                            if correspond_node is None:
                                continue
                            is_self_found = is_self_found or correspond_node is node_acted
                            is_exactly_same = dynamic_root_crt.is_sub_tree_same(actioned_dynamic_root,
                                                                                is_text_diff_allowed=False,
                                                                                stop_situation=lambda x, y: x.is_dynamic_entrance or y.is_dynamic_entrance)

                            if correspond_node is not node_acted and last_action_result_marked_as_inferred is not None:
                                if not is_exactly_same:
                                    correspond_node.add_new_action_result(action_info, ActionResult(
                                        None, None, True, True))  # 不是完全一样的话  就会以一种特殊标记的形式加入
                                elif instance is instance_acted or action_info[0] != Action.SCROLL:
                                    correspond_node.add_new_action_result(
                                        action_info, last_action_result_marked_as_inferred)

                            if action_info in correspond_node.actions_to_act \
                                    and len(correspond_node.action_type_to_action_result[action_info]) > 0:
                                correspond_node.actions_to_act.remove(
                                    action_info)

                            if correspond_node in instance.node_not_tried_to_action:
                                if len(correspond_node.actions_to_act) == 0:
                                    instance.node_not_tried_to_action.remove(
                                        correspond_node)

        assert is_self_found

    def refresh_new_added_instance(self, new_instance):
        # type: (PageInstance) -> None
        # 这个函数需要完成的事情，是将新加的 instance 的操作属性进行更新，因为有可能在新的 instance 加入的时候，有一些节点在其他的 instance 中已经操作过了
        for state in self.page_states:
            for instance in state.page_instances:
                if instance is new_instance:
                    continue

                # 对于这个 instance 中所有节点，并且这个节点有过操作，尝试找到在新的 instance 中的对应节点，并对其进行更新
                q = deque()  # type: Deque[UINode]
                q.append(instance.ui_root)

                while len(q) > 0:
                    crt_node = q.popleft()
                    correspond_node = None  # type: UINode  # 只有在真的需要进行更新的时候才会去寻找对应的节点
                    is_correspond_node_exactly_same = True
                    q.extend(crt_node.children)

                    # 所有的返回按钮是不能被迁移的，除非这两个 instance 有相同的 last action
                    if (crt_node.parent is None or Utility.is_backward_button(crt_node)) \
                            and not Utility.is_state_too_many_instances(new_instance.page_state):
                        is_same_last_page_find = False
                        for action1, action2 in [(x, y) for x in instance.last_actions_into for y in
                                                 new_instance.last_actions_into]:
                            if Application.THIS.get_page_state_belong_to(
                                    action1.page_instance) is Application.THIS.get_page_state_belong_to(
                                    action2.page_instance):
                                is_same_last_page_find = True
                                break
                        if not is_same_last_page_find:
                            continue

                    for action_type_and_attr, res_list in crt_node.action_type_to_action_result.items():
                        # 滚动操作不进行迁移
                        if action_type_and_attr[0] == Action.SCROLL:
                            continue
                        if len(res_list) == 0 and action_type_and_attr in crt_node.actions_to_act:
                            # 说明这个页面还没有被处理过
                            continue
                        if correspond_node is None:
                            # 试图查找对应的节点，如果找不到的话，就直接 break 好了
                            # 分在静态区域和不在静态区域两种情况找到对应的节点，和之前相比最大的区别在于动态区域节点的确定
                            if crt_node.is_in_static_region:
                                correspond_node = new_instance.absolute_id_2_node.get(
                                    crt_node.absolute_id, None)
                                if correspond_node is None:
                                    break

                                # 仅仅要求以当前节点为根的子树是相同的即可
                                if action_type_and_attr[0] != Action.GLOBAL_BACK and not correspond_node.is_sub_tree_same(
                                        crt_node,
                                        is_text_diff_allowed=False,
                                        stop_situation=lambda x, y: x.is_dynamic_entrance and y.is_dynamic_entrance):
                                    correspond_node = None
                                    break
                            else:
                                crt_node_dynamic_root = crt_node.get_dynamic_root_if_in_dynamic_region()  # type: UINode
                                assert crt_node_dynamic_root is not None
                                # 在新的页面中找到对应的 entrance 然后再找到一个 subtree same 的区域，然后再在这个区域中定位这个节点
                                # entrance 可能会被多个入口嵌套，找到的入口也不一定唯一的
                                correspond_dynamic_roots = new_instance.absolute_dynamic_id_2_node.get(
                                    crt_node_dynamic_root.absolute_dynamic_id)
                                if correspond_dynamic_roots is None:
                                    break
                                for dynamic_root in correspond_dynamic_roots:
                                    # 在包含过多的 instance 的情况下放宽对 text 的限制
                                    if dynamic_root.is_sub_tree_same(other_node=crt_node_dynamic_root,
                                                                     is_text_diff_allowed=Utility.is_state_too_many_instances(
                                                                         new_instance.page_state),
                                                                     stop_situation=lambda x, y: x.is_dynamic_entrance or y.is_dynamic_entrance):
                                        correspond_node = dynamic_root.get_node_by_relative_id(
                                            crt_node.get_id_relative_to(crt_node_dynamic_root))
                                        if correspond_node is not None:
                                            break
                                        else:
                                            is_correspond_node_exactly_same = dynamic_root.is_sub_tree_same(other_node=crt_node_dynamic_root,
                                                                                                            is_text_diff_allowed=False,
                                                                                                            stop_situation=lambda x, y: x.is_dynamic_entrance or y.is_dynamic_entrance)

                                # 当同一个 state 中的 instance 数量过多的时候，直接要求 id 匹配就可以了
                                # 如果instance 中的数量实在太多的话
                                if correspond_node is None and len(new_instance.page_state.page_instances) >= 20:
                                    correspond_node = new_instance.absolute_id_2_node.get(
                                        crt_node.absolute_id, None)
                                    is_correspond_node_exactly_same = False
                                if correspond_node is None:
                                    break

                        assert correspond_node is not None
                        for x in res_list:
                            # 注意，inferred 的数据不会被加到 last action info 中去
                            if is_correspond_node_exactly_same:
                                correspond_node.add_new_action_result(
                                    action_type_and_attr, x.get_result_as_inferred())
                            else:
                                correspond_node.add_new_action_result(
                                    action_type_and_attr, ActionResult(None, None, True, True))

                        if action_type_and_attr in correspond_node.actions_to_act:
                            correspond_node.actions_to_act.remove(
                                action_type_and_attr)

                    if correspond_node is not None:
                        # assert correspond_node in new_instance.node_not_tried_to_action
                        if len(correspond_node.actions_to_act) == 0 \
                                and correspond_node in new_instance.node_not_tried_to_action:
                            new_instance.node_not_tried_to_action.remove(
                                correspond_node)


class Application:

    THIS = None  # type: Application

    def __init__(self):
        Application.THIS = self
        self.pages = []  # type: List[Page]
        self.not_finished_page_instance = []  # type: List[PageInstance]
        self.instance_waiting_list = []  # type: List[PageInstance]
        self.init_action_results = []  # type: List[ActionResult]  # 将应用杀死并重新进入之后的状态

    def __getitem__(self, item):
        # type: (Tuple[int, int, int])->WindowStructure.PageInstance
        return self.pages[item[0]].page_states[item[1]].page_instances[item[2]]

    def get_next_search_page(self, crt_search_page, crt_instance_example):
        # type: (PageInstance, PageInstance)->bool
        # 维护 not finished page instance，确定下一个进行搜索的页面是什么
        # 为了使得整个的效果是统一的，这里确定下一个搜索页面是什么，不是直接返回对应的 instance，而是将对应的 instance 放在列表首
        # 返回是不是有一个页面已经结束了
        assert crt_search_page is self.not_finished_page_instance[0]
        one_instance_finished = False
        if len(crt_search_page.node_not_tried_to_action) == 0:
            self.not_finished_page_instance.pop(0)
            one_instance_finished = True
            if crt_search_page in self.instance_waiting_list:
                self.instance_waiting_list.remove(crt_search_page)
        # 有两种选择，一种是从现有列表的下一个开始（即什么都不干），另外则从当前实际所在的页面开始，当然要求这个页面有着较高的优先级
        if len(self.not_finished_page_instance) == 0:
            return one_instance_finished
        origin_next = self.not_finished_page_instance[0]
        end_index = -1
        if origin_next in self.instance_waiting_list:
            end_index = self.instance_waiting_list.index(origin_next)

        # 实际上就是和 default 的下一个进行优先级的比较
        instances_to_cmp = self.instance_waiting_list[0:
                                                      end_index] if end_index > 0 else self.instance_waiting_list[0:]
        for instance in instances_to_cmp:
            # 首先要求在同样的 page
            if instance.page_state.page is not crt_instance_example.page_state.page:
                continue
            # 和页面 search 的时候对节点的要求是吻合的
            if len(instance.node_not_tried_to_action) == 0:
                continue
            next_target = instance.node_not_tried_to_action[0]
            search_res = Utility.get_same_node_from_other_instance(
                next_target, crt_instance_example)
            if len(search_res) > 0:
                self.not_finished_page_instance.remove(instance)
                self.not_finished_page_instance.insert(0, instance)
                return one_instance_finished
        return one_instance_finished

    def add_new_page_instance(self, new_page_instance, is_backward_recover=False, last_action=None):
        # type: (PageInstance, bool, Action) -> Tuple[bool, PageInstance] # 返回是否被成功添加，添加之后这个页面实际上在已经存储的系统中对应了哪一个页面
        # 仅仅对三级的数据结构进行维护，但是不对点击效果进行更新

        # 由于是刚刚加入到数据结构中，所以 last_actions_into 的长度必然为1
        last_instance = new_page_instance.last_actions_into[0].page_instance

        if last_instance is not None and \
                Utility.is_two_region_same(last_instance.ui_root, new_page_instance.ui_root, allow_text_diff=False):
            # 页面完全没有发生变化的情况
            return False, last_instance

        # 检测当前的 page_instance 是不是需要作为一个（潜在的）新的 page state
        # 和到达该页面的路径上的页面进行比较
        # 使用广度优先搜索。不允许出现返回按钮。不允许两次进入同一个 instance
        q = deque()  # type: Deque[Action]
        instance_covered = set()
        instance_covered.add(new_page_instance)  # 即使没有合适的 action，这里还是要加
        q.extend(list(filter(lambda x: not Utility.is_backward_action(
            x), new_page_instance.last_actions_into)))

        # 对于简单恢复的行动
        # 我们现在加入了页面状态的东西，只要是和到达该页面的前驱页面之间相似，但是有变化，就会被记录，无论变化多小
        while len(q) > 0 and not is_backward_recover:
            # 第一个部分，是在所有的前驱页面中寻找
            action = q.popleft()
            pre_instance = action.page_instance
            if pre_instance in instance_covered:
                continue
            instance_covered.add(pre_instance)
            if pre_instance is None:
                continue
            q.extend(list(filter(lambda x: not Utility.is_backward_action(
                x), pre_instance.last_actions_into)))

            pre_state = pre_instance.page_state
            pre_page = pre_state.page

            # 找到的都是到达这个页面的前驱页面
            assert pre_state is not None and pre_page is not None
            if new_page_instance.activity_name is not None \
                    and pre_state.page_instances[0].activity_name is not None \
                    and not Utility.is_two_str_same_without_num(new_page_instance.activity_name,
                                                                pre_state.page_instances[0].activity_name):
                continue
            #  需要作为一个新的 state 的话，必须要和当前所在的 page 中的元素足够相似
            (min_diff, min_diff_instance), (max_diff, max_diff_instance), \
                (min_node_diff, min_node_diff_instance), (max_node_diff, max_node_diff_instance) = pre_page.get_diff_info_to_instance(
                new_page_instance, action.type == Action.SCROLL)  # 此处对滚动的处理应该说是比较合理的
            print('diff_area_ratio', min_diff, max_diff,
                  'diff_node_ratio', min_node_diff, max_node_diff)
            if min_diff > 0.5:  # 两个页面不相似，要求面积的差别大于0.5  但是对于同一个 page 不同 state  对于节点数量 就不要求了
                continue
            if min_diff == 0 or min_node_diff == 0:
                # 说明找到了静态区域相同的元素
                # 说明可能是使得动态区域发生了变化，在这种情况下需要作为一个 instance 加入到对应的 state 中去（只要没有出现完全相同的元素的话）
                similar_state = min_diff_instance.page_state
                for instance in similar_state.page_instances:
                    # 根据当前 state 的数量来确定要求
                    if not instance.ui_root.is_sub_tree_same(
                            new_page_instance.ui_root, is_text_diff_allowed=False,
                            stop_situation=lambda x, y: x.is_dynamic_entrance or y.is_dynamic_entrance):
                        continue

                    same_state_instance_num = len(similar_state.page_instances)
                    th = min(int(same_state_instance_num / 20) * 0.1, 0.5)

                    if Utility.cal_global_area_ratio(instance, new_page_instance) <= th:
                        # 需要加入新的 action list
                        for last_action in new_page_instance.last_actions_into:
                            instance.add_new_last_action(last_action)
                        return False, instance

                # 这里实际上是"区域"的状态发生了变化，在 post processing 中再进行处理
                new_page_instance.last_similar_instance = min_diff_instance
                similar_state.add_new_instance(new_page_instance)
                return True, new_page_instance
            else:
                # 说明静态区域相似但是却没有完全相同
                # 是作为 min_diff_instance 的兄弟 instance
                # 要求静态区域只有文本的区别，并且这个文本是不可点击的，能找到这样的话，就作为一个兄弟 instance 加入其中
                is_similar = True
                diff_list = Utility.get_ui_diff(
                    min_diff_instance, new_page_instance, is_force_static=False)
                for node1, node2 in diff_list:
                    if node1 is None or node2 is None or node1.node_class != node2.node_class \
                       or node1.index != node2.index\
                       or node1.clickable != node2.clickable \
                       or node1.enabled != node2.enabled \
                       or node1.resource_id != node2.resource_id \
                       or node1.is_dynamic_entrance != node2.is_dynamic_entrance:  # todo 我用同一个节点在不同的页面上是不是一个动态入口作为判断的条件，对应的动静区域划分也需要进行相关的处理
                        is_similar = False
                        break
                    # 说明实际上只有文本上的不同了
                    if node1.has_clickable_parent() or node2.has_clickable_parent():
                        is_similar = False
                        break

                has_interactable_diff = False
                for src_node, des_node in diff_list:
                    if Utility.is_region_interactable(src_node) or Utility.is_region_interactable(des_node):
                        has_interactable_diff = True
                        break

                new_page_instance.last_similar_instance = min_diff_instance
                # 否则需要作为一个新的 state 加入到当前的 page 中
                # todo 出现不同的节点必须有可以交互的子节点，才能作为一个新的state。否则，还是作为一个新的 instance 就好
                if has_interactable_diff and not is_similar:
                    new_state = PageState(len(pre_page.page_states), pre_page)
                    pre_page.page_states.append(new_state)
                    new_state.add_new_instance(new_page_instance)
                else:
                    min_diff_instance.page_state.add_new_instance(
                        new_page_instance)
                return True, new_page_instance

        # 说明在前驱页面中，没有找到静态区域类似的页面
        # 那么在其余的页面中，如果能够找到静态区域类似的，就可以作为一个 instance 加入到对应的 state 中去
        # 由于这里已经没有页面的前后跳转关系，要么是作为一个新的 instance 加入到一个已有的 state 中去，要么就新建一个 page，并将这个 instance 作为这个页面的第一个 instance，要么就发现出现了完全一样的界面
        # 不需要对滚动事件进行特殊处理

        min_min_diff = 1
        instance_when_min_min_diff = None

        for page in self.pages:
            if new_page_instance.activity_name is not None \
                    and page.page_states[0].page_instances[0].activity_name is not None \
                    and not Utility.is_two_str_same_without_num(new_page_instance.activity_name,
                                                                page.page_states[0].page_instances[0].activity_name):
                continue
            (min_diff, min_diff_instance), (_, _), (min_node_diff, min_node_diff_instance), (_,
                                                                                             _) = page.get_diff_info_to_instance(new_page_instance, False)
            if min_diff > 0.5 or min_node_diff >= 0.5:
                continue

            if min_diff == 0:  # 如果是一样的话，一定要放在一起
                for instance in min_diff_instance.page_state.page_instances:
                    # 必须要求在静态区域是完全一样的！
                    if not instance.ui_root.is_sub_tree_same(
                            new_page_instance.ui_root, is_text_diff_allowed=False,
                            stop_situation=lambda x, y: x.is_dynamic_entrance or y.is_dynamic_entrance):
                        continue

                    same_state_instance_num = len(
                        min_diff_instance.page_state.page_instances)
                    th = min(int(same_state_instance_num / 10) * 0.1, 0.5)

                    if Utility.cal_global_area_ratio(instance, new_page_instance) <= th:
                        for last_action in new_page_instance.last_actions_into:
                            instance.add_new_last_action(last_action)
                        return False, instance
                    elif instance.ui_root.debug_print_info(0) == new_page_instance.ui_root.debug_print_info(0):
                        print('two cmp methods not match!!')
                        Utility.cal_global_area_ratio(
                            instance, new_page_instance)

            if min_diff < min_min_diff:
                min_min_diff = min_diff
                instance_when_min_min_diff = min_diff_instance

        if min_min_diff <= 0.5:  # 找到一个最为接近的
            assert instance_when_min_min_diff is not None
            # 说明找到了静态区域类似的 instance
            # 就作为 min_diff_instance 的兄弟加入到对应的 state 中（只要不是找到了完全一样）
            similar_state = instance_when_min_min_diff.page_state
            # 说明没有找到完全相同的 instance，就将这个 instance 加入到这个 similar_state
            similar_state.add_new_instance(new_page_instance)
            return True, new_page_instance

        # 作为一个新的 page 加入到这个 Application 中去
        new_page = Page(len(self.pages))
        new_state = PageState(0, new_page)
        new_state.add_new_instance(new_page_instance)
        new_page.page_states.append(new_state)
        self.pages.append(new_page)
        return True, new_page_instance

    def get_page_state_belong_to(self, instance):

        if instance is None:
            return None

        if instance.page_state is not None:
            return [instance.page_state.page], [instance.page_state]

        min_min_diff_ratio = 1
        min_diff_instances_when_min_ratio = None

        # 说明是没有"编制"的instance，需要在所有的页面中进行选择
        for page in self.pages:
            # 首先还是要考虑 activity name
            first_instance = page.page_states[0].page_instances[0]
            if instance.activity_name is not None and first_instance.activity_name is not None \
                    and not Utility.is_two_str_same_without_num(instance.activity_name, first_instance.activity_name):
                continue

            # todo 对于那些只有动态区域，没有静态区域的页面 应该改为 考虑动态区域，并结合跳转路径
            (min_diff_ratio, min_diff_instance), (_, _), (min_node_diff_ratio,
                                                          min_node_diff_instance), (_, _) = page.get_diff_info_to_instance(instance, False)
            if min_diff_ratio <= 0.5 and min_node_diff_ratio < 0.5:
                if min_min_diff_ratio > min_diff_ratio:
                    min_min_diff_ratio = min_diff_ratio
                    min_diff_instances_when_min_ratio = [min_diff_instance]
                elif min_min_diff_ratio == min_diff_ratio:
                    min_diff_instances_when_min_ratio.append(
                        min_diff_instance)  # 如果还是 None 的话，是不可能相等的

        if min_diff_instances_when_min_ratio is None:
            return [], []
        return [x.page_state.page for x in min_diff_instances_when_min_ratio],\
               [x.page_state for x in min_diff_instances_when_min_ratio]


class ContextSource:
    TYPE_TEXT = 1
    TYPE_LIST_SELECT = 2

    def __init__(self, context_type, state, **kwargs):
        # type: (int, PageState, Dict[str, str]) -> None
        self.context_type = context_type  # type: int
        self.page_state = state  # type: PageState or PageInstance
        self.enter_text_node_id = None  # type: Optional[str]

        self.dynamic_entrance_id = None  # type: Optional[str]
        self.select_node_id_to_dynamic_root = None  # type: Optional[str]
        if context_type == ContextSource.TYPE_TEXT:
            self.enter_text_node_id = kwargs['enter_text_node_dynamic_id']
        else:
            self.dynamic_entrance_id = kwargs['dynamic_root_dynamic_id']
            self.select_node_id_to_root = kwargs['select_node_id_to_dynamic_root']

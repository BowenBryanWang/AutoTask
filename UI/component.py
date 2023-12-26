import os.path
from queue import Queue
from typing import List


class UINode:

    STOP_NODE_LIST = []

    MAX_SCROLL_STEP = 1

    def __init__(self, crt_layout, parent, instance):
        if crt_layout is None:
            return
        self.page_instance = instance
        self.depth = 0 if parent is None else parent.depth + 1
        self.parent = parent
        self.index = int(crt_layout['@index'])
        self.page_id = instance.page_cnt
        if '@text' in crt_layout:
            self.text = crt_layout['@text']
        else:
            self.text = ""
        if '@resource-id' in crt_layout:
            self.resource_id = crt_layout['@resource-id']
        else:
            self.resource_id = ""
        self.node_class = crt_layout['@class']
        if '@package' in crt_layout:
            self.package = crt_layout['@package']
        else:
            self.package = ""
        if '@content-desc' in crt_layout:
            self.content_desc = crt_layout['@content-desc']
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
            self.enabled = False
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
        self.executable = self.clickable | self.long_clickable | self.editable | self.scrollable
        self.clone_source = None

        self.bound = [int(x) for x in crt_layout['@bounds'].replace('][', ',').replace(']', '').replace('[', '').split(
            ',')]  # type: List[int]
        self.width = self.bound[2] - self.bound[0]
        self.height = self.bound[3] - self.bound[1]
        self.center = [(self.bound[0] + self.bound[2]) / 2,
                       (self.bound[1] + self.bound[3]) / 2]

        self.area = self.width * self.height
        self.isVisible = (self.bound[0] < self.bound[2]
                          and self.bound[1] < self.bound[3])

        self.absolute_id = self.node_class if self.parent is None else self.parent.absolute_id + '|%d;%s' % (
            self.index, self.node_class)  # type: str

        self.absolute_dynamic_id = None

        if 'node' not in crt_layout.keys():
            self.children = list()  # type: List[UINode]
        elif isinstance(crt_layout['node'], list):
            self.children = [UINode(x, self, instance)
                             for x in crt_layout['node']]  # type: List[UINode]
        else:
            # type: List[UINode]
            self.children = [UINode(crt_layout['node'], self, instance)]
        self.blockRoot = None
        return

    def has_semantic_info(self):
        def hasSemanticInfo(self):
            if self.text != '' or self.content_desc != '':
                return True
            else:
                return False
        if hasSemanticInfo(self):
            return True
        else:

            all_children = [self]
            while all_children:
                current_node = all_children.pop()
                if hasSemanticInfo(current_node):
                    return True
                else:
                    all_children.extend(current_node.children)
            return False

    def generate_all_semantic_info(self):

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

        return res

    def has_similar_children(self):

        all = {"width": [], "height": []}
        if self.children != [] and len(self.children) > 1:
            for child in self.children:
                all["width"].append(child.width)
                all["height"].append(child.height)

            widthModeRatio = all["width"].count(
                max(set(all["width"]), key=all["width"].count))/len(all["width"])
            heightModeRatio = all["height"].count(
                max(set(all["height"]), key=all["height"].count))/len(all["height"])

            if widthModeRatio*heightModeRatio > 0.8:
                return True
        return False

    def is_selected(self):
        prob = 1
        if self.resource_id == "com.android.settings:id/search_action_bar" or self.text == "Search settings" or self.content_desc == "Search settings":
            # disable search
            return 0
        if self.parent is not None and 'action_bar' in self.parent.resource_id and self.content_desc == 'Back':
            # disable back
            return 0

        if self.area > 1080*2310*0.4:
            prob *= 0.5
        if self.clickable:
            prob *= 2
        else:
            prob *= 0.1
        if self.executable:
            prob *= 1.5
        else:
            prob *= 0.5
        if self.scrollable and (self.focusable or self.enabled):
            prob *= 10000
        if self.has_semantic_info():
            prob *= 1.5
        else:
            prob *= 0.5
        if self.text != "":
            prob *= 100
        if self.has_similar_children():
            prob *= 0.5
        if self.editable:
            prob *= 1.5
        if self.node_class == "android.widget.EditText":
            prob *= 2
        if self.parent and len(self.parent.children) > 6:
            prob *= 2
        elif self.parent and len(self.parent.children) > 3:
            prob *= 1.5
        else:
            prob *= 0.5
        if self.selected:
            prob *= 0.5
        if self.checkable:
            return 1

        if prob >= 1:
            # if self.clickable:
            #     if self.depth >= 16:
            #         if self.parent and len(self.parent.children) > 1:
            #             return 0
            #         else:
            #             return 1
            #     else:
            #         if self.parent and len(self.parent.children) > 1:
            #             return 1
            #         else:
            #             if len(self.children) > 0:
            #                 return 0
            #             else:
            #                 return 1
            # else:
            #     if len(self.children) > 0:
            #         if self.parent and len(self.parent.children) > 4:
            #             if self.depth > 12:
            #                 return 0
            #             else:
            #                 return 1
            #         else:
            #             return 0
            #     else:
            #         return 1
            return 1
        else:
            return 0

    def get_all_semantic_nodes(self):

        stack = [self]
        res = {"nodes": [], "info": []}
        while stack:
            node = stack.pop()
            if node.is_selected() >= 1:
                res["nodes"].append(node)
                res["info"].append(node.generate_all_semantic_info())
            for child in reversed(node.children):
                stack.append(child)

        relation = []
        for i in range(len(res["nodes"])):
            for j in range(i+1, len(res["nodes"])):
                if res["nodes"][i] and res["nodes"][j] and res["nodes"][i].is_ancestor(res["nodes"][j]):
                    relation.append((j, i))
                elif res["nodes"][i] and res["nodes"][j] and res["nodes"][j].is_ancestor(res["nodes"][i]):
                    relation.append((i, j))
                elif res["nodes"][i] and res["nodes"][j] and res["info"][i] == res["info"][j] and res["nodes"][i].bound == res["nodes"][j].bound:
                    res["nodes"][j] = None
        res["nodes"] = [node for node in res["nodes"] if node is not None]
        return res, relation

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

    def is_ancestor(self, other_node):
        crt_node = self
        while crt_node is not None:
            if crt_node is other_node:
                return True
            crt_node = crt_node.parent
        return False

    def generate_all_text(self):
        res = []
        q = Queue()
        q.put(self)
        while not q.empty():
            crt_node = q.get()
            for child_node in crt_node.children:
                q.put(child_node)
            if crt_node.text is not None and len(crt_node.text) > 0:
                res.append(crt_node.text)
        return "-".join(res)


class PageInstance:
    store_root = os.path.join(os.getcwd(), 'PageInfo/')
    tmp_root = os.path.join(store_root, 'tmp/')

    def __init__(self):
        self.time_stamp = -1
        self.page_state = None
        self.index = -1

        self.screen_save_path = None
        self.layout_json_path = None

        self.last_actions_into = []

        self.ui_root = None
        self.absolute_id_2_node = {}
        self.absolute_dynamic_id_2_node = {}
        self.node_not_tried_to_action = []
        self.dynamic_entrance = []
        self.activity_name = None
        self.is_static_empty = True
        self.has_semantic_context = False
        self.semantic_source_action = []
        self.added_due_to_back = False
        self.last_similar_instance = None

        self.ori_instance_id = (-1, -1, -1)
        self.crt_instance_id = (-1, -1, -1)

        self.crt_time_stamp = -1

        self.ref_instance = None  # type: PageInstance
        self.state_id = None  # type: str

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

    def generate_dynamic_attr(self, crt_node, dynamic_entrance_store_list, has_encounter_entrance=False):
        if not hasattr(crt_node, "scrollable"):
            crt_node.scrollable = False
        if crt_node.scrollable or 'ListView' in crt_node.node_class or 'RecyclerView' in crt_node.node_class or 'GridView' in crt_node.node_class:
            child_node_num_before = len(crt_node.children)
            all_popped_children = []
            for index in range(len(crt_node.children) - 1, -1, -1):
                if not crt_node.children[index].isVisible:
                    all_popped_children.append(crt_node.children.pop(index))

            if (len(crt_node.children) > 1 or (child_node_num_before == 1)):
                crt_node.is_dynamic_entrance = True
                dynamic_entrance_store_list.append(crt_node)
            elif len(crt_node.children) == 1:
                left_child = crt_node.children[0]
                is_y_overlapped = False
                for popped_child in all_popped_children:
                    if not (popped_child.bound[1] >= left_child.bound[3]
                            or popped_child.bound[3] <= left_child.bound[1]):
                        is_y_overlapped = True
                    if is_y_overlapped:
                        break

                if not is_y_overlapped:
                    crt_node.is_dynamic_entrance = True
                    dynamic_entrance_store_list.append(crt_node)

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

        self.absolute_id_2_node[crt_node.absolute_id] = crt_node
        if crt_node.absolute_dynamic_id not in self.absolute_dynamic_id_2_node:
            self.absolute_dynamic_id_2_node[crt_node.absolute_dynamic_id] = []
        self.absolute_dynamic_id_2_node[crt_node.absolute_dynamic_id].append(
            crt_node)

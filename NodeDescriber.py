from abc import ABCMeta, abstractmethod
from pydoc import describe
import queue
#from asyncio.windows_events import None
# from selectors import EpollSelector
from WindowStructure import *
import math
import copy
from sklearn import tree
from sklearn.tree import DecisionTreeClassifier, export_graphviz
from sklearn.model_selection import train_test_split
import pydotplus

class NodeDescriber:
    # TODO:
    positive_ref_nodes = [] #所有正例节点，(block_root, ref_node)
    positive_nodes = [] #所有正例节点，(block_root, ref_node)
    negative_ref_nodes = [] #所有负例节点，(block_root, ref_node)
    tag = 'NodeDescriber'
    def __init__(self, positive_ref_nodes, negative_ref_nodes):
        self.positive_ref_nodes = positive_ref_nodes
        self.negative_ref_nodes = negative_ref_nodes

    @abstractmethod
    def find_node(self, crt_root):  # 如果是定位列表里的元素（需泛化），则crtRoot为listItem的根节点
        pass

    @abstractmethod
    def match(self, crt_root, check_node):  # crt_root含义与find_node一致，判断check_node是否匹配上
        pass


class SpecialNodeDescriber(NodeDescriber):
    def __init__(self,  positive_ref_nodes, negative_ref_nodes, positive_nodes=[]):
        # type: (list,list,list) -> None
        self.positive_ref_nodes = positive_ref_nodes
        self.negative_ref_nodes = negative_ref_nodes
        self.positive_nodes = positive_nodes
        self.tag = 'SpecialNodeDescriber'
        # self.node = node  # type: UINode
        # self.nodeMethod = 0  # 默认使用原本计算差异值的方法
        # # self.widthHeightRatio = 0
        # self.screenRoot = node.get_root()
        # self.blockRoot = node.findBlockNode()
        # nodeRect_width = self.node.width()
        # nodeRect_height = self.node.height()
        # screenRect_width = self.screenRoot.width()
        # screenRect_height = self.screenRoot.height()
        # blockRect_width = self.BlockRoot.width()
        # blockRect_height = self.BlockRoot.height()

        # self.widthHeightRatio = nodeRect_width / nodeRect_height
        # self.widthScreenRatio = nodeRect_width / screenRect_width
        # self.heightScreenRatio = nodeRect_height / screenRect_height

        # disToBlockLeft = self.node.bound[0] - self.blockRoot.bound[0]
        # self.leftToBlockWidth = disToBlockLeft / blockRect_width

        # disToBlockRight = self.node.bound[2] - self.blockRoot.bound[2]
        # self.rightToBlockWidth = disToBlockRight / blockRect_width

        # disToBlockTop = self.node.bound[1] - self.blockRoot.bound[1]
        # self.topToBlockHeight = disToBlockTop / blockRect_height

        # nodeCentralX = (self.node.bound[0]+self.bound[2])/2.0
        # blockCentralX = (self.blockRoot.bound[0]+self.blockRoot.bound[2])/2.0
        # self.centralXToBlockCentral = abs(
        #     nodeCentralX - blockCentralX) / blockRect_width

    def update(self, positive_ref_node=[], negative_ref_node=[], positive_node=[]):
        if positive_ref_node:
            self.positive_ref_nodes += positive_ref_node
        if negative_ref_node:
            self.negative_ref_nodes += negative_ref_node
        if positive_node:
            self.positive_nodes += positive_node

    def find_node(self, crt_root):
        if len(self.positive_ref_nodes) == 0:
            return None
        minDis = 99.0
        minDisNode = None
        stack = [crt_root]
        while stack:
            node = stack.pop()
            for positive_node_pair in self.positive_ref_nodes:
                dis = self.calNodeDistanceToDescriber(
                    node, positive_node_pair[1])
                if dis <= minDis:
                    minDis = dis
                    minDisNode = node
            for child in node.children:
                stack.append(child)
        print(minDis)
        if minDis <=0.0:
            return minDisNode
        else:
            return None

    def calNodeDistanceToDescriber(self, node: UINode, positive_node: UINode):
        if node == None:
            return 101
        if node.text != "" and positive_node.text == "":
            return 102
        if node.text == "" and positive_node.text != "":
            return 103
        root = node.get_root()
        refroot = positive_node.get_root()
        blockRoot = node.findBlockNode()
        if blockRoot == None:
            blockRoot = root
        refBlockRoot = positive_node.findBlockNode()
        if refBlockRoot == None:
            refBlockRoot = root
        
        nodeRect_width = node.width
        nodeRect_height = node.height
        screenRect_width = root.width
        blockRect_width = blockRoot.width
        blockRect_height = blockRoot.height

        refnodeRect_width = positive_node.width
        refnodeRect_height = positive_node.height
        refscreenRect_width = refroot.width
        refblockRect_width = refBlockRoot.width
        refblockRect_height = refBlockRoot.height

        widthHeightRatioOfGiven = nodeRect_width / nodeRect_height
        widthScreenRatioOfGiven = nodeRect_width / screenRect_width

        refwidthHeightRatioOfGiven = refnodeRect_width / refnodeRect_height
        refwidthScreenRatioOfGiven = refnodeRect_width / refscreenRect_width

        disToBlockLeft = node.bound[0] - blockRoot.bound[0]
        leftToBlockWidthOfGiven = disToBlockLeft / blockRect_width

        disToBlockTop = node.bound[1] - blockRoot.bound[1]
        topToBlockHeightOfGiven = disToBlockTop / blockRect_height

        refdisToBlockLeft = positive_node.bound[0] - refBlockRoot.bound[0]
        refleftToBlockWidthOfGiven = refdisToBlockLeft / refblockRect_width

        refdisToBlockTop = positive_node.bound[1] - refBlockRoot.bound[1]
        reftopToBlockHeightOfGiven = refdisToBlockTop / refblockRect_height

        diffRatioWidthHeightRatio = abs(widthHeightRatioOfGiven - refwidthHeightRatioOfGiven) / (
            min(widthHeightRatioOfGiven, refwidthHeightRatioOfGiven) + 0.00001)
        diffRatioWidthScreenRatio = abs(widthScreenRatioOfGiven - refwidthScreenRatioOfGiven) / (
            min(widthScreenRatioOfGiven, refwidthScreenRatioOfGiven) + 0.00001)
        diffRatioLeftToBlock = abs(leftToBlockWidthOfGiven - refleftToBlockWidthOfGiven) / (
            min(leftToBlockWidthOfGiven, refleftToBlockWidthOfGiven) + 0.0001)
        diffRatioTopToBlock = abs(topToBlockHeightOfGiven - reftopToBlockHeightOfGiven) / (
            min(topToBlockHeightOfGiven, reftopToBlockHeightOfGiven) + 0.0001)

        simRatioId = self.calcSimilarity(positive_node, node)
        if simRatioId == 100:
            return -1
        if simRatioId > 1:
            return 0.0
        if simRatioId == 0.0:
            return 104
        c = 1.0
        if node.clickable and positive_node.clickable:
            c *= 0.9
        if node.editable and positive_node.editable:
            c *= 0.8
        if node.scrollable and positive_node.scrollable:
            c *= 0.7
        # if blockRoot.node_class == refBlockRoot.node_class:
        #     return 105  # ?
        if simRatioId > 0.98:
            if positive_node.text != "" and node.text != "":
                if positive_node.text != "" and positive_node.text == node.text:
                    return -1
            if positive_node.content_desc != "" and node.content_desc != "":
                if positive_node.content_desc != "" and positive_node.content_desc == node.content_desc:
                    return -1
            return c*min(diffRatioWidthHeightRatio+diffRatioWidthScreenRatio+diffRatioLeftToBlock+diffRatioTopToBlock, 1.0)/pow(1.5, simRatioId)

        if positive_node.text != "" and node.text != "":
            if positive_node.text != "" and positive_node.text == node.text:
                return -1
        if diffRatioWidthHeightRatio < 0.25 and diffRatioWidthScreenRatio < 0.25 and diffRatioLeftToBlock < 0.25 and diffRatioTopToBlock < 0.25:
            if positive_node.content_desc != "" and node.content_desc != "":
                if positive_node.content_desc != "" and positive_node.content_desc == node.content_desc:
                    return c*(diffRatioWidthHeightRatio + diffRatioWidthScreenRatio + diffRatioLeftToBlock + diffRatioTopToBlock)*0.8
            return c*(diffRatioWidthHeightRatio + diffRatioWidthScreenRatio + diffRatioLeftToBlock + diffRatioTopToBlock)
        else:
            if diffRatioWidthHeightRatio + diffRatioWidthScreenRatio + diffRatioLeftToBlock < 0.1:
                return diffRatioWidthHeightRatio + diffRatioWidthScreenRatio + diffRatioLeftToBlock
            return 2*c*(diffRatioWidthHeightRatio + diffRatioWidthScreenRatio + diffRatioLeftToBlock + diffRatioTopToBlock)

    def calcSimilarity(self, refNode: UINode, node: UINode):
        if refNode == None or node == None:
            return 0
        if refNode.node_class != node.node_class:
            return 0.0
        st1 = refNode.absolute_id.replace(r"fake.root\\|\\d+", "")
        st2 = node.absolute_id.replace(r"fake.root\\|\\d+", "")
        if st1 == st2:
            return 100
        subList1 = refNode.absolute_id.split(";")
        l1 = len(subList1)
        if "fake" in subList1[0]:
            for i in range(0, l1-1):
                subList1[i] = subList1[i+1]
            l1 = l1-1
        subList2 = node.absolute_id.split(";")
        l2 = len(subList2)
        if "fake" in subList2[0]:
            for i in range(0, l2-1):
                subList2[i] = subList2[i+1]
            l2 = l2-1
        F = [[0 for _ in range(l2)] for __ in range(l1)]
        for i in range(l1):
            for j in range(l2):
                if i != 0:
                    F[i][j] = max(F[i][j], F[i-1][j])
                if j != 0:
                    F[i][j] = max(F[i][j], F[i][j-1])
                tmp = 0
                if i != 0 and j != 0:
                    tmp = F[i-1][j-1]
                if subList1[i] == subList2[j]:
                    tmp += 1
                else:
                    subIdSplited1 = subList1[i].split(r"\\|")
                    subIdSplited2 = subList2[j].split(r"\\|")
                    if subIdSplited1[0] == subIdSplited2[0]:
                        tmp += 0.8
                    else:
                        if i == l1-1 and j == l2-1:
                            return 0.0
                F[i][j] = max(F[i][j], tmp)
        matchedRatio = 2.0*F[l1-1][l2-1]/(l1+l2)
        return matchedRatio

    def match(self, crt_root, check_node):
        if len(self.positive_ref_nodes) == 0:
            return False
        matchedNode = self.find_node(crt_root)
        return matchedNode == check_node


class PathNodeDescriber(NodeDescriber):
    def __init__(self, positive_ref_nodes, negative_ref_nodes):
        self.positive_ref_nodes = positive_ref_nodes
        self.negative_ref_nodes = negative_ref_nodes
        self.tag = 'PathNodeDescriber'

    def update(self, positive_ref_nodes, negative_ref_nodes):
        # TODO:
        pass

    def find_node_by_relative_id(self, crt_root, ori_relative_id):
        ref_sub_id_list = ori_relative_id.split(";")
        ref_len = len(ref_sub_id_list)
        node_queue = queue.Queue()
        node_queue.put(crt_root)
        while (not node_queue.empty()):
            node = node_queue.get()
            if node is None:
                continue
            st = node.get_id_relative_to(crt_root)
            if (st == ori_relative_id):
                return node
            if (len(st) > 0):
                sub_id_list = st.split(";")
                crt_len = len(sub_id_list)
                if crt_len > ref_len:
                    continue
                ref_sub_id_splited = ref_sub_id_list[crt_len-1].split("|")
                if node.node_class is not None:
                    if node.node_class != ref_sub_id_splited[0]:
                        continue
                matched = True
                for i in range(crt_len-1):
                    ref_sub_id_splited = ref_sub_id_list[i].split("|")
                    sub_id_splited = sub_id_list[i].split("|")
                    if (ref_sub_id_splited[0] != sub_id_splited[0]):
                        matched = False
                        break
                    if (ref_sub_id_splited[1] != sub_id_splited[1]):
                        if not node.is_list_item_node():
                            matched = False
                            break
                if not matched:
                    continue
                if crt_len == ref_len:
                    return node
            for child in node.children:
                node_queue.put(child)
        return None

    def find_node(self, crt_root):  # 如果是定位列表里的元素（需泛化），则crtRoot为listItem的根节点；否则是页面根节点
        if len(self.positive_ref_nodes) == 0:
            return None
        absolute_ids = set()
        for ref_node_pair in self.positive_ref_nodes:
            ref_block_root = ref_node_pair[0]
            ref_node = ref_node_pair[1]
            ori_relative_id = ref_node.get_id_relative_to(ref_block_root)
            if ori_relative_id in absolute_ids:
                continue
            absolute_ids.add(ori_relative_id)
            node = self.find_node_by_relative_id(crt_root, ori_relative_id)
            if node is not None:
                return node
        return None

    def match(self, crt_root, check_node):
        if len(self.positive_ref_nodes) == 0:
            return False
        absolute_ids = set()
        for ref_node_pair in self.positive_ref_nodes:
            ref_block_root = ref_node_pair[0]
            ref_node = ref_node_pair[1]
            ori_relative_id = ref_node.get_id_relative_to(ref_block_root)
            if ori_relative_id in absolute_ids:
                continue
            absolute_ids.add(ori_relative_id)
            if (check_node.text == "新的朋友"):
                print("path strict match",ref_node.text)
                print("path strict match",ori_relative_id)
                print(ref_block_root.absolute_id)
                print(crt_root.absolute_id)
            #print("ori_relative_id:", ori_relative_id)
            node = self.find_node_by_relative_id(crt_root, ori_relative_id)
            #print("crt_root:", crt_root.absolute_id, ref_block_root.absolute_id,node)
            if node == check_node:
                return True
        return False


class LayoutNodeDescriber(NodeDescriber):
    # TODO:
    pass


class AutoNodeDescriber(NodeDescriber):
    # TODO:
    page_id_ref_node_id2feature = dict()

    def __init__(self, positive_ref_nodes, negative_ref_nodes, positive_nodes):
        super().__init__(positive_ref_nodes, negative_ref_nodes)
        self.tag = 'AutoNodeDescriber'
        self.positive_nodes = positive_nodes
        for ref_node_pair in self.positive_ref_nodes:
            if ref_node_pair not in self.positive_nodes:
                self.positive_nodes.append(ref_node_pair)
        self.p_nodes = []
        for ref_node_pair in positive_nodes:
            self.p_nodes.append(ref_node_pair[1])
        self.n_nodes = []
        for ref_node_pair in negative_ref_nodes:
            self.n_nodes.append(ref_node_pair[1])
        self.init_all_features()
        self.candidate_negative_nodes = self.predict_negative_nodes(
            self.positive_nodes)
        self.train_model()

    def init_all_features(self):
        # TODO:计算所有feature
        self.node_class_list = []
        self.feature_name_list = ['node_class_id','clickable','editable','path_strict_match','path_match_ratio',
                            'text_match_state','text_match_ratio',
                            'content_match_state','content_match_ratio',
                            'resource_id',
                            'left: global','left: block',
                            'right: global','right: block',
                            'top: global','top: block',
                            'bottom: global','bottom: block',
                            'mid_x: global','mid_x: block',
                            'mid_y: global','mid_y: block']
        #正例
        #for ref_node_pair in self.positive_ref_nodes:
            #crt_feature_list = self.get_all_features_for_positive_node(ref_node_pair)
            #self.positive_X.append(crt_feature_list)
        self.recal_all_features_for_positive_nodes()
        self.recal_all_features_for_negative_ref_nodes()

    def recal_all_features_for_positive_nodes(self):
        #正例
        self.positive_X = []
        for ref_node_pair in self.positive_nodes:
            crt_feature_list = self.get_all_features(ref_node_pair)
            self.positive_X.append(crt_feature_list)

    def recal_all_features_for_negative_ref_nodes(self):
        # 负例
        self.negative_X = []
        for ref_node_pair in self.negative_ref_nodes:
            crt_feature_list = self.get_all_features(ref_node_pair)
            self.negative_X.append(crt_feature_list)

    def recal_all_features_for_candidate_negative_nodes(self):
        self.candidate_negative_X = []
        for ref_node_pair in self.candidate_negative_nodes:
            crt_feature_list = self.get_all_features(ref_node_pair)
            self.candidate_negative_X.append(crt_feature_list)

    def get_all_features_for_positive_node(self, ref_node_pair):
        crt_feature_list = []
        # TODO:
        # 1.1: node_class_id
        node_class_id = self.node_class_list.index(ref_node_pair[1].node_class) if ref_node_pair[1].node_class in self.node_class_list else -1
        if node_class_id == -1:
            self.node_class_list.append(ref_node_pair[1].node_class)
            node_class_id = len(self.node_class_list) - 1
        crt_feature_list.append(node_class_id)
        # 1.2: clickable
        crt_feature_list.append(int(ref_node_pair[1].clickable))
        # 1.3: editable
        crt_feature_list.append(int(ref_node_pair[1].editable))
        # 2.1: path_strict_match
        crt_feature_list.append(1)
        # 2.2: path_match_ratio
        crt_feature_list.append(1)
        # 3.1: text_match_state
        crt_feature_list.append(0)
        # 3.2: text_match_ratio
        crt_feature_list.append(1)
        # 4.1: content_match_state
        crt_feature_list.append(0)
        # 4.2: content_match_ratio
        crt_feature_list.append(1)
        # 5: resource_id
        crt_feature_list.append(1)
        # 6.1.1: left: global
        crt_feature_list.append(ref_node_pair[1].cal_left(0))
        # 6.1.2: left: block
        crt_feature_list.append(ref_node_pair[1].cal_left(1))
        # 6.2.1: right: global
        crt_feature_list.append(ref_node_pair[1].cal_right(0))
        # 6.2.2: right: block
        crt_feature_list.append(ref_node_pair[1].cal_right(1))
        # 6.3.1: top: global
        crt_feature_list.append(ref_node_pair[1].cal_top(0))
        # 6.3.2: top: block
        crt_feature_list.append(ref_node_pair[1].cal_top(1))
        # 6.4.1: bottom: global
        crt_feature_list.append(ref_node_pair[1].cal_bottom(0))
        # 6.4.2: bottom: block
        crt_feature_list.append(ref_node_pair[1].cal_bottom(1))
        # 6.5.1: mid_x: global
        crt_feature_list.append(ref_node_pair[1].cal_mid_x(0))
        # 6.5.2: mid_x: block
        crt_feature_list.append(ref_node_pair[1].cal_mid_x(1))
        # 6.6.1: mid_y: global
        crt_feature_list.append(ref_node_pair[1].cal_mid_y(0))
        # 6.6.2: mid_y: block
        crt_feature_list.append(ref_node_pair[1].cal_mid_y(1))
        return crt_feature_list

    def get_all_features(self, ref_node_pair):
        crt_feature_list = []
        # 1.1: node_class_id
        node_class_id = self.node_class_list.index(ref_node_pair[1].node_class) if ref_node_pair[1].node_class in self.node_class_list else -1
        if node_class_id == -1:
            self.node_class_list.append(ref_node_pair[1].node_class)
            node_class_id = len(self.node_class_list) - 1
        crt_feature_list.append(node_class_id)
        # 1.2: clickable
        crt_feature_list.append(int(ref_node_pair[1].clickable))
        # 1.3: editable
        crt_feature_list.append(int(ref_node_pair[1].editable))
        # 2.1: path_strict_match
        node_describer = PathNodeDescriber(self.positive_ref_nodes, self.negative_ref_nodes)
        crt_feature_list.append(int(node_describer.match(ref_node_pair[0], ref_node_pair[1])))
        # 2.2: path_match_ratio
        path_match_raito = 0
        for positive_ref_node_pair in self.positive_ref_nodes:
            path_match_raito = max(path_match_raito, positive_ref_node_pair[1].cal_path_match_raito(ref_node_pair[1]))
        crt_feature_list.append(path_match_raito)
        # 3.1: text_match_state
        text_match_state = 2
        for positive_ref_node_pair in self.positive_ref_nodes:
            text_match_state = min(text_match_state, positive_ref_node_pair[1].get_text_match_state(ref_node_pair[1]))
        crt_feature_list.append(text_match_state)
        # 3.2: text_match_ratio
        text_match_ratio = 0
        for positive_ref_node_pair in self.positive_ref_nodes:
            text_match_ratio = max(text_match_ratio, positive_ref_node_pair[1].cal_text_match_raito(ref_node_pair[1]))
        crt_feature_list.append(text_match_ratio)
        # 4.1: content_match_state
        content_match_state = 2
        for positive_ref_node_pair in self.positive_ref_nodes:
            content_match_state = min(content_match_state, positive_ref_node_pair[1].cal_content_match_state(ref_node_pair[1]))
        crt_feature_list.append(content_match_state)
        # 4.2: content_match_ratio
        content_match_ratio = 2
        for positive_ref_node_pair in self.positive_ref_nodes:
            content_match_ratio = max(content_match_ratio, positive_ref_node_pair[1].cal_content_match_ratio(ref_node_pair[1]))
        crt_feature_list.append(content_match_ratio)
        # 5: resource_id
        resource_id_match = 0
        for positive_ref_node_pair in self.positive_ref_nodes:
            resource_id_match = max(resource_id_match, positive_ref_node_pair[1].check_resource_id(ref_node_pair[1]))
        crt_feature_list.append(resource_id_match)
        # 6.1.1: left: global
        crt_feature_list.append(ref_node_pair[1].cal_left(0))
        '''min_left_diff = 1<<30
        for positive_ref_node_pair in self.positive_ref_nodes:
            min_left_diff = min(
                min_left_diff, positive_ref_node_pair[1].cal_left_diff(ref_node_pair[1], 0))
        crt_featue_list.append(min_left_diff)'''
        # 6.1.2: left: block
        crt_feature_list.append(ref_node_pair[1].cal_left(1))
        '''min_left_diff = 1<<30
        for positive_ref_node_pair in self.positive_ref_nodes:
            min_left_diff = min(
                min_left_diff, positive_ref_node_pair[1].cal_left_diff(ref_node_pair[1], 1))
        crt_featue_list.append(min_left_diff)'''
        # 6.2.1: right: global
        crt_feature_list.append(ref_node_pair[1].cal_right(0))
        '''min_right_diff = 1<<30
        for positive_ref_node_pair in self.positive_ref_nodes:
            min_right_diff = min(
                min_right_diff, positve_ref_node_pair[1].cal_right_diff(ref_node_pair[1], 0))
        crt_featue_list.append(min_right_diff)'''
        # 6.2.2: right: block
        crt_feature_list.append(ref_node_pair[1].cal_right(1))
        '''min_right_diff = 1<<30
        for positive_ref_node_pair in self.positive_ref_nodes:
            min_right_diff = min(
                min_right_diff, positve_ref_node_pair[1].cal_right_diff(ref_node_pair[1], 1))
        crt_featue_list.append(min_right_diff)'''
        # 6.3.1: top: global
        crt_feature_list.append(ref_node_pair[1].cal_top(0))
        '''min_top_diff = 1<<30
        for positive_ref_node_pair in self.positive_ref_nodes:
            min_top_diff = min(
                min_top_diff, positve_ref_node_pair[1].cal_top_diff(ref_node_pair[1], 0))
        crt_featue_list.append(min_top_diff)'''
        # 6.3.2: top: block
        crt_feature_list.append(ref_node_pair[1].cal_top(1))
        '''min_top_diff = 1<<30
        for positive_ref_node_pair in self.positive_ref_nodes:
            min_top_diff = min(
                min_top_diff, positve_ref_node_pair[1].cal_top_diff(ref_node_pair[1], 1))
        crt_featue_list.append(min_top_diff)'''
        # 6.4.1: bottom: global
        crt_feature_list.append(ref_node_pair[1].cal_bottom(0))
        '''min_bottom_diff = 1<<30
        for positive_ref_node_pair in self.positive_ref_nodes:
            min_bottom_diff = min(
                min_bottom_diff, positve_ref_node_pair[1].cal_bottom_diff(ref_node_pair[1], 0))
        crt_featue_list.append(min_bottom_diff)'''
        # 6.4.2: bottom: block
        crt_feature_list.append(ref_node_pair[1].cal_bottom(1))
        '''min_bottom_diff = 1<<30
        for positive_ref_node_pair in self.positive_ref_nodes:
            min_bottom_diff = min(
                min_bottom_diff, positve_ref_node_pair[1].cal_bottom_diff(ref_node_pair[1], 1))
        crt_featue_list.append(min_bottom_diff)'''
        # 6.5.1: mid_x: global
        min_mid_x_diff = 1 << 30
        for positive_ref_node_pair in self.positive_ref_nodes:
            min_mid_x_diff = min(
                min_mid_x_diff, positive_ref_node_pair[1].cal_mid_x_diff(ref_node_pair[1], 0))
        crt_feature_list.append(min_mid_x_diff)
        # 6.5.2: mid_x: block
        min_mid_x_diff = 1 << 30
        for positive_ref_node_pair in self.positive_ref_nodes:
            min_mid_x_diff = min(
                min_mid_x_diff, positive_ref_node_pair[1].cal_mid_x_diff(ref_node_pair[1], 1))
        crt_feature_list.append(min_mid_x_diff)
        # 6.6.1: mid_y: global
        min_mid_y_diff = 1 << 30
        for positive_ref_node_pair in self.positive_ref_nodes:
            min_mid_y_diff = min(
                min_mid_y_diff, positive_ref_node_pair[1].cal_mid_y_diff(ref_node_pair[1], 0))
        crt_feature_list.append(min_mid_y_diff)
        # 6.6.2: mid_y: block
        min_mid_y_diff = 1 << 30
        for positive_ref_node_pair in self.positive_ref_nodes:
            min_mid_y_diff = min(
                min_mid_y_diff, positive_ref_node_pair[1].cal_mid_y_diff(ref_node_pair[1], 1))
        crt_feature_list.append(min_mid_y_diff)
        return crt_feature_list

    def train_model(self):
        self.X = self.positive_X + self.negative_X
        self.y = []
        for i in range(len(self.positive_X)):
            self.y.append(1)
        for i in range(len(self.negative_X)):
            self.y.append(0)
        for candidate_negative_node in self.candidate_negative_nodes:
            self.X.append(candidate_negative_node[1])
            self.y.append(0)
        print("positive: ",len(self.positive_X))
        print("negative: ",len(self.negative_X))
        print("candidate negative: ", len(self.candidate_negative_nodes))
        print(self.p_nodes)
        for i in range(len(self.X)):
            for j in range(len(self.X)):
                if self.X[i] == self.X[j] and self.y[i] != self.y[j]:
                    print(self.X[i])
                    print(i,j)
                    if i < len(self.positive_X):
                        print(self.positive_nodes[i])
                    if j >= len(self.positive_X)+len(self.negative_X):
                        print(self.candidate_negative_nodes[j-len(self.positive_X)-len(self.negative_X)])
                    quit()
        self.model = DecisionTreeClassifier(criterion='entropy',min_samples_split=2)
        self.model.fit(self.X, self.y)
        self.show_model()
        print("model updated.")

    def show_model(self):
        dot_data = tree.export_graphviz(self.model, out_file=None, feature_names=self.feature_name_list,
                                       filled=True, rounded=True, special_characters=True)
        graph = pydotplus.graph_from_dot_data(dot_data)
        graph.write_pdf('model.pdf')

    def find_node(self, crt_root):
        if len(self.positive_ref_nodes) == 0:
            return None
        nodes = []
        stack = [crt_root]
        while stack:
            node = stack.pop()
            nodes.append(node)
            for child in node.children:
                stack.append(child)
        X = []
        print("check:",crt_root.generate_all_text())
        print("y:",self.y)
        print("predict_y:",self.model.predict(self.X))
        for node in nodes:
            tmp_feature = self.get_all_features((crt_root,node))
            X.append(tmp_feature)
            if node.text == "你好。" or node.text == "111":
                print("crt_feature:",tmp_feature)
                print("positive_x[0]:",self.X[0])
                print("absolute_id same:",self.positive_ref_nodes[0][1].absolute_id == node.absolute_id)

        y = self.model.predict(X)
        for i in range(len(nodes)):
            if y[i] == 0:
                continue
            print("candidate node:", node.bound, node.depth)
            print("candidate node text:", node.generate_all_text())
        print(y)
        for i in range(len(nodes)):
            if (y[i] == 1):
                return nodes[i]
        return None

    def match(self, crt_root, check_node):
        X = [self.get_all_features((crt_root, node))]
        y = self.model.predict(X)
        return (y[0] == 1)

    def update(self, new_positive_ref_nodes=[], new_negative_ref_nodes=[], new_positive_nodes=[]):
        # ！！！注意：positive_ref_nodes和positive_nodes是不一样的，positive_ref_nodes是模板节点
        self.positive_ref_nodes += new_positive_ref_nodes
        self.negative_ref_nodes += new_negative_ref_nodes
        self.positive_nodes += new_positive_nodes
        for ref_node_pair in new_positive_ref_nodes:
            if ref_node_pair not in self.positive_nodes:
                self.positive_nodes.append(ref_node_pair)
        for ref_node_pair in new_positive_nodes:
            self.p_nodes.append(ref_node_pair[1])
        for ref_node_pair in new_negative_ref_nodes:
            self.n_nodes.append(ref_node_pair[1])
        if len(new_positive_ref_nodes) != 0:
            # 则需要全部重算
            self.recal_all_features_for_positive_nodes()
            self.recal_all_features_for_negative_ref_nodes()
            self.candidate_negative_nodes = self.predict_negative_nodes(
                self.positive_nodes)
        else:
            for ref_node_pair in new_positive_nodes:
                crt_feature_list = self.get_all_features(ref_node_pair)
                self.positive_X.append(crt_feature_list)
            for ref_node_pair in new_negative_ref_nodes:
                crt_feature_list = self.get_all_features(ref_node_pair)
                self.negative_X.append(crt_feature_list)
            # filter out positive and negative ref
            tmp_candidates = []
            for candidate_negative_node in self.candidate_negative_nodes:
                if candidate_negative_node[0] in self.p_nodes:
                    continue
                if candidate_negative_node[0] in self.n_nodes:
                    continue
                tmp_candidates.append(candidate_negative_node)
            self.candidate_negative_nodes = tmp_candidates + \
                self.predict_negative_nodes(new_positive_nodes)
        self.train_model()

    def predict_negative_nodes(self, positive_nodes):
        # 根据启发式算法，增加一些负例：到根的路径，非列表项兄弟节点，子树
        # 改成更激进的，同一个block以内除了自己以外都是负例
        res = []
        '''for ref_node_pair in positive_nodes:
            node = ref_node_pair[1].parent
            while node is not None:
                if (node not in self.n_nodes) and (node not in self.p_nodes):
                    res.append((node, self.get_all_features(
                        (node.findBlockNode(), node))))
                node = node.parent
            node = ref_node_pair[1]
            if node.findBlockNode() != node:  # 不是恰好是列表项
                node = node.parent
                if node is not None:
                    for child in node.children:
                        if (child not in self.n_nodes) and (child not in self.p_nodes):
                            res.append((child, self.get_all_features(
                                (child.findBlockNode(), child))))
            stack = [ref_node_pair[1]]
            while stack:
                node = stack.pop()
                if node != ref_node_pair[1]:
                    if (node not in self.n_nodes) and (node not in self.p_nodes):
                        res.append((node, self.get_all_features(
                            (node.findBlockNode(), node))))
                for child in node.children:
                    stack.append(child)'''
        for ref_node_pair in positive_nodes:
            print(ref_node_pair[0].generate_all_text(), ref_node_pair[1].generate_all_text())
            node = ref_node_pair[1].parent
            while node is not None:
                if (node not in self.n_nodes) and (node not in self.p_nodes):
                    res.append((node, self.get_all_features(
                        (node.findBlockNode(), node))))
                node = node.parent
            node = ref_node_pair[1]
            if node.findBlockNode() != node:  # 不是恰好是列表项
                node = node.parent
                if node is not None:
                    for child in node.children:
                        if (child not in self.n_nodes) and (child not in self.p_nodes):
                            res.append((child, self.get_all_features(
                                (child.findBlockNode(), child))))
            stack = [ref_node_pair[0]]
            while stack:
                node = stack.pop()
                if node != ref_node_pair[1]:
                    if (node not in self.n_nodes) and (node not in self.p_nodes) and (node != ref_node_pair[1]):
                        res.append((node, self.get_all_features(
                            (node.findBlockNode(), node))))
                for child in node.children:
                    stack.append(child)
        #print("res:",res)
        return res


if __name__ == '__main__':
    # page = PageInstance()
    # page.load_from_file("./save", "./data/page129.json")
    # root = page.ui_root
    # page_2 = PageInstance()
    # page_2.load_from_file("./save", "./data/page14.json")
    # root_2 = page_2.ui_root
    # stack = [root]
    # while stack:
    #     node = stack.pop()
    #     if node.text == "清华大学信息服务":
    #         break
    #     for child in node.children:
    #         stack.append(child)
    # # node = node.parent
    # print(node.node_class)
    # print(node.text)
    # describer = SpecialNodeDescriber([[node.findBlockNode(), node]], [])
    # # findnode = describer.find_node(node.parent.parent.parent.children[3])
    # # print(findnode.children[0].text)
    # findnode = describer.find_node(root_2)
    # print(findnode.node_class)
    # print(findnode.text)
    page = PageInstance()
    page.load_from_file("./save", "./data/page14.json")
    root = page.ui_root

    node = root.get_node_by_relative_id("android.widget.FrameLayout|0;android.widget.LinearLayout|0;android.widget.FrameLayout|0;android.widget.RelativeLayout|0;android.widget.FrameLayout|0;android.widget.FrameLayout|0;android.widget.LinearLayout|0;android.widget.FrameLayout|0;android.widget.RelativeLayout|0;android.widget.RelativeLayout|1;android.widget.FrameLayout|1;android.widget.LinearLayout|0;android.widget.FrameLayout|0;android.widget.HorizontalScrollView|0;android.widget.LinearLayout|1;android.widget.LinearLayout")
    print(node.node_class)
    print(node.text)
    describer = SpecialNodeDescriber([[node.findBlockNode(), node]], [])
    # findnode = describer.find_node(node.parent.parent.parent.children[3])
    # print(findnode.children[0].text)
    for i in range(1, 261):
        try:
            print(str(i)+" : ")
            page_2 = PageInstance()
            page_2.load_from_file("./save", "./data/page"+str(i)+".json")
            root_2 = page_2.ui_root
            findnode = describer.find_node(root_2)
            # if findnode:
            # print(findnode.get_id_relative_to(root_2))
        except:
            continue

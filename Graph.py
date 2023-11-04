import os
from matplotlib import pyplot as plt
import networkx as nx
import pickle

from src.utility import cal_similarity_one, sort_by_similarity, cal_embedding
from src.utility import process_action_info, simplify_ui_element


class Node:
    def __init__(self,  screen, g=None) -> None:
        self.graph = g
        self.screen = screen
        self.elements = list(
            map(simplify_ui_element, screen.semantic_info_half_warp))

    def __eq__(self, o: object) -> bool:
        return self.elements == o.elements

    def __hash__(self):
        return hash(tuple(self.elements))

    def query(self, query):
        result = sort_by_similarity(query, self.elements)
        result = sorted(result, key=lambda x: x[1], reverse=True)
        result = list(filter(lambda x: x[1] > 0.80, result))
        self.result = list(map(lambda x: x[0], result))
        return self.result


class Edge:
    def __init__(self,  action: str, text: str, node: str, g=None) -> None:
        self.graph = g
        self.action = action
        self.text = text
        self.node = node

    def __eq__(self, __value: object) -> bool:
        return self.action == __value.action

    def __hash__(self) -> int:
        return hash(self.action)


class UINavigationGraph:
    def __init__(self, file_path=None):
        self.graph = nx.DiGraph()
        self.file_path = os.path.join(
            os.path.dirname(__file__), file_path)

    def is_null(self):
        return self.graph.number_of_nodes() == 0

    def add_node(self, page: Node):
        """
        :param page: UI界面
        """
        node = self.find_node(page)
        if node is None:
            page.graph = self
            self.graph.add_node(page)
            self.save_to_pickle()  # 添加保存逻辑
            return page
        else:
            return node

    def add_edge(self, source_page: Node, target_page: Node, Edge: Edge):
        """
        添加有向边表示页面跳转关系。
        :param source_page: 起始界面
        :param target_page: 目标界面
        :param Edge: 边
        """
        e = self.find_edge_from_node(source_page, Edge)
        if e is None:
            Edge.graph = self
            Edge._from = source_page
            Edge._to = target_page
            self.graph.add_edge(source_page, target_page, edge=Edge)
            self.save_to_pickle()  # 添加保存逻辑
        else:
            return e

    def find_node(self, page: Node):
        """
        通过页面找到节点。
        :param page: 页面
        :return: 节点
        """
        for node in self.graph.nodes:
            if node == page:
                return node

    def find_node_to(self, page: Node, action: Edge):
        """
        通过起点和边找到终点。
        :param page: 页面
        :param action: 边
        :return: 终点
        """

    def find_shortest_road_to(self, source: Node, End: Node) -> list:
        """
        找到从source到End的最短路径。
        :param source: 起始节点
        :param End: 终止节点
        :return: 最短路径的操作序列
        """
        path = nx.shortest_path(self.graph, source, End)
        edges = []
        for i in range(len(path) - 1):
            node_from = path[i]
            node_to = path[i + 1]
            edge = self.graph.get_edge_data(node_from, node_to)['edge']
            edges.append(edge)
        return list(map(lambda x: process_action_info(x.action, x.text, x.node), edges))

    def find_neighbour_nodes(self, node: Node) -> list:
        """
        找到所有从node出发的的所有邻居节点
        :param node: 节点
        :return: 邻居节点
        """
        return self.graph.successors(node)

    def find_neighbour_edges(self, node: Node) -> list:
        """
        找到所有从node出发的的所有邻居边
        :param node: 节点
        :return: 邻居边
        """
        edges = self.graph.out_edges(node, data=True)
        return [data['edge'] for _, _, data in edges]

    def find_edge_from_node(self, node: Node, edge: Edge):
        """
        找到node节点的所有出发边当中与edge相同的边。
        """
        edges = self.find_neighbour_edges(node)
        for e in edges:
            if e == edge:
                return e

    def get_all_nodes(self):
        """
        获取所有节点
        :return: 所有节点
        """
        return self.graph.nodes

    def find_target_UI(self, query, similarity_threshold=0.80):
        # 创建一个列表，包含每个节点的元素及其对应的节点
        if self.graph.number_of_nodes() <= 1:
            return [], []

        text_to_ebd = [query, *[element for node in self.get_all_nodes()
                                for element in node.elements]]
        cal_embedding(text_to_ebd)

        element_node_pairs = [(element, node, cal_similarity_one(query, element))
                              for node in self.get_all_nodes() for element in node.elements]

        # 使用similarity对元素进行相似度排序

        sorted_elements = sorted(
            element_node_pairs, key=lambda x: x[2], reverse=True)

        # 筛选出相似度超过阈值的元素及其对应的节点
        filtered_pairs = list(
            filter(lambda x: x[2] > similarity_threshold, sorted_elements))

        # 使用字典来聚合结果
        aggregated_results = {}
        for element, node, score in filtered_pairs:
            if node not in aggregated_results:
                aggregated_results[node] = [element]
            else:
                aggregated_results[node].append(element)

        # 返回聚合后的结果
        return aggregated_results.keys(), aggregated_results.values()

    def save_to_pickle(self):
        """
        保存图到 Pickle 文件。
        """
        if not os.path.exists(os.path.dirname(self.file_path)):
            os.makedirs(os.path.dirname(self.file_path))
        with open(self.file_path, 'wb') as f:
            pickle.dump(self.graph, f)

    def load_from_pickle(self, file_path):
        """
        从 Pickle 文件加载图。
        : param file_path: 文件路径
        """
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                self.graph = pickle.load(f)
        else:
            print("No such file.")

    def merge_from_another_pickle(self, file_path_another: str):
        if os.path.exists(file_path_another):
            with open(file_path_another, "rb") as f:
                graph_another = pickle.load(f)

        for node in graph_another.nodes():
            if not self.graph.has_node(node):
                self.graph.add_node(node)

        for u, v, data in graph_another.edges(data=True):
            has_u = self.graph.has_node(u)
            has_v = self.graph.has_node(v)
            has_edge = self.graph.has_edge(u, v)
            if has_edge:
                continue
            if not has_u:
                self.graph.add_node(u)
            if not has_v:
                self.graph.add_node(v)
            self.graph.add_edge(u, v)

    def merge_from_other_pickles(self, file_path_others: list[str]):
        for file_path in file_path_others:
            self.merge_from_another_pickle(file_path)

    def visualize(self):
        """
        可视化图。
        """
        nx.draw(self.graph, with_labels=True)
        plt.show()

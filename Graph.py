import copy
import os
import random
from matplotlib import pyplot as plt
import networkx as nx
import pickle

from src.utility import GPT, cal_similarity_one, sort_by_similarity, cal_embedding
from src.utility import process_action_info, simplify_ui_element


def coverage(text1, text2):
    if isinstance(text1, str) and isinstance(text2, str):
        words1 = set(text1.split())
        words2 = set(text2.split())
    elif isinstance(text1, list) and isinstance(text2, list):
        words1 = set(text1)
        words2 = set(text2)

    common_words = words1.intersection(words2)

    return len(common_words) / max(len(words1), len(words2))


class Node:
    """UI node in the Graph, representing specific UI page

    Attributes:
        graph: Graph class, representing the navigation graph
        screen: Screen class, representing the UI page
        elements: list of UI elements in the page
    """

    def __init__(self,  screen, g=None) -> None:
        """Initialize the node with the screen and graph"""
        self.graph = g
        self.screen = screen
        self.elements = list(
            map(simplify_ui_element, screen.semantic_info_half_warp))

    def __eq__(self, o: object) -> bool:
        """Override the equal function to compare the elements of the node

        if the coverage of the elements of two nodes is larger than 0.7, then they are equal
        """
        return coverage(" ".join(self.elements), " ".join(o.elements)) >= 0.7

    def __hash__(self):
        """Override the hash function to hash the elements of the node"""
        if self is None:
            return hash(tuple([]))
        return hash(tuple(self.elements))

    def query(self, query):
        """Query the UI elements in this UI page with the query string
        """
        result = sort_by_similarity(query, self.elements)
        result = sorted(result, key=lambda x: x[1], reverse=True)
        result = list(filter(lambda x: x[1] > 0.80, result))
        self.result = list(map(lambda x: x[0], result))
        return self.result


class Edge:
    """
    Class for UI operations, representing the edge in the navigation graph.

    Attributes:
        graph: Graph class, representing the navigation graph
        action: str, representing the UI operation
        text: str, representing the text of the UI element
        node: str, representing the UI element
    """

    def __init__(self,  action: str, text: str, node: str, g=None) -> None:
        """Initialize the edge with the action, text and node"""
        self.graph = g
        self.action = action
        self.text = text
        self.node = node

    def __eq__(self, __value: object) -> bool:
        """Override the equal function to compare node of the edge

        If the node descriptions of two edges are the same, then they are equal
        """
        return self.node == __value.node

    def __hash__(self) -> int:
        return hash(self.node)


class UINavigationGraph:
    """ Class for navigation graph

    This class represents the navigation graph, which is a directed graph of UI pages.

    Attributes:
        graph: networkx.DiGraph, representing the navigation graph
        file_path: str, representing the path of the pickle file
    """

    def __init__(self, file_path=None):
        """Initialize the navigation graph with the pickle file path"""
        self.graph = nx.DiGraph()
        if file_path:
            self.file_path = os.path.join(
                os.path.dirname(__file__), file_path)

    def is_null(self):
        """Return whether the graph is null"""
        return self.graph.number_of_nodes() == 0

    def add_node(self, page: Node):
        """Add a UI page to the navigation graph

        First check whether the page is already in the graph, if not, add it to the graph.

        Args:
            page: Node class, representing the UI page
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
        """Add an edge to the navigation graph

        First check whether the edge is already in the graph, if not, add it to the graph.

        Args:
            source_page: Node class, representing the source UI page
            target_page: Node class, representing the target UI page
            Edge: Edge class, representing the UI operation
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
        """Find the UI page in the graph

        Return the UI page if it is in the graph, otherwise return None.

        Args:
            page: Node class, representing the UI page
        """
        for node in self.graph.nodes:
            if node == page:
                return node

    def find_shortest_road_to(self, source: Node, End: Node) -> list:
        """Find the shortest road from source to End

        Return the shortest road from source to End if it exists, otherwise return None.

        Args:
            source: Node class, representing the source UI page
            End: Node class, representing the target UI page
        """
        try:
            path = nx.shortest_path(self.graph, source, End)
        except:
            return None
        edges = []
        for i in range(len(path) - 1):
            node_from = path[i]
            node_to = path[i + 1]
            edge = self.graph.get_edge_data(node_from, node_to)['edge']
            edges.append(edge)
        return list(map(lambda x: process_action_info(x.action, x.text, x.node), edges))

    def find_neighbour_nodes(self, node: Node) -> list:
        """Return all the successors of the node"""
        return self.graph.successors(node)

    def find_neighbour_edges(self, node: Node) -> list:
        """Return all the edges between the node and its successors"""
        edges = []
        for u, v, data in self.graph.edges(data=True):
            if u == node:
                edges.append((u, v, data))

        return [data['edge'] for _, _, data in edges]

    def find_edge_from_node(self, node: Node, edge: Edge) -> Edge | None:
        """Find the edge from the node which is equal to the edge passed in"""
        edges = self.find_neighbour_edges(node)
        for e in edges:
            if e == edge:
                return e
        return None

    def get_all_nodes(self):
        """Get all the nodes in the graph"""
        return self.graph.nodes

    def get_all_children_successcor_nodes(self, node: Node):
        """Return all the successors of the node"""
        return nx.descendants(self.graph, node)

    def find_target_UI(self, query, refer_node=None, similarity_threshold=0.80):
        """Find the target UI page with the query string

        First find the UI page with the query string, then find the shortest road from the current UI page to the target UI page.

        Args:
            query: str, representing the query string
            refer_node: Node class, representing the current UI page
            similarity_threshold: float, representing the similarity threshold
        """
        if self.graph.number_of_nodes() <= 1:
            return [], []

        text_to_ebd = [query, *[element for node in self.get_all_children_successcor_nodes(refer_node)
                                for element in node.elements]]
        cal_embedding(text_to_ebd)

        element_node_pairs = [(element, node, cal_similarity_one(query, element))
                              for node in self.get_all_nodes() for element in node.elements]

        unique_pairs = {}
        for element, node, similarity in element_node_pairs:
            unique_pairs[element] = (element, node, similarity)

        element_node_pairs = list(unique_pairs.values())
        sorted_elements = sorted(
            element_node_pairs, key=lambda x: x[2], reverse=True)

        filtered_pairs = list(
            filter(lambda x: x[2], sorted_elements))[:10]

        aggregated_results = {}
        for element, node, score in filtered_pairs:
            if node not in aggregated_results:
                aggregated_results[node] = [element]
            else:
                aggregated_results[node].append(element)
        return aggregated_results.keys(), aggregated_results.values()

    def save_to_pickle(self):
        """Save Graph to pickle"""
        if not os.path.exists(os.path.dirname(self.file_path)):
            os.makedirs(os.path.dirname(self.file_path))
        with open(self.file_path, 'wb') as f:
            pickle.dump(self.graph, f)

    def load_from_pickle(self, file_path):
        """Load Graph from pickle"""
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                self.graph = pickle.load(f)
        else:
            print("No such file.")

    def merge_from_another_pickle(self, file_path_another: str):
        """Merge Graph from another pickle"""
        if os.path.exists(file_path_another):
            graph_another = UINavigationGraph()
            graph_another.load_from_pickle(file_path_another)

        node_mapping = {}

        for node in graph_another.get_all_nodes():
            ans = self.add_node(node)
            node_mapping[node] = ans

        for u, v, data in graph_another.graph.edges(data=True):
            u_mapped = node_mapping[u]
            v_mapped = node_mapping[v]

            self.add_edge(u_mapped, v_mapped, Edge=data['edge'])

    def find_similar_node(self, node):
        for n in self.graph.nodes():
            if n == node:
                return n

    def merge_from_other_pickles(self, file_path_others: list[str]):
        for file_path in file_path_others:
            self.merge_from_another_pickle(file_path)

    def visualize(self):
        """
        可视化图。每个label显示节点的元素。
        """
        nx.draw(self.graph, with_labels=True)
        plt.show()

    def merge_from_random(self, task_name="", k=1):
        g = UINavigationGraph("cache/random/Graph_"+str(k)+".pkl")
        cache_list = os.listdir("cache")
        cache_list = [l for l in cache_list if l !=
                      "Graph_"+task_name.replace(" ", "_")]
        random.shuffle(cache_list)

        for file in cache_list[:int(len(cache_list)*k*10//10)]:
            if file.startswith("Graph_"):
                print(file)
                g.merge_from_another_pickle(os.path.join("cache", file))
        g.save_to_pickle()
        print(g.graph.number_of_nodes())
        self.graph = copy.deepcopy(g.graph)
        self.file_path = copy.deepcopy(g.file_path)

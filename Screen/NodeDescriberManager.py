from multiprocessing.dummy import Manager
from Screen.NodeDescriber import *

ratio = 3.3


class NodeDescriberManager:
    def __init__(self, type="", fa_describer=None, model_node_id=""):
        self.model_node_id = model_node_id
        self.describer = SpecialNodeDescriber([], [])
        self.type = type
        self.fa_describer = fa_describer
        if fa_describer:
            self.fa_type = fa_describer.type
        else:
            self.fa_type = None
        self.children = []
        print("init")

    def update(self, ref_positive_nodes, ref_negative_nodes, positive_nodes):
        if ref_negative_nodes is not None:
            if len(ref_negative_nodes) > 0 and (not isinstance(self.describer, AutoNodeDescriber)):
                new_describer = AutoNodeDescriber(self.describer.positive_ref_nodes + ref_positive_nodes,
                                                  self.describer.negative_ref_nodes + ref_negative_nodes, self.describer.positive_nodes + positive_nodes)
                self.describer = new_describer
                print("update Auto_describer")
                print(self.describer.positive_ref_nodes)
                print(self.describer.negative_ref_nodes)
                print(self.describer.positive_nodes)

                '''if self.describer.tag == "AutoNodeDescriber":
                    print("candidate negative:")
                    for node in self.describer.candidate_negative_nodes:
                          print(node[0].generate_all_text())'''
                return
        self.describer.update(ref_positive_nodes,
                              ref_negative_nodes, positive_nodes)
        print("update")

    def update_children(self, child):
        self.children.append(child)

    def save_to_json(self, pageindex):
        data = {"type": self.type, "describer_type": self.describer.tag, "positive_ref": [],
                "negative_ref": [], "positive": [], "pageindex": pageindex}
        for item in self.describer.positive_ref_nodes:
            data["positive_ref"].append(
                {"page_id": item[1].page_id, "index": item[1].get_id_relative_to(item[1].get_root())})
        for item in self.describer.negative_ref_nodes:
            data["negative_ref"].append(
                {"page_id": item[1].page_id, "index": item[1].get_id_relative_to(item[1].get_root())})
        '''if self.describer.tang == "AutoNodeDescriber":
            for item in self.describer.candidate_negative_nodes:
                data["candidate_negative_nodes"].append(
                    {"page_id": item[0].page_id, "index": item[0].get_id_relative_to(item[0].get_root())})'''
        for item in self.describer.positive_nodes:
            data["positive"].append(
                {"page_id": item[1].page_id, "index": item[1].get_id_relative_to(item[1].get_root())})
        return json.dumps(data)

    def calculate(self, node):
        return self.describer.calculate(node)

    def find_node(self, crt_node):
        print(self.type)
        if self.type == "list":
            candidates = self.describer.find_node(crt_node)
            print(candidates)
            return candidates
        elif self.type == "Root":
            return []
            pass
        else:
            if self.fa_type == "list":
                blockroot = self.fa_describer.find_node(crt_node)
                candidates = []
                if blockroot is None:
                    return []
                for child in blockroot.children:
                    print("find")
                    tmp_node = self.describer.find_node(child)
                    if tmp_node is not None:
                        candidates.append(tmp_node)
                # global ratio
                # if self.describer.find_node(child) != None:
                #     candidates.append(
                #         {'x': self.describer.find_node(child).bound[0]/ratio,
                #          'y': self.describer.find_node(child).bound[1]/ratio,
                #          'w': (self.describer.find_node(child).bound[2]-self.describer.find_node(child).bound[0])/ratio,
                #          'h': (self.describer.find_node(child).bound[3]-self.describer.find_node(child).bound[1])/ratio})
            else:
                blocks = self.fa_describer.find_node(crt_node)
                candidates = []
                for block in blocks:
                    tmp_node = self.describer.find_node(block)
                    if tmp_node is not None:
                        candidates.append(tmp_node)
        return candidates

    def transfer_to_auto(self):
        # 出现相似度不能cover的情况，转成决策树方案
        # TODO:
        new_describer = AutoNodeDescriber(
            self.describer.positive_ref_nodes, self.describer.negative_ref_nodes)

        pass


if __name__ == '__main__':
    page = PageInstance()
    page.load_from_file("./save", "./data/page17.json")
    root = page.ui_root
    # stack = [root]
    # while stack:
    #     node = stack.pop()
    #     if node.resource_id == "com.tencent.mm:id/bzq":
    #         break
    #     for child in node.children:
    #         stack.append(child)
    # print(node.get_id_relative_to(root))
    node = root.get_node_by_relative_id(
        "android.widget.FrameLayout|0;android.widget.FrameLayout|0;android.widget.LinearLayout|0;android.widget.FrameLayout|0;android.widget.FrameLayout|0;android.view.ViewGroup")

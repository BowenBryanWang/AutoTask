
import copy


def mask(s):
    match s:
        case "com.tencent.mm:id/kd_":
            return "Tab"
        case "com.tencent.mm:id/iwg":
            return "Item"
        case "com.tencent.mm:id/grs":
            return "Dropdown menu"
        case "com.tencent.mm:id/bth":
            return "message"
        case "com.tencent.mm:id/g0":
            return "Go Back"
        case "com.tencent.mm:id/iwc":
            return "Function"
    return s


def transfer_2_html(semantic_nodes, relation: list[tuple]):
    html_components = []
    real_comp = []

    for node in semantic_nodes:
        if "TextView" in node.node_class:
            temp = node.generate_all_semantic_info()
            html_element = "<p class='{}' {}> {} </p>\n".format(
                mask(node.resource_id),
                "description='"+",".join(temp["content-desc"])+"'" if ",".join(
                    temp["content-desc"]) != "" else "",
                "".join(temp["text"]) if temp["text"] == temp["Major_text"] else temp["Major_text"][0] + "\n    " + "".join(["<p> " + i + " </p>\n    " for i in temp["text"][1:]])[:-5])
            html_components.append(html_element)
        elif "LinearLayout" in node.node_class:
            temp = node.generate_all_semantic_info()
            html_element = "<div id={} class='{}' {}> {} </div>\n".format(
                len(real_comp)+1,
                mask(node.resource_id),
                "description='"+",".join(temp["content-desc"])+"'" if ",".join(
                    temp["content-desc"]) != "" else "",
                "".join(temp["text"]) if temp["text"] == temp["Major_text"] else temp["Major_text"][0] + "\n    " + "".join(["<p> " + i + " </p>\n    " for i in temp["text"][1:]])[:-5])
            html_components.append(html_element)
            real_comp.append(html_element)
        elif "ImageView" in node.node_class or "RelativeLayout" in node.node_class or "FrameLayout" in node.node_class:
            temp = node.generate_all_semantic_info()
            print(temp)
            html_element = "<button id={} class='{}' {}> {} </button>\n".format(
                len(real_comp)+1,
                mask(node.resource_id),
                "description='"+",".join(temp["content-desc"])+"'" if ",".join(
                    temp["content-desc"]) != "" else "",
                "".join(temp["text"]) if temp["text"] == temp["Major_text"] else temp["Major_text"][0] +
                "\n    " +
                "".join(["<p> " + i + " </p>\n    " for i in temp["text"][1:]])[:-5]
            )
            html_components.append(html_element)
            real_comp.append(html_element)
        elif "Switch" in node.node_class:
            html_element = "<switch id={} class='{}' clickable> {} </switch>\n".format(
                len(real_comp)+1,
                mask(node.resource_id),
                "On" if node.checked else "Off",
            )
            html_components.append(html_element)
            real_comp.append(html_element)
        elif "CheckedTextView" in node.node_class or "CheckBox" in node.node_class:
            html_element = "<checkbox id={} class='{}' {}> {} </checkbox>\n".format(
                len(real_comp)+1,
                mask(node.resource_id),
                node.text,
                "On" if node.checked else "Off",

            )
            html_components.append(html_element)
            real_comp.append(html_element)
        else:
            temp = node.generate_all_semantic_info()
            print(temp)
            html_element = "<div id={} class='{}' {}> {} </div>\n".format(
                len(real_comp)+1,
                mask(node.resource_id),
                "description='"+",".join(temp["content-desc"])+"'" if ",".join(
                    temp["content-desc"]) != "" else "",
                "".join(temp["text"]) if temp["text"] == temp["Major_text"] else temp["Major_text"][0] + "\n    " + "".join(["<p> " + i + " </p>\n    " for i in temp["text"][1:]])[:-5])
            html_components.append(html_element)
            real_comp.append(html_element)

    my_list = copy.deepcopy(html_components)
    print(my_list)
    trans_relation = []
    for father, son in relation:
        index_father = semantic_nodes.index(father)
        index_son = semantic_nodes.index(son)
        trans_relation.append((index_father, index_son))
        last_index = html_components[index_father].rfind(" </")
        if last_index != -1 and not html_components[index_son].startswith("<p"):
            html_components[index_father] = html_components[index_father][:last_index] + "\n    " + \
                html_components[index_son] + " </" + \
                html_components[index_father][last_index + 3:]
    for father, son in relation:
        index_son = semantic_nodes.index(son)
        html_components[index_son] = ""
    html_components = [i for i in html_components if i != ""]
    return html_components, my_list, trans_relation


import copy

from page.WindowStructure import UINode


def mask(s):
    return s


def transfer_2_html(semantic_nodes: list[UINode], relation: list[tuple]):
    semantic_info_all_warp = []
    real_comp = []

    for node in semantic_nodes:
        if node.scrollable:
            temp = node.generate_all_semantic_info()
            html_element = "<scroll id={} class={} > </scroll>\n".format(
                len(real_comp)+1,
                node.node_class)
            semantic_info_all_warp.append(html_element)
            real_comp.append(html_element)
        elif (node.node_class == "android.widget.TextView" or ".TextView" in node.node_class) and not node.clickable:
            temp = node.generate_all_semantic_info()
            html_element = "<p class='{}' {} > {} </p>\n".format(
                mask(node.resource_id),
                "description='"+",".join(temp["content-desc"])+"'" if ",".join(
                    temp["content-desc"]) != "" else "",
                "".join(temp["text"]) if temp["text"] == temp["Major_text"] else temp["Major_text"][0] + "\n    " + "".join(["<p> " + i + " </p>\n    " for i in temp["text"][1:]])[:-5])
            semantic_info_all_warp.append(html_element)
        elif "LinearLayout" in node.node_class:
            temp = node.generate_all_semantic_info()
            html_element = "<div id={} class='{}' {} >  </div>\n".format(
                len(real_comp)+1,
                mask(node.resource_id),
                "description='"+",".join(temp["content-desc"])+"'" if ",".join(
                    temp["content-desc"]) != "" else "",
            )
            semantic_info_all_warp.append(html_element)
            real_comp.append(html_element)
        elif "ImageView" in node.node_class or "RelativeLayout" in node.node_class or "FrameLayout" in node.node_class or "Button" in node.node_class:
            temp = node.generate_all_semantic_info()
            print(temp)
            html_element = "<button id={} class='{}' {} > {} </button>\n".format(
                len(real_comp)+1,
                mask(node.resource_id),
                "description='"+",".join(temp["content-desc"])+"'" if ",".join(
                    temp["content-desc"]) != "" else "",
                "".join(temp["text"]) if temp["text"] == temp["Major_text"] else temp["Major_text"][0] +
                "\n    " +
                "".join(["<p> " + i + " </p>\n    " for i in temp["text"]
                        [1:]])[:-5] if node.children == [] else ""
            )
            semantic_info_all_warp.append(html_element)
            real_comp.append(html_element)
        elif "Switch" in node.node_class:
            html_element = "<switch id={} class='{}' clickable > {} </switch>\n".format(
                len(real_comp)+1,
                mask(node.resource_id),
                "On" if node.checked else "Off",
            )
            semantic_info_all_warp.append(html_element)
            real_comp.append(html_element)
        elif "CheckedTextView" in node.node_class or "CheckBox" in node.node_class:
            html_element = "<checkbox id={} class='{}' {} > {} </checkbox>\n".format(
                len(real_comp)+1,
                mask(node.resource_id),
                node.text,
                "On" if node.checked else "Off",

            )
            semantic_info_all_warp.append(html_element)
            real_comp.append(html_element)
        elif "EditText" in node.node_class or "AutoCompleteTextView" in node.node_class:
            temp = node.generate_all_semantic_info()
            if node.editable:
                html_element = "<input id={} class='{}' {} {} editable > {} </input>\n".format(
                    len(real_comp)+1,
                    mask(node.resource_id),
                    "description='"+",".join(temp["content-desc"])+"'" if ",".join(
                        temp["content-desc"]) != "" else "",
                    "enabled" if node.enabled else "Not enabled",
                    node.text
                )
            else:
                html_element = "<button id={} class='{}' {} {} clickable ineditable >  </button>\n".format(
                    len(real_comp)+1,
                    mask(node.resource_id),
                    "description='"+",".join(temp["content-desc"])+"'" if ",".join(
                        temp["content-desc"]) != "" else "",
                    "enabled" if node.enabled else "Not enabled",
                )
            semantic_info_all_warp.append(html_element)
            real_comp.append(html_element)
        else:
            temp = node.generate_all_semantic_info()
            print(temp)
            html_element = "<div id={} class='{}' {} {} {} > {} </div>\n".format(
                len(real_comp)+1,
                mask(node.resource_id),
                "description='" +
                ",".join(temp["content-desc"]) +
                "'" if ",".join(temp["content-desc"]) != "" else "",
                "enabled" if node.enabled else "not_enabled",
                "" if not node.checkable else (
                    'checked' if node.checked else 'not_checked'),
                "".join(temp["text"]) if temp["text"] == temp["Major_text"] else temp["Major_text"][0] +
                "\n    " +
                "".join(["<p> " + i + " </p>\n    " for i in temp["text"]
                        [1:]])[:-5] if node.children == [] else ""
            )
            semantic_info_all_warp.append(html_element)
            real_comp.append(html_element)

    semantic_info_no_warp = copy.deepcopy(semantic_info_all_warp)
    semantic_info_half_warp = copy.deepcopy(semantic_info_all_warp)
    print(semantic_info_no_warp)
    trans_relation = []
    flag_scroll = -1
    for father, _ in relation:
        if semantic_info_all_warp[father].startswith("<scroll"):
            flag_scroll = father
            break
    if flag_scroll != -1:
        scrolls = [i for i in relation if i[0] == flag_scroll]
        no_scrolls = [i for i in relation if i[0] != flag_scroll]
        relation = no_scrolls + scrolls
    to_remove = set()
    for index, (father, son) in enumerate(relation):
        if son in {i[0] for i in relation}:
            son_indexs = [i for i, x in enumerate(relation) if x[0] == son]
            son_sons = [relation[i][1] for i in son_indexs]
            for son_son in son_sons:
                if (father, son_son) in relation:
                    to_remove.add((father, son_son))
    for item in to_remove:
        relation.remove(item)

    for index_father, index_son in relation:
        trans_relation.append((index_father, index_son))
        last_index = semantic_info_all_warp[index_father].rfind(" </")
        if last_index != -1:
            semantic_info_all_warp[index_father] = semantic_info_all_warp[index_father][:last_index] + "\n    " + \
                semantic_info_all_warp[index_son] + " </" + \
                semantic_info_all_warp[index_father][last_index + 3:]

        if last_index != -1 and not semantic_info_half_warp[index_father].startswith("<scroll"):
            semantic_info_half_warp[index_father] = semantic_info_half_warp[index_father][:last_index] + "\n    " + \
                semantic_info_half_warp[index_son] + " </" + \
                semantic_info_half_warp[index_father][last_index + 3:]
            semantic_info_no_warp[index_father] = semantic_info_no_warp[index_father][:last_index] + "\n    " + \
                semantic_info_no_warp[index_son] + " </" + \
                semantic_info_no_warp[index_father][last_index + 3:]

    for father, son in relation:
        semantic_info_all_warp[son] = ""
        if semantic_info_half_warp[father].startswith("<scroll"):
            continue
        else:
            semantic_info_half_warp[son] = ""
    semantic_info_all_warp = [i for i in semantic_info_all_warp if i != ""]
    semantic_info_half_warp = [i for i in semantic_info_half_warp if i != ""]
    return semantic_info_all_warp, semantic_info_half_warp, semantic_info_no_warp, trans_relation

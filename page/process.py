
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


def transfer_2_html(semantic_nodes):
    html_components = []
    for node in semantic_nodes:
        if "LinearLayout" in node.node_class:
            html_element = "<div id={} class='{}' {}> {} </div>\n".format(
                len(html_components)+1,
                mask(node.resource_id),
                "description='"+",".join(node.generate_all_semantic_info()["content-desc"])+"'" if ",".join(
                    node.generate_all_semantic_info()["content-desc"]) != "" else "",
                ",".join(node.generate_all_semantic_info()["Major_text"]))

            html_components.append(html_element)
        elif "ImageView" in node.node_class or "RelativeLayout" in node.node_class or "FrameLayout" in node.node_class:
            html_element = "<button id={} class='{}' {}> {} </button>\n".format(
                len(html_components)+1,
                mask(node.resource_id),
                "description='"+",".join(node.generate_all_semantic_info()["content-desc"])+"'" if ",".join(
                    node.generate_all_semantic_info()["content-desc"]) != "" else "",
                ",".join(node.generate_all_semantic_info()["Major_text"]))

            html_components.append(html_element)
        elif "TextView" in node.node_class:

            html_element = "<p id={} class='{}' {}> {} </p>\n".format(
                len(html_components)+1,
                mask(node.resource_id),
                "description='"+",".join(node.generate_all_semantic_info()["content-desc"])+"'" if ",".join(
                    node.generate_all_semantic_info()["content-desc"]) != "" else "",
                ",".join(node.generate_all_semantic_info()["Major_text"]))
            html_components.append(html_element)
    return html_components

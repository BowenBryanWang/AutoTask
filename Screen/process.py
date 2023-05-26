from Screen.WindowStructure import UINode


def transfer_2_html(semantic_nodes: list(UINode)):
    html_components = []
    for node in semantic_nodes:
        if "LinearLayout" in node.node_class:
            html_element = "<div id={} class='{}' description='{}' type='ListItem'> {} </div>\n".format(
                len(html_components), node.resource_id.split("/")[-1], node.content_desc, node.text)
            html_components.append(html_element)
        elif "ImageView" in node.node_class or "RelativeLayout" in node.node_class:
            html_element = "<button id={} class='{}' description='{}' />\n".format(
                len(html_components), node.resource_id.split("/")[-1], node.content_desc)
            html_components.append(html_element)
        elif "TextView" in node.node_class:
            html_element = "<p id={} class='{}' description='{}'> {} </p>\n".format(
                len(html_components), node.resource_id.split("/")[-1], node.content_desc, node.text)
            html_components.append(html_element)
    return "".join(html_components)

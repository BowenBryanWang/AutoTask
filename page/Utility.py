# coding=utf-8
#  提供一些常用的接口
import os
import numpy as np
import page.WindowStructure
from queue import deque
from string import digits
import random

try:
    from typing import List, Optional, Dict, Callable, Tuple, Any, Deque, Set
except ImportError:
    pass

TOO_LONG_TEXT_TH = 10


def load_screen(save_path):
    android_root = os.environ['ANDROID_SDK_ROOT'] or '/Users/kinnplh/Library/Android/sdk/'
    os.system(os.path.join(android_root, 'platform-tools/adb') +
              ' shell screencap -p /sdcard/tmp.jpg')
    os.system(os.path.join(android_root, 'platform-tools/adb') +
              ' pull /sdcard/tmp.jpg %s' % save_path)


def getLongestSubstring_dp2(str1, str2):
    str1_len = len(str1)
    str2_len = len(str2)

    if (str1_len == 0) | (str2_len == 0):
        return -1

    start_pos1 = 0
    start_pos2 = 0
    longest = 0
    compares = 0

    m = np.zeros([2, str2_len], dtype=np.int)  # 只用两行就可以计算最长子串长度

    for j in range(str2_len):
        if str1[0] == str2[j]:
            compares += 1
            m[0][j] = 1
            if longest == 0:
                longest = 1
                start_pos1 = 0
                start_pos2 = j

    for i in range(1, str1_len):

        # 通过且运算计算出当前行和先前行
        cur = int((i & 1) == 1)
        pre = int((i & 1) == 0)

        if str1[i] == str2[0]:
            compares += 1
            m[cur][0] = 1
            if longest == 0:
                longest = 1
                start_pos1 = i
                start_pos2 = 0

        for j in range(1, str2_len):
            if str1[i] == str2[j]:
                compares += 1
                m[cur][j] = m[pre][j - 1] + 1
                if longest < m[cur][j]:
                    longest = m[cur][j]
                    start_pos1 = i - longest + 1
                    start_pos2 = j - longest + 1

    return longest


def is_str_similar(str1, str2):
    if len(str1) == 0 or len(str2) == 0:
        return False
    str_similarity = 2 * \
        getLongestSubstring_dp2(str1, str2) / float((len(str1) + len(str2)))
    print(str1, str2, 'similarity: ', str_similarity)
    return str_similarity > 0.5


def get_static_ui_diff(page_instance1, page_instance2):
    res = []
    if page_instance1.ui_root.node_class != page_instance2.ui_root.node_class:
        return [(page_instance1.ui_root, page_instance2.ui_root)]
    comp_ui_node(page_instance1.ui_root,
                 page_instance2.ui_root, res, only_static=True)
    return res


def get_global_ui_diff(page_instance1, page_instance2):
    res = []
    if page_instance1.ui_root.node_class != page_instance2.ui_root.node_class:
        return [(page_instance1.ui_root, page_instance2.ui_root)]
    comp_ui_node(page_instance1.ui_root,
                 page_instance2.ui_root, res, only_static=False)
    return res


def is_static_empty(node):
    # if not node.is_in_static_region:
    #     return True
    # if len(node.text) > 0 or (len(node.children) == 0 and len(node.content_desc) > 0):  # or node.clickable
    #     return False
    # for child in node.children:
    #     if not is_static_empty(child):
    #         return False
    return True


def is_two_nodes_sibling(node1, node2):
    # type: (WindowStructure.UINode, WindowStructure.UINode) -> bool
    # 如果两个节点根本不是在同一个页面中的话，那么这两个节点的公共父节点是找不到的
    if node1 is None or node2 is None:
        return False
    if node1 is node2:
        return True

    crt_node1 = node1
    crt_node2 = node2
    common_ancestor = None
    while crt_node1 is not None and crt_node2 is not None:
        if crt_node1.parent is crt_node2.parent:
            common_ancestor = crt_node1.parent
            break
        crt_node1 = crt_node1.parent
        crt_node2 = crt_node2.parent

    if common_ancestor is None:
        return False

    return node1.get_id_relative_to(crt_node1) == node2.get_id_relative_to(crt_node2)


def is_two_node_same(node1, node2):
    # type: (WindowStructure.UINode, WindowStructure.UINode) -> bool
    if node1 is None and node2 is None:
        return True
    elif node1 is None or node2 is None:
        return False
    else:
        if node1.page_instance.page_state.page is not node2.page_instance.page_state.page:
            return False
        return node1.absolute_dynamic_id == node2.absolute_dynamic_id


def get_instance_in_page_state_share_similar_dynamic(page_instance1, another_page_state2):
    # type: (WindowStructure.PageInstance, WindowStructure.PageState) -> WindowStructure.PageInstance

    for instance2 in another_page_state2.page_instances:
        is_first_level_dynamic_entrance_same = True

        dynamic_entrance_id_2 = [
            x.absolute_id for x in instance2.dynamic_entrance]
        for dynamic_entrance1 in page_instance1.dynamic_entrance:
            if not dynamic_entrance1.is_in_static_region:  # 只有在 static region 的 dynamic entrance 才是最外面一层的 entrance
                continue
            if dynamic_entrance1.absolute_id not in dynamic_entrance_id_2:  # 这里要求的是 id 完全一样  实际上是不成立的！
                is_first_level_dynamic_entrance_same = False
                break
        if not is_first_level_dynamic_entrance_same:
            continue

        # 对于每一个在 page_instance1 中出现的最外层的 dynamic entrance，在 instance2 中，都要找到对应的 dynamic entrance，
        # 并且这两个动态入口必须 share 至少一个结构相同的动态子区域
        has_one_entrance_no_similar_structure = False
        for dynamic_entrance1 in page_instance1.dynamic_entrance:
            if not dynamic_entrance1.is_in_static_region:
                continue
            dynamic_entrance2 = instance2.absolute_id_2_node.get(
                dynamic_entrance1.absolute_id, None)
            assert dynamic_entrance2 is not None
            is_similar_structure_found = False
            for dynamic_root1, dynamic_root2 in [(x, y) for x in dynamic_entrance1.children for y in
                                                 dynamic_entrance2.children]:
                if dynamic_root1.is_sub_tree_same(dynamic_root2,
                                                  is_text_diff_allowed=True,
                                                  stop_situation=lambda a,
                                                  b: a.is_dynamic_entrance or b.is_dynamic_entrance,
                                                  is_important_interaction_diff_allowed=False):
                    is_similar_structure_found = True
                    break
            if not is_similar_structure_found:
                has_one_entrance_no_similar_structure = True
                break
        if not has_one_entrance_no_similar_structure:
            return instance2
    return None


def get_ui_diff(page_instance1, page_instance2, is_force_static):
    # type: (WindowStructure.PageInstance, WindowStructure.PageInstance, bool) -> List[Tuple[Optional[WindowStructure.UINode], Optional[WindowStructure.UINode]]]
    # 这里对静态区域为空的情况进行特殊处理。静态区域不为空，则调用 get_static_ui_diff，否则，调用 get_global_ui_diff
    # todo 这里想要处理的是在静态区域全部为空的时候。在这种情况下，有可能所谓的动态区域全部都是静态区域，有可能实际的动态区域就是动态区域
    # 这种情况下，更重要的实际上是  到底是怎么样跳转到当前路径的
    # 对于两个静态区域为空的页面，比较进入他们页面的节点，如果是兄弟关系（存在公共父节点，并且到公共父节点的路径相似），那么就仅对静态区域进行比较；否则就对整体进行比较
    if (page_instance1.is_static_empty or page_instance2.is_static_empty) \
            and not is_force_static:  # todo 这个地方仅仅使用了第一个 Action  是不是有其他的处理方法
        #  如果进入这个页面的节点是相同的，那么就还是仅仅比较静态区域，否则就需要对整体的动态区域进行比较
        is_same_into_node_found = False
        for last_action1 in page_instance1.last_actions_into:
            for last_action2 in page_instance2.last_actions_into:
                if last_action1.type != last_action2.type:
                    continue
                if is_two_node_same(last_action1.node, last_action2.node):
                    is_same_into_node_found = True

                if is_same_into_node_found:
                    break
            if is_same_into_node_found:
                break

        if not is_same_into_node_found:
            return get_global_ui_diff(page_instance1, page_instance2)

    return get_static_ui_diff(page_instance1, page_instance2)


def is_two_str_same_without_num(s1, s2):
    # type: (str, str)->bool
    return filter(lambda x: not x.isdigit(), s1) == filter(lambda x: not x.isdigit(), s2)


def is_crt_info_match(node1, node2):
    # type: (UINode, UINode) -> bool
    # and node1.index == node2.index\
    # edit text 中的文本也要求一致吧  但是不知道会发生什么
    return node1.node_class == node2.node_class \
        and node1.editable == node2.editable \
        and (is_two_str_same_without_num(node1.text, node2.text) or node1.editable) \
        and node1.clickable == node2.clickable \
        and node1.enabled == node2.enabled \
        and is_two_str_same_without_num(node1.resource_id, node2.resource_id) \
        and node1.is_dynamic_entrance == node2.is_dynamic_entrance \
        and (len(node1.children) > 0 or len(node2.children) > 0
             or is_two_str_same_without_num(node1.content_desc, node2.content_desc))


def is_region_interactable(root):
    # type: (WindowStructure.UINode)->bool
    if root is None:
        return False
    if root.clickable or root.scrollable or root.editable or root.long_clickable:
        return True

    for c in root.children:
        if is_region_interactable(c):
            return True
    return False


def lcs_node(list1, list2):
    # type: (List[UINode], List[UINode]) -> List[Tuple[int, int]]
    l1 = len(list1)
    l2 = len(list2)
    dp = [[0 for _ in xrange(l2)] for _ in xrange(l1)]
    record = [[[] for _ in xrange(l2)] for _ in xrange(l1)]

    for index1, node1 in enumerate(list1):
        for index2, node2 in enumerate(list2):
            if is_crt_info_match(node1, node2):
                if index1 > 0 and index2 > 0:
                    dp[index1][index2] = dp[index1 - 1][index2 - 1] + 1
                    record[index1][index2].extend(
                        record[index1 - 1][index2 - 1])
                    record[index1][index2].append((index1, index2))
                else:
                    dp[index1][index2] = 1
                    record[index1][index2].append((index1, index2))
            else:
                if index1 != 0 and index2 != 0:
                    if dp[index1 - 1][index2] > dp[index1][index2 - 1]:
                        dp[index1][index2] = dp[index1 - 1][index2]
                        record[index1][index2].extend(
                            record[index1 - 1][index2])
                    else:
                        dp[index1][index2] = dp[index1][index2 - 1]
                        record[index1][index2].extend(
                            record[index1][index2 - 1])
                elif index1 != 0:
                    dp[index1][index2] = dp[index1 - 1][index2]
                    record[index1][index2].extend(record[index1 - 1][index2])
                elif index2 != 0:
                    dp[index1][index2] = dp[index1][index2 - 1]
                    record[index1][index2].extend(record[index1][index2 - 1])

    return record[l1 - 1][l2 - 1]


def comp_ui_node(ui_src, ui_des, res, only_static):
    # type: (WindowStructure.UINode, WindowStructure.UINode, List[Tuple[Optional[WindowStructure.UINode], Optional[WindowStructure.UINode]]], bool) -> None
    # 在 ui_src 和 ui_des 都是一样的前提下，对各个子节点进行比较
    if (ui_des.is_dynamic_entrance and ui_src.is_dynamic_entrance) and only_static:
        # 要求两个动态区域入口中的各个子区域，至少有一个是一样的

        if ui_src.resource_id is not None and ui_des.resource_id is not None:
            return

        # 两个动态区域入口的 info 是否匹配已经检验过了
        dynamic_region_roots1 = ui_src.children
        dynamic_region_roots2 = ui_des.children

        for root1, root2 in [(x, y) for x in dynamic_region_roots1 for y in dynamic_region_roots2]:
            if root1.is_sub_tree_same(root2, is_text_diff_allowed=True, is_important_interaction_diff_allowed=True,
                                      stop_situation=lambda a, b: a.is_dynamic_entrance and b.is_dynamic_entrance):
                return  # 说明出现了结构相同的节点 认为这两个动态区域入口是一样的

        # 没有找到结构相似的子节点
        res.append((ui_src, ui_des))
        return

    if len(ui_src.children) == len(ui_des.children):
        # 按照顺序比就可以了
        if len(ui_src.children) == 0:
            return
        # todo 这个地方也要最长公共子序列鸭
        src_child_list = ui_src.children[:]
        des_child_list = ui_des.children[:]
        lcs = lcs_node(src_child_list, des_child_list)
        for index1, index2 in lcs:
            comp_ui_node(src_child_list[index1],
                         des_child_list[index2], res, only_static)
            src_child_list[index1] = None
            des_child_list[index2] = None
        src_child_list = filter(lambda x: x is not None, src_child_list)
        des_child_list = filter(lambda x: x is not None, des_child_list)
        assert len(src_child_list) == len(des_child_list)
        for src_child, des_child in zip(src_child_list, des_child_list):
            res.append((src_child, des_child))

    elif len(ui_src.children) > len(ui_des.children):
        # 说明出现了节点减少的情况
        if len(ui_des.children) == 0:
            #  说明该节点的所有子节点都已经减少不见了
            for child_src in ui_src.children:
                res.append((child_src, None))
        else:
            # 以下的处理基于一个假设：所有剩余的子节点的相对位置不会发生改变（最长公共子序列）
            src_child_list = ui_src.children[:]  # type: List[Optional[UINode]]
            des_child_list = ui_des.children[:]  # type: List[Optional[UINode]]
            lcs = lcs_node(src_child_list, des_child_list)
            for index1, index2 in lcs:
                comp_ui_node(
                    src_child_list[index1], des_child_list[index2], res, only_static)
                src_child_list[index1] = None
                des_child_list[index2] = None
            src_child_list = filter(lambda x: x is not None, src_child_list)
            des_child_list = filter(lambda x: x is not None, des_child_list)
            assert len(src_child_list) > len(des_child_list)
            des_child_list.extend(None for _ in range(
                len(src_child_list) - len(des_child_list)))
            for src_child, des_child in zip(src_child_list, des_child_list):
                res.append((src_child, des_child))
    else:
        # 说明出现了节点增加的情况
        if len(ui_src.children) == 0:
            # 说明所有的子节点都是临时生成的
            for child_des in ui_des.children:
                res.append((None, child_des))
        else:
            # 同样的，以下的处理基于一个假设，之前的那些节点在节点增加之后得到的序列中的相对位置不会发生改变（最长公共子序列）
            src_child_list = ui_src.children[:]  # type: List[Optional[UINode]]
            des_child_list = ui_des.children[:]  # type: List[Optional[UINode]]
            lcs = lcs_node(src_child_list, des_child_list)
            for index1, index2 in lcs:
                comp_ui_node(
                    src_child_list[index1], des_child_list[index2], res, only_static)
                src_child_list[index1] = None
                des_child_list[index2] = None
            src_child_list = filter(lambda x: x is not None, src_child_list)
            des_child_list = filter(lambda x: x is not None, des_child_list)
            assert len(src_child_list) < len(des_child_list)
            src_child_list.extend(None for _ in range(
                len(des_child_list) - len(src_child_list)))
            for src_child, des_child in zip(src_child_list, des_child_list):
                res.append((src_child, des_child))


def get_interact_parent(node, working=True):
    # type: (WindowStructure.UINode, bool)->WindowStructure.UINode
    if not working:
        return node

    crt_node = node
    while crt_node is not None:
        if crt_node.clickable or crt_node.long_clickable:
            return crt_node
        crt_node = crt_node.parent
    return None


def cal_diff_area_ratio(instance1, instance2, is_force_static, use_parent_when_count_num=True):
    # type: (PageInstance, PageInstance, bool, bool) -> Tuple[float, float]
    # diff_info = get_static_ui_diff(instance1, instance2)
    diff_info = get_ui_diff(instance1, instance2, is_force_static)
    total_diff_area = 0
    for node1, node2 in diff_info:
        n1 = get_interact_parent(node1, False)  # 第二个参数表示这个函数不会生效，也就是直接使用原来的节点
        n2 = get_interact_parent(node2, False)  # 如果这个函数生效的话，同样也要处理重复计算的问题
        if n1 is None:
            n1 = node1
        if n2 is None:
            n2 = node2
        total_diff_area += \
            max(n1.get_area() if n1 is not None else 0,
                n2.get_area() if n2 is not None else 0)

    min_area = min(float(instance1.ui_root.get_area()),
                   float(instance2.ui_root.get_area()))
    if min_area == 0:
        print("small area strange")
        min_area = 0.1

    # 计算变化的节点的数量所占用的比例。如果是一个大的可交互节点中出现了很多小的节点，这些节点本身不可交互但是数量较多，要防止节点的重复计算
    counted_nodes1 = set()  # type: Set[WindowStructure.UINode]
    counted_nodes2 = set()  # type: Set[WindowStructure.UINode]

    total_diff_node_num = 0
    for node1, node2 in diff_info:
        # 如果子节点中没有可以操作的节点的话，必须找到祖先节点的
        n1 = get_interact_parent(
            node1, use_parent_when_count_num) if count_interactable_node_in_region(node1) == 0 else node1
        n2 = get_interact_parent(
            node2, use_parent_when_count_num) if count_interactable_node_in_region(node2) == 0 else node2
        if n1 is None:
            n1 = node1
        if n2 is None:
            n2 = node2

        if n1 not in counted_nodes1:
            counted_nodes1.add(n1)
        else:
            n1 = None

        if n2 not in counted_nodes2:
            counted_nodes2.add(n2)
        else:
            n2 = None

        total_diff_node_num += max(count_interactable_node_in_region(n1) if n1 is not None else 0,
                                   count_interactable_node_in_region(n2) if n2 is not None else 0)
    min_node_num = min(count_interactable_node_in_region(instance1.ui_root),
                       count_interactable_node_in_region(instance2.ui_root))

    return total_diff_area / min_area, total_diff_node_num / float(min_node_num + 0.1)


def cal_global_area_ratio(instance1, instance2):
    # type: (PageInstance, PageInstance) -> float
    # diff_info = get_static_ui_diff(instance1, instance2)
    diff_info = get_global_ui_diff(instance1, instance2)
    total_diff_area = 0
    for node1, node2 in diff_info:
        total_diff_area += \
            max(node1.get_area() if node1 is not None else 0,
                node2.get_area() if node2 is not None else 0)
    min_area = min(float(instance1.ui_root.get_area()),
                   float(instance2.ui_root.get_area()))
    if min_area == 0:
        print("small area strange")
        min_area = 0.1
    return total_diff_area / min_area


def is_two_region_same(root1, root2, allow_text_diff):
    # type: (UINode, UINode, bool) -> bool
    return root1.is_sub_tree_same(root2, allow_text_diff)


def can_instance1_skip_to_instance2(instance1, instance2):
    # type: (WindowStructure.PageInstance, WindowStructure.PageInstance) -> bool
    for last_action in instance1.last_actions_into:
        if (last_action.page_instance == instance2):
            return True
    return False


def can_intance1_scroll_to_instance2(instance1, instance2):
    # type: (WindowStructure.PageInstance, WindowStructure.PageInstance) -> bool
    for last_action in instance1.last_actions_into:
        if (last_action.page_instance == instance2) \
                and (last_action.type == WindowStructure.Action.SCROLL):
            return True
    return False


def is_two_instance_only_scroll_diff(instance1, instance2):
    # type: (WindowStructure.PageInstance, WindowStructure.PageInstance) -> bool
    # 判断其中一个instance是否能够通过滚动到达另一个instance
    return (can_intance1_scroll_to_instance2(instance1, instance2)) or \
           (can_intance1_scroll_to_instance2(instance2, instance1))


def get_last_no_scroll_action(instance):
    # type: (WindowStructure.PageInstance) -> WindowStructure.Action
    # 获得最后一个点击或者文本输入的操作。广度优先搜索

    q = deque()  # type: Deque[WindowStructure.PageInstance]  # |_________   <-
    instance_covered = set()  # type: Set[WindowStructure.PageInstance]
    q.append(instance)

    while len(q) > 0:
        crt_instance = q.popleft()
        for action in crt_instance.last_actions_into:
            if action.type != WindowStructure.Action.SCROLL:
                return action
            if action.page_instance not in instance_covered:
                q.append(action.page_instance)
                instance_covered.add(action.page_instance)
    assert False


def get_meaningful_nodes(instance):
    # type: (WindowStructure.PageInstance) -> List[WindowStructure.UINode]
    result = []  # type: List[WindowStructure.UINode]
    q = deque()  # type: Deque[WindowStructure.UINode]
    q.append(instance.ui_root)
    while len(q) > 0:
        crt_node = q.popleft()
        if len(crt_node.text) > 0 or len(
                crt_node.content_desc) > 0 or crt_node.clickable or crt_node.editable or crt_node.scrollable:
            result.append(crt_node)

        q.extend(crt_node.children)
    return result


def is_two_node_in_same_dynamic_region(node1, node2):
    # type: (WindowStructure.UINode, WindowStructure.UINode)->bool
    if node1.is_in_static_region or node2.is_in_static_region:
        print('both nodes are not dynamic')
        return False
    region_root1 = node1.get_nearest_entrance_root()  # type: WindowStructure.UINode
    region_root2 = node2.get_nearest_entrance_root()  # type: WindowStructure.UINode
    if region_root1.absolute_dynamic_id != region_root2.absolute_dynamic_id:
        return False
    return region_root1.is_sub_tree_same(region_root2, is_text_diff_allowed=False,
                                         stop_situation=lambda x, y: x.is_dynamic_entrance or y.is_dynamic_entrance)


def copy_list_of_list_of_action(list_of_list):
    # type: (List[List[WindowStructure.Action]]) -> List[List[WindowStructure.Action]]
    res = []
    for l in list_of_list:
        res.append(l[:])
    return res


def is_two_action_list_same(l1, l2):
    # type: (List[WindowStructure.Action], List[WindowStructure.Action]) -> bool
    if l1 is l2:
        return True
    if len(l1) != len(l2):
        return False

    for action1, action2 in zip(l1, l2):
        if not (action1 == action2):
            return False
    return True


def get_same_node_from_other_instance(node, other_instance):
    # type: (WindowStructure.UINode, WindowStructure.PageInstance) -> List[WindowStructure.UINode]
    # 由于动态区域的嵌套的情况，以及动态区域本身内部的数据就可能的重复的情况，这里返回的是一个列表
    # 首先还是要求这两个在同一个 page 内部吧
    res = []
    pages1, states1 = WindowStructure.Application.THIS.get_page_state_belong_to(
        node.page_instance)
    pages2, states2 = WindowStructure.Application.THIS.get_page_state_belong_to(
        other_instance)

    is_same_page_found = False
    for p1, p2 in [(x, y) for x in pages1 for y in pages2]:
        if p1 is p2:
            is_same_page_found = True
            break
    if not is_same_page_found:
        return []

    if node.parent is None:
        return [other_instance.ui_root]

    if node.is_in_static_region:
        if node.absolute_id in other_instance.absolute_id_2_node:
            # 仅要求子区域一致即可
            node_in_other = other_instance.absolute_id_2_node.get(
                node.absolute_id)
            if node.is_sub_tree_same(node_in_other, is_text_diff_allowed=False,
                                     stop_situation=lambda x, y: x.is_dynamic_entrance and y.is_dynamic_entrance):
                res.append(other_instance.absolute_id_2_node.get(
                    node.absolute_id))
        return res  # 在静态区域的节点只有可能有一get_same_node_from_other_instance个对应的节点

    dynamic_root = node.get_nearest_entrance_root()
    dynamic_entrance = dynamic_root.parent
    id_relative_to_dynamic_root = node.get_id_relative_to(dynamic_root)
    assert dynamic_entrance is not None

    dynamic_entrance_list_in_other_instance = get_same_node_from_other_instance(
        dynamic_entrance, other_instance)
    for dynamic_entrance_in_other in dynamic_entrance_list_in_other_instance:
        for dynamic_root_in_other in dynamic_entrance_in_other.children:
            # instance 数量太多的情况下 放宽对 text 的要求
            if not dynamic_root_in_other.is_sub_tree_same(dynamic_root,
                                                          is_text_diff_allowed=False,
                                                          stop_situation=lambda x,
                                                          y: x.is_dynamic_entrance or y.is_dynamic_entrance):
                continue
            node_in_other = dynamic_root_in_other.get_node_by_relative_id(
                id_relative_to_dynamic_root)
            assert node_in_other is not None
            res.append(node_in_other)

    if len(res) == 0 and (is_state_too_many_instances(states1[0])
                          or is_state_too_many_instances(states2[0])):
        # 只有在严格要求文本找不到的前提下才会放宽要求
        for dynamic_entrance_in_other in dynamic_entrance_list_in_other_instance:
            for dynamic_root_in_other in dynamic_entrance_in_other.children:
                # instance 数量太多的情况下 放宽对 text 的要求
                if not dynamic_root_in_other.is_sub_tree_same(dynamic_root,
                                                              is_text_diff_allowed=True,
                                                              stop_situation=lambda x,
                                                              y: x.is_dynamic_entrance or y.is_dynamic_entrance):
                    continue
                node_in_other = dynamic_root_in_other.get_node_by_relative_id(
                    id_relative_to_dynamic_root)
                assert node_in_other is not None
                res.append(node_in_other)

    if len(res) == 0 and (len(states1[0].page_instances) > 20
                          or len(states2[0].page_instances) > 20):
        # 只要 id 匹配就可以了
        node_in_other = other_instance.absolute_id_2_node.get(
            node.absolute_id, None)
        if node_in_other is not None:
            res.append(node_in_other)

    return res


def get_root_from_node(node_in_tree):
    # type: (WindowStructure.UINode)->WindowStructure.UINode
    crt_node = node_in_tree
    while True:
        if crt_node.parent is None:
            return crt_node
        crt_node = crt_node.parent


back_texts = ['关闭', '清空', '返回', '返回上一级', '返回上一页', '返回上一层级',
              '转到上一级', '取消', '转到上一页', '转到上一层级', '离开', 'Navigate up']


def is_backward_button(node):
    # type: (WindowStructure.UINode)->bool
    return (node.all_text.strip() in back_texts or node.all_content.strip() in back_texts) and node.clickable


def is_backward_action(action):
    # type: (WindowStructure.Action) -> bool
    # 判断行动是不是具有返回特征的，包括全局返回、界面上的返回按钮、向前滚动
    if action is None:
        return True

    if action.type == WindowStructure.Action.GLOBAL_BACK:
        return True
    elif action.type == WindowStructure.Action.CLICK:
        # 检查是不是点击了返回按钮
        if action.node.all_text.strip() in back_texts or action.node.all_content.strip() in back_texts:
            return True
    elif action.type == WindowStructure.Action.SCROLL:
        return False
    return False


def get_all_possible_next_instance_with_action_from_one_instance(page_instance, used_jump_edge):
    all_possible_next_action = {}
    # type: Set[WindowStructure.PageInstance]
    all_possible_next_instance = set()
    pages_belong_to, states_belong_to = WindowStructure.Application.THIS.get_page_state_belong_to(
        page_instance)
    if len(pages_belong_to) == 0 or len(states_belong_to) == 0:
        return all_possible_next_action, all_possible_next_instance

    # for page_belong_to in pages_belong_to:
    #     for similar_state in page_belong_to.page_states:
    #         for similar_instance in similar_state.page_instances[:min(10, len(similar_state.page_instances))]:

    # 考虑到这里已经有点击事件的迁移了，没有必要进行重复工作
    similar_instance = page_instance
    q = deque()  # type: Deque[WindowStructure.UINode]
    q.append(similar_instance.ui_root)

    while len(q) > 0:
        crt_focus_node = q.popleft()  # 这里的 focus node 实际上是在其他页面上的
        similar_node_list = get_same_node_from_other_instance(
            crt_focus_node, page_instance)
        if len(similar_node_list) == 0:
            continue

        q.extend(crt_focus_node.children)
        for action_type, action_results in crt_focus_node.action_type_to_action_result.items():
            for node_in_crt_page in similar_node_list:
                crt_action_id = (similar_instance.page_state.page, node_in_crt_page.absolute_id, action_type[0],
                                 action_type[1])  # 这里显然要用节点在当前页面中的 id，因为我们最终是会在当前页面中去寻找的
                if crt_action_id in used_jump_edge:
                    continue

                res_to_add = list(
                    filter(lambda x: not x.is_inferred, action_results))
                if len(res_to_add) == 0:
                    res_to_add = action_results

                for action_result in res_to_add:  # 有不是推测出来的，就使用不是推测出来的数据
                    if action_result.action_target is not None and action_result.action_target not in all_possible_next_instance:

                        if crt_action_id not in all_possible_next_action:
                            all_possible_next_action[crt_action_id] = set()
                        all_possible_next_action[crt_action_id].add(
                            action_result.action_target)
                        all_possible_next_instance.add(
                            action_result.action_target)  # 不允许多个到达同一个 instance。同一个 instance 是可以"再进入"的，但是，允许在 instance 中再进行相同的操作

    return all_possible_next_action, all_possible_next_instance


def is_action_info_back(info):
    # type: (Tuple[WindowStructure.Page, str, int, Any])->bool
    page, absolute_id, action_type, action_attr = info
    if action_type == WindowStructure.Action.GLOBAL_BACK:
        return True
    if action_type == WindowStructure.Action.CLICK:
        # 判断按钮是不是一个返回按钮
        example_instance = page.page_states[0].page_instances[0]
        node = example_instance.ui_root.get_node_by_relative_id(absolute_id)
        if node is None or (not is_backward_button(node)):
            return False
        else:
            return True

    return False


# 当一个 state 中的 instance 数量是 10 及以上的时候，可以对 back 进行推测
INSTANCE_NUM_WHEN_CAN_INFER_BACK = 10


def is_state_too_many_instances(page_state):
    # type: (WindowStructure.PageState)->bool
    if page_state is None:
        return False

    if hasattr(page_state, 'has_too_many_instance') and page_state.has_too_many_instance:
        return True
    else:
        page_state.has_too_many_instance = False

    # 已经得到 back 信息的 instance 达到一定的数量
    if len(page_state.page_instances) < INSTANCE_NUM_WHEN_CAN_INFER_BACK:
        return False

    # 考虑到 global back 的优先性，只要考虑global back 的数据是不是已经拿到就可以了
    count_instance_has_actual_back_res = 0
    for instance in page_state.page_instances:
        if (WindowStructure.Action.GLOBAL_BACK, None) in instance.ui_root.action_type_to_action_result \
                and len(instance.ui_root.action_type_to_action_result[(WindowStructure.Action.GLOBAL_BACK, None)]):
            for res in instance.ui_root.action_type_to_action_result[(WindowStructure.Action.GLOBAL_BACK, None)]:
                if not res.is_inferred:
                    count_instance_has_actual_back_res += 1
                    break
    page_state.has_too_many_instance = count_instance_has_actual_back_res >= INSTANCE_NUM_WHEN_CAN_INFER_BACK
    return page_state.has_too_many_instance


def count_interactable_node_in_region(node):
    # type: (WindowStructure.UINode)->int
    # 计算子节点中有多少可以交互的按钮
    if node is None:
        return 0
    res = 0
    if node.clickable or node.editable or node.scrollable or node.long_clickable:
        res += 1
    if 'WebView' in node.node_class:
        res += 10  # 说明不做限制

    for c in node.children:
        res += count_interactable_node_in_region(c)
    return res


def try_new_rule_res(crawler):
    # type: (Crawler.AppSpider)->None
    # 测试在新的条件之下页面之间相似度判断的性质
    all_instance_list = []  # type: List[List[WindowStructure.PageInstance]]

    for page in crawler.app.pages:
        crt_list = []  # type: List[WindowStructure.PageInstance]
        for state in page.page_states:
            for instance in state.page_instances:
                crt_list.append(instance)
        all_instance_list.append(crt_list)

    for page_index1, instance_list1 in enumerate(all_instance_list):
        for page_index2, instance_list2 in enumerate(all_instance_list):
            if page_index2 < page_index1:
                continue

            print(page_index1, page_index2)
            for instance1, instance2 in [(x, y) for x in instance_list1 for y in instance_list2]:
                if instance1.activity_name is not None and instance2.activity_name is not None \
                        and not is_two_str_same_without_num(instance1.activity_name, instance2.activity_name):
                    continue

                diff_ratio, diff_num_ratio = cal_diff_area_ratio(
                    instance1, instance2, False)
                if diff_ratio <= 0.5 and diff_num_ratio < 0.5 and page_index1 == page_index2:
                    continue
                if (diff_ratio > 0.5 or diff_num_ratio >= 0.5) and page_index1 != page_index2:
                    continue

                print('changed!!!')
                cal_diff_area_ratio(instance1, instance2, False)


def count_node_num(root):
    # type: (WindowStructure.UINode)->int
    if root is None:
        return 0
    res = 1
    for c in root.children:
        res += count_node_num(c)
    return res


def random_long(n=13):
    res = ""
    for i in range(n):
        id = int(random()*10)
        res += char(id+48)
    return int(res)


def get_common_fix(text1, text2):
    # 公共前缀+公共后缀的长度
    len = 0
    i = 0
    max_len = min(len(text1), len(text2))
    while i < max_len:
        if text1[i] == text2[i]:
            len += 1
        else:
            break
        i += 1
    for j in range(max_len-1, i, -1):
        if text1[j] == text2[j]:
            len += 1
        else:
            break
    return float(len)*1.0/len(text1)


def get_common_length(text1, text2):
    l1 = len(text1)
    l2 = len(text2)
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
            if text1[i] == text2[j]:
                tmp += 1
            F[i][j] = max(F[i][j], tmp)
    matched_ratio = float(F[l1-1][l2-1])*1.0/l1
    return matched_ratio

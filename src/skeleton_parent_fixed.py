import pandas as pd
import os

def skeleton_parent_fixed(swc_path):
    """
    修复SWC文件:
    1. 修复根节点
    2. 修复节点遍历顺序
    3. 修复节点类型
    修复后的文件直接覆盖原始SWC文件。

    参数:
        swc_path (str): 输入的SWC文件路径
    """
    # 读取SWC文件
    data = pd.read_csv(swc_path, sep=' ', comment='#', header=None)
    data.columns = ['PointNo', 'Label', 'X', 'Y', 'Z', 'Radius', 'Parent']

    data.loc[(data['Parent'] == -1), 'Label'] = 6

    # 找到叶子节点（Label=6）作为初始叶子节点
    leaf_indices = data[data['Label'] == 6].index

    # 确定根节点：Y值最小的叶子节点作为根节点，其他变为叶子节点
    leaf_nodes = data.loc[leaf_indices]
    root_candidate = leaf_nodes.loc[leaf_nodes['Y'].idxmin()]
    root_index = root_candidate.name  # 根节点索引

    # 更新标签：将多余的根节点改为叶子节点
    data.loc[data['Label'] == 1, 'Label'] = 6  # 全部改为叶子节点
    data.at[root_index, 'Label'] = 1  # 设置真正的根节点为Label=1

    # 找到根节点 (Label == 1)
    root_node = data[data['Label'] == 1].iloc[0]

    # 初始化遍历结果存储结构
    path = []

    # 遍历节点，从根节点开始
    current_node = root_node
    visited_nodes = set()  # 用于检测重复节点

    while True:
        # 存储当前节点的 PointNo 和 Parent
        path.append((int(current_node['PointNo']), int(current_node['Parent'])))
        visited_nodes.add(int(current_node['PointNo']))

        # 检查是否终止遍历
        if current_node['Parent'] == -1 or int(current_node['Parent']) in visited_nodes:
            break  # 到达根节点或检测到循环，结束

        # 查找父节点
        parent_node = data[data['PointNo'] == current_node['Parent']]
        if parent_node.empty:
            break  # 若父节点不存在，结束遍历
        current_node = parent_node.iloc[0]

    # 修改Parent值（保持节点顺序，仅更新Parent字段）
    new_path = []
    for i, (point_no, parent) in enumerate(path):
        if i == 0:
            new_path.append((point_no, -1))  # 根节点的Parent设为-1
        else:
            new_path.append((point_no, new_path[i - 1][0]))  # Parent设为前一个节点的PointNo

    # 将反转后的Parent值写入原始SWC文件
    for point_no, new_parent in new_path:
        data.loc[data['PointNo'] == point_no, 'Parent'] = new_parent

    # 初始化正确骨架列表和断枝列表
    correct_skeleton = []
    broken_branches = []

    # 遍历所有的节点
    for index, node in data.iterrows():
        if node['Label'] == 6:  # 叶子节点
            current_node = node
            path = []

            # 从叶子节点开始遍历父节点直到遇到父节点为 -1 停止
            while current_node['Parent'] != -1:
                path.append(current_node)
                parent_node = data[data['PointNo'] == current_node['Parent']]
                if parent_node.empty:
                    break
                current_node = parent_node.iloc[0]

            # 判断结束节点是否为根节点 (Label == 1)
            if current_node['Label'] == 1:  # 根节点
                correct_skeleton.extend([n['PointNo'] for n in path] + [current_node['PointNo']])  # 加入根节点
            else:  # 不是根节点，存入断枝列表
                broken_branches.extend([n['PointNo'] for n in path] + [current_node['PointNo']])  # 加入当前节点

    # 处理既不是正确骨架也不是断枝的节点（找出没有子节点的节点，将其类型更改为叶子节点）
    for index, node in data.iterrows():
        if node['PointNo'] not in correct_skeleton and node['PointNo'] not in broken_branches:
            # 查找当前节点的子节点
            child_nodes = data[data['Parent'] == node['PointNo']]

            # 如果当前节点没有子节点，则标记为叶子节点
            if child_nodes.empty:
                data.loc[data['PointNo'] == node['PointNo'], 'Label'] = 6  # 叶子节点

    # 保存修复后的数据，覆盖原始SWC文件
    with open(swc_path, 'w') as f:
        f.write("# SWC format file\n")
        f.write("# PointNo Label X Y Z Radius Parent\n")
        f.write("# Labels:\n")
        f.write("# 0 = undefined, 1 = root point, 5 = fork point, 6 = end point\n")
        data.to_csv(f, sep=' ', header=False, index=False, na_rep='None', float_format='%.6f')



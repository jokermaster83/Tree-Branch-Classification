import pandas as pd
import numpy as np
import os


def keypoints_swc(swc_path, swc_keypoints_path):
    """
    对SWC文件进行处,将节点类型为5和6的节点的Parent替换为其最后一个节点的PointNo。
    处理后的文件直接覆盖原始SWC文件。

    参数:
        swc_path (str): 输入的SWC文件路径
    """
    # 读取SWC文件
    data = pd.read_csv(swc_path, sep=' ', comment='#', header=None)
    data.columns = ['PointNo', 'Label', 'X', 'Y', 'Z', 'Radius', 'Parent']

    # 将指定列转换为整数类型
    data['PointNo'] = data['PointNo'].astype(int)
    data['Label'] = data['Label'].astype(int)
    data['Parent'] = data['Parent'].astype(int)

    def build_branch_lists(start_point_no):
        """构建链表，为替换父节点做准备"""
        chain = []
        current_point_no = start_point_no

        # 在原始文件中查找当前节点
        current_node = data[data['PointNo'] == current_point_no]
        current_node = current_node.iloc[0]
        
        # 将当前节点加入链中
        chain.append((int(current_node['PointNo']), int(current_node['Parent']), int(current_node['Label'])))

        # 更新当前节点为其父节点
        current_point_no = int(current_node['Parent'])

        while True:
            # 在原始文件中查找当前节点
            current_node = data[data['PointNo'] == current_point_no]
            if current_node.empty:
                chain = []
                return chain
            current_node = current_node.iloc[0]
            
            # 将当前节点加入链中
            chain.append((int(current_node['PointNo']), int(current_node['Parent']), int(current_node['Label'])))

            # 更新当前节点为其父节点
            current_point_no = int(current_node['Parent'])

            # 如果当前节点的Label为5或1，结束循环
            if current_node['Label'] == 5 or current_node['Label'] == 1:
                break
            # 如果当前节点的Parent为-1或Label为6，删除该链表并返回空值
            if current_node['Parent'] == -1 and current_node['Label'] == 6:
                chain = []
                return chain

        
        return chain

    # 将节点类型为5和6的全部节点放入新列表中
    key_nodes = data[data["Label"].isin([1,5,6])]["PointNo"].tolist()


    # 遍历所有PointNo
    for point_no in key_nodes:
        current_chain = []

        point_no_label = data.loc[data['PointNo'] == point_no, 'Label'].values[0]

        if point_no_label == 1:
            data.loc[data['PointNo'] == point_no, 'Parent'] = -1
            continue
        
        # 获取从当前PointNo开始的链
        current_chain = build_branch_lists(point_no)
        
        # 如果链表为空，跳过此节点
        if not current_chain:
            data = data[data['PointNo'] != point_no]
            continue
        
        # 获取链中最后一个节点的PointNo
        last_node_point_no = current_chain[-1][0]
        
        # 将最后一个节点的PointNo作为当前节点的Parent
        data.loc[data['PointNo'] == point_no, 'Parent'] = last_node_point_no


    # 筛选出Label不为0的节点
    filtered_data = data[data['Label'] != 0]

    # 分别按照节点类型和PointNo进行排序
    sorted_data = filtered_data.sort_values(by=['Label', 'PointNo'])

    # 去除Parent与PointNo相等的节点
    sorted_data = sorted_data[~(sorted_data['Parent'] == sorted_data['PointNo'])]


    new_point_no_map = {old: new for new, old in enumerate(sorted_data['PointNo'], start=0)}

    # Apply the new mapping to PointNo and Parent columns
    sorted_data['PointNo'] = sorted_data['PointNo'].map(new_point_no_map)
    sorted_data['Parent'] = sorted_data['Parent'].map(lambda x: new_point_no_map.get(x, 0))


    # 保存修复后的SWC文件
    with open(swc_keypoints_path, 'w') as f:
        f.write("# SWC format file\n")
        f.write("# PointNo Label X Y Z Radius Parent\n")
        f.write("# Labels:\n")
        f.write("# 0 = undefined, 1 = root point, 5 = fork point, 6 = end point\n")
        sorted_data.to_csv(f, sep=' ', header=False, index=False, na_rep='None')
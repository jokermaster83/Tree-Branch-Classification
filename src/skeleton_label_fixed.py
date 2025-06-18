import pandas as pd

def skeleton_label_fixed(swc_path):
    """
    修复SWC文件的节点标签:
    1. 读取SWC文件。
    2. 修复节点标签：
       - Label为1的节点(根节点）保持不变。
       - 没有子节点的为6(叶子节点）。
       - 只有一个子节点的为0(普通节点）。
       - 有两个子节点的为5(分叉节点）。
    3. 保存修复后的SWC文件(覆盖原文件)。

    Args:
        swc_path (str): SWC文件路径。
    """
    # 读取SWC文件
    data = pd.read_csv(swc_path, sep=' ', comment='#', header=None)
    data.columns = ['PointNo', 'Label', 'X', 'Y', 'Z', 'Radius', 'Parent']
    data['PointNo'] = data['PointNo'].astype(int)
    data['Label'] = data['Label'].astype(int)
    data['Parent'] = data['Parent'].astype(int)

    # 初始化子节点计数
    children_count = {point_no: 0 for point_no in data['PointNo']}

    # 统计每个节点的子节点数量
    for parent in data['Parent']:
        if parent != -1:
            children_count[parent] += 1

    # 修复节点标签
    for index, node in data.iterrows():
        if node['Label'] == 1:  # 根节点
            continue

        parent_count = children_count[node['PointNo']]

        if parent_count == 0:
            data.at[index, 'Label'] = 6  # 叶子节点
        elif parent_count == 1:
            data.at[index, 'Label'] = 0  # 普通节点
        elif parent_count == 2:
            data.at[index, 'Label'] = 5  # 分叉节点

    # 保存修复后的SWC文件
    with open(swc_path, 'w') as f:
        f.write("# SWC format file\n")
        f.write("# PointNo Label X Y Z Radius Parent\n")
        f.write("# Labels:\n")
        f.write("# 0 = undefined, 1 = root point, 5 = fork point, 6 = end point\n")
        data.to_csv(f, sep=' ', header=False, index=False, na_rep='None', float_format='%.6f')

    print(f"文件 {swc_path} 标签值已修复！")

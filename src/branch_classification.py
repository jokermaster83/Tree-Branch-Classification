import math
import open3d as o3d
import pandas as pd
import numpy as np


def branch_classification(swc_path, output_ply_path):

    def build_chains_from_fork(fork_node_id):
        """1、从分叉节点(fork_node_id)构建多条链表,直到遇到关键节点(Label != 0)"""
        chains = []  # 存储多条链表
        
        # 获取分叉节点的所有子节点
        children = data[data['Parent'] == fork_node_id]
        
        # # 确保分叉节点有两个子节点
        # if len(children) != 2:
        #     raise ValueError("分叉节点必须有且只有两个子节点")
        
        # 对于每个子节点，分别构建链表
        for _, child in children.iterrows():
            chain = [fork_node_id]  # 初始化链表并将分叉节点加入链表
            current_node_id = child['PointNo']  # 当前子节点的ID
            
            # 从当前子节点开始遍历，直到遇到关键节点
            while True:
                # 获取当前节点的子节点
                children_of_current = data[data['Parent'] == current_node_id]
                
                # 如果没有子节点或当前节点本身是关键节点，停止遍历
                if len(children_of_current) == 0 or data.loc[data['PointNo'] == current_node_id, 'Label'].iloc[0] != 0:
                    chain.append(current_node_id)  # 将当前节点加入链表
                    break
                
                # 加入当前节点到链表
                chain.append(current_node_id)
                
                # 获取下一个子节点
                next_node = children_of_current.iloc[0]  # 假设每个节点只有一个子节点
                current_node_id = next_node['PointNo']
                
                # 如果下一个子节点是关键节点，停止遍历
                if data.loc[data['PointNo'] == current_node_id, 'Label'].iloc[0] != 0:
                    chain.append(current_node_id)  # 将关键节点加入链表
                    break
            
            # 将该链表添加到chains中
            chains.append(chain)

        return chains



    def build_chain(start_node_id):
        """2、构建从start_node_id开始直到下一个关键节点(Label != 0)的节点链表"""
        chain = []  # 存储遍历过程中所有的节点
        current_node_id = start_node_id
        
        # 确保起始节点是关键节点（Label != 0）
        if data.loc[data['PointNo'] == start_node_id, 'Label'].iloc[0] == 0:
            raise ValueError("起始节点必须是关键节点 (Label != 0)")

        # 从起始节点开始，按父节点→子节点的顺序遍历
        while True:
            chain.append(current_node_id)
            
            # 获取当前节点的子节点
            children = data[data['Parent'] == current_node_id]
            if len(children) == 0:
                break
            
            # 获取下一个子节点
            next_node = children.iloc[0]  # 取第一个子节点
            current_node_id = next_node['PointNo']
            
            # 如果遇到一个关键节点（Label != 0），则停止遍历
            if data.loc[data['PointNo'] == current_node_id, 'Label'].iloc[0] != 0:
                chain.append(current_node_id)  # 将结束节点加入链表
                break

        return chain


    def process_short_chain(sub_chains, level):
        """3、链表长度小于等于10时,将其子链表加入各级别列表中"""
        if level == 1:
            for sub_chain in sub_chains:
                is_fork_node = point_label_map[sub_chain[-1]] == 5
                if is_fork_node:
                    # 处理一级枝链表
                    first_branch.append(sub_chain)
                else:
                    # 加入二级枝链表
                    second_branch.append(sub_chain)
        elif level == 2:
            for sub_chain in sub_chains:
                is_fork_node = point_label_map[sub_chain[-1]] == 5
                if is_fork_node:
                    # 处理二级枝链表
                    second_branch.append(sub_chain)
                else:
                    # 加入三级枝链表
                    third_branch.append(sub_chain)
        elif level == 3:
            for sub_chain in sub_chains:
                is_fork_node = point_label_map[sub_chain[-1]] == 5
                if is_fork_node:
                    # 处理三级枝链表
                    third_branch.append(sub_chain)
                else:
                    # 加入四级枝链表
                    fourth_branch.append(sub_chain)

    def process_angle_chains(chain, sub_chains, level):
        if level == 1:
            if len(sub_chains) == 2:
                # 获取当前链表chain的方向向量
                chain_vector = calculate_vector(data, chain)
                
                # 获取两个子链表的方向向量
                sub_chain1_vector = calculate_vector(data, sub_chains[0])
                sub_chain2_vector = calculate_vector(data, sub_chains[1])
                
                # 计算chain与两个子链表的夹角
                theta1 = calculate_angle(chain_vector, sub_chain1_vector)
                theta2 = calculate_angle(chain_vector, sub_chain2_vector)
                
                # 获取两个子链表的末尾节点的标签
                sub_chain1_label = data.loc[data['PointNo'] == sub_chains[0][-1], 'Label'].iloc[0] == 5
                sub_chain2_label = data.loc[data['PointNo'] == sub_chains[1][-1], 'Label'].iloc[0] == 5

                    # 判断夹角值
                if theta1 > 31 and theta2 > 31:
                    # 如果θ1和θ2都大于15度，两个子链表都加入二级枝
                    second_branch.extend(sub_chains)
                else:
                    # 如果夹角值小于15度，夹角更小的加入一级枝，较大的加入二级枝
                    if theta1 < theta2:
                        if sub_chain1_label:
                            first_branch.append(sub_chains[0])  # 夹角更小的加入一级枝
                            second_branch.append(sub_chains[1])
                        else:
                            second_branch.extend(sub_chains)
                            
                    else:
                        if sub_chain2_label:
                            first_branch.append(sub_chains[1])  # 夹角更小的加入一级枝
                            second_branch.append(sub_chains[0]) 
                        else:
                            second_branch.extend(sub_chains)
            elif len(sub_chains) == 3:
                # 获取当前链表chain的方向向量
                chain_vector = calculate_vector(data, chain)
                
                # 获取三个子链表的方向向量
                sub_chain1_vector = calculate_vector(data, sub_chains[0])
                sub_chain2_vector = calculate_vector(data, sub_chains[1])
                sub_chain3_vector = calculate_vector(data, sub_chains[2])
                
                # 计算chain与三个子链表的夹角
                theta1 = calculate_angle(chain_vector, sub_chain1_vector)
                theta2 = calculate_angle(chain_vector, sub_chain2_vector)
                theta3 = calculate_angle(chain_vector, sub_chain3_vector)
                theta_min = min(theta1, theta2, theta3)
                
                # 获取两个子链表的末尾节点的标签
                sub_chain1_label = data.loc[data['PointNo'] == sub_chains[0][-1], 'Label'].iloc[0] == 5
                sub_chain2_label = data.loc[data['PointNo'] == sub_chains[1][-1], 'Label'].iloc[0] == 5
                sub_chain3_label = data.loc[data['PointNo'] == sub_chains[2][-1], 'Label'].iloc[0] == 5

                    # 判断夹角值
                if theta1 > 31 and theta2 > 31 and theta3 > 31:
                    # 如果都大于31度，三个子链表都加入二级枝
                    second_branch.extend(sub_chains)
                else:
                    # 如果夹角值小于15度，夹角更小的加入一级枝，较大的加入二级枝
                    if theta1 == theta_min:
                        if sub_chain1_label:
                            first_branch.append(sub_chains[0])  # 夹角更小的加入一级枝
                            second_branch.append(sub_chains[1])
                            second_branch.append(sub_chains[2])
                        else:
                            second_branch.extend(sub_chains)  
                    elif theta2 == theta_min:
                        if sub_chain2_label:
                            first_branch.append(sub_chains[1])  # 夹角更小的加入一级枝
                            second_branch.append(sub_chains[0])
                            second_branch.append(sub_chains[2]) 
                        else:
                            second_branch.extend(sub_chains)
                    else:
                        if sub_chain3_label:
                            first_branch.append(sub_chains[2])  # 夹角更小的加入一级枝
                            second_branch.append(sub_chains[1])
                            second_branch.append(sub_chains[0]) 
                        else:
                            second_branch.extend(sub_chains)
            elif len(sub_chains) == 1:
                first_branch.extend(sub_chains)

        elif level == 2:
            if len(sub_chains) == 2:
                # 获取当前链表chain的方向向量
                chain_vector = calculate_vector(data, chain)
                
                # 获取两个子链表的方向向量
                sub_chain1_vector = calculate_vector(data, sub_chains[0])
                sub_chain2_vector = calculate_vector(data, sub_chains[1])
                
                # 计算chain与两个子链表的夹角
                theta1 = calculate_angle(chain_vector, sub_chain1_vector)
                theta2 = calculate_angle(chain_vector, sub_chain2_vector)
                
                # 获取两个子链表的末尾节点的标签
                sub_chain1_label = data.loc[data['PointNo'] == sub_chains[0][-1], 'Label'].iloc[0] == 5
                sub_chain2_label = data.loc[data['PointNo'] == sub_chains[1][-1], 'Label'].iloc[0] == 5

                    # 判断夹角值
                if theta1 > 31 and theta2 > 31:
                    # 如果θ1和θ2都大于15度，两个子链表都加入二级枝
                    third_branch.extend(sub_chains)
                else:
                    # 如果夹角值小于15度，夹角更小的加入一级枝，较大的加入二级枝
                    if theta1 < theta2:
                        if sub_chain1_label:
                            second_branch.append(sub_chains[0])  # 夹角更小的加入一级枝
                            third_branch.append(sub_chains[1])
                        else:
                            third_branch.extend(sub_chains)
                            
                    else:
                        if sub_chain2_label:
                            second_branch.append(sub_chains[1])  # 夹角更小的加入一级枝
                            third_branch.append(sub_chains[0]) 
                        else:
                            third_branch.extend(sub_chains)
            elif len(sub_chains) == 3:
                # 获取当前链表chain的方向向量
                chain_vector = calculate_vector(data, chain)
                
                # 获取三个子链表的方向向量
                sub_chain1_vector = calculate_vector(data, sub_chains[0])
                sub_chain2_vector = calculate_vector(data, sub_chains[1])
                sub_chain3_vector = calculate_vector(data, sub_chains[2])
                
                # 计算chain与三个子链表的夹角
                theta1 = calculate_angle(chain_vector, sub_chain1_vector)
                theta2 = calculate_angle(chain_vector, sub_chain2_vector)
                theta3 = calculate_angle(chain_vector, sub_chain3_vector)
                theta_min = min(theta1, theta2, theta3)
                
                # 获取两个子链表的末尾节点的标签
                sub_chain1_label = data.loc[data['PointNo'] == sub_chains[0][-1], 'Label'].iloc[0] == 5
                sub_chain2_label = data.loc[data['PointNo'] == sub_chains[1][-1], 'Label'].iloc[0] == 5
                sub_chain3_label = data.loc[data['PointNo'] == sub_chains[2][-1], 'Label'].iloc[0] == 5

                    # 判断夹角值
                if theta1 > 31 and theta2 > 31 and theta3 > 31:
                    # 如果都大于31度，三个子链表都加入二级枝
                    third_branch.extend(sub_chains)
                else:
                    # 如果夹角值小于15度，夹角更小的加入一级枝，较大的加入二级枝
                    if theta1 == theta_min:
                        if sub_chain1_label:
                            second_branch.append(sub_chains[0])  # 夹角更小的加入一级枝
                            third_branch.append(sub_chains[1])
                            third_branch.append(sub_chains[2])
                        else:
                            third_branch.extend(sub_chains)  
                    elif theta2 == theta_min:
                        if sub_chain2_label:
                            second_branch.append(sub_chains[1])  # 夹角更小的加入一级枝
                            third_branch.append(sub_chains[0])
                            third_branch.append(sub_chains[2]) 
                        else:
                            third_branch.extend(sub_chains)
                    else:
                        if sub_chain2_label:
                            second_branch.append(sub_chains[2])  # 夹角更小的加入一级枝
                            third_branch.append(sub_chains[1])
                            third_branch.append(sub_chains[0]) 
                        else:
                            third_branch.extend(sub_chains)
            elif len(sub_chains) == 1:
                second_branch.extend(sub_chains)
        elif level == 3:
            if len(sub_chains) == 2:
                # 获取当前链表chain的方向向量
                chain_vector = calculate_vector(data, chain)
                
                # 获取两个子链表的方向向量
                sub_chain1_vector = calculate_vector(data, sub_chains[0])
                sub_chain2_vector = calculate_vector(data, sub_chains[1])
                
                # 计算chain与两个子链表的夹角
                theta1 = calculate_angle(chain_vector, sub_chain1_vector)
                theta2 = calculate_angle(chain_vector, sub_chain2_vector)
                
                # 获取两个子链表的末尾节点的标签
                sub_chain1_label = data.loc[data['PointNo'] == sub_chains[0][-1], 'Label'].iloc[0] == 5
                sub_chain2_label = data.loc[data['PointNo'] == sub_chains[1][-1], 'Label'].iloc[0] == 5

                    # 判断夹角值
                if theta1 > 31 and theta2 > 31:
                    # 如果θ1和θ2都大于15度，两个子链表都加入二级枝
                    fourth_branch.extend(sub_chains)
                else:
                    # 如果夹角值小于15度，夹角更小的加入一级枝，较大的加入二级枝
                    if theta1 < theta2:
                        if sub_chain1_label:
                            third_branch.append(sub_chains[0])  # 夹角更小的加入一级枝
                            fourth_branch.append(sub_chains[1])
                        else:
                            fourth_branch.extend(sub_chains)
                            
                    else:
                        if sub_chain2_label:
                            third_branch.append(sub_chains[1])  # 夹角更小的加入一级枝
                            fourth_branch.append(sub_chains[0]) 
                        else:
                            fourth_branch.extend(sub_chains)
            elif len(sub_chains) == 3:
                # 获取当前链表chain的方向向量
                chain_vector = calculate_vector(data, chain)
                
                # 获取三个子链表的方向向量
                sub_chain1_vector = calculate_vector(data, sub_chains[0])
                sub_chain2_vector = calculate_vector(data, sub_chains[1])
                sub_chain3_vector = calculate_vector(data, sub_chains[2])
                
                # 计算chain与三个子链表的夹角
                theta1 = calculate_angle(chain_vector, sub_chain1_vector)
                theta2 = calculate_angle(chain_vector, sub_chain2_vector)
                theta3 = calculate_angle(chain_vector, sub_chain3_vector)
                theta_min = min(theta1, theta2, theta3)
                
                # 获取两个子链表的末尾节点的标签
                sub_chain1_label = data.loc[data['PointNo'] == sub_chains[0][-1], 'Label'].iloc[0] == 5
                sub_chain2_label = data.loc[data['PointNo'] == sub_chains[1][-1], 'Label'].iloc[0] == 5
                sub_chain3_label = data.loc[data['PointNo'] == sub_chains[2][-1], 'Label'].iloc[0] == 5

                    # 判断夹角值
                if theta1 > 31 and theta2 > 31 and theta3 > 31:
                    # 如果都大于31度，三个子链表都加入二级枝
                    fourth_branch.extend(sub_chains)
                else:
                    # 如果夹角值小于15度，夹角更小的加入一级枝，较大的加入二级枝
                    if theta1 == theta_min:
                        if sub_chain1_label:
                            third_branch.append(sub_chains[0])  # 夹角更小的加入一级枝
                            fourth_branch.append(sub_chains[1])
                            fourth_branch.append(sub_chains[2])
                        else:
                            fourth_branch.extend(sub_chains)  
                    elif theta2 == theta_min:
                        if sub_chain2_label:
                            third_branch.append(sub_chains[1])  # 夹角更小的加入一级枝
                            fourth_branch.append(sub_chains[0])
                            fourth_branch.append(sub_chains[2]) 
                        else:
                            fourth_branch.extend(sub_chains)
                    else:
                        if sub_chain2_label:
                            third_branch.append(sub_chains[2])  # 夹角更小的加入一级枝
                            fourth_branch.append(sub_chains[1])
                            fourth_branch.append(sub_chains[0]) 
                        else:
                            fourth_branch.extend(sub_chains)
            elif len(sub_chains) == 1:
                third_branch.extend(sub_chains)

    def process_new_chains(chains, level):
        # 6、初始构建各级别树枝列表
        if level == 1:
            for chain in chains:
                # 如果该链表已在二级枝中，跳过处理
                if chain in second_branch:
                    continue
                
                # 获取子链表
                sub_chains = get_fork(chain[-1])
                # process_angle_chains(chain, sub_chains, level=1)
                all_forks = all(
                    data.loc[data['PointNo'] == sub_chain[-1], 'Label'].iloc[0] == 5
                    for sub_chain in sub_chains
                )
                if all_forks:
                    process_angle_chains(chain, sub_chains, level=1)
                else:
                    process_short_chain(sub_chains, level=1)

                # 递归处理子分叉链表，增加深度
                process_new_chains(sub_chains, 1)
        elif level == 2:
            for chain in chains:
                # 如果该链表已在三级枝中，跳过处理
                if chain in third_branch:
                    continue
                
                # 获取子链表
                sub_chains = get_fork(chain[-1])
                # process_angle_chains(chain, sub_chains, level=2)
                all_forks = all(
                    data.loc[data['PointNo'] == sub_chain[-1], 'Label'].iloc[0] == 5
                    for sub_chain in sub_chains
                )
                if all_forks:
                    process_angle_chains(chain, sub_chains, level=2)
                else:
                    process_short_chain(sub_chains, level=2)

                # 递归处理子分叉链表，增加深度
                process_new_chains(sub_chains, 2)
        elif level == 3:
            for chain in chains:
                # 如果该链表已在四级枝中，跳过处理
                if chain in fourth_branch:
                    continue
                
                # 获取子链表
                sub_chains = get_fork(chain[-1])
                # process_angle_chains(chain, sub_chains, level=3)
                all_forks = all(
                    data.loc[data['PointNo'] == sub_chain[-1], 'Label'].iloc[0] == 5
                    for sub_chain in sub_chains
                )
                if all_forks:
                    process_angle_chains(chain, sub_chains, level=3)
                else:
                    process_short_chain(sub_chains, level=3)

                # 递归处理子分叉链表，增加深度
                process_new_chains(sub_chains, 3)

    def process_chains(chains, level, max_depth, current_depth=1):
        # 6、初始构建各级别树枝列表
        if level == 1:
            for chain in chains:
                # 如果该链表已在二级枝中，跳过处理
                if chain in second_branch:
                    continue
                
                # 获取子链表
                sub_chains = get_fork(chain[-1])

                # 前两轮根据链表长度处理短链表或长链表
                if current_depth <= 2:
                    if len(chain) <= max_depth:
                        process_short_chain(sub_chains, level=1)
                    else:
                        all_forks = all(
                            data.loc[data['PointNo'] == sub_chain[-1], 'Label'].iloc[0] == 5
                            for sub_chain in sub_chains
                        )
                        if all_forks:
                            process_angle_chains(chain, sub_chains, level=1)
                        else:
                            process_short_chain(sub_chains, level=1)
                else:
                    # 从第三轮开始，使用角度判断
                    process_angle_chains(chain, sub_chains, level=1)

                # 递归处理子分叉链表，增加深度
                process_chains(sub_chains, 1, 10, current_depth + 1)
        elif level == 2:
            for chain in chains:
                # 如果该链表已在三级枝中，跳过处理
                if chain in third_branch:
                    continue
                # 如果该链表末尾节点为叶子节点，跳过处理
                is_leaf_node = data.loc[data['PointNo'] == chain[-1], 'Label'].iloc[0] == 6
                if is_leaf_node:
                    continue

                # 获取子链表
                sub_chains = get_fork(chain[-1])
                if current_depth <= 2:
                    process_short_chain(sub_chains, level=2)
                else:
                    if len(sub_chains) == 1:
                        sub_chain = build_chain(chain[-1])
                        second_branch.append(sub_chain)
                    elif len(sub_chains) == 2:
                        all_forks = all(
                            data.loc[data['PointNo'] == sub_chain[-1], 'Label'].iloc[0] == 5
                            for sub_chain in sub_chains
                        )
                        if all_forks:
                            process_angle_chains(chain, sub_chains, level=2)
                        else:
                            process_short_chain(sub_chains, level=2)
                    elif len(sub_chains) == 3:
                        process_short_chain(sub_chains, level=2)

                # 递归处理子分叉链表，增加深度
                process_chains(sub_chains, 2, max_depth, current_depth + 1)

        elif level == 3:
            for chain in chains:
                # 如果该链表已在三级枝中，跳过处理
                if chain in fourth_branch:
                    continue
                # 如果该链表末尾节点为叶子节点，跳过处理
                is_leaf_node = data.loc[data['PointNo'] == chain[-1], 'Label'].iloc[0] == 6
                if is_leaf_node:
                    continue

                # 获取子链表
                sub_chains = get_fork(chain[-1])
                if current_depth <= 2:
                    process_short_chain(sub_chains, level=3)
                else:
                    if len(sub_chains) == 1:
                        sub_chain = build_chain(chain[-1])
                        third_branch.append(sub_chain)
                    elif len(sub_chains) == 2:
                        all_forks = all(
                            data.loc[data['PointNo'] == sub_chain[-1], 'Label'].iloc[0] == 5
                            for sub_chain in sub_chains
                        )
                        if all_forks:
                            process_angle_chains(chain, sub_chains, level=3)
                        else:
                            process_short_chain(sub_chains, level=3)
                    elif len(sub_chains) == 3:
                        process_short_chain(sub_chains, level=3)

                # 递归处理子分叉链表，增加深度
                process_chains(sub_chains, 3, max_depth, current_depth + 1)



    def calculate_unit_vector(point1, point2):
        """计算两点之间的单位方向向量"""
        vector = np.array(point2) - np.array(point1)
        norm = np.linalg.norm(vector)
        
        # 如果是零向量，返回None表示零向量，不参与后续计算
        if norm == 0:
            return None  # 返回None表示零向量
        
        return vector / norm


    def calculate_vector(data, chain):
        """
        使用加权方向计算链表方向
        参数:
            chain: 链表点的索引列表（可能是浮点数）
            data: 点云数据(Pandas DataFrame)
        返回:
            weighted_vector: 归一化的加权方向向量
        """

        # 确保 chain 中的索引是整数
        chain = [int(idx) for idx in chain]

        # 检查链表长度是否足够
        if len(chain) < 2:
            # 如果链表长度不足，退化为首尾点方向
            return calculate_unit_vector(data.loc[chain[0], ['X', 'Y', 'Z']].values,
                                        data.loc[chain[-1], ['X', 'Y', 'Z']].values)

        vectors = []
        weights = []

        for i in range(len(chain) - 1):
            # 提取当前段的两个点坐标
            point1 = data.loc[chain[i], ['X', 'Y', 'Z']].values
            point2 = data.loc[chain[i + 1], ['X', 'Y', 'Z']].values

            # 计算当前段的方向向量
            vec = calculate_unit_vector(point1, point2)

            # 如果返回了None（零向量），跳过该向量的计算
            if vec is None:
                continue

            # 计算当前段的权重（段长度）
            weight = np.linalg.norm(np.array(point2) - np.array(point1))

            vectors.append(vec)
            weights.append(weight)

        # 如果没有有效的非零向量，返回默认方向向量
        if len(vectors) == 0:
            print("没有有效的非零向量，返回默认方向向量")
            return np.zeros(3)

        # 检查向量维度是否一致
        vector_shape = np.shape(vectors[0])
        for vec in vectors:
            if np.shape(vec) != vector_shape:
                print(f"警告: 向量维度不一致，跳过向量 {vec}")
                continue

        # 加权平均方向向量
        weighted_vector = np.average(vectors, axis=0, weights=weights)

        # 单位化方向向量
        norm = np.linalg.norm(weighted_vector)
        if norm == 0:
            print("加权方向向量为零，返回默认方向向量")
            return np.zeros(3)  # 如果加权方向向量为零，返回零向量
        
        return weighted_vector / norm


    def calculate_angle(vector1, vector2):
        """计算两个向量的夹角（角度值）"""
        dot_product = np.dot(vector1, vector2)
        norm1 = np.linalg.norm(vector1)
        norm2 = np.linalg.norm(vector2)

        # 检查向量模长是否为零
        if norm1 == 0 or norm2 == 0:
            print("向量模长为零,返回角度180度")
            return 180.0  # 返回最大角度

        cos_theta = np.clip(dot_product / (norm1 * norm2), -1.0, 1.0)  # 夹角余弦值
        return math.degrees(math.acos(cos_theta))  # 返回夹角（角度值）


    def process_chains_start(chains, level, max_depth=10):
        if level == 1:
            for chain in chains:
                # 获取子链表
                sub_chains = get_fork(chain[-1])
                
                for sub_chain in sub_chains:
                    if len(sub_chain) <= max_depth:
                        first_branch.append(sub_chain)
                        # 递归处理一级枝的子链表
                        process_chains_start([sub_chain], level=1)
                    else:
                        continue
            return first_branch

        elif level == 2:
            for chain in chains:
                # 获取子链表
                sub_chains = get_fork(chain[-1])
                
                for sub_chain in sub_chains:
                    if len(sub_chain) <= max_depth:
                        second_branch.append(sub_chain)
                        # 递归处理二级枝的子链表
                        process_chains_start([sub_chain], level=2)
                    else:
                        continue
            return second_branch

        elif level == 3:
            for chain in chains:
                # 获取子链表
                sub_chains = get_fork(chain[-1])
                
                for sub_chain in sub_chains:
                    if len(sub_chain) <= max_depth:
                        third_branch.append(sub_chain)
                        # 递归处理三级枝的子链表
                        process_chains_start([sub_chain], level=3)
                    else:
                        continue
            return third_branch

    def calculate_new_vector(data, start_point, end_point):

        """计算从起点到终点的向量"""
        return [
            data.loc[data['PointNo'] == end_point, 'X'].iloc[0] - data.loc[data['PointNo'] == start_point, 'X'].iloc[0],
            data.loc[data['PointNo'] == end_point, 'Y'].iloc[0] - data.loc[data['PointNo'] == start_point, 'Y'].iloc[0],
            data.loc[data['PointNo'] == end_point, 'Z'].iloc[0] - data.loc[data['PointNo'] == start_point, 'Z'].iloc[0],
        ]


    def calculate_new_angle(vector1, vector2):
        """计算两个向量的夹角（角度值）"""
        dot_product = sum(f * s for f, s in zip(vector1, vector2))  # 点积
        norm1 = (sum(f ** 2 for f in vector1)) ** 0.5  # 向量1模长
        norm2 = (sum(s ** 2 for s in vector2)) ** 0.5  # 向量2模长
        cos_theta = dot_product / (norm1 * norm2)  # 夹角余弦值
        return math.degrees(math.acos(cos_theta))  # 返回夹角（角度值）
    
    fork_cache = {}

    def get_fork(point):
        if point not in fork_cache:
            fork_cache[point] = build_chains_from_fork(point)
        return fork_cache[point]


    # 读取 SWC 文件
    data = pd.read_csv(swc_path, sep=' ', comment='#', header=None)
    data.columns = ['PointNo', 'Label', 'X', 'Y', 'Z', 'Radius', 'Parent']
    point_idx_map = dict(zip(data['PointNo'], data.index))
    point_label_map = dict(zip(data['PointNo'], data['Label']))

    # 初始化点云和颜色
    points = o3d.geometry.PointCloud()
    points.points = o3d.utility.Vector3dVector(data[['X', 'Y', 'Z']].values)
    colors = np.ones((len(data), 3))  # 默认白色

    # 初始化链表
    main_branch, first_branch, second_branch, third_branch, fourth_branch = [], [], [], [], []

    # --- 分支构建与修正逻辑（保留你的原始函数调用） ---
    root_node = data[data['Label'] == 1].iloc[0]
    main_branch.append(build_chain(root_node['PointNo']))
    main_chains = get_fork(main_branch[-1][-1])
    first_branch.extend(main_chains)
    process_chains(first_branch, level=1, max_depth=10)

    # 清洗和调整一级二级链
    for chain in second_branch[:]:
        sub_chains = get_fork(chain[-1])
        if any(sub_chain in first_branch for sub_chain in sub_chains):
            second_branch.remove(chain)
            first_branch.append(chain)

    first_new_branch = []
    for chain in second_branch[:]:
        if len(chain) <= 6 and point_label_map[chain[-1]] == 5:
            sub_chains = get_fork(chain[0])
            if all(sub_chain in second_branch for sub_chain in sub_chains):
                second_branch.remove(chain)
                first_branch.append(chain)
                first_new_branch.append(chain)

    for chain in first_new_branch[:]:
        sub_chains = get_fork(chain[-1])
        if len(sub_chains) == 1:
            first_new_branch.remove(chain)
            new_chain = list(dict.fromkeys(chain + build_chain(chain[-1])))
            first_branch.append(new_chain)
            first_new_branch.append(new_chain)

    if first_new_branch:
        process_new_chains(first_new_branch, level=1)

    # 判断短一级枝是否应降级
    for chain in first_branch[:]:
        sub_chains = get_fork(chain[-1])
        if len(chain) == 2 and all(sub_chain in second_branch for sub_chain in sub_chains):
            vec = calculate_new_vector(data, chain[-2], chain[-1])
            vec1 = calculate_new_vector(data, sub_chains[0][0], sub_chains[0][1])
            vec2 = calculate_new_vector(data, sub_chains[1][0], sub_chains[1][1])
            angle1 = calculate_new_angle(vec, vec1)
            angle2 = calculate_new_angle(vec, vec2)
            label1 = point_label_map[sub_chains[0][-1]] == 5
            label2 = point_label_map[sub_chains[1][-1]] == 5
            if angle1 < angle2:
                if label1:
                    first_branch.append(sub_chains[0])
                    second_branch.append(sub_chains[1])
                else:
                    second_branch.extend(sub_chains)
            else:
                if label2:
                    first_branch.append(sub_chains[1])
                    second_branch.append(sub_chains[0])
                else:
                    second_branch.extend(sub_chains)

    # 处理一级枝的两个子链情况
    first_new_branch_2 = []
    for chain in first_branch[:]:
        sub_chains = get_fork(chain[-1])
        if all(sub_chain in second_branch for sub_chain in sub_chains):
            if len(sub_chains) == 1:
                first_branch.append(sub_chains)
                first_new_branch_2.append(sub_chains)
            elif len(sub_chains) == 0:
                continue
            else:
                label1 = point_label_map[sub_chains[0][-1]]
                label2 = point_label_map[sub_chains[1][-1]]
                if label1 != label2:
                    for sub_chain in sub_chains:
                        if point_label_map[sub_chain[-1]] == 5:
                            second_branch.remove(sub_chain)
                            first_branch.append(sub_chain)
                            first_new_branch_2.append(sub_chain)
                elif label1 == label2 == 5:
                    vec = calculate_new_vector(data, chain[0], chain[-1])
                    vec1 = calculate_new_vector(data, sub_chains[0][0], sub_chains[0][-1])
                    vec2 = calculate_new_vector(data, sub_chains[1][0], sub_chains[1][-1])
                    angle1 = calculate_new_angle(vec, vec1)
                    angle2 = calculate_new_angle(vec, vec2)
                    if angle1 < angle2 and label1 != 6:
                        second_branch.remove(sub_chains[0])
                        first_branch.append(sub_chains[0])
                        first_new_branch_2.append(sub_chains[0])
                    elif angle2 < angle1 and label2 != 6:
                        second_branch.remove(sub_chains[1])
                        first_branch.append(sub_chains[1])
                        first_new_branch_2.append(sub_chains[1])

    if first_new_branch_2:
        process_new_chains(first_new_branch_2, level=1)

    # 处理二级分支
    process_chains(second_branch, level=2, max_depth=5)

    # 判断是否将三级枝调整为二级
    second_new_branch = []
    for chain in third_branch[:]:
        if len(chain) <= 6 and point_label_map[chain[-1]] == 5:
            sub_chains = get_fork(chain[0])
            if all(sub_chain in third_branch for sub_chain in sub_chains):
                third_branch.remove(chain)
                second_branch.append(chain)
                second_new_branch.append(chain)

    for chain in second_new_branch[:]:
        sub_chains = get_fork(chain[-1])
        if len(sub_chains) == 1:
            second_new_branch.remove(chain)
            new_chain = list(dict.fromkeys(chain + build_chain(chain[-1])))
            second_branch.append(new_chain)
            second_new_branch.append(new_chain)

    if second_new_branch:
        process_new_chains(second_new_branch, level=2)

    process_chains(third_branch, level=3, max_depth=5)

    # 判断是否将四级枝调整为三级
    third_new_branch = []
    for chain in fourth_branch[:]:
        if len(chain) <= 6 and point_label_map[chain[-1]] == 5:
            sub_chains = get_fork(chain[0])
            if all(sub_chain in fourth_branch for sub_chain in sub_chains):
                fourth_branch.remove(chain)
                third_branch.append(chain)
                third_new_branch.append(chain)

    for chain in third_new_branch[:]:
        sub_chains = get_fork(chain[-1])
        if len(sub_chains) == 1:
            third_new_branch.remove(chain)
            new_chain = list(dict.fromkeys(chain + build_chain(chain[-1])))
            third_branch.append(new_chain)
            third_new_branch.append(new_chain)

    if third_new_branch:
        process_new_chains(third_new_branch, level=3)

    # --- 设置颜色 ---
    def color_branches(branch_list, color):
        for chain in branch_list:
            for node_id in chain:
                idx = point_idx_map.get(node_id)
                if idx is not None:
                    colors[idx] = color

    color_branches(main_branch,  [0, 0, 0])       # 黑
    color_branches(first_branch, [1, 0, 0])       # 红
    color_branches(second_branch,[0, 0, 1])       # 蓝
    color_branches(third_branch, [0, 1, 0])       # 绿
    color_branches(fourth_branch,[1, 0.65, 0])    # 橙

    points.colors = o3d.utility.Vector3dVector(colors)

    # --- 构建连接线 ---
    lines = o3d.geometry.LineSet()
    lines.points = o3d.utility.Vector3dVector(data[['X', 'Y', 'Z']].values)
    lines_indices = [[i, point_idx_map[row['Parent']]] for i, row in data.iterrows() if row['Parent'] != -1]
    lines.lines = o3d.utility.Vector2iVector(lines_indices)

    # --- 导出结果 ---
    o3d.io.write_point_cloud(output_ply_path, points)
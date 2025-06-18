import pandas as pd
import open3d as o3d
import numpy as np

def prunning_branches(swc_path, output_ply_path):
    data = pd.read_csv(swc_path, sep=' ', comment='#', header=None,
                       names=['PointNo', 'Label', 'X', 'Y', 'Z', 'Radius', 'Parent'])

    data['PointNo'] = data['PointNo'].astype(int)
    data['Label'] = data['Label'].astype(int)
    data['Parent'] = data['Parent'].astype(int)

    coords = data[['X', 'Y', 'Z']].values
    point_idx_map = {pid: i for i, pid in enumerate(data['PointNo'])}
    label_map = dict(zip(data['PointNo'], data['Label']))
    parent_map = dict(zip(data['PointNo'], data['Parent']))
    coord_map = dict(zip(data['PointNo'], coords))

    num_points = len(data)
    colors = np.full((num_points, 3), [0.5, 0.5, 0.5])  # default gray

    def calculate_angle(v1, v2):
        cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        return np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0)))

    def calculate_distance(p1, p2):
        return np.linalg.norm(coord_map[p1] - coord_map[p2])

    def calculate_chain_length(chain):
        return sum(calculate_distance(chain[i], chain[i+1]) for i in range(len(chain)-1))

    def build_chains_from_fork(fork_node):
        chains = []
        children = data[data['Parent'] == fork_node]['PointNo'].tolist()
        for child in children:
            chain = [fork_node]
            current = child
            while True:
                chain.append(current)
                if label_map.get(current, -1) != 0:
                    break
                next_nodes = data[data['Parent'] == current]['PointNo'].tolist()
                if not next_nodes:
                    break
                current = next_nodes[0]
            chains.append(chain)
        return chains

    # === 构建所有链表 ===
    chains = []
    chain_id = 1
    leaf_nodes = data[data['Label'] == 6]['PointNo'].tolist()
    for leaf in leaf_nodes:
        current = leaf
        chain = []
        while True:
            chain.append(current)
            if label_map.get(current, -1) != 0 and len(chain) > 1:
                chains.append((chain_id, chain.copy()))
                chain_id += 1
                chain = [current]
            parent = parent_map.get(current, -1)
            if label_map.get(parent, -1) == 1:
                chain.append(parent)
                chains.append((chain_id, chain))
                chain_id += 1
                break
            if parent == -1 or parent not in label_map:
                break
            current = parent

    # === 标记下垂枝（蓝色）===
    valid_chains = []
    for cid, chain in chains:
        start, end = chain[0], chain[-1]
        labels = (label_map[start], label_map[end])
        if 5 in labels and 6 in labels:
            fork_y = coord_map[end][1] if label_map[end] == 5 else coord_map[start][1]
            leaf_y = coord_map[start][1] if label_map[start] == 6 else coord_map[end][1]
            if fork_y >= leaf_y:
                valid_chains.append(chain)
                for node in chain:
                    colors[point_idx_map[node]] = [0, 0, 1]

    # === 标记直立枝（绿色）===
    for cid, chain in chains:
        if chain in valid_chains:
            continue
        start_coords, end_coords = coord_map[chain[0]], coord_map[chain[-1]]
        vec = end_coords - start_coords
        angle = calculate_angle(vec, np.array([0, 1, 0]))
        if angle < 15 or angle > 165:
            for node in chain:
                colors[point_idx_map[node]] = [0, 1, 0]

    # === 标记竞争枝（紫色）===
    completion_branches = []
    fork_nodes = data[data['Label'] == 5]['PointNo'].tolist()
    for fork_node in fork_nodes:
        chains_from_fork = build_chains_from_fork(fork_node)
        if len(chains_from_fork) != 2:
            continue
        chain1, chain2 = chains_from_fork
        is_leaf1 = label_map.get(chain1[-1], -1) == 6
        is_leaf2 = label_map.get(chain2[-1], -1) == 6
        if is_leaf1 and is_leaf2:
            len1 = calculate_distance(chain1[0], chain1[-1])
            len2 = calculate_distance(chain2[0], chain2[-1])
            chosen = chain1 if len1 < len2 else chain2
            completion_branches.append(chosen)
            for node in chosen:
                colors[point_idx_map[node]] = [128/255, 0, 128/255]

    # === 标记密集枝（红色）===
    density_branches = []
    for fork_node in fork_nodes:
        chains_from_fork = build_chains_from_fork(fork_node)
        if len(chains_from_fork) != 2:
            continue
        chain1, chain2 = chains_from_fork
        is_leaf1 = label_map.get(chain1[-1], -1) == 6
        is_leaf2 = label_map.get(chain2[-1], -1) == 6
        if is_leaf1 and not is_leaf2:
            density_branches.append(chain1)
        elif is_leaf2 and not is_leaf1:
            density_branches.append(chain2)

    # 排序 + 删除短的一半
    density_branches_sorted = sorted(density_branches, key=calculate_chain_length)
    num_to_remove = len(density_branches_sorted) // 2
    kept_density_branches = density_branches_sorted[num_to_remove:]

    for chain in kept_density_branches:
        for node in chain:
            colors[point_idx_map[node]] = [1, 0, 0]

    # === 标记断枝（白色）===
    correct_skeleton = set()
    broken_branches = set()
    for leaf in leaf_nodes:
        current = leaf
        path = []
        while current in parent_map and parent_map[current] != -1:
            path.append(current)
            current = parent_map[current]
        if label_map.get(current, -1) == 1:
            correct_skeleton.update(path)
        else:
            broken_branches.update(path)

    for node in broken_branches:
        colors[point_idx_map[node]] = [1, 1, 1]

    # === 输出结果 ===
    points = o3d.geometry.PointCloud()
    points.points = o3d.utility.Vector3dVector(coords)
    points.colors = o3d.utility.Vector3dVector(colors)
    o3d.io.write_point_cloud(output_ply_path, points)
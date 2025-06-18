import json

def json_to_swc(json_path, swc_path):
    with open(json_path, 'r') as f:
        data = json.load(f)

    # 1. 构建节点索引映射与位置表
    id_to_node = {node["id"]: node for node in data["nodes"]}
    id_list = list(id_to_node.keys())

    # 2. 找出 Y 最小的节点作为根节点
    root_id = min(id_list, key=lambda nid: id_to_node[nid]["pos"][1])

    # 3. 构建 child → parent 映射
    child_to_parent = {}
    for link in data["links"]:
        child_to_parent[link["target"]] = link["source"]

    # 4. 给每个节点分配连续的 index（SWC 要求编号连续）
    id_to_index = {nid: idx+1 for idx, nid in enumerate(id_list)}

    # 5. 生成 SWC 行
    swc_lines = []
    for nid in id_list:
        idx = id_to_index[nid]
        x, y, z = id_to_node[nid]["pos"]
        parent_id = child_to_parent.get(nid, -1)
        parent_idx = id_to_index[parent_id] if parent_id in id_to_index else -1
        if nid == root_id:
            parent_idx = -1
        swc_lines.append(f"{idx} 3 {x} {y} {z} 1 {parent_idx}")

    # 6. 写入 SWC 文件
    with open(swc_path, 'w') as f:
        f.write('\n'.join(swc_lines))
        
    print(f"SWC file saved to: {swc_path}")

json_to_swc(r"datas\txt\tree4.json", r"datas\txt\tree4.swc")

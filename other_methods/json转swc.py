import json

def json_to_swc(json_path, swc_path):
    # 读取 JSON 文件
    with open(json_path, 'r') as f:
        data = json.load(f)

    nodes = {node['id']: node['pos'] for node in data['nodes']}
    edges = data.get('links', [])

    # 将节点按 ID 升序排序
    sorted_node_ids = sorted(nodes.keys())
    id_to_index = {node_id: idx for idx, node_id in enumerate(sorted_node_ids)}

    # 解析 links 字典结构（适配 {"source": x, "target": y}）
    parent_map_indexed = {}
    for edge in edges:
        source_id = edge.get("source")
        target_id = edge.get("target")
        if source_id in id_to_index and target_id in id_to_index:
            parent_map_indexed[id_to_index[target_id]] = id_to_index[source_id]

    # 写入 SWC 文件
    header = """# SWC format file
# based on specifications at http://www.neuronland.org/NLMorphologyConverter/MorphologyFormats/SWC/Spec.html
# Created on 2024-06-09 using skeletor (https://github.com/navis-org/skeletor)
# PointNo Label X Y Z Radius Parent
# Labels:
# 0 = undefined, 1 = soma, 5 = fork point, 6 = end point
"""
    with open(swc_path, 'w') as f:
        f.write(header)
        for idx, node_id in enumerate(sorted_node_ids):
            x, y, z = nodes[node_id]
            parent = parent_map_indexed.get(idx, -1)
            f.write(f"{idx} 0 {x} {y} {z} None {parent}\n")
            if idx < len(sorted_node_ids) - 1:
                f.write("\n")

    print(f"SWC file saved to: {swc_path}")

json_to_swc(r"datas\txt\tree4.json", r"datas\txt\tree4.swc")
import json
import random
import numpy as np
from tabulate import tabulate


def save_to_json(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def calculate_c_values(a, level):
    level_ratio = {1: 67 / 150, 2: 53 / 120, 3: 4 / 20}
    ratio = level_ratio.get(level, 1)
    return round(ratio * a[0]), round(ratio * a[1])

def calculate_y_pred(a):
    return round(1.1007 * a[0] + 8.3698), round(1.1007 * a[1] + 8.3698)

def print_branches(branches):
    headers = ['级别', '长度', '杆数', '单杆果数量', '单杆叶片数量区间']
    table = [
        [f"{b['level']}级枝", b['a'], b['b'], 
         calculate_c_values(b['a'], b['level']), 
         calculate_y_pred(b['a'])] 
        for b in branches
    ]
    return tabulate(table, headers, tablefmt="grid")


def distribute_yield_by_ratio(total, ratio):
    parts = sum(ratio)
    return [round((r / parts) * total, 2) for r in ratio]

def fill_fruit_weights(node_count):
    fruit_weights = [16, 18, 20, 22, 24, 26, 28]
    table_data = [
        ['不同头重产量（公斤）'] + fruit_weights,
        ['单果重（克）'] + [round(1000 / w, 2) for w in fruit_weights],
        ['1级枝'] + [''] * len(fruit_weights),
        ['2级枝'] + [''] * len(fruit_weights),
        ['3级枝'] + [''] * len(fruit_weights),
        ['合计'] + [''] * len(fruit_weights)
    ]

    min_nodes, max_nodes = 1642, 11443
    node_ratio = min(max((node_count - min_nodes) / (max_nodes - min_nodes), 0), 1)
    base_yield = 50 + node_ratio * 10  

    for i in range(len(fruit_weights)):
        decay = sum(np.random.uniform(3, 5) for _ in range(i))
        yield_mean = max(30, round(base_yield - decay, 2))

        total_min = max(30, yield_mean - random.uniform(0.5, 1.2))
        total_max = yield_mean + random.uniform(0.5, 1.2)
        table_data[5][i + 1] = f"{total_min:.2f} - {total_max:.2f}"

        ratio = [1, 5.5, 4.5]
        parts = sum(ratio)
        def split_range(total_val):
            return [(r / parts) * total_val for r in ratio]

        min_vals = split_range(total_min)
        max_vals = split_range(total_max)

        table_data[2][i + 1] = f"{min_vals[0]:.2f} - {max_vals[0]:.2f}"
        table_data[3][i + 1] = f"{min_vals[1]:.2f} - {max_vals[1]:.2f}"
        table_data[4][i + 1] = f"{min_vals[2]:.2f} - {max_vals[2]:.2f}"

    return table_data


def save_table_to_json(table_data, filename):
    headers = table_data[0]
    rows = table_data[1:]
    
    json_data = []
    for row in rows:
        row_dict = {headers[i]: row[i] for i in range(len(headers))}
        json_data.append(row_dict)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

def count_swc_nodes(swc_path):
    with open(swc_path, 'r') as f:
        return sum(1 for line in f if line.strip() and not line.startswith('#'))



def fruit_forecast(swc_path, json_path):
    node_count = count_swc_nodes(swc_path)
    table_data = fill_fruit_weights(node_count)
    save_table_to_json(table_data, json_path)
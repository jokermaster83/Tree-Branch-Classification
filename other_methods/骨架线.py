import pandas as pd
import open3d as o3d
import numpy as np

swc_path = r"datas\txt\tree4.swc"

# 读取树骨架swc文件
data = pd.read_csv(swc_path, sep=' ', comment='#', header=None)
data.columns = ['PointNo', 'Label', 'X', 'Y', 'Z', 'Radius', 'Parent']

# 添加结点
points = o3d.geometry.PointCloud()
points.points = o3d.utility.Vector3dVector(data[['X', 'Y', 'Z']].values)

# 添加颜色数组
num_points = len(points.points)
colors = np.ones((num_points, 3))  # Initialize color array for all points (default: white)
                                                                    
# 找到根节点，标记为青色
root_indices = data[data['Label'] == 1].index
colors[root_indices] = [0, 1, 1]  # Cyan color

# 找到分支节点，标记为红色
fork_indices = data[data['Label'] == 5].index
colors[fork_indices] = [1, 0, 0]  # Red color

# 找到叶子节点，标记为蓝色
end_indices = data[data['Label'] == 6].index
colors[end_indices] = [0, 0, 1]  # Blue color

# 找到未定义点，标记为绿色
undefined_indices = data[data['Label'] == 0].index
colors[undefined_indices] = [0, 1, 0]  # Green color

# 将颜色数组应用到点云
points.colors = o3d.utility.Vector3dVector(colors)

# 创建可视化窗口
vis = o3d.visualization.Visualizer()
vis.create_window()

# 将骨架添加到可视化窗口
lines = o3d.geometry.LineSet()
lines.points = o3d.utility.Vector3dVector(data[['X', 'Y', 'Z']].values)

# 构建连线索引
lines_indices = []
for i, row in data.iterrows():
    if row['Parent'] != -1:
        parent_index = data.index[data['PointNo'] == row['Parent']].tolist()[0]
        lines_indices.append([i, parent_index])

lines.lines = o3d.utility.Vector2iVector(lines_indices)

vis.add_geometry(points)
vis.add_geometry(lines)

# 运行可视化窗口
vis.run()
vis.destroy_window()

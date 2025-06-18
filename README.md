## 🌳 Tree Branch Classification Based on 3D Skeleton Extraction

本项目基于果树三维点云的主干结构提取，完成**树枝的自动层级分类**，适用于精准农业场景中的**树形建模、枝条识别与后续剪枝推荐**。

---

### 📌 项目简介

输入果树的三维点云数据（如 `.ply` / `.pcd` 格式），本项目首先提取树体骨架结构，并在骨架上进行拓扑结构分析，自动完成以下功能：

* 🌲 主干识别（Trunk）
* 🌿 一级枝（Primary branch）识别
* 🍃 二级枝（Secondary branch）识别
* 🍂 三级枝（Tertiary branch）识别
* 📏 输出各级枝条的**数量、长度与层级标签**

本项目是剪枝推荐系统的核心前置模块。

---

### 🖼️ 样例结果

>

---

### 📁 项目结构

```bash
Tree-Branch-Classification/
│
├── skeletor/               # 核心算法模块（骨架提取、树枝分类）
│   ├── __init__.py
│   ├── segmentation.py     # 拓扑结构分析
│   └── utilities.py
│
├── data/                   # 示例点云数据（可选上传）
│   └── tree_sample.ply
│
├── results/                # 分类输出结果（自动生成）
│   ├── hierarchy_labels.json
│   └── branch_stats.csv
│
├── tests/                  # 单元测试
│   └── test_skeletor.py
│
├── requirements.txt        # Python依赖
├── README.md               # 项目说明文件
└── run.py                  # 项目入口脚本
```

---

### ⚙️ 安装依赖

建议使用 Python 3.8+ 虚拟环境运行：

```bash
# 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate  # Windows 用 venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

---

### 🚀 快速开始

```bash
python run.py --input ./data/tree_sample.ply --output ./results/
```

默认将输出每一级树枝的数量、长度统计以及分支层级标签。

---

### 🧠 算法原理简述

本方法包含以下核心步骤：

1. **点云骨架提取**（Skeletonization）：采用收缩驱动的算法提取骨架点云。
2. **拓扑结构重建**：识别主干、分叉点，并根据空间与拓扑规则分层归类。
3. **树枝分类与标签标注**：通过主干→一级→二级→三级的方向性生长与连接关系进行分类。
4. **长度与数量计算**：基于空间点坐标测量每个分支的长度和层级归属。

---

### 📦 输出格式说明

* `branch_stats.csv`：每级树枝的数量、平均长度、总长度等
* `hierarchy_labels.json`：每个骨架节点对应的层级标签和连接信息

---

### 🔧 可选参数（`run.py`）

| 参数             | 说明                 | 示例                 |
| -------------- | ------------------ | ------------------ |
| `--input`      | 输入点云路径             | `tree.ply`         |
| `--output`     | 输出文件夹路径            | `./results/`       |
| `--vis`        | 是否显示交互式可视化（Open3D） | `--vis`            |
| `--min_branch` | 最小枝条长度阈值           | `--min_branch 0.1` |

---

### 🧪 测试

```bash
pytest tests/
```

---

### 📚 参考文献与资源

* ***Xu et al.***, *Skeleton-based tree structure analysis for 3D plant point clouds*, CVPR Workshop, 2021.
* ***Panja et al.***, *Topology extraction and classification in plant structures*, TCSVT, 2022.
* 本项目部分结构参考：[PlantStructuralAnalysis](https://github.com/PlantStructuralAnalysis)

---

### 🧑‍💻 开发者

* Author: **龚文俊 Gong Wenjun**
* Email: `your-email@example.com`
* GitHub: [@jokermaster83](https://github.com/jokermaster83)

---

### 📜 License

本项目采用 MIT 协议，详见 [LICENSE](./LICENSE)。

---

如需我补充英文版 README、可视化示例图，或自动生成 `.gitattributes` / `.gitignore` 等附属文件，继续说。

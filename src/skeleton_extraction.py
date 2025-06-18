import trimesh as tm
import skeletor as sk
import os

def skeleton_extraction(obj_path, swc_path):
    # 检查 obj 文件是否存在
    if not os.path.exists(obj_path):
        raise FileNotFoundError(f"OBJ file not found: {obj_path}")
    
    try:
        # loading the obj file
        mesh = tm.load_mesh(obj_path)

        # # 保留最大连通块（去除小碎片）
        mesh = max(mesh.split(only_watertight=False), key=lambda m: len(m.faces))
        
        # pre-processing
        fixed = sk.pre.fix_mesh(mesh,remove_disconnected=500, inplace=True)
        cont = sk.pre.contract(fixed, epsilon=0.03, SL=2, time_lim=30)

        
        # skeletonization
        skel = sk.skeletonize.by_teasar(cont, inv_dist=0.5)

        # 检查是否生成了有效的骨架
        if skel.vertices.shape[0] == 0:
            raise ValueError("Skeletonization failed: No vertices generated.")
        
        # post-processing
        sk.post.clean_up(skel, inplace=True)


        # skel.show(mesh=True)
        skel.save_swc(swc_path)

    except Exception as e:
        raise RuntimeError(f"Skeleton extraction failed: {e}")

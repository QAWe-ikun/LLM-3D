import sys
import os
sys.path.append(os.path.dirname(__file__))

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from Utils import *

# 加载测试模型
glb_path = os.path.join(os.path.dirname(__file__), "..", "0.glb")
vertices, colors = read_glb_vertices(glb_path)

print(f"顶点数量: {len(vertices)}")
print(f"顶点坐标范围:")
print(f"  X: [{np.min(vertices[:, 0]):.3f}, {np.max(vertices[:, 0]):.3f}]")
print(f"  Y: [{np.min(vertices[:, 1]):.3f}, {np.max(vertices[:, 1]):.3f}]")
print(f"  Z: [{np.min(vertices[:, 2]):.3f}, {np.max(vertices[:, 2]):.3f}]")

# 测试向上方向
x, y, z, length, width, height, length_sample_num, width_sample_num, height_sample_num = get_model_size(vertices)
print(f"\n模型尺寸:")
print(f"  原点: ({x:.3f}, {y:.3f}, {z:.3f})")
print(f"  实际尺寸: length={length:.3f}, width={width:.3f}, height={height:.3f}")

# 测试向上采样
dirt = direction.up
origin_z = z + height  # 向上看，原点在顶部
origin = [x, y, origin_z]
print(f"\n测试方向: 向上")
print(f"  原点: {origin}")

# 手动计算几个顶点
plane_axis1, plane_axis2, depth_axis = 0, 1, 2
depth_sign = 1

print(f"\n前10个顶点的深度计算:")
for i in range(min(10, len(vertices))):
    vertex = vertices[i]
    depth = (vertex[depth_axis] - origin[depth_axis]) * depth_sign
    print(f"  顶点{i}: Z={vertex[depth_axis]:.3f}, origin_Z={origin[depth_axis]:.3f}, depth={depth:.3f}")

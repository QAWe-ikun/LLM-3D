import math
import trimesh
import numpy as np
from enum import Enum


sample_num = 64
sample_rate = 1. / sample_num

class direction(Enum):
    up = 0
    down = 5
    left = 1
    right = 4
    forward = 2
    backward = 3

def find_opposite_direction(dirt: direction) -> direction:
    return direction(5 - dirt.value)

def find_glb_model(model_name):
    """
    TODO: connect with db
    """
    pass

def read_glb_vertices(file_path):
    # 加载GLB文件
    mesh = trimesh.load(file_path, force='mesh')

    # 获取顶点缓冲区数据
    v = mesh.vertices # type: ignore
    vertices = np.array(v)

    # 获取顶点颜色数据
    colors = None
    if hasattr(mesh.visual, 'vertex_colors'):
        # 如果有顶点颜色，直接使用
        colors = np.array(mesh.visual.vertex_colors[:, :3])  # 只取RGB，不要alpha通道
    elif hasattr(mesh.visual, 'to_color'):
        # 如果是纹理模型，转换为顶点颜色
        try:
            color_visual = mesh.visual.to_color()
            colors = np.array(color_visual.vertex_colors[:, :3])
        except:
            # 如果转换失败，使用默认白色
            colors = np.ones((len(vertices), 3), dtype=np.uint8) * 255
    else:
        # 如果没有颜色信息，使用默认白色
        colors = np.ones((len(vertices), 3), dtype=np.uint8) * 255

    return vertices, colors, mesh

def normalize_glb(vertices):
    """
    TODO: normalize glb model size
    """
    pass

def get_model_size(item_vertices):
    x = np.min(item_vertices[:, 0])
    length = np.max(item_vertices[:, 0]) - np.min(item_vertices[:, 0])
    y = np.min(item_vertices[:, 1])
    width = np.max(item_vertices[:, 1]) - np.min(item_vertices[:, 1])
    z = np.min(item_vertices[:, 2])
    height = np.max(item_vertices[:, 2]) - np.min(item_vertices[:, 2])

    length_sample_num = math.ceil(length / sample_rate)
    width_sample_num = math.ceil(width / sample_rate)
    height_sample_num = math.ceil(height / sample_rate)

    return x, y, z, length, width, height, length_sample_num, width_sample_num, height_sample_num

def sample(mesh, vertex_colors, dirt: direction, origin: list):
    """
    使用射线追踪对mesh进行采样
    mesh: trimesh对象
    vertex_colors: 顶点颜色数组 (N, 3)
    dirt: 采样方向
    origin: 原点坐标 [x, y, z]
    返回: distance_map 对象
    """
    from room import distance_map

    vertices = mesh.vertices

    # 根据方向确定投影平面和深度轴
    if dirt == direction.up or dirt == direction.down:
        # 投影到XY平面，深度轴是Z
        plane_axis1, plane_axis2, depth_axis = 0, 1, 2
        ray_direction = np.array([0, 0, -1 if dirt == direction.up else 1])
    elif dirt == direction.left or dirt == direction.right:
        # 投影到YZ平面，深度轴是X
        plane_axis1, plane_axis2, depth_axis = 1, 2, 0
        ray_direction = np.array([1 if dirt == direction.left else -1, 0, 0])
    else:  # forward or backward
        # 投影到XZ平面，深度轴是Y
        plane_axis1, plane_axis2, depth_axis = 0, 2, 1
        ray_direction = np.array([0, -1 if dirt == direction.forward else 1, 0])

    # 计算vertices在投影平面上的范围
    plane_coords1 = vertices[:, plane_axis1]
    plane_coords2 = vertices[:, plane_axis2]

    min_coord1 = np.min(plane_coords1)
    max_coord1 = np.max(plane_coords1)
    min_coord2 = np.min(plane_coords2)
    max_coord2 = np.max(plane_coords2)

    # 计算平面上的长宽
    plane_length = max_coord1 - min_coord1
    plane_width = max_coord2 - min_coord2

    # 根据sample_rate计算网格数量
    width = math.ceil(plane_length / sample_rate)
    height = math.ceil(plane_width / sample_rate)

    # 创建距离图和颜色图
    dist_map = np.zeros((height, width), dtype=np.uint8)  # 最远距离
    dist_map_nearest = np.full((height, width), 255, dtype=np.uint8)  # 最近距离（用于颜色）
    color_map = np.ones((height, width, 3), dtype=np.uint8) * 255  # 默认白色

    # 对每个网格中心发射射线
    ray_origins = []
    grid_indices = []

    for grid_y in range(height):
        for grid_x in range(width):
            # 计算网格中心在投影平面上的坐标
            center_coord1 = min_coord1 + (grid_x + 0.5) * sample_rate
            center_coord2 = min_coord2 + (grid_y + 0.5) * sample_rate

            # 构造射线起点（在原点位置）
            ray_origin = [0, 0, 0]
            ray_origin[plane_axis1] = center_coord1
            ray_origin[plane_axis2] = center_coord2
            ray_origin[depth_axis] = origin[depth_axis]

            ray_origins.append(ray_origin)
            grid_indices.append((grid_y, grid_x))

    # 批量射线追踪
    ray_origins = np.array(ray_origins)
    ray_directions = np.tile(ray_direction, (len(ray_origins), 1))

    # 使用trimesh进行射线追踪
    locations, index_ray, index_tri = mesh.ray.intersects_location(
        ray_origins=ray_origins,
        ray_directions=ray_directions,
        multiple_hits=True
    )

    # 处理交点
    if len(locations) > 0:
        for i in range(len(locations)):
            ray_idx = index_ray[i]
            hit_location = locations[i]
            grid_y, grid_x = grid_indices[ray_idx]

            # 计算距离
            distance = np.linalg.norm(hit_location - ray_origins[ray_idx])

            # 转换为uint8范围
            depth_value = min(int(distance / sample_rate), 255)

            # 更新最远距离（用于 dist_map）
            if depth_value > dist_map[grid_y, grid_x]:
                dist_map[grid_y, grid_x] = depth_value

            # 更新最近距离（用于 color_map，避免穿模）
            if depth_value < dist_map_nearest[grid_y, grid_x]:
                dist_map_nearest[grid_y, grid_x] = depth_value

                # 获取交点处的颜色（使用重心坐标插值）
                tri_idx = index_tri[i]
                face = mesh.faces[tri_idx]

                # 获取三角形的三个顶点
                v0, v1, v2 = mesh.vertices[face]

                # 计算重心坐标
                v0v1 = v1 - v0
                v0v2 = v2 - v0
                v0p = hit_location - v0

                d00 = np.dot(v0v1, v0v1)
                d01 = np.dot(v0v1, v0v2)
                d11 = np.dot(v0v2, v0v2)
                d20 = np.dot(v0p, v0v1)
                d21 = np.dot(v0p, v0v2)

                denom = d00 * d11 - d01 * d01
                if abs(denom) > 1e-10:
                    v = (d11 * d20 - d01 * d21) / denom
                    w = (d00 * d21 - d01 * d20) / denom
                    u = 1.0 - v - w

                    # 使用重心坐标插值颜色
                    c0, c1, c2 = vertex_colors[face]
                    color = (u * c0 + v * c1 + w * c2).astype(np.uint8)
                else:
                    # 如果重心坐标计算失败，使用平均颜色
                    color = np.mean(vertex_colors[face], axis=0).astype(np.uint8)

                color_map[grid_y, grid_x] = color

    # 创建并返回distance_map对象
    result = distance_map(dirt, origin[0], origin[1], origin[2], height, width)
    result.set_dist_map(dist_map)
    result.set_color_map(color_map)

    return result
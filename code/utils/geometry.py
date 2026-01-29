import math
import trimesh
import numpy as np
from enum import Enum
from config import DEFAULT_SAMPLE_INTERVAL as SAMPLE_RATE

class direction(Enum):
    up = 0
    down = 5
    left = 1
    right = 4
    forward = 2
    backward = 3

def find_opposite_direction(dirt: direction) -> direction:
    return direction(5 - dirt.value)

def find_glb_model(model_name: str):
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
    if hasattr(mesh.visual, 'vertex_colors'):  # type: ignore
        # 如果有顶点颜色，直接使用
        colors = np.array(mesh.visual.vertex_colors[:, :3])  # type: ignore  # 只取RGB，不要alpha通道
    elif hasattr(mesh.visual, 'to_color'):  # type: ignore
        # 如果是纹理模型，转换为顶点颜色
        try:
            color_visual = mesh.visual.to_color()  # type: ignore
            colors = np.array(color_visual.vertex_colors[:, :3])
        except:
            # 如果转换失败，使用默认白色
            colors = np.ones((len(vertices), 3), dtype=np.uint8) * 255
    else:
        # 如果没有颜色信息，使用默认白色
        colors = np.ones((len(vertices), 3), dtype=np.uint8) * 255

    return vertices, colors, mesh

def get_model_size(item_vertices):   
    """                                                                                                                                            
    计算3D模型的边界框尺寸和采样参数                                                                                                               
  
    参数:
        item_vertices: numpy数组，形状为(N, 3)，包含模型的所有顶点坐标

    返回:
        tuple: (x, y, z, length, width, height, length_sample_num, width_sample_num, height_sample_num)
            - x, y, z: 模型在各轴的最小坐标值（边界框起点）
            - length, width, height: 模型在各轴的尺寸
            - length_sample_num, width_sample_num, height_sample_num: 各轴的采样点数量
    """
    # 计算各轴的最小值和最大值（一次性计算，避免重复）
    min_coords = np.min(item_vertices, axis=0)  # [x_min, y_min, z_min]
    max_coords = np.max(item_vertices, axis=0)  # [x_max, y_max, z_max]

    # 提取边界框起点坐标
    x, y, z = min_coords

    # 计算各轴的尺寸（长度、宽度、高度）
    dimensions = max_coords - min_coords
    length, width, height = dimensions

    # 根据采样率计算各轴需要的采样点数量
    length_sample_num = math.ceil(length / SAMPLE_RATE)
    width_sample_num = math.ceil(width / SAMPLE_RATE)
    height_sample_num = math.ceil(height / SAMPLE_RATE)

    return x, y, z, length, width, height, length_sample_num, width_sample_num, height_sample_num

def normalize_glb(vertices, theoretical_volume: float, actual_volume: float, center: bool = True) -> tuple:
    """
    归一化GLB模型的顶点坐标，使其符合真实世界的尺寸比例

    参数:
        vertices: numpy数组，形状为(N, 3)的顶点坐标
        theoretical_volume: 理论体积（立方米），表示模型在现实世界中的体积
        actual_volume: GLB单位转换系数，表示现实世界的一立方米对应GLB空间中的体积
        center: 是否将模型中心移到原点，默认为True

    返回:
        tuple: (normalized_vertices, center_point)
            - normalized_vertices: 归一化后的顶点坐标数组
            - center_point: 模型的中心点坐标

    示例:
        如果一个立方体在现实中是1m³，GLB体积中=0.01，则：
        theoretical_volume = 1.0
        actual_volume = 0.01
    """
    # 确保输入为float64类型，提高计算精度
    vertices = np.array(vertices, dtype=np.float64)

    # 计算当前模型的边界框
    min_coords = np.min(vertices, axis=0)
    max_coords = np.max(vertices, axis=0)

    # 计算当前尺寸（长、宽、高）
    current_size = max_coords - min_coords

    # 计算当前体积（近似为长方体）
    current_volume = np.prod(current_size)  # 等价于 current_size[0] * current_size[1] * current_size[2]

    # 防止除零错误
    if current_volume < 1e-10:
        raise ValueError("模型体积过小或为零，无法进行归一化")

    # 计算缩放因子
    # theoretical_volume: 真实世界体积（m³）
    # actual_volume: 米到GLB单位的转换系数
    # current_volume: GLB空间中的当前体积
    # 目标：将GLB模型缩放到真实世界尺寸
    volume_ratio = theoretical_volume * actual_volume / current_volume
    scale_factor = np.cbrt(volume_ratio)  # 体积比的立方根得到线性缩放因子

    # 应用缩放
    normalized_vertices = vertices * scale_factor

    # 中心化处理
    # 计算缩放后的边界框中心点
    min_normalized = np.min(normalized_vertices, axis=0)
    max_normalized = np.max(normalized_vertices, axis=0)
    center_point = (min_normalized + max_normalized) / 2

    if center:
        # 将中心移到原点
        normalized_vertices = normalized_vertices - center_point
        center_point = np.array([0.0, 0.0, 0.0])

    return normalized_vertices, center_point

def sample(mesh, vertex_colors, dirt: direction):
    """
    使用射线追踪对mesh进行采样
    mesh: trimesh对象
    vertex_colors: 顶点颜色数组 (N, 3)
    dirt: 采样方向

    返回: distance_map 对象
    """
    from models.distance_map import DistanceMap

    vertices = mesh.vertices

    x = np.min(vertices[:, 0])
    length = np.max(vertices[:, 0]) - np.min(vertices[:, 0])
    y = np.min(vertices[:, 1])
    width = np.max(vertices[:, 1]) - np.min(vertices[:, 1])
    z = np.min(vertices[:, 2])
    height = np.max(vertices[:, 2]) - np.min(vertices[:, 2])

    # 根据方向确定投影平面和深度轴
    if dirt == direction.up or dirt == direction.down:
        # 投影到XY平面，深度轴是Z
        plane_axis1, plane_axis2, depth_axis = 0, 1, 2
        ray_direction = np.array([0, 0, -1 if dirt == direction.up else 1])
        origin_z = z if dirt == direction.down else z + height
        origin = [x, y, origin_z]
        min_coord1, min_coord2 = x, y
        plane_length, plane_width, plane_height = length, width, height
    elif dirt == direction.left or dirt == direction.right:
        # 投影到YZ平面，深度轴是X
        plane_axis1, plane_axis2, depth_axis = 1, 2, 0
        ray_direction = np.array([1 if dirt == direction.left else -1, 0, 0])
        origin_x = x if dirt == direction.left else x + length
        origin = [origin_x, y, z]
        min_coord1, min_coord2 = y, z
        plane_length, plane_width, plane_height = width, height, length
    else:  # forward or backward
        # 投影到XZ平面，深度轴是Y
        plane_axis1, plane_axis2, depth_axis = 0, 2, 1
        ray_direction = np.array([0, -1 if dirt == direction.forward else 1, 0])
        origin_y = y if dirt == direction.backward else y + width
        origin = [x, origin_y, z]
        min_coord1, min_coord2 = x, z
        plane_length, plane_width, plane_height = length, height, width

    # 根据sample_rate计算网格数量
    length = math.ceil(plane_length / SAMPLE_RATE)
    width = math.ceil(plane_width / SAMPLE_RATE)
    height = math.ceil(plane_height / SAMPLE_RATE)


    # 创建距离图和颜色图
    dist_map_nearest = np.full((width, length), height + 1, dtype=np.int16)  # 最近距离（用于颜色）
    color_map = np.ones((width, length, 3), dtype=np.uint8) * 255  # 默认白色

    # 对每个网格中心发射射线
    ray_origins = []
    grid_indices = []

    for grid_y in range(width):
        for grid_x in range(length):
            # 计算网格中心在投影平面上的坐标
            center_coord1 = min_coord1 + (grid_x + 0.5) * SAMPLE_RATE
            center_coord2 = min_coord2 + (grid_y + 0.5) * SAMPLE_RATE

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

            depth_value = int(distance / SAMPLE_RATE)

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
    result = DistanceMap(dirt, origin[0], origin[1], origin[2], width, length)
    dist_map =  height - dist_map_nearest

    result.set_dist_map(dist_map)
    result.set_color_map(color_map)

    return result
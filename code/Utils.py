import math
import trimesh
import numpy as np
from enum import Enum


sample_num = 256
sample_rate = 1. / sample_num

class direction(Enum):
    up = 0
    down = 5
    left = 1
    right = 5
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
    v = mesh.vertices
    vertices = np.array(v)

    return vertices

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

    return x, y, z, length_sample_num, width_sample_num, height_sample_num

def sample(vertices, dirt: direction, width: int, height: int, origin: list[int]):
    """
    sample farthest pixel's vertex coordinates in each direction
    """
    pass
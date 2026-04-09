"""
物体模块

包含 Item 类，表示3D场景中的一个物体
"""

import numpy as np
from typing import Union, List, Tuple
from ..utils import direction, find_glb_model, read_glb_vertices, sample, normalize_glb
from .distance_map import DistanceMap


class Item:
    """
    物体类，表示3D场景中的一个物体
    """
    def __init__(
        self,
        item_name: str,
        item_description: str,
        theoretical_volume: float,
        volume_rate: float
    ):
        """
        初始化物体

        参数:
            item_name: 物体名称
            item_description: 物体描述信息
            theoretical_volume: 物体在现实世界中的理论体积（立方米）
            volunme_rate: GLB单位到真实世界的转换系数（GLB体积/真实体积）
        """
        self.item_name = item_name
        self.item_description = item_description
        self.theoretical_volume = theoretical_volume

        # 加载GLB模型文件
        file_path = find_glb_model(item_name)
        vertices, colors, mesh = read_glb_vertices(file_path)

        # 使用 normalize_glb 标准化顶点
        # volunme_rate 已经从 build 函数传入，表示 GLB单位到真实世界的转换系数
        normalized_vertices, center_point = normalize_glb(
            vertices=vertices,
            theoretical_volume=theoretical_volume,
            volume_rate=volume_rate,
            center=True
        )

        # 使用标准化后的顶点
        self.vertices = normalized_vertices
        self.colors = colors
        self.mesh = mesh

        # 获取标准化后的模型位置
        self.x, self.y, self.z = [0, 0, 0]
                   
        # 计算各个方向的距离图
        self.round_distance: dict[direction, DistanceMap] = {}
        self._get_round_distance()

        self.width = np.max(self.round_distance[direction.forward].get_dist_map())
        self.length = np.max(self.round_distance[direction.left].get_dist_map())
        self.height = np.max(self.round_distance[direction.floor].get_dist_map())

    def _get_round_distance(self):
        """
        计算物体在各个方向上的采样距离图（私有方法）

        返回:
            字典，键为方向，值为对应的距离图对象
        """
        for dirt in direction:
            self.round_distance[dirt] = sample(self.mesh, self.colors, dirt)

    def get_distance_map(self, dirt: direction) -> DistanceMap:
        """
        获取指定方向的距离图

        参数:
            dirt: 方向枚举值

        返回:
            对应方向的距离图对象
        """
        return self.round_distance[dirt]

    def set_item_location(self, location: Union[List[int], Tuple[int, int, int]]) -> None:
        """
        设置物体的位置，并更新各个方向距离图的原点坐标

        参数:
            location: 物体的新位置 [x, y, z] 或 (x, y, z)
        """
        if len(location) != 3:
            raise ValueError("location必须包含3个坐标值[x, y, z]")
    
        self.x, self.y, self.z = location

        for dirt in direction:
            # 根据方向计算距离图的原点位置
            temp_location = list(location)  # 使用对齐后的位置

            if dirt == direction.floor or dirt == direction.ceil:
                # 上下方向：调整y坐标
                y = self.y if dirt == direction.floor else self.y + self.height
                temp_location[1] = y
            elif dirt == direction.left or dirt == direction.right:
                # 左右方向：调整x坐标
                x = self.x if dirt == direction.left else self.x + self.length
                temp_location[0] = x
            else:  # forward or backward
                # 前后方向：调整z坐标
                z = self.z if dirt == direction.backward else self.z + self.width
                temp_location[2] = z

            self.round_distance[dirt].move_dist_map(location=temp_location)

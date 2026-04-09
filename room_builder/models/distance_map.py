"""
距离图模块

包含 DistanceMap 类，用于存储和管理某个方向上的距离和颜色信息
"""
import numpy as np
from typing import Tuple, Union, List
from ..utils import direction, SAMPLE_RATE


class DistanceMap:
    """
    距离图类，用于存储和管理某个方向上的距离和颜色信息
    """
    def __init__(
        self,
        dirt: direction,
        x: int,
        y: int,
        z: int,
        height: int,
        width: int,
        initial_distance: int = 0,
        initial_color: Tuple[int, int, int] = (255, 255, 255)
    ):
        """
        初始化距离图

        参数:
            dirt: 距离平面的方向（direction枚举）
            x, y, z: 距离平面原点的坐标
            height: 距离图的高度（采样点数）
            width: 距离图的宽度（采样点数）
            initial_distance: 初始高度（默认为0）
            initial_color: 初始颜色RGB值（默认为白色(255, 255, 255)）
        """
        self.dirt = dirt
        self.x = x
        self.y = y
        self.z = z
        self.height = height
        self.width = width
        # 距离数据：存储每个采样点到表面的距离
        self.distance = np.full((height, width), initial_distance, dtype=np.int16)
        # 颜色数据：存储每个采样点的RGB颜色
        self.color = np.full((height, width, 3), initial_color, dtype=np.uint8)

    def set_dist_map(self, dist_map: np.ndarray) -> None:
        """
        设置距离图数据

        参数:
            dist_map: 距离数据数组，形状应为(height, width)
        """
        if dist_map.shape != (self.height, self.width):
            raise ValueError(f"距离图形状不匹配: 期望{(self.height, self.width)}, 实际{dist_map.shape}")
        self.distance = dist_map

    def set_color_map(self, color_map: np.ndarray) -> None:
        """
        设置颜色图数据

        参数:
            color_map: 颜色数据数组，形状应为(height, width, 3)
        """
        if color_map.shape != (self.height, self.width, 3):
            raise ValueError(f"颜色图形状不匹配: 期望{(self.height, self.width, 3)}, 实际{color_map.shape}")
        self.color = color_map

    def move_dist_map(self, location: Union[List[int], Tuple[int, int, int]]) -> None:
        """
        移动距离图的原点位置

        参数:
            location: 新的原点坐标 [x, y, z] 或 (x, y, z)
        """
        if len(location) != 3:
            raise ValueError("location必须包含3个坐标值[x, y, z]")
        self.x = location[0]
        self.y = location[1]
        self.z = location[2]

    def get_shape(self) -> Tuple[int, int]:
        """
        获取距离图的形状

        返回:
            (height, width) 二元组
        """
        return (self.height, self.width)

    def update(self, 
               cover_distance_map: 'DistanceMap',
               cover_color_map: 'DistanceMap',
               cover_threshold: int = 5) -> None:
        """
        更新距离图，根据覆盖距离图的位置进行局部更新

        参数:
            cover_distance_map: 平面相反方向的距离图对象，用于计算剩余可用空间
            cover_color_map: 平面相同方向的距离图对象，用于得出覆盖的颜色
            cover_threshold: 颜色更新阈值（网格点数量），当物体与平面的距离小于此值时颜色覆盖
        """
        if cover_distance_map.get_shape() != cover_color_map.get_shape():
            raise ValueError(f"cover_distance_map 和 cover_color_map 的形状必须相同，但得到 {cover_distance_map.get_shape()} 和 {cover_color_map.get_shape()}")

        # 计算覆盖距离图在当前距离图中的位置偏移（以采样点为单位）
        offset_x = cover_distance_map.x - self.x
        offset_y = cover_distance_map.y - self.y
        offset_z = cover_distance_map.z - self.z

        # 根据 cover_distance_map 的方向确定平面偏移和深度偏移
        if cover_distance_map.dirt == direction.floor or cover_distance_map.dirt == direction.ceil:
            # XZ平面投影，Y为深度
            plane_offset_1 = offset_x
            plane_offset_2 = offset_z
            depth_offset = abs(offset_y)
        elif cover_distance_map.dirt == direction.left or cover_distance_map.dirt == direction.right:
            # YZ平面投影，X为深度
            plane_offset_1 = offset_y
            plane_offset_2 = offset_z
            depth_offset = abs(offset_x)
        else:  # forward or backward
            # XY平面投影，Z为深度
            plane_offset_1 = offset_x
            plane_offset_2 = offset_y
            depth_offset = abs(offset_z)

        # 获取覆盖距离图的数据
        cover_data = cover_distance_map.get_dist_map()
        cover_height, cover_width = cover_data.shape

        # 计算重叠区域
        # 在当前距离图中的起始和结束位置
        start_y = int(max(0, plane_offset_2))
        start_x = int(max(0, plane_offset_1))
        end_y = int(min(self.height, plane_offset_2 + cover_height))
        end_x = int(min(self.width, plane_offset_1 + cover_width))

        # 如果有重叠区域，进行更新
        if start_y < end_y and start_x < end_x:
            # 在覆盖距离图中的起始和结束位置
            cover_start_y = int(max(0, -plane_offset_2))
            cover_start_x = int(max(0, -plane_offset_1))
            cover_end_y = cover_start_y + (end_y - start_y)
            cover_end_x = cover_start_x + (end_x - start_x)

            # 提取重叠区域
            current_region: np.ndarray = self.distance[start_y:end_y, start_x:end_x].copy()
            cover_region: np.ndarray = cover_data[cover_start_y:cover_end_y, cover_start_x:cover_end_x]

            # 取最小值更新（表示最近的障碍物），同时加上深度偏移
            cover_region_with_offset = depth_offset - cover_region
            updated_distance = np.minimum(current_region, cover_region_with_offset)
            self.distance[start_y:end_y, start_x:end_x] = updated_distance

            # 同样更新颜色图
            if np.min(cover_region_with_offset) < cover_threshold:
                # 根据距离阈值决定使用哪个颜色
                # 当距离大于阈值时，使用平面颜色（保持不变）
                # 当距离小于等于阈值时，使用物体颜色
                cover_color = cover_color_map.get_color_map()

                if cover_color is not None and cover_color.size > 0:
                    cover_color_region: np.ndarray = cover_color[cover_start_y:cover_end_y, cover_start_x:cover_end_x]
                    self.color[start_y:end_y, start_x:end_x] = cover_color_region

    def update_color(self, 
                     cover_color_map: 'DistanceMap') -> None:
        """
        更新颜色图，根据覆盖颜色图的位置进行局部更新
        参数:
            cover_color_map: 平面相同方向的距离图对象，用于得出覆盖的颜色
        """
        # 计算覆盖颜色图在当前颜色图中的位置偏移（以采样点为单位）
        offset_x = cover_color_map.x - self.x
        offset_y = cover_color_map.y - self.y
        offset_z = cover_color_map.z - self.z

        # 根据 cover_color_map 的方向确定平面偏移和深度偏移
        if cover_color_map.dirt == direction.floor or cover_color_map.dirt == direction.ceil:
            # XZ平面投影，Y为深度
            plane_offset_1 = offset_x
            plane_offset_2 = offset_z
        elif cover_color_map.dirt == direction.left or cover_color_map.dirt == direction.right:
            # YZ平面投影，X为深度
            plane_offset_1 = offset_y
            plane_offset_2 = offset_z
        else:  # forward or backward
            # XY平面投影，Z为深度
            plane_offset_1 = offset_x
            plane_offset_2 = offset_y

        # 获取覆盖颜色图的数据
        cover_color_data = cover_color_map.get_color_map()
        cover_height, cover_width, _ = cover_color_data.shape

        # 计算重叠区域
        # 在当前颜色图中的起始和结束位置
        start_y = max(0, plane_offset_2)
        start_x = max(0, plane_offset_1)
        end_y = min(self.height, plane_offset_2 + cover_height)
        end_x = min(self.width, plane_offset_1 + cover_width)

        # 如果有重叠区域，进行更新
        if start_y < end_y and start_x < end_x:

            # 在覆盖颜色图中的起始和结束位置
            cover_start_y = max(0, -plane_offset_2)
            cover_start_x = max(0, -plane_offset_1)
            cover_end_y = cover_start_y + (end_y - start_y)
            cover_end_x = cover_start_x + (end_x - start_x)
            
            # 提取重叠区域
            cover_color_region: np.ndarray = cover_color_data[cover_start_y:cover_end_y, cover_start_x:cover_end_x]
            self.color[start_y:end_y, start_x:end_x] = cover_color_region

    def get_dist_map(self) -> np.ndarray:
        """
        获取距离图数据

        返回:
            距离数据数组
        """
        return self.distance

    def get_color_map(self) -> np.ndarray:
        """
        获取颜色图数据

        返回:
            颜色数据数组
        """
        return self.color

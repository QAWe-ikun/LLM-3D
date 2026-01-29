"""
距离图模块

包含 DistanceMap 类，用于存储和管理某个方向上的距离和颜色信息
"""
import numpy as np
from Utils import direction


class DistanceMap:
    """
    距离图类，用于存储和管理某个方向上的距离和颜色信息
    """
    def __init__(
        self,
        dirt: direction,
        x: float,
        y: float,
        z: float,
        height: int,
        width: int,
        initial_distance: float = 0.0,
        initial_color: tuple[int, int, int] = (255, 255, 255)
    ):
        """
        初始化距离图

        参数:
            dirt: 距离平面的方向（direction枚举）
            x, y, z: 距离平面原点的坐标
            height: 距离图的高度（采样点数）
            width: 距离图的宽度（采样点数）
            initial_distance: 初始距离值（默认为0）
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

    def move_dist_map(self, location: list[float] | tuple[float, float, float]) -> None:
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

    def update(self, cover_dist_map: np.ndarray) -> None:
        """
        更新距离图，取当前距离和覆盖距离的最小值

        参数:
            cover_dist_map: 覆盖的距离图数据
        """
        self.distance = np.minimum(self.distance, cover_dist_map)

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

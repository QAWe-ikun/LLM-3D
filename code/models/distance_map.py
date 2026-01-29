"""
距离图模块

包含 DistanceMap 类，用于存储和管理某个方向上的距离和颜色信息
"""
import numpy as np
from utils import direction, SAMPLE_RATE


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

    def update(self, cover_distance_map: 'DistanceMap', color_threshold: int = 5) -> None:
        """
        更新距离图，根据覆盖距离图的位置进行局部更新

        参数:
            cover_distance_map: 覆盖的距离图对象
            color_threshold: 颜色更新阈值（网格点数量），当距离小于此值时使用平面颜色，否则使用物体颜色
        """
        # 计算覆盖距离图在当前距离图中的位置偏移（以采样点为单位）
        offset_x = int(round((cover_distance_map.x - self.x) / SAMPLE_RATE))
        offset_y = int(round((cover_distance_map.y - self.y) / SAMPLE_RATE))
        offset_z = int(round((cover_distance_map.z - self.z) / SAMPLE_RATE))

        # 根据 cover_distance_map 的方向确定平面偏移和深度偏移
        if cover_distance_map.dirt == direction.up or cover_distance_map.dirt == direction.down:
            # XY平面投影，Z为深度
            plane_offset_1 = offset_x
            plane_offset_2 = offset_y
            depth_offset = offset_z
        elif cover_distance_map.dirt == direction.left or cover_distance_map.dirt == direction.right:
            # YZ平面投影，X为深度
            plane_offset_1 = offset_y
            plane_offset_2 = offset_z
            depth_offset = offset_x
        else:  # forward or backward
            # XZ平面投影，Y为深度
            plane_offset_1 = offset_x
            plane_offset_2 = offset_z
            depth_offset = offset_y

        # 获取覆盖距离图的数据
        cover_data = cover_distance_map.get_dist_map()
        cover_height, cover_width = cover_data.shape

        # 计算重叠区域
        # 在当前距离图中的起始和结束位置
        start_y = max(0, plane_offset_2)
        start_x = max(0, plane_offset_1)
        end_y = min(self.height, plane_offset_2 + cover_height)
        end_x = min(self.width, plane_offset_1 + cover_width)

        # 如果有重叠区域，进行更新
        if start_y < end_y and start_x < end_x:
            # 在覆盖距离图中的起始和结束位置
            cover_start_y = max(0, -plane_offset_2)
            cover_start_x = max(0, -plane_offset_1)
            cover_end_y = cover_start_y + (end_y - start_y)
            cover_end_x = cover_start_x + (end_x - start_x)

            # 提取重叠区域
            current_region: np.ndarray = self.distance[start_y:end_y, start_x:end_x].copy()
            cover_region: np.ndarray = cover_data[cover_start_y:cover_end_y, cover_start_x:cover_end_x]

            # 计算 mask（考虑深度偏移后的距离比较）
            mask = (cover_region + depth_offset) < current_region

            # 取最小值更新（表示最近的障碍物），同时加上深度偏移
            # 使用 int32 避免溢出
            cover_region_with_offset = cover_region.astype(np.int32) + depth_offset
            updated_distance = np.minimum(current_region.astype(np.int32), cover_region_with_offset).astype(np.int16)
            self.distance[start_y:end_y, start_x:end_x] = updated_distance

            # 同样更新颜色图
            cover_color = cover_distance_map.get_color_map()
            if cover_color is not None and cover_color.size > 0 and np.any(mask):
                # 根据距离阈值决定使用哪个颜色
                # 当距离大于阈值时，使用平面颜色（保持不变）
                # 当距离小于等于阈值时，使用物体颜色
                updated_color: np.ndarray = self.color[start_y:end_y, start_x:end_x].copy()
                cover_color_region: np.ndarray = cover_color[cover_start_y:cover_end_y, cover_start_x:cover_end_x]

                # 计算更新后的距离（与上面保持一致）
                cover_region_with_offset = cover_region.astype(np.int32) + depth_offset
                updated_distance = np.minimum(current_region.astype(np.int32), cover_region_with_offset).astype(np.int16)

                # 创建颜色更新的 mask：距离大于等于阈值且需要更新的位置
                color_update_mask = mask & (updated_distance >= color_threshold)

                # 只在满足条件的位置更新为物体颜色
                if np.any(color_update_mask):
                    updated_color[color_update_mask] = cover_color_region[color_update_mask]

                self.color[start_y:end_y, start_x:end_x] = updated_color

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

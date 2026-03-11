"""
平面图模块

包含 PlaneMap 类，表示某个方向上的一个平面及其上的物体
"""
import numpy as np

from ..utils import direction, SAMPLE_RATE, find_opposite_direction
from .distance_map import DistanceMap
from .item import Item


class PlaneMap:
    """
    平面图类，表示某个方向上的一个平面及其上的物体
    """
    def __init__(
        self,
        plane_loc: list[int],
        dirt: direction,
        carry: list[str],
        description: str,
        item_list: list[Item],
        initial_color: tuple[int, int, int] = (255, 255, 255)
    ):
        """
        初始化平面图

        参数:
            plane_loc: 平面位置参数 [x, y, z, height, width, initial_distance]
            dirt: 平面的方向
            carry: 平面上物体的名称列表
            description: 平面的描述
            item_list: 平面上的物体对象列表
            initial_color: 初始颜色 RGB 值（默认为白色 (255, 255, 255)）
        """
        if len(plane_loc) != 6:
            raise ValueError("plane_loc 必须包含 6 个参数 [x, y, z, height, width, initial_distance]")

        self.plane_loc = plane_loc
        self.carry = carry
        self.description = description
        self.item_list = item_list
        self.dirt = dirt

        # 创建该平面的距离图，使用指定的初始距离和颜色
        self.distance = DistanceMap(
            dirt,
            plane_loc[0],
            plane_loc[1],
            plane_loc[2],
            plane_loc[3],
            plane_loc[4],
            initial_distance=plane_loc[5],
            initial_color=initial_color
        )

    def get_dirt(self) -> direction:
        """
        获取平面的方向

        返回:
            方向枚举值
        """
        return self.dirt

    def get_distance(self) -> DistanceMap:
        """
        获取平面的距离图对象

        返回:
            距离图对象
        """
        return self.distance

    def get_dist_map(self) -> np.ndarray:
        """
        获取平面的距离图数组

        返回:
            距离图数组
        """
        return self.distance.get_dist_map()

    def get_color_map(self) -> np.ndarray:
        """
        获取平面的颜色图数组

        返回:
            颜色图数组
        """
        return self.distance.get_color_map()

    def init_color_map(self, init_color_map: np.ndarray) -> None:
        """
        初始化平面的颜色图为默认颜色

        参数:
            init_color_map: 初始颜色图数组
        """
        self.distance.set_color_map(init_color_map)

    def init_dist_map(self, init_dist_map: np.ndarray) -> None:
        """
        初始化平面的距离图为默认距离

        参数:
            init_dist_map: 初始距离图数组
        """
        self.distance.set_dist_map(init_dist_map)

    def update(self, new_item: Item) -> None:
        """
        更新平面的距离图

        参数:
            new_item: 新的物体对象
        """
        self.distance.update(
            cover_distance_map=new_item.get_distance_map(dirt=find_opposite_direction(self.dirt)),
            cover_color_map=new_item.get_distance_map(dirt=self.dirt))

    def find_location(self, new_item: Item) -> tuple[int, int, int] | None:
        """
        为新物体寻找合适的放置位置

        参数:
            new_item: 待放置的物体

        返回:
            合适的位置坐标 (x, y, z)
        """
        return self._find_location_with_distance_map(new_item)

    def _find_location_with_distance_map(self, new_item: Item) -> tuple[int, int, int] | None:
        """
        基于距离图为新物体寻找合适的放置位置

        参数:
            new_item: 待放置的物体

        返回:
            合适的位置坐标 (x, y, z)
        """
        dist_map = self.get_dist_map()
        item_dist_map = new_item.get_distance_map(self.dirt).get_dist_map()

        plane_height, plane_width = dist_map.shape
        proj_h, proj_w = item_dist_map.shape

        # 寻找可以放置物体的位置
        best_location = None

        for i in range(plane_height - proj_h + 1):
            for j in range(plane_width - proj_w + 1):
                region = dist_map[i:i+proj_h, j:j+proj_w] - item_dist_map
                min_distance = np.min(region)

                if min_distance >= 0:
                    best_location = (i, j)
                    break
            
            if best_location:
                break

        if best_location is None:
            return None

        grid_i, grid_j = best_location

        if self.dirt in [direction.floor, direction.ceil]:
            world_x = self.distance.x + grid_j
            world_z = self.distance.z + grid_i
            world_y = self.distance.y
        elif self.dirt in [direction.left, direction.right]:
            world_y = self.distance.y + grid_j
            world_z = self.distance.z + grid_i
            world_x = self.distance.x
        else:
            world_x = self.distance.x + grid_j
            world_y = self.distance.y + grid_i
            world_z = self.distance.z

        if self.dirt == direction.floor:
            return (world_x, world_y, world_z)
        elif self.dirt == direction.ceil:
            return (world_x, world_y - new_item.height, world_z)
        elif self.dirt == direction.left:
            return (world_x, world_y, world_z)
        elif self.dirt == direction.right:
            return (world_x - new_item.length, world_y, world_z)
        elif self.dirt == direction.backward:
            return (world_x, world_y, world_z)
        else:
            return (world_x, world_y, world_z - new_item.height)

    def add_item(self, new_item: Item) -> None:
        """
        向平面添加新物体

        参数:
            new_item: 要添加的物体对象
        """
        self.carry.append(new_item.item_name)
        self.item_list.append(new_item)
        self.update(new_item)

    def update_color(self, new_item: Item) -> None:
        """
        更新平面的颜色图

        参数:
            new_item: 新的物体对象
        """
        self.distance.update_color(
            cover_color_map=new_item.get_distance_map(dirt=self.dirt))

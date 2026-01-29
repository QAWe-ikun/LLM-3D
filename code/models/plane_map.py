"""
平面图模块

包含 PlaneMap 类，表示某个方向上的一个平面及其上的物体
"""
from utils import direction, SAMPLE_RATE
from .distance_map import DistanceMap
from .item import Item


class PlaneMap:
    """
    平面图类，表示某个方向上的一个平面及其上的物体
    """
    def __init__(
        self,
        plane_loc: list[float],
        dirt: direction,
        carry: list[str],
        description: list[str],
        item_list: list[Item],
        initial_color: tuple[int, int, int] = (255, 255, 255)
    ):
        """
        初始化平面图

        参数:
            plane_loc: 平面位置参数 [x, y, z, height, width, initial_distance]
            dirt: 平面的方向
            carry: 平面上物体的名称列表
            description: 平面上物体的描述列表
            item_list: 平面上的物体对象列表
            initial_color: 初始颜色RGB值（默认为白色(255, 255, 255)）
        """
        if len(plane_loc) != 6:
            raise ValueError("plane_loc必须包含6个参数[x, y, z, height, width, initial_distance]")

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
            int(plane_loc[3]),
            int(plane_loc[4]),
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

    def update_distance(self, distance: DistanceMap) -> None:
        """
        更新平面的距离图

        参数:
            distance: 新的距离图对象（通常是物体的距离图）
        """
        self.distance.update(cover_distance_map=distance)

    def find_location(self, new_item: Item) -> tuple[float, float, float]:
        """
        为新物体寻找合适的放置位置

        参数:
            new_item: 待放置的物体

        返回:
            合适的位置坐标 (x, y, z)

        TODO: 实现基于距离图的位置搜索算法
        """
        # TODO: 实现位置搜索逻辑
        # 可以基于距离图找到空闲区域
        # 考虑物体尺寸和碰撞检测
        raise NotImplementedError("find_location方法尚未实现")

    def add_item(self, new_item: Item) -> None:
        """
        向平面添加新物体

        参数:
            new_item: 要添加的物体对象
        """
        self.carry.append(new_item.item_name)
        self.description.append(new_item.item_description)
        self.item_list.append(new_item)

        # 更新平面的距离图
        self.update_distance(new_item.get_distance_map(dirt=self.dirt))

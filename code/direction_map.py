"""
方向图模块

包含 DirectionMap 类，管理某个方向上的所有平面图
"""
from Utils import direction, find_opposite_direction
from plane_map import PlaneMap
from item import Item


class DirectionMap:
    """
    方向图类，管理某个方向上的所有平面图
    """
    def __init__(self, dirt: direction):
        """
        初始化方向图

        参数:
            dirt: 方向枚举值
        """
        self.dirt = dirt
        self.plane_map_list: list[PlaneMap] = []

    def add_plane_map(self, new_plane_map: PlaneMap) -> None:
        """
        添加新的平面图

        参数:
            new_plane_map: 要添加的平面图对象

        TODO: 实现基于LLM的智能决策，判断是否需要添加新平面
        """
        # TODO: 使用LLM判断是否应该添加这个平面
        # 可以基于语义相似度、空间关系等因素决策
        self.plane_map_list.append(new_plane_map)

    def choice_plane_map(self, new_item: Item) -> PlaneMap:
        """
        为新物体选择合适的平面图

        参数:
            new_item: 待放置的物体

        返回:
            选中的平面图对象

        TODO: 实现基于word2vec和关系计算的平面选择算法
        """
        # TODO: 使用word2vec计算语义相似度
        # 结合空间关系选择最合适的平面
        # 如果没有合适的平面，可能需要创建新平面
        raise NotImplementedError("choice_plane_map方法尚未实现")

    def update_plane(self, new_item: Item) -> None:
        """
        更新所有平面图的距离信息

        参数:
            new_item: 新添加的物体
        """
        for plane in self.plane_map_list:
            plane_dirt = plane.get_dirt()
            # 获取相反方向（物体对平面的影响方向）
            dirt = find_opposite_direction(plane_dirt)
            plane.update_distance(new_item.get_distance_map(dirt=dirt))

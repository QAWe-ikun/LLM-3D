"""
方向图模块

包含 DirectionMap 类，管理某个方向上的所有平面图
"""
import json
from ..utils import direction, find_opposite_direction
from .plane_map import PlaneMap
from .item import Item
from ..services import get_client


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

        使用LLM判断是否应该添加这个平面
        """
        # 如果是第一个平面，直接添加
        if len(self.plane_map_list) == 0:
            self.plane_map_list.append(new_plane_map)
            print(f"  → 添加第一个平面到 {self.dirt.name} 方向")
            return

        # 构造提示词，让LLM判断是否应该添加新平面
        existing_planes_info = []
        for plane in self.plane_map_list:
            plane_info = {
                "物体数量": len(plane.item_list),
                "物体列表": plane.carry,
                "平面描述": plane.description
            }
            existing_planes_info.append(plane_info)

        new_plane_info = {
            "平面描述": new_plane_map.description
        }

        prompt = f"""
你是一个3D场景布局专家。现在需要判断是否应该在 {self.dirt.name} 方向添加一个新的平面。

当前方向已有的平面：
{json.dumps(existing_planes_info, ensure_ascii=False, indent=2)}

待添加的新平面：
{json.dumps(new_plane_info, ensure_ascii=False, indent=2)}

请判断是否应该添加这个新平面。考虑因素：
1. 语义相关性：新平面上的物体与现有平面的物体是否应该分开放置
2. 功能分区：是否需要创建新的功能区域

请只回答 "是" 或 "否"，不要有其他内容。
"""

        try:
            client = get_client()
            response = client.chat(prompt)
            should_add = "是" in response.strip()

            if should_add:
                self.plane_map_list.append(new_plane_map)
                print(f"  → LLM决策：添加新平面到 {self.dirt.name} 方向")
            else:
                print(f"  → LLM决策：不添加新平面，使用现有平面")
        except Exception as e:
            # 如果LLM调用失败，默认不添加
            print(f"  ⚠ LLM调用失败: {e}，默认不添加平面")

    def choice_plane_map(self, new_item: Item) -> PlaneMap:
        """
        为新物体选择合适的平面图

        参数:
            new_item: 待放置的物体

        返回:
            选中的平面图对象

        使用LLM基于语义相似度和空间关系选择最合适的平面
        """
        if len(self.plane_map_list) == 0:
            raise ValueError(f"{self.dirt.name} 方向没有可用的平面")

        # 如果只有一个平面，直接返回
        if len(self.plane_map_list) == 1:
            print(f"  → 只有一个平面，直接选择")
            return self.plane_map_list[0]

        # 构造提示词，让LLM选择最合适的平面
        planes_info = []
        for i, plane in enumerate(self.plane_map_list):
            plane_info = {
                "平面编号": i,
                "物体数量": len(plane.item_list),
                "物体列表": plane.carry,
                "平面描述": plane.description
            }
            planes_info.append(plane_info)

        item_info = {
            "物体名称": new_item.item_name,
            "物体描述": new_item.item_description
        }

        prompt = f"""
你是一个3D场景布局专家。现在需要为一个新物体选择最合适的平面进行放置。

方向：{self.dirt.name}

可选的平面：
{json.dumps(planes_info, ensure_ascii=False, indent=2)}

待放置的物体：
{json.dumps(item_info, ensure_ascii=False, indent=2)}

请选择最合适的平面编号。考虑因素：
1. 语义相关性：新物体与平面上已有物体的功能关联
2. 空间利用：平面上的物体数量和空间占用
3. 场景合理性：物体的摆放是否符合真实场景的习惯

请只回答平面编号（数字），不要有其他内容。
"""

        try:
            client = get_client()
            response = client.chat(prompt)

            # 解析响应，提取平面编号
            plane_index = int(response.strip())

            if 0 <= plane_index < len(self.plane_map_list):
                print(f"  → LLM选择：平面 {plane_index}")
                return self.plane_map_list[plane_index]
            else:
                print(f"  ⚠ LLM返回的平面编号 {plane_index} 无效，使用第一个平面")
                return self.plane_map_list[0]

        except Exception as e:
            # 如果LLM调用失败，默认选择第一个平面
            print(f"  ⚠ LLM调用失败: {e}，使用第一个平面")
            return self.plane_map_list[0]

    def update_plane(self, new_item: Item) -> None:
        """
        更新所有平面图的距离信息

        参数:
            new_item: 新添加的物体
        """
        for plane in self.plane_map_list:
            plane.update(new_item)

    def update_base_plane(self, new_item: Item) -> None:
        """
        更新基础平面的距离信息

        参数:
            new_item: 新添加的物体
        """
        if len(self.plane_map_list) == 0:
            raise ValueError(f"{self.dirt.name} 方向没有可用的平面")
        # 第一个平面是基础平面
        base_plane = self.plane_map_list[0]
        if new_item not in base_plane.item_list:
            base_plane.update_color(new_item)

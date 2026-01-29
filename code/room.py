"""
房间模块

包含 Room 类，表示一个完整的3D场景空间
"""
from Utils import direction
from direction_map import DirectionMap
from plane_map import PlaneMap
from item import Item


class Room:
    """
    房间类，表示一个完整的3D场景空间
    """
    def __init__(
        self,
        room_type: str,
        length: float,
        width: float,
        height: float,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        sample_interval: float = 0.1,
        initial_color: tuple[int, int, int] = (255, 255, 255)
    ):
        """
        初始化房间

        参数:
            room_type: 房间类型（如"卧室"、"客厅"、"厨房"等）
            length: 房间长度（x方向）
            width: 房间宽度（y方向）
            height: 房间高度（z方向）
            x: 房间原点x坐标（默认为0）
            y: 房间原点y坐标（默认为0）
            z: 房间原点z坐标（默认为0）
            sample_interval: 采样间隔（米），用于计算距离图的采样点数量（默认0.1米）
            initial_color: 初始颜色RGB值（默认为白色(255, 255, 255)）
        """
        self.room_type = room_type
        self.length = length
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.z = z
        self.sample_interval = sample_interval
        self.initial_color = initial_color

        self.direction_map_dict: dict[direction, DirectionMap] = {}

        # 计算采样点数量
        length_samples = int(length / sample_interval)
        width_samples = int(width / sample_interval)
        height_samples = int(height / sample_interval)

        # 为每个方向创建方向图并添加初始平面
        for dirt in direction:
            self.direction_map_dict[dirt] = DirectionMap(dirt=dirt)

            # 根据方向确定平面的位置、尺寸和初始距离
            if dirt == direction.down:
                # 地板：xy平面，位置在底部，初始距离为房间高度
                plane_loc = [x, y, z, length_samples, width_samples, height]
            elif dirt == direction.up:
                # 天花板：xy平面，位置在顶部，初始距离为房间高度
                plane_loc = [x, y, z + height, length_samples, width_samples, height]
            elif dirt == direction.left:
                # 左墙：yz平面，位置在左侧，初始距离为房间长度
                plane_loc = [x, y, z, width_samples, height_samples, length]
            elif dirt == direction.right:
                # 右墙：yz平面，位置在右侧，初始距离为房间长度
                plane_loc = [x + length, y, z, width_samples, height_samples, length]
            elif dirt == direction.backward:
                # 后墙：xz平面，位置在后侧，初始距离为房间宽度
                plane_loc = [x, y, z, length_samples, height_samples, width]
            else:  # direction.forward
                # 前墙：xz平面，位置在前侧，初始距离为房间宽度
                plane_loc = [x, y + width, z, length_samples, height_samples, width]

            # 创建初始平面（空的，没有物体）
            initial_plane = PlaneMap(
                plane_loc=plane_loc,
                dirt=dirt,
                carry=[],
                description=[],
                item_list=[],
                initial_color=self.initial_color
            )

            # 将初始平面添加到方向图
            self.direction_map_dict[dirt].add_plane_map(initial_plane)

    def choice_direction_map(self, new_item: Item) -> DirectionMap:
        """
        为新物体选择合适的方向图

        参数:
            new_item: 待放置的物体

        返回:
            选中的方向图对象

        TODO: 实现基于word2vec和关系计算的方向选择算法
        """
        # TODO: 使用word2vec计算语义相似度
        # 结合物体属性和房间布局选择最合适的方向
        # 例如：画应该挂在墙上（left/right/forward/backward）
        #      灯应该在天花板上（up）
        #      地毯应该在地板上（down）
        raise NotImplementedError("choice_direction_map方法尚未实现")

    def update_direction(self, new_item: Item) -> None:
        """
        更新所有方向图的距离信息

        参数:
            new_item: 新添加的物体
        """
        for dirt_map in self.direction_map_dict.values():
            dirt_map.update_plane(new_item)

    def add_item(self, new_item: Item) -> None:
        """
        向房间添加新物体

        参数:
            new_item: 要添加的物体对象
        """
        print(f"\n{'='*60}")
        print(f"开始添加物体: {new_item.item_name}")
        print(f"物体描述: {new_item.item_description}")
        print(f"{'='*60}")

        # 1. 选择合适的方向
        print(f"\n[步骤 1/6] 选择合适的方向...")
        direction_map = self.choice_direction_map(new_item)
        print(f"✓ 已选择方向: {direction_map.dirt.name}")

        # 2. 在该方向上选择合适的平面
        print(f"\n[步骤 2/6] 在 {direction_map.dirt.name} 方向上选择合适的平面...")
        plane_map = direction_map.choice_plane_map(new_item)
        print(f"✓ 已选择平面，当前平面上有 {len(plane_map.item_list)} 个物体")

        # 3. 在平面上找到合适的位置
        print(f"\n[步骤 3/6] 在平面上寻找合适的位置...")
        location = plane_map.find_location(new_item)
        print(f"✓ 找到位置: ({location[0]:.2f}, {location[1]:.2f}, {location[2]:.2f})")

        # 4. 设置物体位置
        print(f"\n[步骤 4/6] 设置物体位置...")
        new_item.set_item_location(location)
        print(f"✓ 物体位置已设置")

        # 5. 将物体添加到平面
        print(f"\n[步骤 5/6] 将物体添加到平面...")
        plane_map.add_item(new_item)
        print(f"✓ 物体已添加到平面，平面上现有 {len(plane_map.item_list)} 个物体")

        # 6. 更新所有方向的距离信息
        print(f"\n[步骤 6/6] 更新所有方向的距离信息...")
        self.update_direction(new_item)
        print(f"✓ 距离信息已更新")

        print(f"\n{'='*60}")
        print(f"物体 {new_item.item_name} 添加完成！")
        print(f"房间内共有 {self.get_item_count()} 个物体")
        print(f"{'='*60}\n")

    def get_all_items(self) -> list[Item]:
        """
        获取房间中的所有物体

        返回:
            物体对象列表
        """
        items = []
        for dirt_map in self.direction_map_dict.values():
            for plane_map in dirt_map.plane_map_list:
                items.extend(plane_map.item_list)
        return items

    def get_item_count(self) -> int:
        """
        获取房间中物体的总数

        返回:
            物体数量
        """
        return len(self.get_all_items())

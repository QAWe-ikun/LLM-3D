"""
3D场景布局系统的核心模块

包含距离图、物体、平面图、方向图和房间等核心类
"""
import numpy as np
from Utils import direction, find_glb_model, read_glb_vertices, get_model_size, sample, find_opposite_direction, SAMPLE_RATE


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


class Item:
    """
    物体类，表示3D场景中的一个物体
    """
    def __init__(self, item_name: str, item_description: str):
        """
        初始化物体

        参数:
            item_name: 物体名称
            item_description: 物体描述信息
        """
        self.item_name = item_name
        self.item_description = item_description

        # 加载GLB模型文件
        file_path = find_glb_model(item_name)
        vertices, colors, mesh = read_glb_vertices(file_path)

        self.vertices = vertices
        self.colors = colors
        self.mesh = mesh

        # 获取模型尺寸和采样参数
        x, y, z, length, width, height, length_sample_num, width_sample_num, height_sample_num = get_model_size(
            item_vertices=vertices
        )

        # 边界框起点坐标
        self.x, self.y, self.z = x, y, z
        # 边界框尺寸
        self.length, self.width, self.height = length, width, height
        # 采样点数量
        self.length_sample_num = length_sample_num
        self.width_sample_num = width_sample_num
        self.height_sample_num = height_sample_num

        # 计算各个方向的距离图
        self.round_distance = self._get_round_distance()

    def _get_round_distance(self) -> dict[direction, DistanceMap]:
        """
        计算物体在各个方向上的采样距离图（私有方法）

        返回:
            字典，键为方向，值为对应的距离图对象
        """
        round_distance = {}
        for dirt in direction:
            round_distance[dirt] = sample(self.mesh, self.colors, dirt)
        return round_distance

    def get_distance_map(self, dirt: direction) -> DistanceMap:
        """
        获取指定方向的距离图

        参数:
            dirt: 方向枚举值

        返回:
            对应方向的距离图对象
        """
        return self.round_distance[dirt]

    def set_item_location(self, location: list[float] | tuple[float, float, float]) -> None:
        """
        设置物体的位置，并更新各个方向距离图的原点坐标

        参数:
            location: 物体的新位置 [x, y, z] 或 (x, y, z)
        """
        if len(location) != 3:
            raise ValueError("location必须包含3个坐标值[x, y, z]")

        for dirt in direction:
            # 根据方向计算距离图的原点位置
            temp_location = list(location)  # 转换为list以便修改

            if dirt == direction.up or dirt == direction.down:
                # 上下方向：调整z坐标
                z = self.z if dirt == direction.down else self.z + self.height
                temp_location[2] = z
            elif dirt == direction.left or dirt == direction.right:
                # 左右方向：调整x坐标
                x = self.x if dirt == direction.left else self.x + self.length
                temp_location[0] = x
            else:  # forward or backward
                # 前后方向：调整y坐标
                y = self.y if dirt == direction.backward else self.y + self.width
                temp_location[1] = y

            self.round_distance[dirt].move_dist_map(location=temp_location)


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
            distance: 新的距离图对象
        """
        self.distance.update(cover_dist_map=distance.get_dist_map())

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

def build(
    room_type: str,
    length: float,
    width: float,
    height: float,
    item_list: list[tuple[str, str]],
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
    sample_interval: float = SAMPLE_RATE,
    initial_color: tuple[int, int, int] = (255, 255, 255)
) -> Room:
    """
    构建房间布局

    参数:
        room_type: 房间类型（如"卧室"、"客厅"、"厨房"等）
        length: 房间长度（x方向）
        width: 房间宽度（y方向）
        height: 房间高度（z方向）
        item_list: 物体信息列表，每个元素是 (物体名称, 物体描述) 的元组
        x: 房间原点x坐标（默认为0）
        y: 房间原点y坐标（默认为0）
        z: 房间原点z坐标（默认为0）
        sample_interval: 采样间隔（米），用于计算距离图的采样点数量
        initial_color: 初始颜色RGB值（默认为白色(255, 255, 255)）

    返回:
        构建好的房间对象

    示例:
        >>> item_list = [("床", "双人床"), ("桌子", "书桌")]
        >>> room = build("卧室", 5.0, 4.0, 3.0, item_list)
        >>> # 自定义初始颜色为浅灰色
        >>> room = build("卧室", 5.0, 4.0, 3.0, item_list, initial_color=(200, 200, 200))
    """
    room = Room(
        room_type=room_type,
        length=length,
        width=width,
        height=height,
        x=x,
        y=y,
        z=z,
        sample_interval=sample_interval,
        initial_color=initial_color
    )
    for item_name, item_description in item_list:
        # 根据物体名称和描述创建Item对象
        item = Item(item_name=item_name, item_description=item_description)
        room.add_item(item)
    return room


"""
房间模块

包含 Room 类，表示一个完整的3D场景空间
"""
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 设置非交互式后端，避免Tk错误
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from ..utils import direction, SAMPLE_RATE, find_opposite_direction, align_to_sample_grid
from .direction_map import DirectionMap
from .plane_map import PlaneMap
from .item import Item
from ..services import get_client


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
        sample_interval: float = SAMPLE_RATE,
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
            sample_interval: 采样间隔（米），用于计算距离图的采样点数量，默认使用全局 SAMPLE_RATE
            initial_color: 初始颜色RGB值（默认为白色(255, 255, 255)）
        """
        self.room_type = room_type
        self.length = length
        self.width = width
        self.height = height
        self.x = align_to_sample_grid(x)
        self.y = align_to_sample_grid(y)
        self.z = align_to_sample_grid(z)
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
            if dirt == direction.floor:
                # 地板：xz平面，位置在底部，初始距离为房间高度
                plane_loc = [align_to_sample_grid(x), align_to_sample_grid(y), align_to_sample_grid(z), length_samples, height_samples, width_samples]
            elif dirt == direction.ceil:
                # 天花板：xz平面，位置在顶部，初始距离为房间高度
                plane_loc = [align_to_sample_grid(x), align_to_sample_grid(y + width), align_to_sample_grid(z), length_samples, height_samples, width_samples]
            elif dirt == direction.left:
                # 左墙：yz平面，位置在左侧，初始距离为房间长度
                plane_loc = [align_to_sample_grid(x), align_to_sample_grid(y), align_to_sample_grid(z), width_samples, height_samples, length_samples]
            elif dirt == direction.right:
                # 右墙：yz平面，位置在右侧，初始距离为房间长度
                plane_loc = [align_to_sample_grid(x + length), align_to_sample_grid(y), align_to_sample_grid(z), width_samples, height_samples, length_samples]
            elif dirt == direction.backward:
                # 后墙：xy平面，位置在后侧，初始距离为房间宽度
                plane_loc = [align_to_sample_grid(x), align_to_sample_grid(y), align_to_sample_grid(z + height), length_samples, width_samples, height_samples]
            else:  # direction.forward
                # 前墙：xy平面，位置在前侧，初始距离为房间宽度
                plane_loc = [align_to_sample_grid(x), align_to_sample_grid(y), align_to_sample_grid(z), length_samples, width_samples, height_samples]

            # 创建初始平面（空的，没有物体）
            initial_plane = PlaneMap(
                plane_loc=plane_loc,
                dirt=dirt,
                carry=[],
                description=f"初始平面:{dirt.name}",
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

        使用LLM基于语义和场景常识选择最合适的方向
        """
        # 构造提示词，让LLM选择最合适的方向
        item_info = {
            "物体名称": new_item.item_name,
            "物体描述": new_item.item_description
        }

        # 收集各个方向的信息
        directions_info = {}
        for dirt, dirt_map in self.direction_map_dict.items():
            total_items = sum(len(plane.item_list) for plane in dirt_map.plane_map_list)
            all_items = []
            for plane in dirt_map.plane_map_list:
                all_items.extend(plane.carry)

            directions_info[dirt.name] = {
                "物体数量": total_items,
                "物体列表": all_items
            }

        prompt = f"""
你是一个3D场景布局专家。现在需要为一个新物体选择最合适的放置方向。

房间类型：{self.room_type}
房间尺寸：长{self.length}米 × 宽{self.width}米 × 高{self.height}米

待放置的物体：
{json.dumps(item_info, ensure_ascii=False, indent=2)}

各个方向的当前状态：
{json.dumps(directions_info, ensure_ascii=False, indent=2)}

可选方向说明：
- ceil: 天花板（适合吊灯、吊扇等）
- floor: 地板（适合家具、地毯等）
- left/right/forward/backward: 墙面（适合挂画、壁灯、柜子等）

请根据物体的特性和真实场景的常识，选择最合适的方向。
例如：
- 床、桌子、椅子 → floor（地板）
- 吊灯、吊扇 → ceil（天花板）
- 挂画、壁灯、书架 → left/right/forward/backward（墙面）

请只回答方向名称（ceil/floor/left/right/forward/backward），不要有其他内容。
"""

        try:
            client = get_client()
            response = client.chat(prompt)

            # 解析响应，提取方向
            direction_name = response.strip().lower()

            # 尝试匹配方向
            for dirt in direction:
                if dirt.name.lower() == direction_name:
                    print(f"  → LLM选择方向: {dirt.name}")
                    return self.direction_map_dict[dirt]

            # 如果没有匹配到，默认选择 floor（地板）
            print(f"  ⚠ LLM返回的方向 '{direction_name}' 无效，使用默认方向 floor")
            return self.direction_map_dict[direction.floor]

        except Exception as e:
            # 如果LLM调用失败，默认选择 floor（地板）
            print(f"  ⚠ LLM调用失败: {e}，使用默认方向 floor")
            return self.direction_map_dict[direction.floor]

    def update_direction(self, new_item: Item, placed_dirt: direction) -> None:
        """
        更新所有方向图的距离信息

        参数:
            new_item: 新添加的物体
        """
        for dirt, dirt_map in self.direction_map_dict.items():
            if dirt != placed_dirt:
                dirt_map.update_plane(new_item)

    def create_and_add_plane_from_item(self, new_item: Item, direction_map: DirectionMap, plane_map: PlaneMap) -> None:
        """
        根据新添加的物体创建新平面并判断是否添加到方向图中

        当一个物体被添加到某个方向的平面上后，该物体可能会在这个方向上形成一个新的"层"。
        例如：在地板上放置桌子后，桌子顶部可以作为一个新的平面层。

        参数:
            new_item: 新添加的物体
            direction_map: 物体所在的方向图
            plane_map: 物体所在的平面图
        """
        # 根据方向确定新平面的位置和尺寸
        if direction_map.dirt == direction.ceil:
            # 地板方向：新平面在物体顶部，xz平面
            plane_loc = [
                align_to_sample_grid(new_item.x),
                align_to_sample_grid(new_item.y),
                align_to_sample_grid(new_item.z),
                new_item.length,
                new_item.height,
                new_item.width
            ]
        elif direction_map.dirt == direction.floor:
            # 天花板方向：新平面在物体底部，xz平面
            plane_loc = [
                align_to_sample_grid(new_item.x),
                align_to_sample_grid(new_item.y + new_item.width),
                align_to_sample_grid(new_item.z),
                new_item.length,
                new_item.height,
                new_item.width
            ]
        elif direction_map.dirt == direction.left:
            # 左墙方向：新平面在物体右侧，yz平面
            plane_loc = [
                align_to_sample_grid(new_item.x + new_item.length),
                align_to_sample_grid(new_item.y),
                align_to_sample_grid(new_item.z),
                new_item.width,
                new_item.height,
                new_item.length
            ]
        elif direction_map.dirt == direction.right:
            # 右墙方向：新平面在物体左侧，yz平面
            plane_loc = [
                align_to_sample_grid(new_item.x),
                align_to_sample_grid(new_item.y),
                align_to_sample_grid(new_item.z),
                new_item.width,
                new_item.height,
                new_item.length
            ]
        elif direction_map.dirt == direction.backward:
            # 后墙方向：新平面在物体前侧，xy平面
            plane_loc = [
                align_to_sample_grid(new_item.x),
                align_to_sample_grid(new_item.y),
                align_to_sample_grid(new_item.z),
                new_item.length,
                new_item.width,
                new_item.height
            ]
        else:  # direction.forward
            # 前墙方向：新平面在物体后侧，xy平面
            plane_loc = [
                align_to_sample_grid(new_item.x),
                align_to_sample_grid(new_item.y),
                align_to_sample_grid(new_item.z + new_item.height),
                new_item.length,
                new_item.width,
                new_item.height
            ]

        # 创建新的平面对象
        new_plane = PlaneMap(
            plane_loc=plane_loc,
            dirt=direction_map.dirt,
            carry=[],
            description=f"物体{new_item.item_name}的{direction_map.dirt.name}平面，物体的具体描述{new_item.item_description}",
            item_list=[],
            initial_color=self.initial_color
        )

        # 获取相反方向的距离图用于初始化颜色图
        opposite_dirt = find_opposite_direction(direction_map.dirt)
        opposite_color_map = new_item.get_distance_map(opposite_dirt).get_color_map()
        
        # 获取新平面的距离图对象
        new_plane_dist = new_plane.get_distance()
        
        # 确保颜色图形状与平面距离图匹配
        expected_shape = (new_plane_dist.height, new_plane_dist.width, 3)
        if opposite_color_map.shape != expected_shape:
            # 如果形状不匹配，进行转置或裁剪
            if len(opposite_color_map.shape) == 3 and opposite_color_map.shape[0:2] == (new_plane_dist.width, new_plane_dist.height):
                # 需要转置
                opposite_color_map = np.transpose(opposite_color_map, (1, 0, 2))
            else:
                # 创建默认颜色图
                opposite_color_map = np.full(expected_shape, 255, dtype=np.uint8)
        
        # 初始化新平面的颜色图
        new_plane.init_color_map(opposite_color_map)

        # 获取new_item的距离图对象和数据
        item_height, item_width = new_plane_dist.get_dist_map().shape

        # 创建一个与item_dist_map同样大小的数组，初始化为plane_map的初始距离
        new_dist_map = np.full((item_height, item_width), 0, dtype=np.int16)

        # 计算new_item在plane_map中的位置偏移（以采样点为单位）
        offset_x = new_plane_dist.x - plane_map.get_distance().x
        offset_y = new_plane_dist.y - plane_map.get_distance().y
        offset_z = new_plane_dist.z - plane_map.get_distance().z

        # 根据方向确定平面偏移
        if direction_map.dirt == direction.floor or direction_map.dirt == direction.ceil:
            plane_offset_1 = offset_x
            plane_offset_2 = offset_y
        elif direction_map.dirt == direction.left or direction_map.dirt == direction.right:
            plane_offset_1 = offset_y
            plane_offset_2 = offset_z
        else:
            plane_offset_1 = offset_x
            plane_offset_2 = offset_z

        # 计算重叠区域
        plane_dist_map = plane_map.get_dist_map()
        plane_height, plane_width = plane_dist_map.shape

        # 在plane_map中的起始和结束位置
        plane_start_y = max(0, plane_offset_2)
        plane_start_x = max(0, plane_offset_1)
        plane_end_y = min(plane_height, plane_offset_2 + item_height)
        plane_end_x = min(plane_width, plane_offset_1 + item_width)

        # 在item中的起始和结束位置
        item_start_y = max(0, -plane_offset_2)
        item_start_x = max(0, -plane_offset_1)
        item_end_y = item_start_y + (plane_end_y - plane_start_y)
        item_end_x = item_start_x + (plane_end_x - plane_start_x)

        # 如果有重叠区域，进行相减
        if plane_start_y < plane_end_y and plane_start_x < plane_end_x:
            plane_region = plane_dist_map[plane_start_y:plane_end_y, plane_start_x:plane_end_x]
            item_region = new_plane_dist.get_dist_map()[item_start_y:item_end_y, item_start_x:item_end_x]
            new_dist_map[item_start_y:item_end_y, item_start_x:item_end_x] = plane_region - item_region

        # 初始化新平面的距离图
        new_plane.init_dist_map(new_dist_map)

        # 调用 add_plane_map 进行判断和添加
        direction_map.add_plane_map(new_plane)

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
        print(f"\n[步骤 1/7] 选择合适的方向...")
        direction_map = self.choice_direction_map(new_item)
        print(f"[OK] 已选择方向: {direction_map.dirt.name}")

        # 2. 在该方向上选择合适的平面
        print(f"\n[步骤 2/7] 在 {direction_map.dirt.name} 方向上选择合适的平面...")
        plane_map = direction_map.choice_plane_map(new_item)
        print(f"[OK] 已选择平面，当前平面上有 {len(plane_map.item_list)} 个物体")

        # 3. 在平面上找到合适的位置
        print(f"\n[步骤 3/7] 在平面上寻找合适的位置...")
        location = plane_map.find_location(new_item)
        if location is None:
            print(f"[错误] 未找到合适的位置")
            return
        print(f"[OK] 找到位置: ({location[0]}, {location[1]}, {location[2]})")

        # 4. 设置物体位置
        print(f"\n[步骤 4/7] 设置物体位置...")
        new_item.set_item_location(location)
        print(f"[OK] 物体位置已设置")

        # 5. 将物体添加到平面
        print(f"\n[步骤 5/7] 将物体添加到平面...")
        plane_map.add_item(new_item)
        print(f"[OK] 物体已添加到平面，平面上现有 {len(plane_map.item_list)} 个物体")

        # 6. 更新所有方向的距离信息
        print(f"\n[步骤 6/7] 更新所有其他方向的距离信息...")
        self.update_direction(new_item, direction_map.dirt)
        self.direction_map_dict[direction_map.dirt].update_base_plane(new_item)
        print(f"[OK] 距离信息已更新")

        # 7. 判断是否应该新增平面
        print(f"\n[步骤 7/7] 判断是否需要新增平面...")
        self.create_and_add_plane_from_item(new_item, direction_map, plane_map)
        print(f"[OK] 平面判断完成")

        print(f"\n{'='*60}")
        print(f"物体 {new_item.item_name} 添加完成！")
        print(f"房间内现有 {self.get_item_count()} 个物体")
        print(f"{'='*60}\n")

        # 可视化当前房间平面图
        self.visualize_floor_plan()

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

    def visualize_floor_plan(self) -> None:
        """
        可视化房间的俯视平面图（从上往下看）
        基于地板方向的color_map显示
        """
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

        # 获取地板方向的平面列表
        floor_direction = self.direction_map_dict[direction.floor]
        plane_map = floor_direction.plane_map_list[0]

        # 获取该平面的颜色图
        color_map = plane_map.distance.get_color_map()
        dist_map = plane_map.distance.get_dist_map()
        items = self.get_item_count()

        import os
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        plt.imshow(color_map)
        filename = f'{output_dir}/floor_plan_{items}_items.png'
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"平面图已保存: {filename}")

        plt.imshow(dist_map)
        filename = f'{output_dir}/floor_plan_{items}_items_dist.png'
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"平面图已保存: {filename}")

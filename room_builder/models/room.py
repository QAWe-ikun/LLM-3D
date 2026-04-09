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

        # 计算采样点数量 - 确保转成Python原生整数
        length_samples = int(float(length) / float(sample_interval))
        width_samples = int(float(width) / float(sample_interval))
        height_samples = int(float(height) / float(sample_interval))

        # 为每个方向创建方向图并添加初始平面
        for dirt in direction:
            self.direction_map_dict[dirt] = DirectionMap(dirt=dirt)

            # 根据方向确定平面的位置、尺寸和初始距离
            if dirt == direction.floor:
                plane_loc = [
                    align_to_sample_grid(x), 
                    align_to_sample_grid(y), 
                    align_to_sample_grid(z), 
                    int(length_samples),
                    int(height_samples), 
                    int(width_samples)
                ]
            elif dirt == direction.ceil:
                plane_loc = [
                    align_to_sample_grid(x), 
                    align_to_sample_grid(y + width), 
                    align_to_sample_grid(z), 
                    int(length_samples),
                    int(height_samples), 
                    int(width_samples)
                ]
            elif dirt == direction.left:
                plane_loc = [
                    align_to_sample_grid(x), 
                    align_to_sample_grid(y), 
                    align_to_sample_grid(z), 
                    int(width_samples),
                    int(height_samples), 
                    int(length_samples)
                ]
            elif dirt == direction.right:
                plane_loc = [
                    align_to_sample_grid(x + length), 
                    align_to_sample_grid(y), 
                    align_to_sample_grid(z), 
                    int(width_samples),
                    int(height_samples), 
                    int(length_samples)
                ]
            elif dirt == direction.backward:
                plane_loc = [
                    align_to_sample_grid(x), 
                    align_to_sample_grid(y), 
                    align_to_sample_grid(z + height), 
                    int(length_samples),
                    int(width_samples), 
                    int(height_samples)
                ]
            else:  # direction.forward
                plane_loc = [
                    align_to_sample_grid(x), 
                    align_to_sample_grid(y), 
                    align_to_sample_grid(z), 
                    int(length_samples),
                    int(width_samples), 
                    int(height_samples)
                ]

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
        """为新物体选择合适的方向图"""
        item_info = {
            "物体名称": new_item.item_name,
            "物体描述": new_item.item_description
        }

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
            direction_name = response.strip().lower()

            for dirt in direction:
                if dirt.name.lower() == direction_name:
                    print(f"  → LLM选择方向: {dirt.name}")
                    return self.direction_map_dict[dirt]

            print(f"  LLM返回的方向 '{direction_name}' 无效，使用默认方向 floor")
            return self.direction_map_dict[direction.floor]

        except Exception as e:
            import traceback
            traceback.print_exc()
            raise
            # print(f"  LLM调用失败: {e}，使用默认方向 floor")
            # return self.direction_map_dict[direction.floor]

    def update_direction(self, new_item: Item, placed_dirt: direction) -> None:
        """更新所有方向图的距离信息"""
        for dirt, dirt_map in self.direction_map_dict.items():
            if dirt != placed_dirt:
                dirt_map.update_plane(new_item)

    def create_and_add_plane_from_item(self, new_item: Item, direction_map: DirectionMap, plane_map: PlaneMap) -> None:
        """根据新添加的物体创建新平面并判断是否添加到方向图中"""
        if direction_map.dirt == direction.ceil:
            plane_loc = [
                align_to_sample_grid(new_item.x),
                align_to_sample_grid(new_item.y),
                align_to_sample_grid(new_item.z),
                int(new_item.length),
                int(new_item.height),
                int(new_item.width)
            ]
        elif direction_map.dirt == direction.floor:
            plane_loc = [
                align_to_sample_grid(new_item.x),
                align_to_sample_grid(new_item.y + new_item.width),
                align_to_sample_grid(new_item.z),
                int(new_item.length),
                int(new_item.height),
                int(new_item.width)
            ]
        elif direction_map.dirt == direction.left:
            plane_loc = [
                align_to_sample_grid(new_item.x + new_item.length),
                align_to_sample_grid(new_item.y),
                align_to_sample_grid(new_item.z),
                int(new_item.width),
                int(new_item.height),
                int(new_item.length)
            ]
        elif direction_map.dirt == direction.right:
            plane_loc = [
                align_to_sample_grid(new_item.x),
                align_to_sample_grid(new_item.y),
                align_to_sample_grid(new_item.z),
                int(new_item.width),
                int(new_item.height),
                int(new_item.length)
            ]
        elif direction_map.dirt == direction.backward:
            plane_loc = [
                align_to_sample_grid(new_item.x),
                align_to_sample_grid(new_item.y),
                align_to_sample_grid(new_item.z),
                int(new_item.length),
                int(new_item.width),
                int(new_item.height)
            ]
        else:  # direction.forward
            plane_loc = [
                align_to_sample_grid(new_item.x),
                align_to_sample_grid(new_item.y),
                align_to_sample_grid(new_item.z + new_item.height),
                int(new_item.length),
                int(new_item.width),
                int(new_item.height)
            ]

        new_plane = PlaneMap(
            plane_loc=plane_loc,
            dirt=direction_map.dirt,
            carry=[],
            description=f"物体{new_item.item_name}的{direction_map.dirt.name}平面，物体的具体描述{new_item.item_description}",
            item_list=[],
            initial_color=self.initial_color
        )

        opposite_dirt = find_opposite_direction(direction_map.dirt)
        opposite_color_map = new_item.get_distance_map(opposite_dirt).get_color_map()
        
        new_plane_dist = new_plane.get_distance()
        expected_shape = (new_plane_dist.height, new_plane_dist.width, 3)
        
        if opposite_color_map.shape != expected_shape:
            if len(opposite_color_map.shape) == 3 and opposite_color_map.shape[0:2] == (new_plane_dist.width, new_plane_dist.height):
                opposite_color_map = np.transpose(opposite_color_map, (1, 0, 2))
            else:
                opposite_color_map = np.full(expected_shape, 255, dtype=np.uint8)
        
        new_plane.init_color_map(opposite_color_map)

        # 修复点1：强制转整数，确保item_height/item_width是纯整数
        item_dist_map = new_plane_dist.get_dist_map()
        item_height = int(item_dist_map.shape[0])
        item_width = int(item_dist_map.shape[1])
        new_dist_map = np.full((item_height, item_width), 0, dtype=np.int16)

        # 偏移量计算 - 确保转成整数
        offset_x = int(round(float(new_plane_dist.x - plane_map.get_distance().x)))
        offset_y = int(round(float(new_plane_dist.y - plane_map.get_distance().y)))
        offset_z = int(round(float(new_plane_dist.z - plane_map.get_distance().z)))

        if direction_map.dirt == direction.floor or direction_map.dirt == direction.ceil:
            plane_offset_1 = offset_x
            plane_offset_2 = offset_y
        elif direction_map.dirt == direction.left or direction_map.dirt == direction.right:
            plane_offset_1 = offset_y
            plane_offset_2 = offset_z
        else:
            plane_offset_1 = offset_x
            plane_offset_2 = offset_z

        plane_dist_map = plane_map.get_dist_map()
        # 修复点2：强制转整数，确保plane_height/plane_width是纯整数
        plane_height = int(plane_dist_map.shape[0])
        plane_width = int(plane_dist_map.shape[1])

        # 修复点3：所有切片边界强制转int，避免浮点类型
        plane_start_y = int(max(0, plane_offset_2))
        plane_start_x = int(max(0, plane_offset_1))
        plane_end_y = int(min(plane_height, plane_offset_2 + item_height))
        plane_end_x = int(min(plane_width, plane_offset_1 + item_width))

        item_start_y = int(max(0, -plane_offset_2))
        item_start_x = int(max(0, -plane_offset_1))
        item_end_y = int(item_start_y + (plane_end_y - plane_start_y))
        item_end_x = int(item_start_x + (plane_end_x - plane_start_x))

        # 切片操作前增加类型校验
        if plane_start_y < plane_end_y and plane_start_x < plane_end_x:
            # 确保所有切片索引都是整数
            plane_region = plane_dist_map[plane_start_y:plane_end_y, plane_start_x:plane_end_x]
            item_region = item_dist_map[item_start_y:item_end_y, item_start_x:item_end_x]
            new_dist_map[item_start_y:item_end_y, item_start_x:item_end_x] = plane_region - item_region

        new_plane.init_dist_map(new_dist_map)
        direction_map.add_plane_map(new_plane)

    def add_item(self, new_item: Item) -> None:
        """向房间添加新物体"""
        print(f"\n{'='*60}")
        print(f"开始添加物体: {new_item.item_name}")
        print(f"物体描述: {new_item.item_description}")
        print(f"{'='*60}")

        print(f"\n[步骤 1/7] 选择合适的方向...")
        direction_map = self.choice_direction_map(new_item)
        print(f"[OK] 已选择方向: {direction_map.dirt.name}")

        print(f"\n[步骤 2/7] 在 {direction_map.dirt.name} 方向上选择合适的平面...")
        plane_map = direction_map.choice_plane_map(new_item)
        if not plane_map:
            print(f"[错误] 无可用平面")
            return
        print(f"[OK] 已选择平面，当前平面上有 {len(plane_map.item_list)} 个物体")

        print(f"\n[步骤 3/7] 在平面上寻找合适的位置...")
        location = plane_map.find_location(new_item)
        if location is None:
            print(f"[错误] 未找到合适的位置")
            return
        print(f"[OK] 找到位置: ({location[0]}, {location[1]}, {location[2]})")

        print(f"\n[步骤 4/7] 设置物体位置...")
        new_item.set_item_location(location)
        print(f"[OK] 物体位置已设置")

        print(f"\n[步骤 5/7] 将物体添加到平面...")
        plane_map.add_item(new_item)
        print(f"[OK] 物体已添加到平面，平面上现有 {len(plane_map.item_list)} 个物体")

        print(f"\n[步骤 6/7] 更新所有其他方向的距离信息...")
        self.update_direction(new_item, direction_map.dirt)
        self.direction_map_dict[direction_map.dirt].update_base_plane(new_item)
        print(f"[OK] 距离信息已更新")

        print(f"\n[步骤 7/7] 判断是否需要新增平面...")
        self.create_and_add_plane_from_item(new_item, direction_map, plane_map)
        print(f"[OK] 平面判断完成")

        print(f"\n{'='*60}")
        print(f"物体 {new_item.item_name} 添加完成！")
        print(f"房间内现有 {self.get_item_count()} 个物体")
        print(f"{'='*60}\n")

        self.visualize_floor_plan()

    def get_all_items(self) -> list[Item]:
        """获取房间中的所有物体"""
        items = []
        for dirt_map in self.direction_map_dict.values():
            for plane_map in dirt_map.plane_map_list:
                items.extend(plane_map.item_list)
        return items

    def get_item_count(self) -> int:
        """获取房间中物体的总数"""
        return len(self.get_all_items())

    def visualize_floor_plan(self) -> None:
        """可视化房间的俯视平面图（从上往下看）"""
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

        floor_direction = self.direction_map_dict[direction.floor]
        plane_map = floor_direction.plane_map_list[0]

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
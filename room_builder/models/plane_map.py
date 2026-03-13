"""
平面图模块

包含 PlaneMap 类，表示某个方向上的一个平面及其上的物体
"""
import numpy as np
import json
import re

from ..utils import direction, SAMPLE_RATE, find_opposite_direction
from .distance_map import DistanceMap
from .item import Item
from ..services.llm_service import get_client


def _parse_vlm_response(response: str) -> tuple[int, int] | None:
    """
    解析 VLM 返回的坐标，支持多种格式

    参数:
        response: VLM 的响应文本

    返回:
        (x, y) 归一化坐标 (0-1000)，解析失败返回 None
    """
    try:
        # 尝试提取 JSON 格式
        # 1. 尝试直接解析整个响应
        try:
            data = json.loads(response)
            if isinstance(data, dict) and "x" in data and "y" in data:
                return (int(data["x"]), int(data["y"]))
        except json.JSONDecodeError:
            pass

        # 2. 尝试从 Markdown 代码块中提取
        json_match = re.search(r'```(?:json)?\s*(\{[^`]+\})\s*```', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
            if isinstance(data, dict) and "x" in data and "y" in data:
                return (int(data["x"]), int(data["y"]))

        # 3. 尝试从文本中提取 JSON 对象
        json_match = re.search(r'\{[^}]*"x"[^}]*"y"[^}]*\}', response)
        if json_match:
            data = json.loads(json_match.group(0))
            if isinstance(data, dict) and "x" in data and "y" in data:
                return (int(data["x"]), int(data["y"]))

        # 4. 使用正则表达式直接提取坐标
        x_match = re.search(r'"x"\s*:\s*(\d+)', response)
        y_match = re.search(r'"y"\s*:\s*(\d+)', response)
        if x_match and y_match:
            return (int(x_match.group(1)), int(y_match.group(1)))

        return None
    except Exception as e:
        print(f"解析 VLM 响应失败: {e}")
        return None


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
        # 优先使用 VLM，最多重试 3 次
        max_retries = 3
        previous_attempts = []

        for attempt in range(1, max_retries + 1):
            print(f"[PlaneMap] 尝试使用 VLM 为 {new_item.item_name} 寻找位置 (第 {attempt}/{max_retries} 次)")
            vlm_result = self._find_location_with_VLM(new_item, previous_attempts)

            if vlm_result is not None:
                print(f"[PlaneMap] VLM 成功找到位置: {vlm_result}")
                return vlm_result
            else:
                print(f"[PlaneMap] VLM 第 {attempt} 次尝试失败")

        # VLM 多次尝试失败后回退到距离图算法
        print(f"[PlaneMap] VLM {max_retries} 次尝试均失败，回退到距离图算法")
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

    def _find_location_with_VLM(
        self,
        new_item: Item,
        previous_attempts: list[dict] | None = None
    ) -> tuple[int, int, int] | None:
        """
        基于VLM为新物体寻找合适的放置位置

        参数:
            new_item: 待放置的物体
            previous_attempts: 之前尝试失败的记录列表

        返回:
            合适的位置坐标 (x, y, z)
        """
        # 步骤 A: 准备数据
        dist_map = self.get_dist_map()
        color_map = self.get_color_map()
        item_dist_map = new_item.get_distance_map(self.dirt).get_dist_map()
        item_color_map = new_item.get_distance_map(self.dirt).get_color_map()

        plane_height, plane_width = dist_map.shape
        item_height, item_width = item_dist_map.shape

        print(f"[VLM] 平面尺寸: {plane_width}x{plane_height}, 物体尺寸: {item_width}x{item_height}")

        # 步骤 B: 构造 Prompt
        prompt = f"""你是一个室内设计助手。请分析这两张图片：

第一张图：当前平面的俯视图（尺寸：{plane_width}x{plane_height} 像素）
第二张图：待放置物体的俯视图（尺寸：{item_width}x{item_height} 像素）

任务：为第二张图中的物体在第一张图的平面上选择一个最佳放置位置。

坐标系统说明：
- 使用归一化坐标：X 和 Y 的范围都是 0-1000
- 原点 (0, 0) 位于平面的【左上角】
- X 轴向右增长，Y 轴向下增长
- 你返回的坐标 (x, y) 表示物体的【左上角】位置，不是中心位置

要求：
1. 选择的位置应该合理、美观、符合室内设计原则
2. 考虑物体与已有物体的空间关系和距离
3. 确保物体完全在平面内（物体左上角坐标 + 物体尺寸 ≤ 平面尺寸）
4. 避免物体之间的碰撞和重叠

请以 JSON 格式输出：
{{"x": <0-1000的整数>, "y": <0-1000的整数>, "reasoning": "选择理由"}}"""

        # 如果有之前的失败尝试，添加到 prompt 中
        if previous_attempts:
            attempts_info = "\n\n【重要提示】之前的尝试失败了，请避免以下位置：\n"
            for i, attempt in enumerate(previous_attempts, 1):
                attempts_info += f"{i}. 归一化坐标 ({attempt['x']}, {attempt['y']}) "
                attempts_info += f"[网格坐标 ({attempt['grid_x']}, {attempt['grid_y']})] - "
                attempts_info += f"{attempt['reason']}\n"

            attempts_info += "\n请选择一个不同的位置，避开上述失败的区域。"
            prompt += attempts_info

        # 步骤 C: 调用 VLM
        try:
            client = get_client()
            response = client.chat_with_image(prompt, [color_map, item_color_map], "qwen-vl-max")
            print(f"[VLM] 响应: {response}")

            # 处理响应格式：如果是列表，提取文本内容
            if isinstance(response, list):
                if len(response) > 0:
                    first_item = response[0]
                    if isinstance(first_item, dict) and 'text' in first_item:
                        response = first_item['text'] # type: ignore
                    else:
                        print(f"[VLM] 无法解析响应格式")
                        return None
                else:
                    print(f"[VLM] 响应列表为空")
                    return None
        except Exception as e:
            print(f"[VLM] 调用失败: {e}")
            return None

        # 步骤 D: 解析响应
        coords = _parse_vlm_response(response)
        if coords is None:
            print("[VLM] 解析响应失败")
            # 记录失败信息（无具体坐标）
            if previous_attempts is not None:
                previous_attempts.append({
                    'x': -1,
                    'y': -1,
                    'grid_x': -1,
                    'grid_y': -1,
                    'reason': '解析响应失败',
                    'min_distance': None
                })
            return None

        norm_x, norm_y = coords
        print(f"[VLM] 解析得到归一化坐标: ({norm_x}, {norm_y})")

        # 步骤 E: 坐标转换和验证
        # 验证归一化坐标范围
        if not (0 <= norm_x <= 1000 and 0 <= norm_y <= 1000):
            print(f"[VLM] 归一化坐标超出范围: ({norm_x}, {norm_y})")
            # 记录失败信息
            if previous_attempts is not None:
                previous_attempts.append({
                    'x': norm_x,
                    'y': norm_y,
                    'grid_x': -1,
                    'grid_y': -1,
                    'reason': f'归一化坐标超出范围 (0-1000)',
                    'min_distance': None
                })
            return None

        # 转换为网格坐标
        grid_j = int(norm_x * plane_width / 1000)
        grid_i = int(norm_y * plane_height / 1000)

        # 检查物体是否完全在平面内
        if grid_i + item_height > plane_height:
            grid_i = plane_height - item_height
            print(f"[VLM] 调整 Y 坐标到边界: {grid_i}")
        if grid_j + item_width > plane_width:
            grid_j = plane_width - item_width
            print(f"[VLM] 调整 X 坐标到边界: {grid_j}")

        if grid_i < 0 or grid_j < 0:
            print(f"[VLM] 物体过大，无法放置")
            # 记录失败信息
            if previous_attempts is not None:
                previous_attempts.append({
                    'x': norm_x,
                    'y': norm_y,
                    'grid_x': grid_j,
                    'grid_y': grid_i,
                    'reason': f'物体过大，无法放置在平面内',
                    'min_distance': None
                })
            return None

        print(f"[VLM] 网格坐标: ({grid_j}, {grid_i})")

        # 进行距离图碰撞检测
        region = dist_map[grid_i:grid_i+item_height, grid_j:grid_j+item_width] - item_dist_map
        min_distance = np.min(region)

        if min_distance < 0:
            print(f"[VLM] 碰撞检测失败，最小距离: {min_distance}")
            # 记录失败信息
            if previous_attempts is not None:
                previous_attempts.append({
                    'x': norm_x,
                    'y': norm_y,
                    'grid_x': grid_j,
                    'grid_y': grid_i,
                    'reason': f'碰撞检测失败（最小距离: {min_distance}）',
                    'min_distance': min_distance
                })
            return None

        print(f"[VLM] 碰撞检测通过，最小距离: {min_distance}")

        # 步骤 F: 转换为世界坐标
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
            result = (world_x, world_y, world_z)
        elif self.dirt == direction.ceil:
            result = (world_x, world_y - new_item.height, world_z)
        elif self.dirt == direction.left:
            result = (world_x, world_y, world_z)
        elif self.dirt == direction.right:
            result = (world_x - new_item.length, world_y, world_z)
        elif self.dirt == direction.backward:
            result = (world_x, world_y, world_z)
        else:
            result = (world_x, world_y, world_z - new_item.height)

        print(f"[VLM] 最终世界坐标: {result}")
        return result

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

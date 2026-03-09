"""
平面图模块

包含 PlaneMap 类，表示某个方向上的一个平面及其上的物体
"""
import json
import numpy as np
from ..utils import direction, SAMPLE_RATE, find_opposite_direction
from .distance_map import DistanceMap
from .item import Item
from ..services import get_client


class PlaneMap:
    """
    平面图类，表示某个方向上的一个平面及其上的物体
    """
    def __init__(
        self,
        plane_loc: list[float],
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
            int(plane_loc[3]),
            int(plane_loc[4]),
            initial_distance=int(plane_loc[5]),
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

    def get_distance_map(self) -> np.ndarray:
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

    def update_distance(self, new_item: Item) -> None:
        """
        更新平面的距离图

        参数:
            new_item: 新的物体对象
        """
        if new_item not in self.item_list:
            self.distance.update(
                cover_distance_map=new_item.get_distance_map(dirt=find_opposite_direction(self.dirt)),
                cover_color_map=new_item.get_distance_map(dirt=self.dirt))

    def _create_visualization_image(self, new_item: Item) -> np.ndarray:
        """
        创建距离图和颜色图的可视化图像，用于 VLM 分析

        参数:
            new_item: 待放置的物体

        返回:
            RGB 图像数组 (H, W, 3)
        """
        import cv2

        dist_map = self.get_distance_map()
        color_map = self.get_color_map()

        # 获取物体在平面上的投影尺寸
        if self.dirt in [direction.floor, direction.ceil]:
            proj_h = new_item.length_sample_num
            proj_w = new_item.width_sample_num
        elif self.dirt in [direction.left, direction.right]:
            proj_h = new_item.width_sample_num
            proj_w = new_item.height_sample_num
        else:
            proj_h = new_item.length_sample_num
            proj_w = new_item.width_sample_num

        # 创建可视化图像
        vis_height, vis_width = dist_map.shape

        # 创建画布
        vis_image = np.ones((vis_height, vis_width, 3), dtype=np.uint8) * 255

        # 绘制颜色图（作为背景）
        vis_image[:, :, :3] = color_map[:, :, :3]

        # 使用 cv2 创建热力图
        dist_normalized = (dist_map.astype(np.float64) - np.min(dist_map)) / (np.max(dist_map) - np.min(dist_map) + 1e-8)
        dist_scaled = (dist_normalized * 255).astype(np.uint8)
        dist_heatmap = cv2.applyColorMap(dist_scaled, cv2.COLORMAP_JET)  # type: ignore
        dist_heatmap = cv2.cvtColor(dist_heatmap, cv2.COLOR_BGR2RGB)  # type: ignore

        # 混合热力图和颜色图
        vis_image = cv2.addWeighted(vis_image, 0.5, dist_heatmap, 0.5, 0)  # type: ignore

        # 绘制物体尺寸参考框（在左上角，红色边框）
        box_h = max(1, min(proj_h, vis_height // 8))
        box_w = max(1, min(proj_w, vis_width // 8))
        cv2.rectangle(vis_image, (5, 5), (5 + box_w, 5 + box_h), (255, 0, 0), 1)  # type: ignore

        # 添加图例说明
        # 在底部添加颜色条表示距离
        legend_height = max(1, vis_height // 20)
        legend_y = vis_height - legend_height - 5

        for i in range(vis_width):
            ratio = i / vis_width
            color_val = np.uint8([[int(ratio * 255)]]) # type: ignore
            color = cv2.applyColorMap(color_val, cv2.COLORMAP_JET)[0][0]  # type: ignore
            vis_image[legend_y:legend_y + legend_height, i] = color

        # 添加文字标签
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.3
        cv2.putText(vis_image, "近", (5, legend_y - 2), font, font_scale, (0, 0, 0), 1)  # type: ignore
        cv2.putText(vis_image, "远", (vis_width - 20, legend_y - 2), font, font_scale, (0, 0, 0), 1)  # type: ignore

        return vis_image

    def find_location(self, new_item: Item) -> tuple[float, float, float]:
        """
        为新物体寻找合适的放置位置（使用 VLM 视觉语言模型）

        参数:
            new_item: 待放置的物体

        返回:
            合适的位置坐标 (x, y, z)
        """
        try:
            # 尝试使用 VLM 进行位置选择
            return self._find_location_with_vlm(new_item)
        except Exception as e:
            print(f"  ⚠ VLM 位置查找失败：{e}，使用备用算法")
            # VLM 失败时使用基于距离图的算法
            return self._find_location_with_distance_map(new_item)

    def _find_location_with_vlm(self, new_item: Item) -> tuple[float, float, float]:
        """
        使用 VLM 视觉语言模型为新物体寻找合适的放置位置

        参数:
            new_item: 待放置的物体

        返回:
            合适的位置坐标 (x, y, z)
        """
        # 创建可视化图像
        vis_image = self._create_visualization_image(new_item)

        # 获取平面信息
        dist_map = self.get_distance_map()
        vis_height, vis_width = dist_map.shape

        # 构建提示词
        prompt = f"""
你是一个 3D 空间布局专家。请分析这张平面图并为新物体找到最佳放置位置。

图像说明:
- 这是{self.dirt.name}方向的平面图
- 背景颜色表示已有物体的颜色和纹理
- 蓝色区域表示距离障碍物较远（空闲空间）
- 红色区域表示距离障碍物较近（拥挤空间）
- 左上角红色框表示新物体的相对大小

房间信息:
- 房间类型：{getattr(self, 'room_type', '未知')}
- 平面尺寸：{vis_width} x {vis_height} 个采样点
- 采样间隔：{SAMPLE_RATE} 米

新物体信息:
- 名称：{new_item.item_name}
- 描述：{new_item.item_description}
- 尺寸：{new_item.length:.2f}m x {new_item.width:.2f}m x {new_item.height:.2f}m

平面上已有物体：{self.carry}

任务:
请在图像中为新物体找到一个合适的放置位置。
位置应该:
1. 避开已有物体（选择蓝色/空闲区域）
2. 符合空间布局常识（如床靠墙放、桌子放在合适位置等）
3. 留出足够的活动空间

请只返回 JSON 格式的位置信息:
{{"grid_x": x 坐标，"grid_y": y 坐标}}

其中 grid_x 和 grid_y 是放置位置左上角在距离图网格中的坐标（从 0 开始）。
"""

        try:
            client = get_client()
            response = client.chat_with_image(
                prompt=prompt,
                image_data=vis_image,
                model="qwen-vl-max"
            )

            # 解析响应，提取 JSON
            import re
            json_match = re.search(r'\{[^{}]*"grid_x"[^{}]*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                grid_x = int(result.get("grid_x", 0))
                grid_y = int(result.get("grid_y", 0))

                # 边界检查
                grid_x = max(0, min(grid_x, vis_height - 1))
                grid_y = max(0, min(grid_y, vis_width - 1))

                print(f"  → VLM 选择位置：grid=({grid_x}, {grid_y})")
            else:
                raise ValueError("无法从 VLM 响应中解析位置信息")

        except Exception as e:
            raise e

        # 将网格坐标转换为世界坐标
        grid_i, grid_j = grid_x, grid_y

        # 根据方向计算实际的世界坐标
        if self.dirt in [direction.floor, direction.ceil]:
            # XZ 平面：grid_i 对应 X, grid_j 对应 Z
            world_x = self.distance.x + grid_i * SAMPLE_RATE
            world_z = self.distance.z + grid_j * SAMPLE_RATE
            world_y = self.distance.y
        elif self.dirt in [direction.left, direction.right]:
            # YZ 平面：grid_i 对应 Y, grid_j 对应 Z
            world_y = self.distance.y + grid_i * SAMPLE_RATE
            world_z = self.distance.z + grid_j * SAMPLE_RATE
            world_x = self.distance.x
        else:
            # XY 平面：grid_i 对应 X, grid_j 对应 Y
            world_x = self.distance.x + grid_i * SAMPLE_RATE
            world_y = self.distance.y + grid_j * SAMPLE_RATE
            world_z = self.distance.z

        # 根据方向调整物体的实际放置位置
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

    def _find_location_with_distance_map(self, new_item: Item) -> tuple[float, float, float]:
        """
        备用算法：基于距离图为新物体寻找合适的放置位置

        参数:
            new_item: 待放置的物体

        返回:
            合适的位置坐标 (x, y, z)
        """
        dist_map = self.get_distance_map()
        plane_height, plane_width = dist_map.shape

        # 获取新物体的尺寸（以采样点为单位）
        item_h_samples = new_item.height_sample_num
        item_w_samples = new_item.width_sample_num
        item_l_samples = new_item.length_sample_num

        # 根据平面方向确定物体在平面上的投影尺寸
        if self.dirt in [direction.floor, direction.ceil]:
            proj_h = item_l_samples
            proj_w = item_w_samples
        elif self.dirt in [direction.left, direction.right]:
            proj_h = item_w_samples
            proj_w = item_h_samples
        else:
            proj_h = item_l_samples
            proj_w = item_w_samples

        # 寻找可以放置物体的位置
        best_location = None
        best_score = float('inf')

        for i in range(plane_height - proj_h + 1):
            for j in range(plane_width - proj_w + 1):
                region = dist_map[i:i+proj_h, j:j+proj_w]
                min_distance = np.min(region)

                if min_distance >= 0:
                    avg_distance = np.mean(region)
                    if avg_distance < best_score:
                        best_score = avg_distance
                        best_location = (i, j)

        if best_location is None:
            max_dist = -float('inf')
            for i in range(plane_height - proj_h + 1):
                for j in range(plane_width - proj_w + 1):
                    region = dist_map[i:i+proj_h, j:j+proj_w]
                    min_distance = np.min(region)
                    if min_distance > max_dist:
                        max_dist = min_distance
                        best_location = (i, j)

        if best_location is None:
            best_location = (plane_height // 2, plane_width // 2)

        grid_i, grid_j = best_location

        if self.dirt in [direction.floor, direction.ceil]:
            world_x = self.distance.x + grid_i * SAMPLE_RATE
            world_z = self.distance.z + grid_j * SAMPLE_RATE
            world_y = self.distance.y
        elif self.dirt in [direction.left, direction.right]:
            world_y = self.distance.y + grid_i * SAMPLE_RATE
            world_z = self.distance.z + grid_j * SAMPLE_RATE
            world_x = self.distance.x
        else:
            world_x = self.distance.x + grid_i * SAMPLE_RATE
            world_y = self.distance.y + grid_j * SAMPLE_RATE
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
        self.update_distance(new_item)

    def update_color(self, new_item: Item) -> None:
        """
        更新平面的颜色图

        参数:
            new_item: 新的物体对象
        """
        self.distance.update_color(
            cover_color_map=new_item.get_distance_map(dirt=self.dirt))

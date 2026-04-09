"""
主程序模块

包含 build 函数，用于构建房间布局
"""
from .utils import SAMPLE_RATE
from .models import Room, Item


def build(
    room_type: str,
    length: float,
    width: float,
    height: float,
    room_theoretical_volume: float,
    item_list: list[tuple[str, str, float]],
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
        length: 房间长度（GLB单位）
        width: 房间宽度（GLB单位）
        height: 房间高度（GLB单位）
        room_theoretical_volume: 房间在现实世界中的理论体积（立方米）
        item_list: 物体信息列表，每个元素是 (物体名称, 物体描述, 理论体积) 的元组
            - 物体名称: str, 物体的名称
            - 物体描述: str, 物体的详细描述
            - 理论体积: float, 物体在现实世界中的体积（立方米）
        x: 房间原点x坐标（默认为0）
        y: 房间原点y坐标（默认为0）
        z: 房间原点z坐标（默认为0）
        sample_interval: 采样间隔（米），用于计算距离图的采样点数量
        initial_color: 初始颜色RGB值（默认为白色(255, 255, 255)）

    返回:
        构建好的房间对象

    示例:
        >>> # 创建一个 5m x 4m x 3m = 60m³ 的卧室
        >>> item_list = [("床", "双人床", 2.0), ("桌子", "书桌", 0.5)]
        >>> room = build("卧室", 5.0, 4.0, 3.0, 60.0, item_list)
        >>> # 自定义初始颜色为浅灰色
        >>> room = build("卧室", 5.0, 4.0, 3.0, 60.0, item_list, initial_color=(200, 200, 200))
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

    # 计算 GLB 单位到真实世界的转换系数
    room_glb_volume = length * width * height
    volume_rate = room_glb_volume / room_theoretical_volume

    for item_name, item_description, theoretical_volume in item_list:
        # 根据物体名称、描述和理论体积创建Item对象
        item = Item(
            item_name=item_name,
            item_description=item_description,
            theoretical_volume=theoretical_volume,
            volume_rate=volume_rate
        )
        room.add_item(item)

    return room


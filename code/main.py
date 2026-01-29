"""
主程序模块

包含 build 函数，用于构建房间布局
"""
from Utils import SAMPLE_RATE
from room import Room
from item import Item


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

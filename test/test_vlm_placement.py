"""
VLM 驱动的物体位置选择测试代码

测试 VLM 如何为物体选择放置位置
"""
import sys
import os
import json
import numpy as np

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from room_builder import build
from room_builder.models.item import Item
from room_builder.utils import direction


def get_models_as_item_list():
    """
    从 models/item_lists.json 读取模型信息并转换为 item_list 格式

    返回:
        list[tuple[str, str, float]]: 物体信息列表
    """
    json_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'item_lists.json')

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    item_list = [(item['name'], item['description'], item['volume']) for item in data]
    return item_list

def test_vlm_with_visualization():
    """测试 VLM 放置并可视化平面图"""
    print("\n" + "="*70)
    print("测试 3：VLM 放置 + 平面图可视化")
    print("="*70)

    room_type = "森林"
    length = 4.0
    width = 4.0
    height = 3.0
    room_theoretical_volume = 48.0

    print(f"\n【步骤 1】创建房间")
    item_list = get_models_as_item_list()

    try:
        room = build(
            room_type=room_type,
            length=length,
            width=width,
            height=height,
            room_theoretical_volume=room_theoretical_volume,
            item_list=item_list
        )
        print("  [成功] 房间构建完成")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise
        # print(f"  [错误] 房间构建失败：{e}")
        # return None

    print(f"\n【步骤 2】获取地板平面图")
    floor_map = room.direction_map_dict.get(direction.floor)
    if floor_map and len(floor_map.plane_map_list) > 0:
        plane = floor_map.plane_map_list[0]
        color_map = plane.get_color_map()
        print(f"  地板平面图尺寸：{color_map.shape}")
        print(f"  地板上的物体：{plane.carry}")
        
    else:
        print("  [警告] 未找到地板平面图")

    return room


if __name__ == "__main__":
    print("\n" + "#"*70)
    print("# VLM 物体放置测试")
    print("#"*70)

    # 测试: 带可视化的放置
    room = test_vlm_with_visualization()

    print("\n" + "#"*70)
    print("# 所有测试完成")
    print("#"*70)



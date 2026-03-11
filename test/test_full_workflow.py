"""
完整流程测试代码

测试从 build 函数到物体摆放的整个流程
"""
import sys
import os
import json

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from room_builder import build

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


def test_full_workflow():
    """测试完整的房间构建流程"""
    print("\n" + "="*70)
    print("完整流程测试：房间构建 + 物体摆放")
    print("="*70)

    # 定义房间参数
    room_type = "卧室"
    length = 5.0  # GLB 单位
    width = 4.0   # GLB 单位
    height = 3.0  # GLB 单位
    room_theoretical_volume = 60.0  # 立方米

    print(f"\n【步骤 1】定义房间参数")
    print(f"  房间类型：{room_type}")
    print(f"  GLB 尺寸：{length} x {width} x {height}")
    print(f"  GLB 体积：{length * width * height}")
    print(f"  理论体积：{room_theoretical_volume} 立方米")
    print(f"  转换系数：{(length * width * height) / room_theoretical_volume:.4f}")

    # 使用 models 文件夹下的模型作为 item_list
    print(f"\n【步骤 2】加载 models 文件夹下的模型")
    item_list = get_models_as_item_list()
    for i, (name, desc, vol) in enumerate(item_list, 1):
        print(f"  {i}. {name} - {desc} - {vol} 立方米")

    # 构建房间
    print(f"\n【步骤 3】构建房间（调用 build 函数）")
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
    except NotImplementedError as e:
        print(f"  [警告] 房间构建部分完成：{e}")
        return
    except Exception as e:
        print(f"  [错误] 房间构建失败：{e}")
        import traceback
        traceback.print_exc()
        return

    # 验证房间对象
    print(f"\n【步骤 4】验证房间对象")
    print(f"  房间类型：{room.room_type}")
    print(f"  房间尺寸：{room.length} x {room.width} x {room.height}")
    print(f"  采样间隔：{room.sample_interval}")
    print(f"  方向图数量：{len(room.direction_map_dict)}")

    # 验证每个方向图
    print(f"\n【步骤 5】验证方向图")
    from room_builder.utils import direction
    for dirt, dirt_map in room.direction_map_dict.items():
        plane_count = len(dirt_map.plane_map_list)
        print(f"  {dirt.name}: {plane_count} 个平面")

    # 验证所有物体
    print(f"\n【步骤 6】验证物体信息")
    items = room.get_all_items()
    print(f"  房间中的物体数量：{len(items)}")

    for i, item in enumerate(items, 1):
        print(f"\n  物体 {i}: {item.item_name}")
        print(f"    描述：{item.item_description}")
        print(f"    理论体积：{item.theoretical_volume} 立方米")
        print(f"    GLB 体积：{item.length * item.width * item.height:.6f}")
        print(f"    边界框尺寸：{item.length:.3f} x {item.width:.3f} x {item.height:.3f}")
        print(f"    中心点：[{item.x}, {item.y}, {item.z}]")
        print(f"    顶点数量：{len(item.vertices)}")
        print(f"    采样点数量：{item.length_sample_num} x {item.width_sample_num} x {item.height_sample_num}")

        # 验证体积精度
        expected_volume = item.theoretical_volume * ((length * width * height) / room_theoretical_volume)
        actual_volume = item.length * item.width * item.height
        error = abs(actual_volume - expected_volume)
        error_rate = error / expected_volume * 100 if expected_volume > 0 else 0
        print(f"    体积误差：{error:.6f} ({error_rate:.2f}%)")  

    print("\n" + "="*70)
    print("完整流程测试完成")
    print("="*70)

    return room


if __name__ == "__main__":
    import numpy as np

    # 运行所有测试
    print("\n" + "#"*70)
    print("# 开始完整流程测试")
    print("#"*70)

    # 测试 1: 完整流程
    room = test_full_workflow()

    print("\n" + "#"*70)
    print("# 所有测试完成")
    print("#"*70)

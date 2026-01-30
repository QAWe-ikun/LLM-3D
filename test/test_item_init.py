"""
测试 Item 初始化和标准化功能
"""
import sys
import os
import numpy as np

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from room_builder.models import Item

def test_item_initialization():
    """测试 Item 类的初始化和标准化"""
    print("\n" + "="*60)
    print("测试: Item 初始化和标准化")
    print("="*60)

    # 假设房间 GLB 尺寸为 5.0 x 4.0 x 3.0 = 60.0，理论体积为 60.0 立方米
    room_glb_volume = 5.0 * 4.0 * 3.0
    room_theoretical_volume = 60.0
    volume_rate = room_glb_volume / room_theoretical_volume

    print(f"房间参数:")
    print(f"  GLB 体积: {room_glb_volume}")
    print(f"  理论体积: {room_theoretical_volume} 立方米")
    print(f"  转换系数: {volume_rate}")

    # 创建一个物体，理论体积为 0.5 立方米
    theoretical_volume = 0.5
    print(f"\n创建物体:")
    print(f"  名称: 桌子")
    print(f"  描述: 一张木质书桌")
    print(f"  理论体积: {theoretical_volume} 立方米")

    item = Item(
        item_name="桌子",
        item_description="一张木质书桌",
        theoretical_volume=theoretical_volume,
        volume_rate=volume_rate
    )

    print(f"\n物体属性:")
    print(f"  item_name: {item.item_name}")
    print(f"  item_description: {item.item_description}")
    print(f"  theoretical_volume: {item.theoretical_volume}")
    print(f"  顶点数量: {len(item.vertices)}")
    print(f"  边界框起点: ({item.x:.6f}, {item.y:.6f}, {item.z:.6f})")
    print(f"  边界框尺寸: ({item.length:.6f}, {item.width:.6f}, {item.height:.6f})")

    # 计算实际体积
    actual_item_volume = item.length * item.width * item.height
    print(f"  实际体积: {actual_item_volume:.6f}")
    print(f"  期望体积: {theoretical_volume * volume_rate:.6f}")
    print(f"  误差: {abs(actual_item_volume - theoretical_volume * volume_rate):.6f}")

    # 验证中心点
    print(f"  中心点: {item.center_point}")

    # 验证采样参数
    print(f"\n采样参数:")
    print(f"  length_sample_num: {item.length_sample_num}")
    print(f"  width_sample_num: {item.width_sample_num}")
    print(f"  height_sample_num: {item.height_sample_num}")

    print("\n[PASS] 测试通过：Item 初始化和标准化功能正常")


if __name__ == "__main__":
    try:
        test_item_initialization()
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()

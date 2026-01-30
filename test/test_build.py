"""
build 函数测试模块

测试 build 函数的功能，包括房间创建和物体添加
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from room_builder import build, Room, Item  # type: ignore


def test_build_basic():
    """测试 build 函数的基本功能"""
    print("\n" + "="*60)
    print("测试 1: build 函数基本功能")
    print("="*60)

    # 创建一个简单的房间，添加一个物体
    # 房间 GLB 尺寸为 5.0 x 4.0 x 3.0 = 60.0，理论体积为 60.0 m³
    item_list = [("桌子", "一张木质书桌", 0.5)]

    room = build(
        room_type="书房",
        length=5.0,
        width=4.0,
        height=3.0,
        room_theoretical_volume=60.0,
        item_list=item_list
    )

    # 验证房间属性
    assert isinstance(room, Room), "返回的对象应该是 Room 类型"
    assert room.room_type == "书房", "房间类型应该是'书房'"
    assert room.length == 5.0, "房间长度应该是 5.0"
    assert room.width == 4.0, "房间宽度应该是 4.0"
    assert room.height == 3.0, "房间高度应该是 3.0"

    # 验证物体数量
    item_count = room.get_item_count()
    assert item_count == 1, f"房间应该有 1 个物体，实际有 {item_count} 个"

    # 验证物体属性
    items = room.get_all_items()
    assert len(items) == 1, "应该有 1 个物体"
    assert items[0].item_name == "桌子", "物体名称应该是'桌子'"
    assert items[0].item_description == "一张木质书桌", "物体描述应该是'一张木质书桌'"
    assert items[0].theoretical_volume == 0.5, "物体理论体积应该是 0.5 m³"

    print("[PASS] 测试通过：build 函数基本功能正常")


def test_build_multiple_items():
    """测试添加多个物体"""
    print("\n" + "="*60)
    print("测试 2: 添加多个物体")
    print("="*60)

    # 创建一个房间，添加多个物体
    # 房间 GLB 尺寸为 6.0 x 5.0 x 3.0 = 90.0，理论体积为 90.0 m³
    item_list = [
        ("床", "双人床", 2.0),
        ("桌子", "书桌", 0.5),
        ("椅子", "办公椅", 0.2)
    ]

    room = build(
        room_type="卧室",
        length=6.0,
        width=5.0,
        height=3.0,
        room_theoretical_volume=90.0,
        item_list=item_list
    )

    # 验证物体数量
    item_count = room.get_item_count()
    assert item_count == 3, f"房间应该有 3 个物体，实际有 {item_count} 个"

    # 验证所有物体
    items = room.get_all_items()
    assert len(items) == 3, "应该有 3 个物体"

    item_names = [item.item_name for item in items]
    assert "床" in item_names, "应该包含'床'"
    assert "桌子" in item_names, "应该包含'桌子'"
    assert "椅子" in item_names, "应该包含'椅子'"

    print("[PASS] 测试通过：多个物体添加成功")


def test_build_custom_position():
    """测试自定义房间位置"""
    print("\n" + "="*60)
    print("测试 3: 自定义房间位置")
    print("="*60)

    # 房间 GLB 尺寸为 7.0 x 6.0 x 3.5 = 147.0，理论体积为 147.0 m³
    item_list = [("沙发", "三人沙发", 1.5)]

    room = build(
        room_type="客厅",
        length=7.0,
        width=6.0,
        height=3.5,
        room_theoretical_volume=147.0,
        item_list=item_list,
        x=10.0,
        y=20.0,
        z=0.0
    )

    # 验证房间位置
    assert room.x == 10.0, "房间 x 坐标应该是 10.0"
    assert room.y == 20.0, "房间 y 坐标应该是 20.0"
    assert room.z == 0.0, "房间 z 坐标应该是 0.0"

    print("[PASS] 测试通过：自定义房间位置正常")


def test_build_custom_color():
    """测试自定义初始颜色"""
    print("\n" + "="*60)
    print("测试 4: 自定义初始颜色")
    print("="*60)

    # 房间 GLB 尺寸为 5.0 x 4.0 x 3.0 = 60.0，理论体积为 60.0 m³
    item_list = [("柜子", "衣柜", 1.0)]

    # 使用浅灰色作为初始颜色
    custom_color = (200, 200, 200)

    room = build(
        room_type="卧室",
        length=5.0,
        width=4.0,
        height=3.0,
        room_theoretical_volume=60.0,
        item_list=item_list,
        initial_color=custom_color
    )

    # 验证初始颜色
    assert room.initial_color == custom_color, f"初始颜色应该是 {custom_color}"

    print("[PASS] 测试通过：自定义初始颜色正常")


def test_build_empty_room():
    """测试创建空房间（不添加物体）"""
    print("\n" + "="*60)
    print("测试 5: 创建空房间")
    print("="*60)

    # 创建一个空房间
    # 房间 GLB 尺寸为 3.0 x 3.0 x 2.5 = 22.5，理论体积为 22.5 m³
    room = build(
        room_type="储藏室",
        length=3.0,
        width=3.0,
        height=2.5,
        room_theoretical_volume=22.5,
        item_list=[]
    )

    # 验证房间属性
    assert isinstance(room, Room), "返回的对象应该是 Room 类型"
    assert room.get_item_count() == 0, "空房间应该没有物体"

    print("[PASS] 测试通过：空房间创建成功")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始运行 build 函数测试套件")
    print("="*60)

    try:
        test_build_basic()
        test_build_multiple_items()
        test_build_custom_position()
        test_build_custom_color()
        test_build_empty_room()

        print("\n" + "="*60)
        print("[SUCCESS] 所有测试通过！")
        print("="*60 + "\n")

    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}\n")
        raise
    except Exception as e:
        print(f"\n[ERROR] 测试出错: {e}\n")
        raise


if __name__ == "__main__":
    run_all_tests()

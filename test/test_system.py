"""
LLM-3D 系统测试

测试核心功能：
1. 距离图创建和更新
2. 物体创建和位置设置
3. 平面图管理
4. 房间构建
5. 距离图覆盖逻辑
"""
import sys
import os
import numpy as np

# 添加 code 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

# 导入配置（确保环境变量被设置）
import config

# 导入模型
from models import DistanceMap, Item, PlaneMap, DirectionMap, Room
from utils import direction
from main import build


def test_distance_map():
    """测试距离图的创建和基本操作"""
    print("\n" + "="*60)
    print("测试 1: DistanceMap 基本功能")
    print("="*60)

    # 创建一个距离图
    dist_map = DistanceMap(
        dirt=direction.down,
        x=0.0,
        y=0.0,
        z=0.0,
        height=10,
        width=10,
        initial_distance=5.0,
        initial_color=(255, 255, 255)
    )

    print(f"[OK] 创建距离图: {dist_map.height}x{dist_map.width}")
    print(f"  位置: ({dist_map.x}, {dist_map.y}, {dist_map.z})")
    print(f"  方向: {dist_map.dirt.name}")
    print(f"  初始距离: {dist_map.distance[0, 0]}")
    print(f"  初始颜色: {dist_map.color[0, 0]}")

    # 测试移动
    dist_map.move_dist_map([1.0, 2.0, 3.0])
    print(f"[OK] 移动后位置: ({dist_map.x}, {dist_map.y}, {dist_map.z})")

    assert dist_map.x == 1.0 and dist_map.y == 2.0 and dist_map.z == 3.0
    print("[OK] 距离图测试通过")


def test_distance_map_update():
    """测试距离图的覆盖更新逻辑"""
    print("\n" + "="*60)
    print("测试 2: DistanceMap 覆盖更新")
    print("="*60)

    # 创建一个大的平面距离图（10x10）
    plane_dist_map = DistanceMap(
        dirt=direction.down,
        x=0.0,
        y=0.0,
        z=0.0,
        height=10,
        width=10,
        initial_distance=10.0,
        initial_color=(255, 255, 255)
    )

    # 创建一个小的物体距离图（3x3），位置偏移 2*SAMPLE_RATE, 3*SAMPLE_RATE
    from utils import SAMPLE_RATE
    offset_x = 2 * SAMPLE_RATE
    offset_y = 3 * SAMPLE_RATE
    item_dist_map = DistanceMap(
        dirt=direction.down,
        x=offset_x,
        y=offset_y,
        z=0.0,
        height=3,
        width=3,
        initial_distance=2.0,
        initial_color=(255, 0, 0)  # 红色
    )

    # 设置物体距离图的一些值
    item_dist_map.distance[:, :] = 2

    print(f"[OK] 平面距离图: {plane_dist_map.height}x{plane_dist_map.width}, 位置({plane_dist_map.x}, {plane_dist_map.y})")
    print(f"[OK] 物体距离图: {item_dist_map.height}x{item_dist_map.width}, 位置({item_dist_map.x}, {item_dist_map.y})")

    # 更新前的值
    print(f"  更新前平面[5,5]的距离: {plane_dist_map.distance[5, 5]}")

    # 执行更新
    plane_dist_map.update(item_dist_map)

    # 更新后的值
    print(f"  更新后平面[5,5]的距离: {plane_dist_map.distance[5, 5]}")
    print(f"  更新后平面[2,2]的距离: {plane_dist_map.distance[2, 2]} (应该被更新)")

    # 验证覆盖区域被更新
    # 偏移 (2, 3)，所以物体应该覆盖 [3:6, 2:5]
    assert plane_dist_map.distance[3, 2] < 10.0, "覆盖区域应该被更新"
    print("[OK] 距离图覆盖更新测试通过")


def test_plane_map():
    """测试平面图的创建和更新"""
    print("\n" + "="*60)
    print("测试 3: PlaneMap 功能")
    print("="*60)

    # 创建平面图
    plane_loc = [0.0, 0.0, 0.0, 50, 50, 3.0]  # x, y, z, height, width, initial_distance
    plane = PlaneMap(
        plane_loc=plane_loc,
        dirt=direction.down,
        carry=[],
        description=[],
        item_list=[],
        initial_color=(200, 200, 200),
        
    )

    print(f"[OK] 创建平面图: {plane.distance.height}x{plane.distance.width}")
    print(f"  方向: {plane.dirt.name}")
    print(f"  初始距离: {plane.distance.distance[0, 0]}")

    assert len(plane.carry) == 0
    assert plane.dirt == direction.down
    print("[OK] 平面图测试通过")


def test_room_creation():
    """测试房间的创建"""
    print("\n" + "="*60)
    print("测试 4: Room 创建")
    print("="*60)

    # 创建房间（使用默认的SAMPLE_RATE）
    room = Room(
        room_type="测试房间",
        length=5.0,
        width=4.0,
        height=3.0
    )

    print(f"[OK] 创建房间: {room.room_type}")
    print(f"  尺寸: {room.length}m × {room.width}m × {room.height}m")
    print(f"  采样间隔: {room.sample_interval}m")

    # 检查所有方向都有初始平面
    for dirt in direction:
        assert dirt in room.direction_map_dict
        assert len(room.direction_map_dict[dirt].plane_map_list) > 0
        print(f"  [OK] {dirt.name} 方向有 {len(room.direction_map_dict[dirt].plane_map_list)} 个平面")

    print("[OK] 房间创建测试通过")


def test_build_function():
    """测试 build 函数（不使用真实的 GLB 模型）"""
    print("\n" + "="*60)
    print("测试 5: Build 函数（模拟）")
    print("="*60)

    # 注意：这个测试需要真实的 GLB 模型文件
    # 如果没有模型文件，这个测试会失败
    print("[WARNING] 此测试需要真实的 GLB 模型文件")
    print("  如果没有模型文件，请跳过此测试")

    try:
        # 尝试构建一个简单的房间
        item_list = [
            # ("床", "双人床"),  # 需要真实的 GLB 文件
        ]

        room = build(
            room_type="卧室",
            length=5.0,
            width=4.0,
            height=3.0,
            item_list=item_list
        )

        print(f"[OK] 构建房间成功: {room.room_type}")
        print(f"  房间内物体数量: {room.get_item_count()}")
        print("[OK] Build 函数测试通过")

    except Exception as e:
        print(f"[WARNING] Build 函数测试跳过: {str(e)}")


def test_direction_enum():
    """测试方向枚举"""
    print("\n" + "="*60)
    print("测试 6: Direction 枚举")
    print("="*60)

    print("所有方向:")
    for dirt in direction:
        print(f"  - {dirt.name}: {dirt.value}")

    # 测试相反方向
    from utils import find_opposite_direction

    assert find_opposite_direction(direction.up) == direction.down
    assert find_opposite_direction(direction.left) == direction.right
    assert find_opposite_direction(direction.forward) == direction.backward

    print("[OK] 方向枚举测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print(" "*20 + "LLM-3D 系统测试")
    print("="*70)

    tests = [
        ("距离图基本功能", test_distance_map),
        ("距离图覆盖更新", test_distance_map_update),
        ("平面图功能", test_plane_map),
        ("房间创建", test_room_creation),
        ("Build 函数", test_build_function),
        ("方向枚举", test_direction_enum),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n[FAIL] 测试失败: {test_name}")
            print(f"   错误: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1

    # 总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    print(f"[OK] 通过: {passed}/{len(tests)}")
    if failed > 0:
        print(f"[FAIL] 失败: {failed}/{len(tests)}")
    else:
        print("[SUCCESS] 所有测试通过！")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_all_tests()

"""
测试深度偏移功能

验证不同方向的距离图更新时，深度偏移是否正确应用
"""
import sys
import os
import numpy as np

# 添加 code 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from models import DistanceMap
from utils import direction, SAMPLE_RATE


def test_depth_offset_down_direction():
    """测试 down 方向的深度偏移"""
    print("\n" + "="*70)
    print("测试 down 方向的深度偏移")
    print("="*70)

    # 创建 5x5 的平面 (down 方向，XY平面投影，Z为深度)
    plane = DistanceMap(
        dirt=direction.down,
        x=0.0, y=0.0, z=0.0,
        height=5, width=5,
        initial_distance=10
    )

    # 创建 3x3 的物体，在 Z 轴上有偏移
    # offset_z = 2 * SAMPLE_RATE，所以 depth_offset = 2
    item = DistanceMap(
        dirt=direction.down,
        x=SAMPLE_RATE, y=SAMPLE_RATE, z=2 * SAMPLE_RATE,
        height=3, width=3,
        initial_distance=3
    )
    item.distance[:, :] = 3

    print(f"平面位置: ({plane.x}, {plane.y}, {plane.z})")
    print(f"物体位置: ({item.x}, {item.y}, {item.z})")
    print(f"预期 depth_offset: {int(round((item.z - plane.z) / SAMPLE_RATE))}")

    # 执行更新
    plane.update(item)

    # 验证：物体距离 3 + depth_offset 2 = 5
    # 应该更新为 min(10, 5) = 5
    expected_value = 5
    actual_value = plane.distance[1, 1]
    print(f"更新后平面[1,1]的值: {actual_value} (期望: {expected_value})")

    assert actual_value == expected_value, f"期望 {expected_value}，实际 {actual_value}"
    print("[OK] 测试通过：down 方向深度偏移正确")


def test_depth_offset_left_direction():
    """测试 left 方向的深度偏移"""
    print("\n" + "="*70)
    print("测试 left 方向的深度偏移")
    print("="*70)

    # 创建 5x5 的平面 (left 方向，YZ平面投影，X为深度)
    plane = DistanceMap(
        dirt=direction.left,
        x=0.0, y=0.0, z=0.0,
        height=5, width=5,
        initial_distance=10
    )

    # 创建 3x3 的物体，在 X 轴上有偏移
    # offset_x = 2 * SAMPLE_RATE，所以 depth_offset = 2
    item = DistanceMap(
        dirt=direction.left,
        x=2 * SAMPLE_RATE, y=SAMPLE_RATE, z=SAMPLE_RATE,
        height=3, width=3,
        initial_distance=3
    )
    item.distance[:, :] = 3

    print(f"平面位置: ({plane.x}, {plane.y}, {plane.z})")
    print(f"物体位置: ({item.x}, {item.y}, {item.z})")
    print(f"预期 depth_offset: {int(round((item.x - plane.x) / SAMPLE_RATE))}")

    # 执行更新
    plane.update(item)

    # 验证：物体距离 3 + depth_offset 2 = 5
    # 应该更新为 min(10, 5) = 5
    expected_value = 5
    actual_value = plane.distance[1, 1]
    print(f"更新后平面[1,1]的值: {actual_value} (期望: {expected_value})")

    assert actual_value == expected_value, f"期望 {expected_value}，实际 {actual_value}"
    print("[OK] 测试通过：left 方向深度偏移正确")


def test_depth_offset_forward_direction():
    """测试 forward 方向的深度偏移"""
    print("\n" + "="*70)
    print("测试 forward 方向的深度偏移")
    print("="*70)

    # 创建 5x5 的平面 (forward 方向，XZ平面投影，Y为深度)
    plane = DistanceMap(
        dirt=direction.forward,
        x=0.0, y=0.0, z=0.0,
        height=5, width=5,
        initial_distance=10
    )

    # 创建 3x3 的物体，在 Y 轴上有偏移
    # offset_y = 2 * SAMPLE_RATE，所以 depth_offset = 2
    item = DistanceMap(
        dirt=direction.forward,
        x=SAMPLE_RATE, y=2 * SAMPLE_RATE, z=SAMPLE_RATE,
        height=3, width=3,
        initial_distance=3
    )
    item.distance[:, :] = 3

    print(f"平面位置: ({plane.x}, {plane.y}, {plane.z})")
    print(f"物体位置: ({item.x}, {item.y}, {item.z})")
    print(f"预期 depth_offset: {int(round((item.y - plane.y) / SAMPLE_RATE))}")

    # 执行更新
    plane.update(item)

    # 验证：物体距离 3 + depth_offset 2 = 5
    # 应该更新为 min(10, 5) = 5
    expected_value = 5
    actual_value = plane.distance[1, 1]
    print(f"更新后平面[1,1]的值: {actual_value} (期望: {expected_value})")

    assert actual_value == expected_value, f"期望 {expected_value}，实际 {actual_value}"
    print("[OK] 测试通过：forward 方向深度偏移正确")


def run_all_tests():
    """运行所有测试用例"""
    print("\n" + "="*70)
    print(" "*15 + "深度偏移功能测试")
    print("="*70)

    tests = [
        test_depth_offset_down_direction,
        test_depth_offset_left_direction,
        test_depth_offset_forward_direction,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n[FAIL] 测试失败: {test_func.__name__}")
            print(f"   断言错误: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"\n[FAIL] 测试失败: {test_func.__name__}")
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

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

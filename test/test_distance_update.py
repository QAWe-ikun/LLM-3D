"""
距离图更新逻辑的单元测试

专门测试不同大小的距离图覆盖更新功能
"""
import sys
import os
import numpy as np

# 添加 code 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from models import DistanceMap
from utils import direction, SAMPLE_RATE


def visualize_distance_map(dist_map, title="Distance Map"):
    """可视化距离图（简单的文本表示）"""
    print(f"\n{title}:")
    print(f"  尺寸: {dist_map.height}x{dist_map.width}")
    print(f"  位置: ({dist_map.x:.2f}, {dist_map.y:.2f}, {dist_map.z:.2f})")
    print("  数据预览 (前5x5):")
    preview = dist_map.distance[:min(5, dist_map.height), :min(5, dist_map.width)]
    for row in preview:
        print("    " + " ".join(f"{val:3d}" for val in row))


def test_case_1_centered_overlap():
    """测试用例 1: 中心对齐的覆盖"""
    print("\n" + "="*70)
    print("测试用例 1: 中心对齐的覆盖")
    print("="*70)

    # 创建 10x10 的平面
    plane = DistanceMap(
        dirt=direction.down,
        x=0.0, y=0.0, z=0.0,
        height=10, width=10,
        initial_distance=10.0
    )

    # 创建 3x3 的物体，位置偏移 2*SAMPLE_RATE, 3*SAMPLE_RATE
    offset_x = 2 * SAMPLE_RATE
    offset_y = 3 * SAMPLE_RATE
    item = DistanceMap(
        dirt=direction.down,
        x=offset_x, y=offset_y, z=0.0,
        height=3, width=3,
        initial_distance=2.0
    )
    item.distance[:, :] = 2  # 设置为 2

    visualize_distance_map(plane, "更新前的平面")
    visualize_distance_map(item, "物体距离图")

    # 执行更新
    plane.update(item)

    visualize_distance_map(plane, "更新后的平面")

    # 验证：偏移 (2, 3)，所以应该在 [3:6, 2:5] 区域被更新
    assert plane.distance[3, 2] == 2, f"期望 2，实际 {plane.distance[3, 2]}"
    assert plane.distance[0, 0] == 10, f"未覆盖区域应保持原值"

    print("[OK] 测试通过：中心对齐的覆盖正确")


def test_case_2_edge_overlap():
    """测试用例 2: 边缘部分重叠"""
    print("\n" + "="*70)
    print("测试用例 2: 边缘部分重叠")
    print("="*70)

    # 创建 10x10 的平面
    plane = DistanceMap(
        dirt=direction.down,
        x=0.0, y=0.0, z=0.0,
        height=10, width=10,
        initial_distance=10.0
    )

    # 创建 5x5 的物体，位置偏移 7*SAMPLE_RATE, 8*SAMPLE_RATE，会部分超出平面
    offset_x = 7 * SAMPLE_RATE
    offset_y = 8 * SAMPLE_RATE
    item = DistanceMap(
        dirt=direction.down,
        x=offset_x, y=offset_y, z=0.0,
        height=5, width=5,
        initial_distance=3.0
    )
    item.distance[:, :] = 3

    visualize_distance_map(plane, "更新前的平面")
    visualize_distance_map(item, "物体距离图（部分超出）")

    # 执行更新
    plane.update(item)

    visualize_distance_map(plane, "更新后的平面")

    # 验证：偏移 (7, 8)，物体 5x5，平面 10x10
    # 重叠区域应该是 [8:10, 7:10]（平面坐标）
    assert plane.distance[8, 7] == 3, "边缘重叠区域应该被更新"
    assert plane.distance[0, 0] == 10, "未覆盖区域应保持原值"

    print("[OK] 测试通过：边缘部分重叠正确处理")


def test_case_3_no_overlap():
    """测试用例 3: 完全不重叠"""
    print("\n" + "="*70)
    print("测试用例 3: 完全不重叠")
    print("="*70)

    # 创建 10x10 的平面
    plane = DistanceMap(
        dirt=direction.down,
        x=0.0, y=0.0, z=0.0,
        height=10, width=10,
        initial_distance=10.0
    )

    # 创建 3x3 的物体，位置在 20*SAMPLE_RATE，完全在平面外
    offset = 20 * SAMPLE_RATE
    item = DistanceMap(
        dirt=direction.down,
        x=offset, y=offset, z=0.0,
        height=3, width=3,
        initial_distance=5.0
    )
    item.distance[:, :] = 5

    visualize_distance_map(plane, "更新前的平面")
    visualize_distance_map(item, "物体距离图（完全不重叠）")

    # 执行更新
    plane.update(item)

    visualize_distance_map(plane, "更新后的平面")

    # 验证：所有值应该保持不变
    assert np.all(plane.distance == 10), "不重叠时平面应保持不变"

    print("[OK] 测试通过：完全不重叠时正确处理")


def test_case_4_minimum_value():
    """测试用例 4: 取最小值逻辑"""
    print("\n" + "="*70)
    print("测试用例 4: 取最小值逻辑")
    print("="*70)

    # 创建 10x10 的平面，初始值为 5
    plane = DistanceMap(
        dirt=direction.down,
        x=0.0, y=0.0, z=0.0,
        height=10, width=10,
        initial_distance=5.0
    )

    # 创建 3x3 的物体，位置偏移 2*SAMPLE_RATE
    offset = 2 * SAMPLE_RATE
    item = DistanceMap(
        dirt=direction.down,
        x=offset, y=offset, z=0.0,
        height=3, width=3,
        initial_distance=0.0
    )
    # 设置一些值大于平面，一些值小于平面
    item.distance[0, 0] = 3  # 小于 5，应该更新
    item.distance[1, 1] = 7  # 大于 5，不应该更新
    item.distance[2, 2] = 2  # 小于 5，应该更新

    visualize_distance_map(plane, "更新前的平面")
    visualize_distance_map(item, "物体距离图（混合值）")

    # 执行更新
    plane.update(item)

    visualize_distance_map(plane, "更新后的平面")

    # 验证：只有更小的值会更新
    # 偏移 (2, 2)
    assert plane.distance[2, 2] == 3, "更小的值应该更新"
    assert plane.distance[3, 3] == 5, "更大的值不应该更新"
    assert plane.distance[4, 4] == 2, "更小的值应该更新"

    print("[OK] 测试通过：最小值逻辑正确")


def test_case_5_color_update():
    """测试用例 5: 颜色同步更新"""
    print("\n" + "="*70)
    print("测试用例 5: 颜色同步更新")
    print("="*70)

    # 创建 10x10 的平面，白色
    plane = DistanceMap(
        dirt=direction.down,
        x=0.0, y=0.0, z=0.0,
        height=10, width=10,
        initial_distance=10.0,
        initial_color=(255, 255, 255)
    )

    # 创建 3x3 的物体，红色，位置偏移 2*SAMPLE_RATE
    offset = 2 * SAMPLE_RATE
    item = DistanceMap(
        dirt=direction.down,
        x=offset, y=offset, z=0.0,
        height=3, width=3,
        initial_distance=7.0,
        initial_color=(255, 0, 0)
    )
    item.distance[:, :] = 7  # 设置为 7，大于 color_threshold (5)，会触发颜色更新

    print(f"更新前平面[2,2]颜色: {plane.color[2, 2]}")
    print(f"物体颜色: {item.color[0, 0]}")

    # 执行更新
    plane.update(item)

    print(f"更新后平面[2,2]颜色: {plane.color[2, 2]}")

    # 验证：颜色应该被更新为红色
    assert np.array_equal(plane.color[2, 2], [255, 0, 0]), "颜色应该被更新"
    assert np.array_equal(plane.color[0, 0], [255, 255, 255]), "未覆盖区域颜色应保持不变"

    print("[OK] 测试通过：颜色同步更新正确")


def run_all_tests():
    """运行所有测试用例"""
    print("\n" + "="*70)
    print(" "*15 + "距离图更新逻辑单元测试")
    print("="*70)

    tests = [
        test_case_1_centered_overlap,
        test_case_2_edge_overlap,
        test_case_3_no_overlap,
        test_case_4_minimum_value,
        test_case_5_color_update,
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

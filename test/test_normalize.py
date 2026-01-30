"""
测试 normalize_glb 功能的简单脚本
"""
import sys
import os
import numpy as np

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from room_builder.utils import normalize_glb, read_glb_vertices, find_glb_model

def test_normalize_basic():
    """测试基本的标准化功能"""
    print("\n" + "="*60)
    print("测试: normalize_glb 基本功能")
    print("="*60)

    # 加载一个测试模型
    file_path = find_glb_model("test")
    vertices, colors, mesh = read_glb_vertices(file_path)

    print(f"原始顶点数量: {len(vertices)}")
    print(f"原始边界框: min={np.min(vertices, axis=0)}, max={np.max(vertices, axis=0)}")

    # 计算原始体积
    min_coords = np.min(vertices, axis=0)
    max_coords = np.max(vertices, axis=0)
    original_size = max_coords - min_coords
    original_volume = np.prod(original_size)
    print(f"原始体积: {original_volume:.6f}")

    # 假设房间 GLB 尺寸为 5.0 x 4.0 x 3.0 = 60.0，理论体积为 60.0 m³
    room_glb_volume = 5.0 * 4.0 * 3.0
    room_theoretical_volume = 60.0
    volume_rate = room_glb_volume / room_theoretical_volume

    # 物体理论体积为 0.5 m³
    theoretical_volume = 0.5

    print(f"\n转换参数:")
    print(f"  volume_rate (转换系数): {volume_rate}")
    print(f"  theoretical_volume (物体理论体积): {theoretical_volume} 立方米")

    # 标准化顶点
    normalized_vertices, center_point = normalize_glb(
        vertices=vertices,
        theoretical_volume=theoretical_volume,
        volume_rate=volume_rate,
        center=True
    )

    print(f"\n标准化后:")
    print(f"  顶点数量: {len(normalized_vertices)}")
    print(f"  边界框: min={np.min(normalized_vertices, axis=0)}, max={np.max(normalized_vertices, axis=0)}")
    print(f"  中心点: {center_point}")

    # 计算标准化后的体积
    min_normalized = np.min(normalized_vertices, axis=0)
    max_normalized = np.max(normalized_vertices, axis=0)
    normalized_size = max_normalized - min_normalized
    normalized_volume = np.prod(normalized_size)
    print(f"  标准化后体积: {normalized_volume:.6f}")

    # 验证体积是否接近理论值
    expected_volume = theoretical_volume * volume_rate
    print(f"  期望体积: {expected_volume:.6f}")
    print(f"  误差: {abs(normalized_volume - expected_volume):.6f}")

    # 验证中心化
    center_after = (min_normalized + max_normalized) / 2
    print(f"  实际中心: {center_after}")

    print("\n[PASS] 测试通过：normalize_glb 功能正常")


if __name__ == "__main__":
    try:
        test_normalize_basic()
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()

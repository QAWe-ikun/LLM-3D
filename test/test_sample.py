import sys
import os
sys.path.append(os.path.dirname(__file__))

# 设置控制台编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from Utils import *
import matplotlib.pyplot as plt
import matplotlib

# 配置 matplotlib 支持中文显示
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']  # 指定中文字体
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def test_sample():
    """测试 sample 函数"""
    print("=" * 50)
    print("开始测试 sample 函数")
    print("=" * 50)

    # 加载测试模型
    glb_path = os.path.join(os.path.dirname(__file__), "..", "0.glb")
    print(f"\n1. 加载模型: {glb_path}")

    try:
        vertices, colors, mesh = read_glb_vertices(glb_path)
        print(f"   ✓ 成功加载模型")
        print(f"   - 顶点数量: {len(vertices)}")
        print(f"   - 三角面数量: {len(mesh.faces)}")
        print(f"   - 顶点坐标范围:")
        print(f"     X: [{np.min(vertices[:, 0]):.3f}, {np.max(vertices[:, 0]):.3f}]")
        print(f"     Y: [{np.min(vertices[:, 1]):.3f}, {np.max(vertices[:, 1]):.3f}]")
        print(f"     Z: [{np.min(vertices[:, 2]):.3f}, {np.max(vertices[:, 2]):.3f}]")
        print(f"   - 颜色数据形状: {colors.shape}")
    except Exception as e:
        print(f"   ✗ 加载模型失败: {e}")
        return

    # 计算模型尺寸
    print(f"\n2. 计算模型尺寸")
    x, y, z, length, width, height, length_sample_num, width_sample_num, height_sample_num = get_model_size(vertices)
    print(f"   - 原点: ({x:.3f}, {y:.3f}, {z:.3f})")
    print(f"   - 实际尺寸: length={length:.3f}, width={width:.3f}, height={height:.3f}")
    print(f"   - 网格数量: {length_sample_num} x {width_sample_num} x {height_sample_num}")

    # 测试每个方向的采样
    print(f"\n3. 测试各个方向的采样")
    test_directions = [
        (direction.up, "向上"),
        (direction.down, "向下"),
        (direction.left, "向左"),
        (direction.right, "向右"),
        (direction.forward, "向前"),
        (direction.backward, "向后")
    ]

    results = {}
    for dirt, name in test_directions:
        print(f"\n   测试方向: {name} ({dirt.name})")

        # 设置原点
        if dirt == direction.up or dirt == direction.down:
            origin_z = z if dirt == direction.down else z + height
            origin = [x, y, origin_z]
        elif dirt == direction.left or dirt == direction.right:
            origin_x = x if dirt == direction.left else x + length
            origin = [origin_x, y, z]
        else:
            origin_y = y if dirt == direction.backward else y + width
            origin = [x, origin_y, z]

        try:
            # 调用 sample 函数
            dist_map = sample(mesh, dirt, origin)

            print(f"   ✓ 采样成功")
            print(f"     - 网格尺寸: {dist_map.width} x {dist_map.height}")
            print(f"     - 距离图形状: {dist_map.distance.shape}")
            print(f"     - 颜色图形状: {dist_map.color.shape}")
            print(f"     - 最大距离值: {np.max(dist_map.distance)}")
            print(f"     - 非零距离点数: {np.count_nonzero(dist_map.distance)}")

            results[dirt.name] = dist_map
        except Exception as e:
            print(f"   ✗ 采样失败: {e}")
            import traceback
            traceback.print_exc()

    # 可视化结果
    print(f"\n4. 可视化结果")
    try:
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Sample 函数测试结果 - 各方向距离图', fontsize=16)

        for idx, (dirt, name) in enumerate(test_directions):
            ax = axes[idx // 3, idx % 3]

            if dirt.name in results:
                dist_map = results[dirt.name]

                # 显示距离图
                im = ax.imshow(dist_map.distance, cmap='viridis', origin='lower')
                ax.set_title(f'{name} ({dist_map.width}x{dist_map.height})')
                ax.set_xlabel('Width')
                ax.set_ylabel('Height')
                plt.colorbar(im, ax=ax, label='Distance')
            else:
                ax.text(0.5, 0.5, '采样失败', ha='center', va='center')
                ax.set_title(name)

        plt.tight_layout()

        # 保存图像
        output_path = os.path.join(os.path.dirname(__file__), "test_sample_result.png")
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"   ✓ 结果已保存到: {output_path}")

        # 显示图像
        plt.show()
    except Exception as e:
        print(f"   ✗ 可视化失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    test_sample()

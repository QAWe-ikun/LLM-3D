# 测试文档

## 概述

本目录包含 LLM-3D 项目的测试代码。

## 测试文件

### test_build.py

测试 `build` 函数的功能，包括：

1. **test_build_basic**: 测试基本功能，创建房间并添加一个物体
2. **test_build_multiple_items**: 测试添加多个物体
3. **test_build_custom_position**: 测试自定义房间位置
4. **test_build_custom_color**: 测试自定义初始颜色
5. **test_build_empty_room**: 测试创建空房间

## 运行测试

```bash
cd test
python test_build.py
```

## 导入方式

测试代码使用以下方式导入 room_builder 包：

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from room_builder import build, Room, Item
```

## 当前状态

测试代码已经编写完成，但由于以下功能尚未实现，测试暂时无法完全通过：

- `PlaneMap.find_location()` - 在平面上寻找合适的位置放置物体
- 其他可能的未实现功能

## 已实现的功能

以下功能已经实现并可以测试：

1. ✓ `find_glb_model()` - 查找 GLB 模型文件
2. ✓ `Room` 类初始化
3. ✓ `Item` 类初始化和模型加载
4. ✓ `DirectionMap` 类和方向选择
5. ✓ `PlaneMap` 类和平面选择
6. ✓ `create_and_add_plane_from_item()` - 创建新平面
7. ✓ `room_builder` 包的 `__init__.py` - 提供统一的导入接口

## 使用的模型

测试使用 `models/0.glb` 文件作为所有物体的模型。这是一个临时方案，将来会根据物体名称加载不同的模型。

## 注意事项

1. 测试代码使用 ASCII 字符（如 `[OK]`, `[FAIL]`）而不是 Unicode 字符，以避免 Windows 控制台编码问题
2. 测试需要访问 LLM API，确保已正确配置 API 密钥
3. 测试可能需要较长时间运行，因为涉及 LLM 调用
4. 包名已从 `code` 改为 `room_builder`，避免与 Python 标准库冲突

## 下一步

一旦 `find_location` 等方法实现后，测试应该能够完全通过。

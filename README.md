# LLM-3D 代码结构

## 目录结构

```
code/
├── models/              # 数据模型层
│   ├── __init__.py     # 模型导出
│   ├── distance_map.py # 距离图类
│   ├── item.py         # 物体类
│   ├── plane_map.py    # 平面图类
│   ├── direction_map.py# 方向图类
│   └── room.py         # 房间类
│
├── services/           # 服务层
│   ├── __init__.py    # 服务导出
│   └── llm_service.py # 百炼大模型服务
│
├── utils/             # 工具函数层
│   ├── __init__.py   # 工具导出
│   └── geometry.py   # 几何计算工具
│
├── config.py         # 配置文件
└── main.py          # 主程序入口
```

## 模块说明

### 1. models/ - 数据模型层
核心数据结构和业务逻辑

- **DistanceMap**: 距离图类，存储和管理某个方向上的距离和颜色信息
- **Item**: 物体类，表示3D场景中的一个物体
- **PlaneMap**: 平面图类，表示某个方向上的一个平面及其上的物体
- **DirectionMap**: 方向图类，管理某个方向上的所有平面图
- **Room**: 房间类，表示一个完整的3D场景空间

### 2. services/ - 服务层
外部服务和业务逻辑

- **llm_service**: 百炼大模型客户端，提供与阿里云百炼API的交互接口
  - `BailianClient`: 客户端类
  - `get_client()`: 获取全局客户端实例

### 3. utils/ - 工具函数层
通用工具函数

- **geometry**: 几何计算和采样工具
  - `direction`: 方向枚举
  - `find_glb_model()`: 查找GLB模型文件
  - `read_glb_vertices()`: 读取GLB顶点数据
  - `get_model_size()`: 获取模型尺寸
  - `sample()`: 采样函数
  - `find_opposite_direction()`: 查找相反方向
  - `SAMPLE_RATE`: 采样率常量

### 4. config.py - 配置文件
项目配置参数

- API配置（百炼大模型）
- 模型配置
- 场景布局配置
- 日志配置

### 5. main.py - 主程序入口
程序入口和构建函数

- `build()`: 构建房间布局的主函数

## 使用方式

### 导入模块

```python
# 导入模型
from models import Room, Item, PlaneMap, DirectionMap, DistanceMap

# 导入服务
from services import get_client

# 导入工具
from utils import direction, SAMPLE_RATE

# 导入主函数
from main import build
```

### 构建房间

```python
from main import build

# 定义物体列表
item_list = [
    ("床", "双人床"),
    ("桌子", "书桌"),
    ("椅子", "办公椅")
]

# 构建房间
room = build(
    room_type="卧室",
    length=5.0,
    width=4.0,
    height=3.0,
    item_list=item_list
)
```

## 依赖关系

```
config.py (配置)
    ↓
utils/ (工具层)
    ↓
services/ (服务层)
    ↓
models/ (模型层)
    ↓
main.py (入口)
```

## 特性

- **层次分明**: 清晰的三层架构（模型层、服务层、工具层）
- **模块化**: 每个模块职责单一，易于维护
- **可扩展**: 便于添加新的模型、服务或工具
- **智能决策**: 集成百炼大模型进行智能布局决策


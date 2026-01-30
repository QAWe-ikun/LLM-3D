"""
room_builder 代码包

这是 LLM-3D 项目的主代码包，提供基于大语言模型的3D场景布局功能。

主要功能：
- 使用 LLM 智能布局3D场景
- 支持多种房间类型和物体
- 自动计算物体位置和方向
- 生成距离图和颜色图

快速开始：
    >>> from room_builder import build
    >>> item_list = [("床", "双人床"), ("桌子", "书桌")]
    >>> room = build("卧室", 5.0, 4.0, 3.0, item_list)

版本：0.1.0
"""

# 导入主函数
from .main import build

# 导入核心模型类
from .models import (
    Room,
    Item,
    PlaneMap,
    DirectionMap,
    DistanceMap,
)

# 导入工具函数和常量
from .utils import (
    direction,
    find_glb_model,
    read_glb_vertices,
    get_model_size,
    sample,
    find_opposite_direction,
    SAMPLE_RATE,
)

# 导入服务
from .services import (
    BailianClient,
    get_client,
)

# 导入配置常量
from .config import (
    DEFAULT_MODEL,
    AVAILABLE_MODELS,
    DEFAULT_SAMPLE_INTERVAL,
    DEFAULT_INITIAL_COLOR,
    VERBOSE_LOGGING,
    SHOW_LLM_DECISIONS,
)

# 定义公共接口
__all__ = [
    # 主函数
    'build',

    # 核心模型类
    'Room',
    'Item',
    'PlaneMap',
    'DirectionMap',
    'DistanceMap',

    # 工具函数
    'direction',
    'find_glb_model',
    'read_glb_vertices',
    'get_model_size',
    'sample',
    'find_opposite_direction',

    # 服务
    'BailianClient',
    'get_client',

    # 常量
    'SAMPLE_RATE',
    'DEFAULT_MODEL',
    'AVAILABLE_MODELS',
    'DEFAULT_SAMPLE_INTERVAL',
    'DEFAULT_INITIAL_COLOR',
    'VERBOSE_LOGGING',
    'SHOW_LLM_DECISIONS',
]

# 版本信息
__version__ = '0.1.0'
__author__ = 'LLM-3D Team'
__description__ = '基于大语言模型的3D场景布局系统'

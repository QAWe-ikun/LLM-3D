"""
服务层

包含外部服务和业务逻辑
"""
from .llm_service import BailianClient, get_client

__all__ = [
    'BailianClient',
    'get_client',
]

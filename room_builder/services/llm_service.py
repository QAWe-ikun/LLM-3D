"""
百炼大模型客户端模块

提供与阿里云百炼大模型 API 的交互接口
"""
import os
from typing import Optional, Union, List
import requests
import json
import base64
import numpy as np

# 导入配置
try:
    import config  # 确保配置被加载
except ImportError:
    pass


class BailianClient:
    """
    百炼大模型客户端类
    """
    def __init__(self, api_key: Optional[str] = None, model: str = "qwen-plus"):
        """
        初始化百炼客户端

        参数:
            api_key: API 密钥，如果不提供则从环境变量 DASHSCOPE_API_KEY 读取
            model: 使用的模型名称，默认为 qwen-plus
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("API 密钥未提供，请设置环境变量 DASHSCOPE_API_KEY 或传入 api_key 参数")

        self.model = model
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        # 视觉模型 API 地址
        self.vl_base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

    def chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        调用百炼大模型进行对话

        参数:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）

        返回:
            模型的响应文本
        """
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        messages.append({
            "role": "user",
            "content": prompt
        })

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "result_format": "message"
            }
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            # 解析响应
            if result.get("output") and result["output"].get("choices"):
                return result["output"]["choices"][0]["message"]["content"]
            else:
                raise ValueError(f"API 响应格式错误：{result}")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"调用百炼 API 失败：{str(e)}")

    def chat_with_image(self, prompt: str, image_data: Union[np.ndarray, List[np.ndarray]], model: str = "qwen-vl-max") -> str:
        """
        调用百炼视觉模型进行图文对话

        参数:
            prompt: 用户提示词
            image_data: numpy 数组或数组列表，形状为 (H, W, 3) 的 RGB 图像数据
            model: 使用的视觉模型名称，默认为 qwen-vl-max

        返回:
            模型的响应文本
        """
        # 将 numpy 数组转换为 base64 编码的 JPEG 图像
        import io
        from PIL import Image

        # 统一处理为列表
        if isinstance(image_data, np.ndarray):
            image_list = [image_data]
        else:
            image_list = image_data

        # 构建 content 列表，先添加所有图片
        content = []
        for img_array in image_list:
            img = Image.fromarray(img_array)
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            content.append({"image": f"data:image/jpeg;base64,{img_base64}"})

        # 最后添加文本提示
        content.append({"text": prompt})

        messages = [
            {
                "role": "user",
                "content": content
            }
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "result_format": "message"
            }
        }

        try:
            response = requests.post(
                self.vl_base_url,
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()

            # 解析响应
            if result.get("output") and result["output"].get("choices"):
                return result["output"]["choices"][0]["message"]["content"]
            else:
                raise ValueError(f"API 响应格式错误：{result}")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"调用百炼视觉 API 失败：{str(e)}")


# 全局客户端实例（懒加载）
_client: Optional[BailianClient] = None


def get_client() -> BailianClient:
    """
    获取全局百炼客户端实例

    返回:
        BailianClient 实例
    """
    global _client
    if _client is None:
        _client = BailianClient()
    return _client

"""应用内使用的 Pydantic 数据模型。

包含整合的模型元数据（ModelMeta，通常由 Civitai 获取并在本地缓存）。
"""
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from api.utils.civitai import AIR
from .draw import DrawArgs, Example


class ModelMeta(BaseModel):
    """
    模型元数据。
    
    概念说明：
    - ecosystem: 生态系统/技术代际（sd1, sd2, sdxl）
    - base_model: 基础模型（pony, illustrious, standard 等）
    """
    filename: str
    name: str
    version: str
    desc: str | None
    model_id: int
    version_id: int
    type: Literal['checkpoint', 'lora', 'vae']  # 模型类型
    ecosystem: Literal['sd1', 'sd2', 'sdxl']  # 生态系统/技术代际
    base_model: str | None = None  # 基础模型（pony, illustrious, standard 等），可选
    sha256: str
    trained_words: list[str] = []
    url: str | None = None  # 下载链接（可选）
    web_page_url: str | None = None  # 模型网页链接（如 Civitai 页面）
    examples: list[Example] = []
    preference: Literal['liked', 'neutral', 'disliked'] = 'neutral'  # 模型偏好：喜欢、中性、不喜欢（默认中性）

    @property
    def version_name(self) -> str:
        """
        获取模型版本名称。
        """
        return f'{self.name}-{self.version}'


    @property
    def air(self) -> str:
        """
        生成 AIR (Artificial Intelligence Resources) 标识符。
        
        格式：urn:air:{ecosystem}:{type}:civitai:{model_id}@{version_id}
        
        示例：
        - Checkpoint: urn:air:sd1:checkpoint:civitai:4384@128713
        - LoRA: urn:air:sdxl:lora:civitai:328553@368189
        """
        air = AIR(
            ecosystem=self.ecosystem,
            type=self.type,
            model_id=self.model_id,
            version_id=self.version_id,
        )
        return str(air)

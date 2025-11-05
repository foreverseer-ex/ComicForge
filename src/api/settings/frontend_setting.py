"""
前端 UI 设置
"""
from pydantic import BaseModel, Field


class FrontendSettings(BaseModel):
    """前端 UI 设置类"""
    image_cache_size: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="图片缓存数量（10-1000）"
    )


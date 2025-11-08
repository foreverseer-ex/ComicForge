"""
Civitai 服务配置
"""
import os
from typing import Optional
from pydantic import BaseModel, Field


class CivitaiSettings(BaseModel):
    """Civitai API 配置类。

    配置 Civitai 服务的基础 URL、API 密钥和请求超时。
    
    环境变量支持：
    - CIVITAI_API_TOKEN: 设置 api_token
    """
    api_token: Optional[str] = Field(
        default_factory=lambda: os.getenv("CIVITAI_API_TOKEN"),
        description="Civitai API Token（可选，用于访问私有内容）。可通过环境变量 CIVITAI_API_TOKEN 设置"
    )
    
    timeout: float = Field(
        default=60.0,
        gt=0,
        description="API 请求超时时间（秒），默认60秒"
    )
    
    parallel_workers: int = Field(
        default=4,
        ge=1,
        le=10,
        description="并行下载元数据时的线程数（1-10），默认4"
    )
    
    draw_timeout: int = Field(
        default=600,
        ge=60,
        le=3600,
        description="绘图任务超时时间（秒），60-3600秒，默认10分钟"
    )
    
    retry_count: int = Field(
        default=5,
        ge=1,
        le=10,
        description="API 调用失败时的重试次数（1-10），默认5次"
    )
    
    retry_delay: float = Field(
        default=5.0,
        gt=0,
        le=60,
        description="重试延迟时间（秒），0-60秒，默认5秒"
    )
"""
模型元数据服务模块。

提供数据库和 Civitai 两种模型元数据服务，都实现了统一的基类接口。
模型元数据存储在数据库中，不再使用 JSON 文件存储。
"""
from .base import AbstractModelMetaService
from .civitai import CivitaiModelMetaService, civitai_model_meta_service
from .db import ModelMetaDbService, model_meta_db_service

__all__ = [
    # 基类
    "AbstractModelMetaService",
    # Civitai 服务
    "CivitaiModelMetaService",
    "civitai_model_meta_service",
    # 数据库服务
    "ModelMetaDbService",
    "model_meta_db_service",
]

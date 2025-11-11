"""应用内使用的 Pydantic 数据模型。

包含整合的模型元数据（ModelMeta，通常由 Civitai 获取并在本地缓存）。
"""
from pathlib import Path
from typing import Literal, List, Dict, Any, Optional
from datetime import datetime

from pydantic import BaseModel, Field as PydanticField
from sqlmodel import SQLModel, Field, Index
from sqlalchemy import Column, String, JSON
from sqlalchemy.ext.mutable import MutableList, MutableDict
from loguru import logger

from api.utils.civitai import AIR
from .draw import DrawArgs, Example


class ModelMetaTable(SQLModel, table=True):
    """
    模型元数据数据库表。
    
    使用 SQLModel 存储模型元数据，支持通过数据库查询。
    examples 和 trained_words 使用 JSON 列存储。
    """
    __tablename__ = "model_meta"
    __table_args__ = (
        Index('idx_version_id', 'version_id', unique=True),
        Index('idx_model_id', 'model_id'),
        Index('idx_type', 'type'),
        Index('idx_ecosystem', 'ecosystem'),
        Index('idx_name_version', 'name', 'version'),
    )
    
    version_id: int = Field(primary_key=True, description="模型版本 ID（Civitai version_id）")
    filename: str = Field(sa_column=Column(String(255), nullable=False), description="模型文件名")
    name: str = Field(sa_column=Column(String(255), nullable=False), description="模型名称")
    version: str = Field(sa_column=Column(String(100), nullable=False), description="模型版本")
    desc: Optional[str] = Field(default=None, sa_column=Column(String(2000)), description="模型描述")
    model_id: int = Field(index=True, description="模型 ID（Civitai model_id）")
    type: str = Field(sa_column=Column(String(20), nullable=False), description="模型类型：checkpoint, lora, vae")
    ecosystem: str = Field(sa_column=Column(String(10), nullable=False), description="生态系统：sd1, sd2, sdxl")
    base_model: Optional[str] = Field(default=None, sa_column=Column(String(50)), description="基础模型")
    sha256: str = Field(sa_column=Column(String(64), nullable=False), description="文件 SHA-256 哈希值")
    trained_words: list[str] = Field(
        default_factory=list,
        sa_column=Column(MutableList.as_mutable(JSON())),
        description="训练关键词列表"
    )
    url: Optional[str] = Field(default=None, sa_column=Column(String(500)), description="下载链接")
    web_page_url: Optional[str] = Field(default=None, sa_column=Column(String(500)), description="网页链接")
    examples: list[dict] = Field(
        default_factory=list,
        sa_column=Column(MutableList.as_mutable(JSON())),
        description="示例图片列表（JSON）"
    )
    preference: str = Field(default='neutral', sa_column=Column(String(20)), description="模型偏好：liked, neutral, disliked")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    @property
    def version_name(self) -> str:
        """获取模型版本名称。"""
        return f'{self.name}-{self.version}'


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
    
    @classmethod
    def from_table(cls, table: ModelMetaTable) -> 'ModelMeta':
        """从数据库表转换为 Pydantic 模型。"""
        # 将 examples JSON 转换为 Example 对象列表
        example_objs = []
        for ex_dict in (table.examples or []):
            try:
                # 如果已经是字典格式，处理它
                if isinstance(ex_dict, dict):
                    # 确保有必要的字段
                    if 'filename' not in ex_dict:
                        continue
                    
                    # 处理 url：确保 url 在 extra 中（Example 的 url 属性从 extra 读取）
                    if 'url' in ex_dict and 'extra' not in ex_dict:
                        ex_dict['extra'] = {'url': ex_dict['url']}
                    elif 'url' in ex_dict and 'extra' in ex_dict:
                        # 如果 extra 存在，确保 url 在其中
                        if not isinstance(ex_dict['extra'], dict):
                            ex_dict['extra'] = {}
                        ex_dict['extra']['url'] = ex_dict['url']
                    elif 'extra' in ex_dict and isinstance(ex_dict['extra'], dict) and 'url' in ex_dict['extra']:
                        # 如果 url 在 extra 中，也添加到顶层（向后兼容）
                        ex_dict['url'] = ex_dict['extra']['url']
                    
                    # 处理 draw_args（可能为 None 或不存在）
                    if 'draw_args' not in ex_dict or ex_dict['draw_args'] is None:
                        # 如果没有 draw_args，创建一个默认的 DrawArgs
                        from .draw import DrawArgs
                        ex_dict['draw_args'] = DrawArgs(
                            prompt="",
                            negative_prompt="",
                            model="",
                            width=1024,
                            height=1024,
                            seed=-1
                        )
                    elif isinstance(ex_dict['draw_args'], dict):
                        # 如果 draw_args 是字典，转换为 DrawArgs 对象
                        from .draw import DrawArgs
                        ex_dict['draw_args'] = DrawArgs(**ex_dict['draw_args'])
                    
                    example_objs.append(Example(**ex_dict))
                elif isinstance(ex_dict, Example):
                    example_objs.append(ex_dict)
            except Exception as e:
                # 如果转换失败，记录日志并跳过
                logger.debug(f"转换 Example 失败: {ex_dict}, 错误: {e}")
                continue
        
        return cls(
            filename=table.filename,
            name=table.name,
            version=table.version,
            desc=table.desc,
            model_id=table.model_id,
            version_id=table.version_id,
            type=table.type,  # type: ignore
            ecosystem=table.ecosystem,  # type: ignore
            base_model=table.base_model,
            sha256=table.sha256,
            trained_words=table.trained_words or [],
            url=table.url,
            web_page_url=table.web_page_url,
            examples=example_objs,
            preference=table.preference,  # type: ignore
        )

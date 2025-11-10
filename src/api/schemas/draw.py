"""
绘图相关的数据模型。
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field as PydanticField, model_serializer
from sqlalchemy import Column, JSON
from sqlalchemy.ext.mutable import MutableList
from sqlmodel import SQLModel, Field


class DrawArgs(BaseModel):
    """绘图参数。
    
    包含所有 Stable Diffusion 绘图所需的参数。
    """
    model: str
    prompt: str
    negative_prompt: str = ""
    steps: int = 20
    cfg_scale: float = 7.0
    sampler: str = "Euler a"
    seed: int = -1
    width: int = 512
    height: int = 512
    clip_skip: int | None = 2
    vae: str | None = None  # VAE 模型名称
    loras: dict[str, float] | None = None  # LoRA 字典 {name: weight}，权重可以是负数（负数表示负面 LoRA，会被添加到负面提示词）


class Example(BaseModel):
    """示例图（立绘或模型示例图）。
    
    统一的示例图结构，用于：
    - Actor 的立绘示例
    - Model 的示例图
    
    字段说明：
    - title: 示例标题（可选）
    - desc: 示例说明（可选）
    - extra: 额外数据字典，用于存储：
        - url: 图片 URL（用于模型示例）
        - job_id: 关联的 job ID（用于从 job 添加的立绘）
        - batch_id: 关联的 batch ID（用于从 batch 添加的立绘）
    - draw_args: 生成参数
    - filename: 文件名（必需，在创建时提供）
    
    注意：
    - 图片的生成状态由关联的 Job 对象的 status 字段管理（pending/completed/failed）
    - 如果文件不存在，应通过 job_id 查询 Job 状态以确定原因
    """
    title: str | None = None
    desc: str | None = None
    extra: dict = PydanticField(default_factory=dict)
    draw_args: DrawArgs
    filename: str
    
    @property
    def url(self) -> str | None:
        """从 extra 中获取 URL（向后兼容）。"""
        return self.extra.get('url')
    
    @model_serializer
    def ser_model(self) -> dict:
        """自定义序列化，将 extra['url'] 提取为顶层字段。"""
        data = {
            'title': self.title,
            'desc': self.desc,
            'extra': self.extra,
            'draw_args': self.draw_args.model_dump() if self.draw_args else None,
            'filename': self.filename,
        }
        # 将 url 提取为顶层字段（方便前端访问）
        if 'url' in self.extra:
            data['url'] = self.extra['url']
        return data


class Job(SQLModel, table=True):
    """
    单个绘图任务。
    
    记录单次图像生成任务的基本信息。
    """
    job_id: Optional[str] = Field(description="任务唯一标识", primary_key=True,default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = Field(default=None, description="任务名称")
    desc: Optional[str] = Field(default=None, description="任务描述")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间（成功或失败都会设置）")
    status: Optional[str] = Field(default=None, description="任务状态：completed（成功）、failed（失败）、pending（进行中）")
    draw_args: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON()),
        description="绘图参数（DrawArgs 的字典形式）"
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON()),
        description="额外数据（JSON 格式），用于存储后端特定的信息，如 Civitai 的 job_token"
    )


class BatchJob(SQLModel, table=True):
    """
    批量绘图任务。
    
    管理一批相关的绘图任务。
    """
    batch_id: Optional[str] = Field(description="批次唯一标识", primary_key=True,default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    job_ids: list[str] = Field(
        default_factory=list,
        sa_column=Column(MutableList.as_mutable(JSON())),
        description="关联的任务 ID 列表"
    )


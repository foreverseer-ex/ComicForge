"""
记忆系统相关的数据模型。

用于存储背景设定、世界观、用户偏好、章节信息等上下文信息。
键值对设计，所有配置通过 MemoryEntry 存储，键名定义在 constants/memory.py 中。

所有 value 统一使用纯文本字符串，不使用 JSON 格式。
对于列表类型的数据（如标签列表），使用逗号分隔的字符串存储，例如 "tag1, tag2, tag3"。
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON, Index
from pydantic import BaseModel


class MemoryEntry(SQLModel, table=True):
    """
    记忆条目 - 简化的键值对存储。
    
    常见的 key 类型：
    - 世界观设定：使用 constants.memory.novel_memory_description 中定义的中文键
      如：'作品类型'、'主题'、'背景设定'、'主要地点'、'故事梗概'
    - 用户偏好：使用 constants.memory.user_memory_description 中定义的中文键
      如：'艺术风格'、'避免的标签'、'喜欢的标签'、'补充说明'、'其他偏好'
    - 章节信息：通过 ChapterSummary 专门处理
    - 其他：自定义 key，如重要情节、角色笔记、用户反馈等
    """
    memory_id: Optional[str] = Field(description="记忆唯一标识", primary_key=True, default_factory=lambda: str(uuid.uuid4()))
    project_id: Optional[str] = Field(default=None, description="所属项目ID（None 表示默认工作空间）", index=True)
    key: str = Field(description="记忆键名（建议使用 constants.memory.memory_description 中定义的键）", index=True)
    value: str = Field(description="记忆值（纯文本字符串，列表类型使用逗号分隔）")
    description: Optional[str] = Field(default=None,
                                       description="键的描述（可从 constants.memory.memory_description 自动填充）")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ChapterSummary(SQLModel, table=True):
    """
    章节摘要。
    
    用于存储章节的元数据和AI生成的梗概。
    小说按行解析，每行对应一个段落和一张图片。
    
    注意：
    - chapter_index = -1 表示全文摘要（文章摘要）
    - chapter_index >= 0 表示章节摘要
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: Optional[str] = Field(default=None, description="所属项目ID（None 表示默认工作空间）", index=True)
    chapter_index: int = Field(ge=-1, description="章节索引（-1 表示全文摘要，>=0 表示章节索引，从0开始）", index=True)
    title: str = Field(description="章节标题（全文摘要时通常为项目标题）")
    summary: Optional[str] = Field(default=None, description="章节故事梗概（AI生成）")
    start_line: int = Field(ge=0, description="起始行号（全文摘要时为0）")
    end_line: int = Field(ge=0, description="结束行号（全文摘要时为最后一行的行号）")


class ChatSummary(SQLModel, table=True):
    """
    聊天摘要。
    
    用于存储聊天的摘要内容。
    """

    project_id: str = Field(description="所属项目ID", index=True, primary_key=True)
    data: Optional[str] = Field(default=None, description="摘要内容")
    created_at: datetime = Field(default_factory=datetime.now)

class DrawIteration(SQLModel, table=True):
    """
    迭代式绘图的数据库模型。
    
    状态说明：
    - pending: 创建状态（初始化），没有 draw_args 和 summary，但其他参数已初始化
    - drawing: 绘图状态，已经生成了 draw_args 和 summary，但还没有生成实际的图像
    - completed: 完成状态，即有 draw_args，也有 summary，并且已经生成了实际图像
    - cancelled: 取消状态，用户主动取消的任务，迭代过程中遇到此状态会提前退出
    """
    __table_args__ = (
        Index('idx_draw_iteration_project_index', 'project_id', 'index', unique=True),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: str = Field(description="所属项目ID", index=True)
    index: int = Field(description="迭代索引", index=True)
    status: str = Field(default="pending", description="任务状态：pending（创建状态）、drawing（绘图状态）、completed（完成状态）、cancelled（取消状态）", index=True)
    summary: Optional[str] = Field(default=None, description="迭代摘要")
    draw_args: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="绘图参数（JSON格式）")

class MemoryCreateRequest(BaseModel):
    """创建记忆条目的请求模型"""
    project_id: Optional[str] = None
    key: str
    value: str
    description: Optional[str] = None


class MemoryUpdateRequest(BaseModel):
    """更新记忆条目的请求模型"""
    key: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None

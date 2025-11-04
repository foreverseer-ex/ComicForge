"""
聊天消息数据库模型。

使用简单的数据库结构存储聊天消息：
- project_id: 项目ID
- index: 消息顺序（0-based）
- message_id: 消息唯一标识
- status: 消息状态（ready/thinking/error）
- message_type: 消息类型（normal/iteration）
- message: 消息内容（字符串，JSON序列化）
- tools: 工具调用（JSON）
- data: 额外数据（JSON，用于迭代消息等）
"""
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON, Index
from sqlalchemy import String


class ChatMessageDB(SQLModel, table=True):
    """
    聊天消息数据库模型。
    
    简化的数据库结构，避免复杂的嵌套结构。
    """
    __tablename__ = "chat_message"
    __table_args__ = (
        Index('idx_session_index', 'project_id', 'index'),
        Index('idx_session_message_id', 'project_id', 'message_id'),
    )
    
    id: int | None = Field(default=None, primary_key=True, description="自增主键")
    project_id: str = Field(
        sa_column=Column(String(36), nullable=False, index=True),
        description="项目ID"
    )
    index: int = Field(ge=0, description="消息顺序（0-based）")
    message_id: str = Field(
        sa_column=Column(String(36), nullable=False, index=True),
        description="消息唯一标识（UUID）"
    )
    status: str = Field(
        default="ready",
        sa_column=Column(String(20), nullable=False),
        description="消息状态：ready（就绪）、thinking（AI思考中）、error（错误）"
    )
    message_type: str = Field(
        default="normal",
        sa_column=Column(String(20), nullable=False),
        description="消息类型：normal（普通消息）、iteration（迭代消息）"
    )
    role: str = Field(
        sa_column=Column(String(20), nullable=False),
        description="消息角色：system、user、assistant"
    )
    message: str = Field(
        default="",
        sa_column=Column(String(10000), nullable=False),
        description="消息内容（文本内容，JSON序列化）"
    )
    tools: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
        description="工具调用列表（JSON格式）"
    )
    data: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
        description="额外数据（JSON格式，用于迭代消息的index、stop、step、summary等）"
    )
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


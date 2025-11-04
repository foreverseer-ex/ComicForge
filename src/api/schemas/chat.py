from datetime import datetime
from typing import Optional, Any

from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field
from pydantic import BaseModel


class ChatIteration(BaseModel):
    """迭代消息"""
    # 迭代模式专用字段
    target: str = Field(
        description="迭代目标，描述要做什么（如：'提取全文角色'、'生成章节摘要'）"
    )

    index: int = Field(
        description="当前迭代索引。对于全文迭代，这是当前行号；对于部分迭代，这是起始行号"
    )

    stop: int = Field(
        description="迭代终止条件。对于全文迭代，这是终止行号（通常是project.total_lines）"
    )

    step: int = Field(
        default=100,
        description="迭代步长。对于全文迭代，这是每次迭代处理的行数。默认100行"
    )

    summary: str = Field(
        default="",
        description="迭代摘要。每次迭代时模型返回的信息会累积到这里"
    )


class ToolCall(BaseModel):
    """工具调用"""
    name: str = Field(description="工具名称")
    args: dict = Field(default_factory=dict, description="工具参数")
    result: str | None = Field(default=None, description="工具执行结果")
    tool_call_id: str | None = Field(default=None, description="工具调用ID（LangChain 内部使用）")


class ChatMessage(SQLModel, table=True):
    """
    聊天消息模型。

    继承自 ChatMessagePydantic，添加数据库 ID 字段。
    """
    message_id: Optional[str] = Field(
        default=None,
        description="消息唯一标识",
        primary_key=True)
    project_id: str = Field(description="会话唯一标识", index=True)
    index: int = Field(description="消息索引",
                       index=True,
                       default=-1,
                       )
    status: str = Field(
        default="ready",
        description="消息状态：ready（就绪）、error（错误）、success（成功）"
    )
    message_type: str = Field(
        default="normal",
        description="消息类型：normal（普通消息）、iteration（迭代消息）、tool（工具调用）"
    )
    role: str = Field(
        description="消息角色：system、user、assistant"
    )
    context: str = Field(
        default="",
        description="消息正文"
    )
    tools: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
        description="工具调用列表（存储为 JSON，可用 ToolCall.model_validate() 解析）"
    )
    suggests: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
        description="""
        建议列表，例子如下
        # 例子1：提供多个文字建议，如果提供建议，
        # 用户可以选中其中一个建议，用作“下一个消息”（即用户的回复）
        >>> [
                "建议1",
                "建议2",
                "建议3",
        ]
        
        # 例子2，图片建议：如果在任务中，调用了生成图片，而且不止一个，会产生多个图片建议
        # 选择即表示，接受该建议作为图片
        >>> [
            "image:example1.png",
            "image:example2.png",
            "image:example3.png",
            ...
        ]
        """,
    )
    data: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
        description="额外数据（JSON格式，例如ChatIteration）"
    )
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

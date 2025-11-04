"""
聊天事件定义。

用于发布-订阅机制，实现前端被动接收更新。
"""
from typing import Literal, Optional, Union
from pydantic import BaseModel, Field
from api.schemas.desperate.chat import ChatMessage, IterationChatMessage, ToolCall


# ============ 事件基类 ============

class ChatEvent(BaseModel):
    """聊天事件基类"""
    event_type: str = Field(description="事件类型")
    project_id: str = Field(description="项目ID")
    message_id: Optional[str] = Field(default=None, description="消息ID")


# ============ 消息事件 ============

class MessageChunkEvent(ChatEvent):
    """消息文本块事件（流式输出时）"""
    event_type: Literal["message_chunk"] = "message_chunk"
    chunk: str = Field(description="文本块内容")
    message_id: str = Field(description="消息ID")


class MessageCreatedEvent(ChatEvent):
    """消息创建事件"""
    event_type: Literal["message_created"] = "message_created"
    message: ChatMessage | IterationChatMessage = Field(description="消息对象")
    message_id: str = Field(description="消息ID")


class MessageUpdatedEvent(ChatEvent):
    """消息更新事件"""
    event_type: Literal["message_updated"] = "message_updated"
    message: ChatMessage | IterationChatMessage = Field(description="更新后的消息对象")
    message_id: str = Field(description="消息ID")


class MessageCompleteEvent(ChatEvent):
    """消息完成事件"""
    event_type: Literal["message_complete"] = "message_complete"
    message_id: str = Field(description="消息ID")


class MessageFailedEvent(ChatEvent):
    """消息失败事件"""
    event_type: Literal["message_failed"] = "message_failed"
    message_id: str = Field(description="消息ID")
    error: str = Field(description="错误信息")


# ============ 工具调用事件 ============

class ToolCallStartEvent(ChatEvent):
    """工具调用开始事件"""
    event_type: Literal["tool_call_start"] = "tool_call_start"
    message_id: str = Field(description="消息ID")
    tool_name: str = Field(description="工具名称")
    arguments: dict = Field(description="工具参数")


class ToolCallCompleteEvent(ChatEvent):
    """工具调用完成事件"""
    event_type: Literal["tool_call_complete"] = "tool_call_complete"
    message_id: str = Field(description="消息ID")
    tool_call: ToolCall = Field(description="工具调用对象")


# ============ 迭代事件 ============

class IterationStartEvent(ChatEvent):
    """迭代开始事件"""
    event_type: Literal["iteration_start"] = "iteration_start"
    iteration_message: IterationChatMessage = Field(description="迭代消息对象")
    message_id: str = Field(description="消息ID")


class IterationUpdateEvent(ChatEvent):
    """迭代更新事件"""
    event_type: Literal["iteration_update"] = "iteration_update"
    iteration_message: IterationChatMessage = Field(description="更新后的迭代消息对象")
    message_id: str = Field(description="消息ID")


class IterationCompleteEvent(ChatEvent):
    """迭代完成事件"""
    event_type: Literal["iteration_complete"] = "iteration_complete"
    iteration_message: IterationChatMessage = Field(description="完成后的迭代消息对象")
    message_id: str = Field(description="消息ID")


# ============ 事件联合类型 ============

ChatEventType = Union[
    MessageChunkEvent,
    MessageCreatedEvent,
    MessageUpdatedEvent,
    MessageCompleteEvent,
    MessageFailedEvent,
    ToolCallStartEvent,
    ToolCallCompleteEvent,
    IterationStartEvent,
    IterationUpdateEvent,
    IterationCompleteEvent,
]


"""
聊天消息管理的路由。

提供聊天消息的 CRUD 操作：创建、查询、更新、删除。
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from loguru import logger

from api.schemas.chat import ChatMessage
from api.services.db import HistoryService
from api.services.db.base import normalize_project_id

router = APIRouter(
    prefix="/history",
    tags=["聊天历史"],
    responses={404: {"description": "资源不存在"}},
)


# ==================== 聊天消息操作 ====================

@router.post("/message", summary="创建聊天消息")
def create_chat_message(
        message_type: str,
        role: str,
        context: str,
        status: str = "ready",
        data: dict | None = None,
        index: int = -1,
        project_id: str | None = None,
) -> dict:
    """
    创建聊天消息。

    Args:
        message_type: 消息类型 （normal、iteration、tool）
        role: 消息角色 （system、user、assistant）
        context: 消息正文
        status: 消息状态 （ready、error、success）
        data: 额外数据（可选）
        index: 消息索引，默认值为-1（自动计算）
        project_id: 项目唯一标识（None 表示默认工作空间）
    
    Returns:
        创建的消息ID（message_id）
    """
    project_id = normalize_project_id(project_id)
    if index < 0:
        index = HistoryService.count(project_id) + index + 1
    if data is None:
        data = dict()

    # 创建消息（ID 会自动生成）
    message = ChatMessage(
        project_id=project_id,
        index=index,
        status=status,
        message_type=message_type,
        role=role,
        context=context,
        data=data,
    )
    message = HistoryService.create(message)
    logger.info(f"创建聊天消息: {message.message_id} (project: {project_id}, index: {index})")
    return {"message_id": message.message_id}


# ==================== 查询操作（固定路径必须放在动态路径之前） ====================

@router.get("/by_index", response_model=ChatMessage, summary="根据索引获取聊天消息")
def get_chat_message_by_index(
    project_id: Optional[str] = None,
    index: int = 0
) -> ChatMessage:
    """
    根据项目ID和索引获取聊天消息。
    
    Args:
        project_id: 项目ID
        index: 消息索引（负数表示从末尾倒数，如-1表示最后一条）
    
    Returns:
        聊天消息对象
    
    Raises:
        404: 消息不存在
    """
    project_id = normalize_project_id(project_id)
    # 处理负数索引（从末尾倒数）
    if index < 0:
        count = HistoryService.count(project_id)
        index = count + index
    
    message = HistoryService.get_by_index(project_id, index)
    if not message:
        raise HTTPException(
            status_code=404, 
            detail=f"聊天消息不存在: session={project_id}, index={index}"
        )
    
    return message


@router.get("/all", response_model=List[ChatMessage], summary="列出项目的所有消息")
def get_all_chat_messages(
    project_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0
) -> List[ChatMessage]:
    """
    根据项目ID获取聊天消息列表，支持分页。
    
    Args:
        project_id: 项目ID（查询参数）
        limit: 返回数量限制（可选，None表示无限制）
        offset: 偏移量（默认0）
    
    Returns:
        聊天消息列表（按索引排序）
    """
    project_id = normalize_project_id(project_id)
    messages = HistoryService.get_all(project_id)
    messages_list = list(messages)
    
    # 应用分页
    if limit is not None:
        return messages_list[offset:offset + limit]
    return messages_list[offset:]


@router.get("/ids", summary="列出项目的所有消息ID")
def list_chat_message_ids(
    project_id: Optional[str] = None
) -> List[str]:
    """
    根据项目ID获取聊天消息ID列表。
    
    Args:
        project_id: 项目ID
    
    Returns:
        消息ID列表
    """
    project_id = normalize_project_id(project_id)
    message_ids = HistoryService.list_ids(project_id)
    return message_ids


@router.get("/count", summary="获取项目的消息数量")
def get_chat_message_count(
    project_id: Optional[str] = None
) -> int:
    """
    根据项目ID获取聊天消息数量。
    
    Args:
        project_id: 项目ID
    
    Returns:
        消息数量
    """
    project_id = normalize_project_id(project_id)
    count = HistoryService.count(project_id)
    return count


# ==================== 基于ID的CRUD操作 ====================
# 注意：ID参数通过路径参数传递，权限验证在服务层进行

@router.get("/{message_id}", response_model=ChatMessage, summary="获取聊天消息")
def get_chat_message(message_id: str) -> ChatMessage:
    """
    根据消息ID获取聊天消息。
    
    Args:
        message_id: 消息ID（路径参数）
    
    Returns:
        聊天消息对象
    
    Raises:
        404: 消息不存在
    """
    message = HistoryService.get(message_id)
    if not message:
        raise HTTPException(status_code=404, detail=f"聊天消息不存在: {message_id}")
    
    return message


# ==================== 更新和删除操作 ====================
# 注意：固定路径必须放在动态路径之前，避免路由冲突

@router.delete("/clear", summary="清空项目的所有消息")
def clear_chat_messages(
    project_id: Optional[str] = None
) -> dict:
    """
    根据项目ID删除所有聊天消息。
    
    Args:
        project_id: 项目ID
    
    Returns:
        删除结果
    
    警告:
        - 此操作不可恢复
        - 会删除该项目的所有聊天消息
    """
    project_id = normalize_project_id(project_id)
    count = HistoryService.count(project_id)
    HistoryService.clear(project_id)
    logger.info(f"清空项目的所有消息: project={project_id}, 删除了 {count} 条")
    return {
        "message": "项目的所有消息已清空",
        "project_id": project_id,
        "deleted_count": count
    }


@router.delete("/by_index", summary="根据索引删除聊天消息")
def remove_chat_message_by_index(
    project_id: Optional[str] = None,
    index: int = 0
) -> dict:
    """
    根据项目ID和索引删除聊天消息。
    
    Args:
        project_id: 项目ID
        index: 消息索引（负数表示从末尾倒数，如-1表示最后一条）
    
    Returns:
        删除结果
    
    Raises:
        404: 消息不存在
    """
    project_id = normalize_project_id(project_id)
    # 处理负数索引（从末尾倒数）
    actual_index = index
    if index < 0:
        count = HistoryService.count(project_id)
        actual_index = count + index
    
    # 先获取消息（用于返回 message_id）
    message = HistoryService.get_by_index(project_id, actual_index)
    if not message:
        raise HTTPException(
            status_code=404,
            detail=f"聊天消息不存在: session={project_id}, index={index}"
        )
    
    # 删除消息（remove_by_index 内部也会处理负数索引，但我们已经处理了，直接传实际索引）
    HistoryService.remove_by_index(project_id, actual_index)
    logger.info(f"根据索引删除聊天消息: session={project_id}, index={index} (actual={actual_index})")
    return {
        "message": "聊天消息删除成功",
        "project_id": project_id,
        "index": index,
        "message_id": message.message_id
    }


@router.put("/{message_id}", response_model=ChatMessage, summary="更新聊天消息")
def update_chat_message(
    message_id: str,
    status: Optional[str] = None,
    message_type: Optional[str] = None,
    role: Optional[str] = None,
    context: Optional[str] = None,
    data: Optional[dict] = None,
    index: Optional[int] = None
) -> ChatMessage:
    """
    更新聊天消息。
    
    Args:
        message_id: 消息ID（路径参数）
        status: 消息状态（可选）
        message_type: 消息类型（可选）
        role: 消息角色（可选）
        context: 消息正文（可选）
        data: 额外数据（可选）
        index: 消息索引（可选）
    
    Returns:
        更新后的聊天消息对象
    
    Raises:
        404: 消息不存在
    """
    # 检查消息是否存在
    message = HistoryService.get(message_id)
    if not message:
        raise HTTPException(status_code=404, detail=f"聊天消息不存在: {message_id}")
    
    # 更新字段
    if status is not None:
        message.status = status
    if message_type is not None:
        message.message_type = message_type
    if role is not None:
        message.role = role
    if context is not None:
        message.context = context
    if data is not None:
        message.data = data
    if index is not None:
        message.index = index
    
    # 保存更新
    updated_message = HistoryService.update(message)
    logger.info(f"更新聊天消息: {message_id} (project: {updated_message.project_id})")
    return updated_message


@router.delete("/{message_id}", summary="删除聊天消息")
def remove_chat_message(message_id: str) -> dict:
    """
    根据消息ID删除聊天消息。
    
    Args:
        message_id: 消息ID（路径参数）
    
    Returns:
        删除结果
    """
    # 检查消息是否存在
    message = HistoryService.get(message_id)
    if not message:
        # 消息不存在，但返回成功而不是404错误
        # 这可能是临时项目已被清理的情况
        logger.debug(f"尝试删除不存在的聊天消息: {message_id}")
        return {
            "message_id": message_id,
            "message": "消息不存在或已被删除",
            "deleted": False
        }
    
    # 删除消息
    HistoryService.remove(message_id)
    logger.info(f"删除聊天消息: {message_id} (project: {message.project_id})")
    return {
        "message_id": message_id,
        "message": "消息删除成功",
        "deleted": True,
        "project_id": message.project_id
    }

"""
记忆管理的路由。

存储和检索项目上下文信息：背景设定、世界观、用户偏好、重要情节等。
为 AI 提供长期记忆能力。

简化设计：
- 所有记忆使用 MemoryEntry 键值对存储
- 键名定义在 constants.memory 中：
  - novel_memory_description: 与小说内容相关（世界观、情节等）
  - user_memory_description: 与用户偏好相关（艺术风格、标签偏好等）
  - memory_description: 合并了上述两个字典
- 所有 value 统一使用纯文本字符串（列表类型用逗号分隔）
- 支持灵活的查询和聚合
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException
from loguru import logger

from api.schemas.memory import MemoryEntry, MemoryCreateRequest, MemoryUpdateRequest
from api.constants.memory import memory_description
from api.services.db import MemoryService

router = APIRouter(
    prefix="/memory",
    tags=["记忆系统"],
    responses={404: {"description": "记忆不存在"}},
)


# ==================== 记忆条目操作 ====================

@router.post("/create", summary="创建记忆条目")
async def create_memory(
    request: MemoryCreateRequest
) -> dict:
    """
    创建新的记忆条目。
    
    Args:
        request: 创建记忆的请求体，包含 project_id, key, value, description
    
    Returns:
        创建的记忆条目ID（memory_id）
    
    实现要点：
    - 生成唯一 memory_id
    - 自动记录时间戳
    - 如果 description 为空，自动从 constants.memory.memory_description 获取
    """
    # 生成唯一记忆ID
    memory_id = str(uuid.uuid4())
    
    # 如果没有提供描述，从预定义字典获取
    description = request.description
    if description is None:
        description = memory_description.get(request.key, "")
    
    # 创建记忆条目对象
    entry = MemoryEntry(
        memory_id=memory_id,
        project_id=request.project_id,
        key=request.key,
        value=request.value,
        description=description,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    # 保存到数据库
    MemoryService.create(entry)
    logger.info(f"创建记忆条目: {request.key} (project: {request.project_id})")
    
    return {"memory_id": memory_id}


@router.get("/all", response_model=List[MemoryEntry], summary="列出记忆")
async def get_all_memories(
    project_id: str,
    key: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[MemoryEntry]:
    """
    列出项目的记忆条目，支持分页。
    
    Args:
        project_id: 项目ID（查询参数）
        key: 按键名过滤（可选，精确匹配）
        limit: 返回数量限制（默认100，最大1000）
        offset: 偏移量（默认0）
    
    Returns:
        符合条件的记忆列表
    """
    # 获取项目的所有记忆条目
    entries = MemoryService.get_all(project_id, limit=limit + offset)
    
    # 如果提供了键名过滤，应用过滤
    if key:
        entries = [e for e in entries if e.key == key]
    
    # 应用偏移量（简单的内存分页）
    return entries[offset:offset + limit]


# ==================== 预定义键查询 ====================
# 注意：这些路由必须在 /{memory_id} 之前定义，避免路径冲突

@router.get("/key-description", summary="获取键的描述（建议）")
async def get_key_description(
    key: str
) -> Dict[str, str]:
    """
    获取键的描述（如果在预定义列表中）。
    
    Args:
        key: 记忆键名（查询参数）
    
    Returns:
        包含键和描述的字典 {"key": "...", "description": "..."}
        如果键不在预定义列表中，返回提示信息
    
    实现要点：
    - 从 constants.memory.memory_description 查找
    - 如果键不存在，返回提示而非报错（允许自定义 key）
    """
    if key not in memory_description:
        return {
            "key": key,
            "description": f"'{key}' 不在预定义列表中，但可以作为自定义键使用。建议确保键名具体明确。"
        }
    
    return {
        "key": key,
        "description": memory_description[key]
    }


@router.get("/key-descriptions", summary="获取所有预定义键和描述")
async def get_all_key_descriptions() -> Dict[str, str]:
    """
    获取所有预定义的记忆键和描述。
    
    Returns:
        所有预定义的键值对字典
    
    实现要点：
    - 返回 constants.memory.memory_description 完整字典
    - 包含 novel_memory_description 和 user_memory_description 的所有键
    
    示例返回：
    {
        "作品类型": "小说的类型/题材，如：修仙、都市、科幻...",
        "主题": "作品的核心主题和表达的思想...",
        "艺术风格": "用户偏好的画面风格",
        ...
    }
    """
    return memory_description


# ==================== 批量操作 ====================
# 注意：这些路由必须在 /{memory_id} 之前定义，避免路径冲突

@router.delete("/clear", summary="清空项目的所有记忆")
async def clear_memories(
    project_id: str
) -> dict:
    """
    清空指定项目的所有记忆条目。
    
    Args:
        project_id: 项目ID（查询参数）
    
    Returns:
        删除结果（包含删除的记录数）
    
    警告：
    - 此操作不可恢复
    - 会删除该项目的所有记忆条目
    """
    count = MemoryService.clear(project_id)
    logger.info(f"清空项目 {project_id} 的所有记忆: {count} 条")
    return {
        "message": f"已清空项目的所有记忆条目",
        "project_id": project_id,
        "deleted_count": count
    }


# ==================== 基于ID的CRUD操作 ====================
# 注意：ID参数通过路径参数传递，权限验证在服务层进行
# 注意：这些路由必须在具体路径（如 /clear）之后定义，避免路径冲突

@router.get("/{memory_id}", response_model=MemoryEntry, summary="获取记忆条目")
async def get_memory(memory_id: str) -> MemoryEntry:
    """
    获取指定记忆条目。
    
    Args:
        memory_id: 记忆ID（路径参数）
    
    Returns:
        记忆条目
    
    Raises:
        404: 记忆条目不存在
    """
    entry = MemoryService.get(memory_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"记忆条目不存在: {memory_id}")
    
    return entry


@router.put("/{memory_id}", response_model=MemoryEntry, summary="更新记忆")
async def update_memory(
    memory_id: str,
    request: MemoryUpdateRequest
) -> MemoryEntry:
    """
    更新记忆条目。
    
    Args:
        memory_id: 记忆ID（路径参数）
        request: 更新记忆的请求体，包含 key, value, description（都是可选的）
    
    Returns:
        更新后的记忆条目
    
    Raises:
        404: 记忆条目不存在
    """
    # 检查记忆是否存在
    entry = MemoryService.get(memory_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"记忆条目不存在: {memory_id}")
    
    # 构建更新字典
    update_data = {"updated_at": datetime.now()}
    if request.key is not None:
        update_data["key"] = request.key
    if request.value is not None:
        update_data["value"] = request.value
    if request.description is not None:
        update_data["description"] = request.description
    
    # 更新记忆
    updated_entry = MemoryService.update(memory_id, **update_data)
    if not updated_entry:
        raise HTTPException(status_code=404, detail=f"记忆条目不存在: {memory_id}")
    
    logger.info(f"更新记忆条目: {memory_id} (project: {updated_entry.project_id})")
    return updated_entry


@router.delete("/{memory_id}", summary="删除记忆")
async def delete_memory(memory_id: str) -> dict:
    """
    删除记忆条目。
    
    Args:
        memory_id: 记忆ID（路径参数）
    
    Returns:
        删除的记忆ID
    
    Raises:
        404: 记忆条目不存在
    """
    # 检查记忆是否存在
    entry = MemoryService.get(memory_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"记忆条目不存在: {memory_id}")
    
    # 删除记忆
    success = MemoryService.remove(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"记忆条目不存在: {memory_id}")
    
    logger.info(f"删除记忆条目: {memory_id} (project: {entry.project_id})")
    return {"memory_id": memory_id}


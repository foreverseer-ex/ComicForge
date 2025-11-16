"""
摘要管理的路由。

提供章节摘要和全文摘要的增删改查操作。
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Body
from loguru import logger
from pydantic import BaseModel

from api.schemas.memory import ChapterSummary
from api.services.db import SummaryService
from api.services.db.base import normalize_project_id

router = APIRouter(
    prefix="/summary",
    tags=["摘要管理"],
    responses={404: {"description": "摘要不存在"}},
)


# ==================== 摘要基本操作 ====================

@router.post("/create", summary="创建摘要")
async def create_summary(
    project_id: Optional[str] = None,
    chapter_index: int = Body(..., ge=-1, description="章节索引（-1 表示全文摘要，>=0 表示章节索引）"),
    title: str = Body(..., description="摘要标题"),
    summary: Optional[str] = Body(None, description="摘要内容"),
    start_line: int = Body(0, ge=0, description="起始行号"),
    end_line: int = Body(0, ge=0, description="结束行号")
) -> int:
    """
    创建新摘要。
    
    Args:
        project_id: 项目ID（查询参数，None 表示默认工作空间）
        chapter_index: 章节索引（-1 表示全文摘要，>=0 表示章节索引）
        title: 摘要标题
        summary: 摘要内容（可选）
        start_line: 起始行号
        end_line: 结束行号
    
    Returns:
        创建的摘要 ID
    """
    project_id = normalize_project_id(project_id)
    
    summary_obj = ChapterSummary(
        project_id=project_id,
        chapter_index=chapter_index,
        title=title,
        summary=summary,
        start_line=start_line,
        end_line=end_line
    )
    
    created = SummaryService.create(summary_obj)
    logger.info(f"创建摘要: project={project_id}, chapter_index={chapter_index}, id={created.id}")
    
    return created.id if created.id else 0


@router.get("/all", response_model=List[ChapterSummary], summary="列出所有摘要")
async def get_all_summaries(
    project_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0
) -> List[ChapterSummary]:
    """
    列出项目的所有摘要，支持分页。
    
    Args:
        project_id: 项目ID（查询参数，None 表示默认工作空间）
        limit: 返回数量限制（None 表示无限制）
        offset: 跳过的记录数
    
    Returns:
        摘要列表
    """
    project_id = normalize_project_id(project_id)
    return SummaryService.get_all(project_id, limit=limit, offset=offset)


@router.get("/full", response_model=Optional[ChapterSummary], summary="获取全文摘要")
async def get_full_summary(
    project_id: Optional[str] = None
) -> Optional[ChapterSummary]:
    """
    获取项目的全文摘要（chapter_index = -1）。
    
    Args:
        project_id: 项目ID（查询参数，None 表示默认工作空间）
    
    Returns:
        全文摘要对象，如果不存在则返回 None
    """
    project_id = normalize_project_id(project_id)
    return SummaryService.get(project_id, -1)


@router.get("/chapter/{chapter_index}", response_model=Optional[ChapterSummary], summary="获取章节摘要")
async def get_chapter_summary(
    project_id: Optional[str] = None,
    chapter_index: int = -1
) -> Optional[ChapterSummary]:
    """
    获取指定章节的摘要。
    
    Args:
        project_id: 项目ID（查询参数，None 表示默认工作空间）
        chapter_index: 章节索引（>=0 表示章节索引，-1 表示全文摘要）
    
    Returns:
        章节摘要对象，如果不存在则返回 None
    """
    project_id = normalize_project_id(project_id)
    if chapter_index < -1:
        raise HTTPException(status_code=400, detail="chapter_index 必须 >= -1")
    
    return SummaryService.get(project_id, chapter_index)


# ==================== 摘要更新和删除 ====================

class SummaryUpdateRequest(BaseModel):
    """摘要更新请求"""
    title: Optional[str] = None
    summary: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None


@router.put("/{chapter_index}", response_model=ChapterSummary, summary="更新摘要")
async def update_summary(
    project_id: Optional[str] = None,
    chapter_index: int = -1,
    request: SummaryUpdateRequest = Body(...)
) -> ChapterSummary:
    """
    更新摘要信息。
    
    Args:
        project_id: 项目ID（查询参数，None 表示默认工作空间）
        chapter_index: 章节索引（-1 表示全文摘要，>=0 表示章节索引）
        request: 更新请求体
    
    Returns:
        更新后的摘要对象
    
    Raises:
        404: 摘要不存在
    """
    project_id = normalize_project_id(project_id)
    if chapter_index < -1:
        raise HTTPException(status_code=400, detail="chapter_index 必须 >= -1")
    
    update_data = {}
    if request.title is not None:
        update_data["title"] = request.title
    if request.summary is not None:
        update_data["summary"] = request.summary
    if request.start_line is not None:
        update_data["start_line"] = request.start_line
    if request.end_line is not None:
        update_data["end_line"] = request.end_line
    
    updated = SummaryService.update(project_id, chapter_index, **update_data)
    if not updated:
        raise HTTPException(status_code=404, detail=f"摘要不存在: project_id={project_id}, chapter_index={chapter_index}")
    
    return updated


@router.delete("/{chapter_index}", summary="删除摘要")
async def delete_summary(
    project_id: Optional[str] = None,
    chapter_index: int = -1
) -> dict:
    """
    删除摘要。
    
    Args:
        project_id: 项目ID（查询参数，None 表示默认工作空间）
        chapter_index: 章节索引（-1 表示全文摘要，>=0 表示章节索引）
    
    Returns:
        操作结果
    
    Raises:
        404: 摘要不存在
    """
    project_id = normalize_project_id(project_id)
    if chapter_index < -1:
        raise HTTPException(status_code=400, detail="chapter_index 必须 >= -1")
    
    success = SummaryService.remove(project_id, chapter_index)
    if not success:
        raise HTTPException(status_code=404, detail=f"摘要不存在: project_id={project_id}, chapter_index={chapter_index}")
    
    logger.info(f"删除摘要: project_id={project_id}, chapter_index={chapter_index}")
    return {
        "success": True,
        "project_id": project_id,
        "chapter_index": chapter_index,
        "message": "摘要删除成功"
    }


@router.delete("/clear/all", summary="清空所有摘要")
async def clear_all_summaries(
    project_id: Optional[str] = None
) -> dict:
    """
    删除项目的所有摘要。
    
    Args:
        project_id: 项目ID（查询参数，None 表示默认工作空间）
    
    Returns:
        操作结果（包含删除的记录数）
    """
    project_id = normalize_project_id(project_id)
    count = SummaryService.clear(project_id)
    
    logger.info(f"清空所有摘要: project_id={project_id}, 共删除 {count} 条")
    return {
        "success": True,
        "project_id": project_id,
        "deleted_count": count,
        "message": f"已删除 {count} 条摘要"
    }


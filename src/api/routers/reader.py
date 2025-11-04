"""
阅读器的路由。

简化设计：按行读取小说，每行对应一个段落/一张图片。
基于 NovelContentService 实现。
"""
from typing import List
from fastapi import APIRouter, HTTPException
from loguru import logger

from api.schemas.novel import NovelContent
from api.schemas.memory import ChapterSummary
from api.services.db import NovelContentService
from api.services.db.summary_service import SummaryService

router = APIRouter(
    prefix="/reader",
    tags=["阅读器"],
    responses={404: {"description": "内容不存在"}},
)


# ==================== 行读取 ====================

@router.get("/line/{project_id}/{chapter}/{line}", summary="读取指定行", response_model=NovelContent)
async def get_line(
    project_id: str,
    chapter: int,
    line: int
) -> NovelContent:
    """
    读取指定行的内容。
    
    Args:
        project_id: 项目ID
        chapter: 章节号（从0开始）
        line: 行号（从0开始）
    
    Returns:
        行内容对象
    
    Raises:
        HTTPException: 内容不存在时返回 404
    """
    content = NovelContentService.get_by_line(project_id, chapter, line)
    if not content:
        raise HTTPException(
            status_code=404,
            detail=f"行内容不存在: chapter={chapter}, line={line}"
        )
    return content


@router.get("/lines/{project_id}/{chapter}", summary="读取章节的所有行", response_model=List[NovelContent])
async def get_chapter_lines(
    project_id: str,
    chapter: int
) -> List[NovelContent]:
    """
    读取指定章节的所有行。
    
    Args:
        project_id: 项目ID
        chapter: 章节号
    
    Returns:
        章节所有行的内容列表
    """
    return NovelContentService.get_by_chapter(project_id, chapter)


@router.get("/lines/range/{project_id}", summary="批量读取行范围的内容", response_model=List[NovelContent])
async def get_lines_range(
    project_id: str,
    start_line: int,
    end_line: int,
    chapter: int | None = None
) -> List[NovelContent]:
    """
    批量读取指定行范围的内容。
    
    可以读取指定章节的行范围，也可以跨章节读取（不指定chapter时）。
    
    Args:
        project_id: 项目ID
        start_line: 起始行号（包含，从0开始）
        end_line: 结束行号（包含）
        chapter: 章节号（可选，不指定则跨章节查询）
    
    Returns:
        行内容列表（按章节和行号排序）
    
    Examples:
        # 读取第0章的第0-9行
        get_lines_range(project_id="xxx", start_line=0, end_line=9, chapter=0)
        
        # 跨章节读取第0-99行（所有章节）
        get_lines_range(project_id="xxx", start_line=0, end_line=99)
    """
    return NovelContentService.get_line_range(project_id, start_line, end_line, chapter=chapter)


# ==================== 章节管理 ====================

@router.get("/chapters/{project_id}", summary="获取所有章节", response_model=List[ChapterSummary])
async def get_chapters(project_id: str) -> List[ChapterSummary]:
    """
    获取项目的所有章节摘要列表。
    
    Args:
        project_id: 项目ID
    
    Returns:
        章节摘要列表
    """
    return SummaryService.list(project_id)


@router.get("/chapter/{project_id}/{chapter_index}", summary="获取章节详情", response_model=ChapterSummary)
async def get_chapter(
    project_id: str,
    chapter_index: int
) -> ChapterSummary:
    """
    获取指定章节的详细信息。
    
    Args:
        project_id: 项目ID
        chapter_index: 章节索引
    
    Returns:
        章节摘要
    
    Raises:
        HTTPException: 章节不存在时返回 404
    """
    summary = SummaryService.get(chapter_index)
    if not summary or summary.project_id != project_id:
        raise HTTPException(
            status_code=404,
            detail=f"章节不存在: chapter_index={chapter_index}"
        )
    return summary


@router.get("/chapter/{project_id}/{chapter_index}/summary", summary="获取章节梗概")
async def get_chapter_summary(
    project_id: str,
    chapter_index: int
) -> dict:
    """
    获取指定章节的故事梗概（AI生成）。
    
    Args:
        project_id: 项目ID
        chapter_index: 章节索引
    
    Returns:
        包含梗概的字典，如果未生成则返回 None
    """
    summary = SummaryService.get(chapter_index)
    if not summary or summary.project_id != project_id:
        raise HTTPException(
            status_code=404,
            detail=f"章节不存在: chapter_index={chapter_index}"
        )
    return {
        "project_id": project_id,
        "chapter_index": chapter_index,
        "summary": summary.summary
    }


@router.put("/chapter/{project_id}/{chapter_index}/summary", summary="设置章节梗概", response_model=ChapterSummary)
async def put_chapter_summary(
    project_id: str,
    chapter_index: int,
    summary_text: str
) -> ChapterSummary:
    """
    设置/更新章节的故事梗概。
    
    Args:
        project_id: 项目ID
        chapter_index: 章节索引
        summary_text: 故事梗概内容
    
    Returns:
        更新后的章节摘要
    
    Raises:
        HTTPException: 章节不存在时返回 404
    """
    # 更新摘要
    updated_summary = SummaryService.update(
        chapter_index=chapter_index,
        summary=summary_text
    )
    
    if not updated_summary or updated_summary.project_id != project_id:
        raise HTTPException(
            status_code=404,
            detail=f"章节不存在: chapter_index={chapter_index}"
        )
    
    logger.info(f"更新章节梗概: session={project_id}, chapter={chapter_index}")
    return updated_summary


# ==================== 统计信息 ====================

@router.get("/stats/{project_id}", summary="获取阅读统计信息")
async def get_stats(project_id: str) -> dict:
    """
    获取会话的阅读统计信息。
    
    Args:
        project_id: 项目ID
    
    Returns:
        统计信息字典，包含总行数、章节数等
    """
    total_lines = NovelContentService.count_by_session(project_id)
    total_chapters = NovelContentService.count_chapters(project_id)
    
    return {
        "project_id": project_id,
        "total_lines": total_lines,
        "total_chapters": total_chapters
    }

"""
小说内容管理的路由。

提供对小说文本内容的 CRUD 操作，按章节和行号组织。
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from loguru import logger

from api.schemas.novel import NovelContent
from api.services.db import NovelContentService

router = APIRouter(
    prefix="/novel",
    tags=["小说内容"],
    responses={404: {"description": "内容不存在"}},
)


# ==================== 小说内容操作 ====================

@router.post("/content", summary="创建小说内容")
async def create_content(
    project_id: str,
    chapter: int,
    line: int,
    content: str
) -> dict:
    """
    创建新的小说内容条目。
    
    Args:
        project_id: 项目ID
        chapter: 章节号（从0开始）
        line: 行号（从0开始）
        content: 行内容
    
    Returns:
        创建的小说内容ID（id）
    """
    novel_content = NovelContent(
        project_id=project_id,
        chapter=chapter,
        line=line,
        content=content
    )
    created = NovelContentService.create(novel_content)
    logger.info(f"创建小说内容: project={project_id}, chapter={chapter}, line={line}")
    return {"id": created.id}


@router.post("/content/batch", summary="批量创建小说内容", response_model=List[NovelContent])
async def batch_create_content(
    contents: List[dict]
) -> List[NovelContent]:
    """
    批量创建小说内容。
    
    Args:
        contents: 内容列表，每项包含 project_id, chapter, line, content
    
    Returns:
        创建的小说内容列表
    """
    novel_contents = [
        NovelContent(
            project_id=c["project_id"],
            chapter=c["chapter"],
            line=c["line"],
            content=c["content"]
        )
        for c in contents
    ]
    created = NovelContentService.batch_create(novel_contents)
    logger.info(f"批量创建小说内容: {len(created)} 条")
    return created


@router.get("/content/project", summary="获取项目的所有内容", response_model=List[NovelContent])
async def get_project_content(
    project_id: str,
    limit: Optional[int] = None
) -> List[NovelContent]:
    """
    获取项目的所有小说内容。
    
    Args:
        project_id: 项目ID（查询参数）
        limit: 返回数量限制（查询参数）
    
    Returns:
        小说内容列表
    """
    return NovelContentService.get_by_session(project_id, limit=limit)


@router.get("/content/chapter", summary="获取指定章节的内容", response_model=List[NovelContent])
async def get_chapter_content(
    project_id: str,
    chapter: int
) -> List[NovelContent]:
    """
    获取指定章节的所有内容。
    
    Args:
        project_id: 项目ID（查询参数）
        chapter: 章节号（查询参数）
    
    Returns:
        章节内容列表
    """
    return NovelContentService.get_by_chapter(project_id, chapter)


@router.get("/content/line", summary="获取指定行的内容", response_model=NovelContent)
async def get_line_content(
    project_id: str,
    chapter: int,
    line: int
) -> NovelContent:
    """
    获取指定行的内容。
    
    Args:
        project_id: 项目ID（查询参数）
        chapter: 章节号（查询参数）
        line: 行号（查询参数）
    
    Returns:
        行内容
    
    Raises:
        HTTPException: 内容不存在时返回 404
    """
    content = NovelContentService.get_by_line(project_id, chapter, line)
    if not content:
        raise HTTPException(status_code=404, detail=f"内容不存在: chapter={chapter}, line={line}")
    return content


@router.get("/content/range", summary="获取行范围的内容", response_model=List[NovelContent])
async def get_line_range_content(
    project_id: str,
    chapter: int,
    start_line: int,
    end_line: int
) -> List[NovelContent]:
    """
    获取指定行范围的内容。
    
    Args:
        project_id: 项目ID（查询参数）
        chapter: 章节号（查询参数）
        start_line: 起始行号（包含，查询参数）
        end_line: 结束行号（包含，查询参数）
    
    Returns:
        行内容列表
    """
    return NovelContentService.get_line_range(project_id, start_line, end_line, chapter=chapter)


@router.get("/content/count", summary="获取项目的内容总数")
async def count_project_content(project_id: str) -> dict:
    """
    获取项目的小说内容总数。
    
    Args:
        project_id: 项目ID（查询参数）
    
    Returns:
        包含总数的字典
    """
    count = NovelContentService.count_by_session(project_id)
    return {"project_id": project_id, "count": count}


@router.get("/content/chapters/count", summary="获取项目的章节总数")
async def count_project_chapters(project_id: str) -> dict:
    """
    获取项目的章节总数。
    
    Args:
        project_id: 项目ID（查询参数）
    
    Returns:
        包含章节数的字典
    """
    count = NovelContentService.count_chapters(project_id)
    return {"project_id": project_id, "chapters": count}


@router.delete("/content/project", summary="删除项目的所有内容")
async def delete_project_content(project_id: str) -> dict:
    """
    删除项目的所有小说内容。
    
    Args:
        project_id: 项目ID（查询参数）
    
    Returns:
        删除结果
    """
    count = NovelContentService.delete_by_session(project_id)
    logger.info(f"删除项目小说内容: {project_id}, 共 {count} 条")
    return {"message": "项目内容删除成功", "project_id": project_id, "deleted_count": count}


@router.delete("/content/chapter", summary="删除指定章节的内容")
async def delete_chapter_content(project_id: str, chapter: int) -> dict:
    """
    删除指定章节的所有内容。
    
    Args:
        project_id: 项目ID（查询参数）
        chapter: 章节号（查询参数）
    
    Returns:
        删除结果
    """
    count = NovelContentService.delete_by_chapter(project_id, chapter)
    logger.info(f"删除章节内容: project={project_id}, chapter={chapter}, 共 {count} 条")
    return {"message": "章节内容删除成功", "project_id": project_id, "chapter": chapter, "deleted_count": count}


"""
小说内容管理的路由。

提供对小说文本内容的 CRUD 操作，按章节和行号组织。
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from api.schemas.novel import NovelContent
from api.services.db import NovelContentService

router = APIRouter(
    prefix="/novel",
    tags=["小说内容"],
    responses={404: {"description": "内容不存在"}},
)


# ==================== 请求模型 ====================

class UpdateContentRequest(BaseModel):
    """更新内容的请求模型"""
    content: str


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


@router.put("/content", summary="更新单行内容", response_model=NovelContent)
async def update_content(
    project_id: str,
    chapter: int,
    line: int,
    request: UpdateContentRequest
) -> NovelContent:
    """
    更新指定行的内容。
    
    Args:
        project_id: 项目ID（查询参数）
        chapter: 章节号（查询参数）
        line: 行号（查询参数）
        request: 更新请求体，包含新的内容
    
    Returns:
        更新后的行内容
    
    Raises:
        HTTPException: 内容不存在时返回 404
    """
    updated = NovelContentService.update(project_id, chapter, line, request.content)
    if not updated:
        raise HTTPException(
            status_code=404,
            detail=f"内容不存在: chapter={chapter}, line={line}"
        )
    logger.info(f"更新小说内容: project={project_id}, chapter={chapter}, line={line}")
    return updated


@router.delete("/content", summary="删除单行内容")
async def delete_content(
    project_id: str,
    chapter: int,
    line: int
) -> dict:
    """
    删除指定行的内容。
    
    Args:
        project_id: 项目ID（查询参数）
        chapter: 章节号（查询参数）
        line: 行号（查询参数）
    
    Returns:
        删除结果
    """
    success = NovelContentService.delete_single(project_id, chapter, line)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"内容不存在: chapter={chapter}, line={line}"
        )
    logger.info(f"删除小说内容: project={project_id}, chapter={chapter}, line={line}")
    return {
        "message": "内容删除成功",
        "project_id": project_id,
        "chapter": chapter,
        "line": line
    }


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


@router.post("/content/insert", summary="插入内容并重新编号")
async def insert_content(
    project_id: str,
    chapter: int,
    line: int,
    content: str
) -> dict:
    """
    在指定位置插入内容，并自动重新编号后续行。
    
    Args:
        project_id: 项目ID（查询参数）
        chapter: 章节号（查询参数）
        line: 插入位置的行号（新内容将插入在这个位置，原位置及后续行号+1）
        content: 要插入的内容
    
    Returns:
        插入结果
    """
    # 先重新编号：将line及之后的所有行的行号+1
    NovelContentService.shift_lines(project_id, chapter, line, 1)
    
    # 创建新内容
    novel_content = NovelContent(
        project_id=project_id,
        chapter=chapter,
        line=line,
        content=content
    )
    created = NovelContentService.create(novel_content)
    logger.info(f"插入小说内容: project={project_id}, chapter={chapter}, line={line}")
    return {"id": created.id}


@router.post("/content/insert/batch", summary="批量插入内容并重新编号")
async def batch_insert_content(
    project_id: str,
    chapter: int,
    line: int,
    contents: List[str]
) -> dict:
    """
    在指定位置批量插入内容，并自动重新编号后续行。
    
    Args:
        project_id: 项目ID（查询参数）
        chapter: 章节号（查询参数）
        line: 插入位置的行号（新内容将插入在这个位置，原位置及后续行号+N，N为插入的段落数）
        contents: 要插入的内容列表（每个元素是一个段落）
    
    Returns:
        插入结果
    """
    if not contents:
        return {"message": "没有内容需要插入", "count": 0}
    
    # 先重新编号：将line及之后的所有行的行号+N（N为插入的段落数）
    NovelContentService.shift_lines(project_id, chapter, line, len(contents))
    
    # 批量创建新内容
    novel_contents = [
        NovelContent(
            project_id=project_id,
            chapter=chapter,
            line=line + i,
            content=content
        )
        for i, content in enumerate(contents)
    ]
    
    NovelContentService.batch_create(novel_contents)
    logger.info(f"批量插入小说内容: project={project_id}, chapter={chapter}, line={line}, count={len(contents)}")
    return {"message": "批量插入成功", "count": len(contents)}


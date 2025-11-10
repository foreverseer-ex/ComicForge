"""
内容服务路由。

统一管理小说内容、章节、段落、图像等资源。
合并了原 reader.py 和 novel.py 的功能。
"""
import uuid
from pathlib import Path
from typing import List, Optional

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from loguru import logger

from api.schemas import ChapterSummary
from api.schemas.novel import NovelContent
from api.services.db import NovelContentService, ProjectService
from api.services.db.summary_service import SummaryService
from api.utils.path import project_home, app_temp_path

router = APIRouter(
    prefix="/context",
    tags=["内容服务"],
    responses={404: {"description": "资源不存在"}},
)


# ==================== 小说文件上传 ====================

@router.post("/upload", summary="上传小说文件")
async def upload_novel(file: UploadFile = File(...)) -> dict:
    """
    上传小说文件到服务器。
    
    Args:
        file: 上传的文件（multipart/form-data）
    
    Returns:
        包含文件路径的字典
    
    Raises:
        HTTPException: 文件格式不支持或上传失败
    """
    # 验证文件格式
    allowed_extensions = ['.txt', '.pdf', '.doc', '.docx', '.md']
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}。支持格式: {', '.join(allowed_extensions)}"
        )
    
    # 验证文件大小（限制为100MB）
    max_size = 100 * 1024 * 1024
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail="文件大小不能超过100MB"
        )
    
    try:
        # 确保上传目录存在
        upload_dir = app_temp_path / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名（保留原扩展名）
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / unique_filename
        
        # 保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        logger.info(f"文件上传成功: {file.filename} -> {file_path}")
        
        # 返回文件路径（绝对路径）
        return {"file_path": str(file_path.absolute())}
        
    except Exception as e:
        logger.exception(f"文件上传失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"文件上传失败: {str(e)}"
        )


@router.get("/novel-file", response_class=FileResponse, summary="获取项目小说文件")
async def get_novel_file(project_id: str) -> FileResponse:
    """
    获取项目的原始小说文件。
    
    Args:
        project_id: 项目ID（查询参数）
    
    Returns:
        小说文件
    
    Raises:
        HTTPException: 文件不存在时返回 404
    """
    session = ProjectService.get(project_id)
    if not session or not session.novel_path:
        raise HTTPException(status_code=404, detail="小说文件不存在")
    
    novel_path = Path(session.novel_path)
    if not novel_path.exists():
        raise HTTPException(status_code=404, detail="小说文件不存在")
    
    return FileResponse(
        path=str(novel_path),
        media_type="text/plain",
        filename=novel_path.name
    )


# ==================== 内容行操作（CRUD）====================

@router.post("/line", summary="创建内容行")
async def create_line(
    project_id: str,
    chapter: int,
    line: int,
    content: str
) -> dict:
    """
    创建新的内容行。
    
    Args:
        project_id: 项目ID
        chapter: 章节号（从0开始）
        line: 行号（从0开始）
        content: 行内容
    
    Returns:
        创建的内容ID
    """
    novel_content = NovelContent(
        project_id=project_id,
        chapter=chapter,
        line=line,
        content=content
    )
    created = NovelContentService.create(novel_content)
    logger.info(f"创建内容行: project={project_id}, chapter={chapter}, line={line}")
    return {"id": created.id}


@router.get("/line", summary="获取指定行内容")
async def get_line(
    project_id: str,
    chapter: int,
    line: int
) -> NovelContent:
    """
    获取指定行的内容。
    
    Args:
        project_id: 项目ID（查询参数）
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


@router.put("/line", summary="更新行内容")
async def update_line(
    project_id: str,
    chapter: int,
    line: int,
    content: str
) -> NovelContent:
    """
    更新指定行的内容。
    
    Args:
        project_id: 项目ID
        chapter: 章节号
        line: 行号
        content: 新的内容
    
    Returns:
        更新后的行内容
    
    Raises:
        HTTPException: 内容不存在时返回 404
    """
    updated = NovelContentService.update(project_id, chapter, line, content)
    if not updated:
        raise HTTPException(
            status_code=404,
            detail=f"内容不存在: chapter={chapter}, line={line}"
        )
    logger.info(f"更新内容行: project={project_id}, chapter={chapter}, line={line}")
    return updated


@router.delete("/line", summary="删除行内容")
async def delete_line(
    project_id: str,
    chapter: int,
    line: int
) -> dict:
    """
    删除指定行的内容。
    
    Args:
        project_id: 项目ID
        chapter: 章节号
        line: 行号
    
    Returns:
        删除结果
    """
    success = NovelContentService.delete_single(project_id, chapter, line)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"内容不存在: chapter={chapter}, line={line}"
        )
    logger.info(f"删除内容行: project={project_id}, chapter={chapter}, line={line}")
    return {
        "message": "内容删除成功",
        "project_id": project_id,
        "chapter": chapter,
        "line": line
    }


# ==================== 批量行操作 ====================

@router.post("/lines/batch", summary="批量创建内容行")
async def create_lines_batch(
    contents: List[dict]
) -> List[NovelContent]:
    """
    批量创建内容行。
    
    Args:
        contents: 内容列表，每项包含 project_id, chapter, line, content
    
    Returns:
        创建的内容列表
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
    logger.info(f"批量创建内容: {len(created)} 行")
    return created


@router.get("/lines", summary="获取章节的所有行")
async def get_chapter_lines(
    project_id: str,
    chapter: int
) -> List[NovelContent]:
    """
    获取指定章节的所有行。
    
    Args:
        project_id: 项目ID
        chapter: 章节号
    
    Returns:
        章节所有行的内容列表
    """
    return NovelContentService.get_by_chapter(project_id, chapter)


@router.get("/lines/range", summary="获取行范围的内容")
async def get_lines_range(
    project_id: str,
    start_line: int,
    end_line: int,
    chapter: Optional[int] = None
) -> List[NovelContent]:
    """
    获取指定行范围的内容。
    
    可以读取指定章节的行范围，也可以跨章节读取（不指定chapter时）。
    
    Args:
        project_id: 项目ID
        start_line: 起始行号（包含，从0开始）
        end_line: 结束行号（包含）
        chapter: 章节号（可选，不指定则跨章节查询）
    
    Returns:
        行内容列表（按章节和行号排序）
    """
    return NovelContentService.get_line_range(project_id, start_line, end_line, chapter=chapter)


@router.post("/line/insert", summary="插入内容并重新编号")
async def insert_line(
    project_id: str,
    chapter: int,
    line: int,
    content: str
) -> dict:
    """
    在指定位置插入内容，并自动重新编号后续行。
    
    Args:
        project_id: 项目ID
        chapter: 章节号
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
    logger.info(f"插入内容: project={project_id}, chapter={chapter}, line={line}")
    return {"id": created.id}


@router.post("/lines/insert-batch", summary="批量插入内容并重新编号")
async def insert_lines_batch(
    project_id: str,
    chapter: int,
    line: int,
    contents: List[str]
) -> dict:
    """
    在指定位置批量插入内容，并自动重新编号后续行。
    
    Args:
        project_id: 项目ID
        chapter: 章节号
        line: 插入位置的行号
        contents: 要插入的内容列表
    
    Returns:
        插入结果
    """
    if not contents:
        return {"message": "没有内容需要插入", "count": 0}
    
    # 先重新编号
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
    logger.info(f"批量插入内容: project={project_id}, chapter={chapter}, line={line}, count={len(contents)}")
    return {"message": "批量插入成功", "count": len(contents)}


# ==================== 章节管理 ====================

@router.get("/chapters", summary="获取所有章节")
async def get_chapters(project_id: str) -> List[ChapterSummary]:
    """
    获取项目的所有章节摘要列表。
    
    Args:
        project_id: 项目ID
    
    Returns:
        章节摘要列表
    """
    return SummaryService.get_all(project_id)


@router.get("/chapter", summary="获取章节详情")
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
    summary = SummaryService.get(project_id, chapter_index)
    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"章节不存在: chapter_index={chapter_index}"
        )
    return summary


@router.put("/chapter", summary="更新章节详情")
async def update_chapter(
    project_id: str,
    chapter_index: int,
    summary: Optional[str] = None,
    title: Optional[str] = None,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None
) -> ChapterSummary:
    """
    更新章节详情。
    
    Args:
        project_id: 项目ID
        chapter_index: 章节索引
        summary: 故事梗概内容（可选）
        title: 章节标题（可选）
        start_line: 起始行号（可选）
        end_line: 结束行号（可选）
    
    Returns:
        更新后的章节摘要
    
    Raises:
        HTTPException: 章节不存在时返回 404
    """
    # 构建更新字典
    update_data = {}
    if summary is not None:
        update_data["summary"] = summary
    if title is not None:
        update_data["title"] = title
    if start_line is not None:
        update_data["start_line"] = start_line
    if end_line is not None:
        update_data["end_line"] = end_line
    
    # 更新摘要
    updated_summary = SummaryService.update(project_id, chapter_index, **update_data)
    
    if not updated_summary:
        raise HTTPException(
            status_code=404,
            detail=f"章节不存在: chapter_index={chapter_index}"
        )
    
    logger.info(f"更新章节详情: project={project_id}, chapter={chapter_index}")
    return updated_summary


@router.delete("/chapter", summary="删除指定章节的内容")
async def delete_chapter(project_id: str, chapter: int) -> dict:
    """
    删除指定章节的所有内容。
    
    Args:
        project_id: 项目ID
        chapter: 章节号
    
    Returns:
        删除结果
    """
    count = NovelContentService.delete_by_chapter(project_id, chapter)
    logger.info(f"删除章节内容: project={project_id}, chapter={chapter}, 共 {count} 条")
    return {"message": "章节内容删除成功", "project_id": project_id, "chapter": chapter, "deleted_count": count}


# ==================== 项目级操作 ====================

@router.get("/project", summary="获取项目的所有内容")
async def get_project_content(
    project_id: str,
    limit: Optional[int] = None
) -> List[NovelContent]:
    """
    获取项目的所有内容。
    
    Args:
        project_id: 项目ID
        limit: 返回数量限制
    
    Returns:
        内容列表
    """
    return NovelContentService.get_by_session(project_id, limit=limit)


@router.delete("/project", summary="删除项目的所有内容")
async def delete_project_content(project_id: str) -> dict:
    """
    删除项目的所有内容。
    
    Args:
        project_id: 项目ID
    
    Returns:
        删除结果
    """
    count = NovelContentService.delete_by_session(project_id)
    logger.info(f"删除项目内容: {project_id}, 共 {count} 条")
    return {"message": "项目内容删除成功", "project_id": project_id, "deleted_count": count}


# ==================== 统计信息 ====================

@router.get("/stats", summary="获取内容统计信息")
async def get_stats(project_id: str) -> dict:
    """
    获取项目的内容统计信息。
    
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


# ==================== 内容图像访问 ====================

@router.get("/image", response_class=FileResponse, summary="获取内容行的生成图像")
async def get_line_image(project_id: str, line: int) -> FileResponse:
    """
    获取指定行的生成图像。
    
    Args:
        project_id: 项目ID
        line: 行号（从0开始）
    
    Returns:
        图像文件
    
    Raises:
        HTTPException: 图像不存在时返回 404
    """
    # 图像保存在项目的 images 目录
    image_path = project_home / project_id / "images" / f"{line}.png"
    
    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"生成图像不存在: line={line}"
        )
    
    return FileResponse(
        path=str(image_path),
        media_type="image/png",
        filename=f"{line}.png"
    )

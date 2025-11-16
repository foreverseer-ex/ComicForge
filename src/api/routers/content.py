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
from fastapi.responses import FileResponse, Response
from loguru import logger

from api.schemas import ChapterSummary
from api.schemas.content import NovelContent
from api.services.db import ContentService, ProjectService
from api.services.db.summary_service import SummaryService
from api.utils.path import project_home, app_temp_path

router = APIRouter(
    prefix="/content",
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
) -> str:
    """
    创建新的内容行。
    
    Args:
        project_id: 项目ID
        chapter: 章节号（从0开始）
        line: 行号（从0开始）
        content: 行内容
    
    Returns:
        创建的内容ID字符串
    """
    novel_content = NovelContent(
        project_id=project_id,
        chapter=chapter,
        line=line,
        content=content
    )
    created = ContentService.create(novel_content)
    logger.info(f"创建内容行: project={project_id}, chapter={chapter}, line={line}")
    return str(created.id)


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
    content = ContentService.get_by_line(project_id, chapter, line)
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
    updated = ContentService.update(project_id, chapter, line, content)
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
    success = ContentService.delete_single(project_id, chapter, line)
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
    created = ContentService.batch_create(novel_contents)
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
    return ContentService.get_by_chapter(project_id, chapter)


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
    return ContentService.get_line_range(project_id, start_line, end_line, chapter=chapter)


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
    ContentService.shift_lines(project_id, chapter, line, 1)
    
    # 创建新内容
    novel_content = NovelContent(
        project_id=project_id,
        chapter=chapter,
        line=line,
        content=content
    )
    created = ContentService.create(novel_content)
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
    ContentService.shift_lines(project_id, chapter, line, len(contents))
    
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
    
    ContentService.batch_create(novel_contents)
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
    count = ContentService.delete_by_chapter(project_id, chapter)
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
    return ContentService.get_by_session(project_id, limit=limit)


@router.delete("/project", summary="删除项目的所有内容")
async def delete_project_content(project_id: str) -> dict:
    """
    删除项目的所有内容。
    
    Args:
        project_id: 项目ID
    
    Returns:
        删除结果
    """
    count = ContentService.delete_by_session(project_id)
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
    total_lines = ContentService.count_by_session(project_id)
    total_chapters = ContentService.count_chapters(project_id)
    
    return {
        "project_id": project_id,
        "total_lines": total_lines,
        "total_chapters": total_chapters
    }


# ==================== 内容图像访问 ====================

@router.get("/draw_iteration", summary="获取指定行的 DrawIteration")
async def get_draw_iteration(
    project_id: str,
    index: int
) -> dict:
    """
    获取指定行的 DrawIteration 信息（包括状态）。
    
    Args:
        project_id: 项目ID
        index: 行号（从0开始）
    
    Returns:
        包含 DrawIteration 信息的字典，如果不存在则返回 None
    """
    from api.services.db.base import normalize_project_id
    from api.services.db import DrawIterationService
    
    project_id = normalize_project_id(project_id)
    iteration = DrawIterationService.get(project_id, index)
    
    if not iteration:
        return {
            "project_id": project_id,
            "index": index,
            "status": None,
            "summary": None,
            "draw_args": None
        }
    
    return {
        "project_id": iteration.project_id,
        "index": iteration.index,
        "status": iteration.status,
        "summary": iteration.summary,
        "draw_args": iteration.draw_args
    }


@router.get("/image", response_class=FileResponse, summary="获取内容行的生成图像")
async def get_line_image(project_id: str, index: int) -> FileResponse:
    """
    获取指定行的生成图像。
    
    Args:
        project_id: 项目ID
        index: 行号（从0开始）
    
    Returns:
        图像文件
    
    Raises:
        HTTPException: 图像不存在时返回 404
    """
    from api.services.db.base import normalize_project_id
    project_id = normalize_project_id(project_id)
    # 如果 project_id 为 None，使用 "default" 作为目录名
    actual_project_id = project_id if project_id is not None else "default"
    # 图像保存在项目的 images 目录
    image_path = project_home / actual_project_id / "images" / f"{index}.png"
    
    # 添加调试日志
    logger.debug(f"尝试获取图片: project_id={project_id}, actual_project_id={actual_project_id}, index={index}, path={image_path}")
    
    if not image_path.exists():
        # 图片不存在，返回1x1透明PNG（避免浏览器控制台404错误）
        # 这是一个1x1透明PNG的字节数据
        transparent_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        return Response(
            content=transparent_png,
            media_type="image/png",
            headers={"Cache-Control": "no-cache"}
        )
    
    return FileResponse(
        path=str(image_path),
        media_type="image/png",
        filename=f"{index}.png"
    )


@router.post("/bind_image_from_job", summary="从 job_id 绑定图像到段落")
async def bind_image_from_job(
    project_id: str,
    job_id: str,
    index: int
) -> dict:
    """
    从已存在的 job_id 绑定图像到段落。
    
    此函数会：
    1. 检查 job 状态
    2. 如果 job 已完成（图片已存在），直接复制图像到项目文件夹
    3. 如果 job 未完成，启动监控任务，完成后复制图像
    
    Args:
        project_id: 项目ID
        job_id: 绘图任务 ID
        index: 行号（从0开始）
    
    Returns:
        包含 job_id、project_id、index 的字典
    
    Raises:
        HTTPException: job 不存在或项目不存在
    """
    from api.services.db.base import normalize_project_id
    from api.services.db import JobService
    from api.utils.path import jobs_home
    import asyncio
    import shutil
    
    project_id = normalize_project_id(project_id)
    
    # 检查 job 是否存在
    job = JobService.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"任务不存在: {job_id}")
    
    # 检查项目是否存在
    project = ProjectService.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
    
    # 如果 project_id 为 None，使用 "default" 作为目录名
    actual_project_id = project_id if project_id is not None else "default"
    # 图像保存在项目的 images 目录
    out_dir = project_home / actual_project_id / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{index}.png"
    
    # 添加调试日志
    logger.debug(f"准备保存图片: project_id={project_id}, actual_project_id={actual_project_id}, index={index}, path={out_path}")
    
    # 检查 job 状态
    job_image_path = jobs_home / f"{job_id}.png"
    job_completed = job.status == "completed" and job_image_path.exists()
    
    if job_completed:
        # Job 已完成，直接复制图像
        shutil.copy2(job_image_path, out_path)
        logger.info(f"已复制任务图像: {job_image_path} -> {out_path}")
        # 验证文件是否成功复制
        if out_path.exists():
            logger.debug(f"图片已成功保存: {out_path}, 大小={out_path.stat().st_size} bytes")
            # 更新 DrawIteration 状态为 completed
            from api.services.db import DrawIterationService
            DrawIterationService.update(
                project_id=project_id,
                index=index,
                status="completed"
            )
            logger.info(f"已更新 DrawIteration 状态为 completed: project_id={project_id}, index={index}")
        else:
            logger.error(f"图片保存失败: {out_path} 不存在")
        return {
            "job_id": job_id,
            "project_id": project_id,
            "index": index,
            "completed": True
        }
    else:
        # Job 未完成，启动监控任务
        asyncio.create_task(
            _monitor_single_job_and_bind_image(
                job_id=job_id,
                project_id=project_id,
                index=index
            )
        )
        logger.info(f"已启动监控任务: job_id={job_id}, project_id={project_id}, index={index}")
        return {
            "job_id": job_id,
            "project_id": project_id,
            "index": index,
            "completed": False
        }


async def _monitor_single_job_and_bind_image(
    job_id: str,
    project_id: str,
    index: int
):
    """
    监控单个 job 状态，完成后复制图像到项目文件夹。
    
    这是一个后台任务函数，会轮询检查 job 状态，直到完成或超时。
    
    Args:
        job_id: 要监控的 job ID
        project_id: 项目 ID
        index: 行号（从0开始）
    """
    from api.services.db import JobService
    from api.services.db.base import normalize_project_id
    from api.settings import app_settings
    from api.utils.path import jobs_home
    import shutil
    import asyncio
    
    project_id = normalize_project_id(project_id)
    
    # 根据后端类型设置超时时间
    backend = app_settings.draw.backend
    if backend == "civitai":
        # Civitai 超时时间（秒），从配置中读取
        timeout_seconds = app_settings.civitai.draw_timeout
        max_attempts = int(timeout_seconds)  # 每秒检查一次
    else:
        # SD-Forge 默认超时时间：30分钟（1800秒）
        timeout_seconds = app_settings.sd_forge.generate_timeout
        max_attempts = int(timeout_seconds)
    
    attempt = 0
    last_error = None
    
    while attempt < max_attempts:
        try:
            # 检查 job 状态
            job = JobService.get(job_id)
            if not job:
                logger.error(f"监控任务失败: Job 不存在 {job_id}")
                return
            
            # 检查 job 状态是否为 completed
            if job.status == "completed" and job.completed_at is not None:
                # Job 已完成，文件应该已经完全写入
                job_image_path = jobs_home / f"{job_id}.png"
                
                # 再次确认文件存在（双重检查）
                if not job_image_path.exists():
                    logger.warning(f"Job 标记为完成，但文件不存在: {job_id}, 等待文件生成...")
                    await asyncio.sleep(1)
                    attempt += 1
                    continue
                
                # 如果 project_id 为 None，使用 "default" 作为目录名
                actual_project_id = project_id if project_id is not None else "default"
                # 图像保存在项目的 images 目录
                out_dir = project_home / actual_project_id / "images"
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / f"{index}.png"
                
                # 从 jobs 文件夹复制图片到项目文件夹
                shutil.copy2(job_image_path, out_path)
                logger.info(f"已复制任务图像: {job_image_path} -> {out_path}")
                # 验证文件是否成功复制
                if out_path.exists():
                    logger.debug(f"图片已成功保存: {out_path}, 大小={out_path.stat().st_size} bytes")
                    # 更新 DrawIteration 状态为 completed
                    from api.services.db import DrawIterationService
                    DrawIterationService.update(
                        project_id=project_id,
                        index=index,
                        status="completed"
                    )
                    logger.info(f"已更新 DrawIteration 状态为 completed: project_id={project_id}, index={index}")
                else:
                    logger.error(f"图片保存失败: {out_path} 不存在")
                return
            
            elif job.status == "failed":
                logger.error(f"Job 执行失败: {job_id}")
                return
            
            # Job 还在进行中，等待后继续检查
            await asyncio.sleep(1)
            attempt += 1
            
        except Exception as e:
            last_error = e
            logger.error(f"监控任务出错: {e}", exc_info=True)
            await asyncio.sleep(1)
            attempt += 1
    
    # 超时
    error_msg = f"监控任务超时: job_id={job_id}"
    if last_error:
        error_msg += f", 最后错误: {last_error}"
    logger.error(error_msg)


@router.get("/paragraph_index", summary="根据章节和行号获取全局索引")
async def get_paragraph_index(
    project_id: str,
    chapter: int,
    line: int
) -> dict:
    """
    根据章节号和行号获取全局行索引。
    
    Args:
        project_id: 项目ID
        chapter: 章节号（从0开始）
        line: 行号（从0开始）
    
    Returns:
        包含全局索引的字典
    
    Raises:
        HTTPException: 如果段落不存在，返回404
    """
    from api.services.db.base import normalize_project_id
    
    project_id = normalize_project_id(project_id)
    
    # 获取所有内容，按章节和行号排序
    contents = ContentService.get_by_session(project_id)
    
    # 找到匹配的内容
    for index, content in enumerate(contents):
        if content.chapter == chapter and content.line == line:
            return {
                "project_id": project_id,
                "chapter": chapter,
                "line": line,
                "index": index
            }
    
    raise HTTPException(status_code=404, detail=f"段落不存在: project_id={project_id}, chapter={chapter}, line={line}")


# 注意：get_draw_iteration 函数已在上面定义（第561行），这里不再重复定义

@router.delete("/draw_iteration/all", summary="清空项目的所有段落图像")
async def clear_all_draw_iterations(
    project_id: str
) -> dict:
    """
    清空项目的所有 DrawIteration 记录和对应的图像文件。
    
    Args:
        project_id: 项目ID
    
    Returns:
        包含删除结果的字典
    
    Raises:
        HTTPException: 如果项目不存在，返回404
    """
    from api.services.db.base import normalize_project_id
    from api.services.db import DrawIterationService, ProjectService
    import os
    from pathlib import Path
    
    project_id = normalize_project_id(project_id)
    
    # 检查项目是否存在
    project = ProjectService.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
    
    # 删除所有 DrawIteration 记录
    deleted_count = DrawIterationService.delete_all(project_id)
    
    # 删除所有图像文件
    actual_project_id = project_id if project_id is not None else "default"
    images_dir = project_home / actual_project_id / "images"
    if images_dir.exists():
        image_count = 0
        for image_file in images_dir.glob("*.png"):
            try:
                os.remove(image_file)
                image_count += 1
            except Exception as e:
                logger.error(f"删除图像文件失败: {image_file}, 错误: {e}")
        logger.info(f"已删除 {image_count} 个图像文件")
    else:
        image_count = 0
    
    return {
        "success": True,
        "project_id": project_id,
        "deleted_iterations": deleted_count,
        "deleted_images": image_count,
        "message": f"成功清空 {deleted_count} 个 DrawIteration 记录和 {image_count} 个图像文件"
    }


@router.post("/draw_iteration/cancel", summary="停止迭代（取消 pending 状态的任务）")
async def cancel_draw_iterations(
    project_id: str,
    start_index: int
) -> dict:
    """
    将指定索引之后的所有 pending 状态的 DrawIteration 更新为 cancelled。
    
    Args:
        project_id: 项目ID
        start_index: 起始索引（不包含，即从 start_index + 1 开始取消）
    
    Returns:
        包含取消结果的字典
    
    Raises:
        HTTPException: 如果项目不存在，返回404
    """
    from api.services.db.base import normalize_project_id
    from api.services.db import DrawIterationService, ProjectService
    
    project_id = normalize_project_id(project_id)
    
    # 检查项目是否存在
    project = ProjectService.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
    
    # 取消 pending 状态的任务
    cancelled_count = DrawIterationService.cancel_pending_after_index(project_id, start_index)
    
    return {
        "success": True,
        "project_id": project_id,
        "start_index": start_index,
        "cancelled_count": cancelled_count,
        "message": f"成功取消 {cancelled_count} 个 pending 状态的任务"
    }




@router.delete("/draw_iteration", summary="删除指定行的DrawIteration和图像")
async def delete_draw_iteration(
    project_id: str,
    index: int
) -> dict:
    """
    删除指定行的DrawIteration记录和对应的图像文件。
    
    Args:
        project_id: 项目ID
        index: 行号（从0开始）
    
    Returns:
        包含删除结果的字典
    
    Raises:
        HTTPException: 如果记录不存在，返回404
    """
    from api.services.db.base import normalize_project_id
    from api.services.db import DrawIterationService
    import os
    
    project_id = normalize_project_id(project_id)
    
    # 检查DrawIteration是否存在
    iteration = DrawIterationService.get(project_id, index)
    if not iteration:
        raise HTTPException(status_code=404, detail=f"DrawIteration不存在: project_id={project_id}, index={index}")
    
    # 删除图像文件
    actual_project_id = project_id if project_id is not None else "default"
    image_path = project_home / actual_project_id / "images" / f"{index}.png"
    if image_path.exists():
        try:
            os.remove(image_path)
            logger.info(f"已删除图像文件: {image_path}")
        except Exception as e:
            logger.error(f"删除图像文件失败: {image_path}, 错误: {e}")
            # 继续删除数据库记录，即使文件删除失败
    
    # 删除DrawIteration记录
    deleted = DrawIterationService.delete(project_id, index)
    if not deleted:
        raise HTTPException(status_code=500, detail=f"删除DrawIteration失败: project_id={project_id}, index={index}")
    
    return {
        "success": True,
        "project_id": project_id,
        "index": index,
        "message": "删除成功"
    }


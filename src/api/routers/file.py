"""
文件管理的路由。

简化设计：主要提供图像文件的访问。
小说文件的上传和管理通过 Session 和 NovelContent 服务处理。
"""
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from loguru import logger
import aiofiles
import uuid

from api.services.db import ActorService, JobService
from api.schemas.actor import ActorExample
from api.utils.path import project_home, app_temp_path, jobs_home

router = APIRouter(
    prefix="/file",
    tags=["文件管理"],
    responses={404: {"description": "文件不存在"}},
)

# ==================== 文件上传 ====================

@router.post("/upload", summary="上传文件")
async def upload_file(file: UploadFile = File(...)) -> dict:
    """
    上传文件到服务器。
    
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


# ==================== Actor 示例图访问 ====================

@router.get("/actor-example", response_class=FileResponse, summary="获取 Actor 示例图")
async def get_actor_example_image(actor_id: str, example_index: int) -> FileResponse:
    """
    获取 Actor 示例图文件。
    
    Args:
        actor_id: Actor ID（查询参数）
        example_index: 示例图索引（查询参数）
    
    Returns:
        图像文件
    
    Raises:
        HTTPException: 图像不存在时返回 404
    """
    actor = ActorService.get(actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail=f"Actor 不存在: {actor_id}")
    
    if example_index < 0 or example_index >= len(actor.examples):
        raise HTTPException(status_code=404, detail=f"示例图索引越界: {example_index}")
    
    example_dict = actor.examples[example_index]
    example = ActorExample(**example_dict)
    
    # 如果 image_path 为 None，说明正在生成中
    if example.image_path is None:
        raise HTTPException(status_code=404, detail="示例图正在生成中")
    
    # image_path 只保存文件名，实际文件保存在 projects/{project_id}/actors/{filename}
    # 需要从 actor 获取 project_id，然后构建完整路径
    project_id = actor.project_id
    image_path = project_home / project_id / "actors" / example.image_path
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail=f"示例图文件不存在: {example.image_path}")
    
    return FileResponse(
        path=str(image_path),
        media_type="image/png",
        filename=image_path.name
    )


# ==================== 生成图像访问 ====================

@router.get("/image", response_class=FileResponse, summary="获取生成的图像")
async def get_generated_image(project_id: str, line: int) -> FileResponse:
    """
    获取指定行的生成图像。
    
    Args:
        project_id: 项目ID（查询参数）
        line: 行号（从0开始，查询参数）
    
    Returns:
        图像文件
    
    Raises:
        HTTPException: 图像不存在时返回 404
    """
    # 图像保存在项目的 images 目录
    from api.utils.path import project_home
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


# ==================== 任务图像访问 ====================

@router.get("/job-image", response_class=FileResponse, summary="获取绘图任务图像")
async def get_job_image(job_id: str) -> FileResponse:
    """
    获取绘图任务生成的图像文件。
    
    从 jobs/{job_id}.png 读取图像文件并返回。
    
    Args:
        job_id: 任务ID（查询参数）
    
    Returns:
        图像文件
    
    Raises:
        HTTPException: 任务不存在或图像文件不存在时返回 404
    """
    # 检查任务是否存在
    job = JobService.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"任务不存在: {job_id}")
    
    # 从 jobs 文件夹读取图像文件
    job_image_path = jobs_home / f"{job_id}.png"
    
    if not job_image_path.exists():
        raise HTTPException(status_code=404, detail=f"任务图像文件不存在: {job_id}")
    
    return FileResponse(
        path=str(job_image_path),
        media_type="image/png",
        filename=f"job_{job_id}.png"
    )


# ==================== 项目文件访问 ====================

@router.get("/project/novel", response_class=FileResponse, summary="获取项目小说文件")
async def get_project_novel(project_id: str) -> FileResponse:
    """
    获取项目的原始小说文件。
    
    Args:
        project_id: 项目ID（查询参数）
    
    Returns:
        小说文件
    
    Raises:
        HTTPException: 文件不存在时返回 404
    
    注意：
        这个路由返回原始上传的小说文件，
        不是数据库中的 NovelContent。
    """
    from api.services.db import ProjectService
    
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

"""
绘图管理的路由。

专注于绘图功能：创建绘图任务、接受结果、管理绘图任务。
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import httpx
from loguru import logger

from api.services.db import JobService, BatchJobService
from api.schemas.draw import Job, BatchJob, DrawArgs
from api.services.draw import get_current_draw_service
from api.services.draw.sd_forge import SdForgeDrawService
from api.utils.path import project_home, jobs_home
from api.settings import app_settings


router = APIRouter(
    prefix="/draw",
    tags=["绘图管理"],
    responses={404: {"description": "资源不存在"}},
)


# ==================== SD-Forge 可用模型查询 ====================
# 注意：这些API仅在使用SD-Forge后端时有效，返回的是当前可用的模型列表

@router.get("/checkpoint", summary="获取 SD-Forge 可用 Checkpoint 模型列表")
async def get_checkpoints() -> List[Dict[str, Any]]:
    """
    获取 SD-Forge 后端当前可用的 Checkpoint 模型列表。
    
    注意：此API仅在使用SD-Forge后端时有效。
    如果需要获取所有模型元数据（包括不可用的），请使用 /model-meta/checkpoint。
    
    Returns:
        Checkpoint 模型列表（来自 sd-forge /sdapi/v1/sd-models）
    """
    try:
        models_data = SdForgeDrawService._get_sd_models()  # pylint: disable=protected-access
        # SD-Forge 返回的是列表格式
        if isinstance(models_data, list):
            return models_data
        # 如果是字典，转换为列表
        return [models_data] if models_data else []
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"SD-Forge 连接失败: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {e}") from e


@router.get("/loras", summary="获取 SD-Forge 可用 LoRA 模型列表")
async def get_loras() -> List[Dict[str, Any]]:
    """
    获取 SD-Forge 后端当前可用的 LoRA 模型列表。
    
    注意：此API仅在使用SD-Forge后端时有效。
    如果需要获取所有LoRA元数据（包括不可用的），请使用 /model-meta/loras。
    
    Returns:
        LoRA 模型列表（来自 sd-forge /sdapi/v1/loras）
    """
    try:
        loras_data = SdForgeDrawService._get_loras()  # pylint: disable=protected-access
        # SD-Forge 返回的是列表格式
        if isinstance(loras_data, list):
            return loras_data
        # 如果是字典，转换为列表
        return [loras_data] if loras_data else []
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"SD-Forge 连接失败: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 LoRA 列表失败: {e}") from e


# ==================== 图像生成 ====================

@router.post("", summary="创建绘图任务（文生图）")
async def create_draw(
    model: str,
    prompt: str,
    negative_prompt: str = "",
    loras: Optional[Dict[str, float] | str] = None,
    seed: int = -1,
    sampler_name: str = "DPM++ 2M Karras",
    steps: int = 30,
    cfg_scale: float = 7.0,
    width: int = 1024,
    height: int = 1024,
    clip_skip: Optional[int] = None,
    vae: Optional[str] = None,
    name: Optional[str] = None,
    desc: Optional[str] = None,
    batch_size: int = 1,
) -> str:
    """
    创建绘图任务（文生图），返回 batch_id。
    
    Args:
        model: SD模型名称
        prompt: 正向提示词
        negative_prompt: 负向提示词
        loras: LoRA 配置 {name: weight}
        seed: 随机种子（-1 表示随机）
        sampler_name: 采样器名称
        steps: 采样步数
        cfg_scale: CFG Scale
        width: 图像宽度
        height: 图像高度
        clip_skip: CLIP skip
        vae: VAE 模型
        name: 任务名称（可选）
        desc: 任务描述（可选）
        batch_size: 批量大小（1-16，默认1）
    
    Returns:
        batch_id（批次 ID）
    """
    try:
        import json
        
        # 验证 batch_size
        if batch_size < 1 or batch_size > 16:
            raise HTTPException(status_code=400, detail="batch_size 必须在 1-16 之间")
        
        # 解析 loras
        loras_dict: Optional[Dict[str, float]] = None
        if loras:
            if isinstance(loras, str):
                try:
                    loras_dict = json.loads(loras)
                except json.JSONDecodeError:
                    logger.warning(f"LoRA 参数格式错误: {loras}")
                    loras_dict = None
            elif isinstance(loras, dict):
                loras_dict = loras
        
        args = DrawArgs(
            model=model,
            prompt=prompt,
            negative_prompt=negative_prompt or "",
            steps=steps,
            cfg_scale=cfg_scale,
            sampler=sampler_name,
            seed=seed,
            width=width,
            height=height,
            clip_skip=clip_skip,
            vae=vae,
            loras=loras_dict or {},
        )
        
        # 如果是 Civitai 后端，检查并调整宽高限制（最大 1024）
        backend = app_settings.draw.backend
        if backend == "civitai":
            original_width = args.width
            original_height = args.height
            
            if args.width > 1024 or args.height > 1024:
                if args.width > args.height:
                    scale = 1024 / args.width
                    args.width = 1024
                    args.height = int(args.height * scale)
                else:
                    scale = 1024 / args.height
                    args.height = 1024
                    args.width = int(args.width * scale)
                
                if args.width > 1024:
                    args.width = 1024
                if args.height > 1024:
                    args.height = 1024
                
                logger.warning(
                    f"⚠️ Civitai 后端：图像尺寸已自动调整 "
                    f"（{original_width}x{original_height} → {args.width}x{args.height}，最大限制 1024）"
                )
        
        # 调用绘图服务
        draw_service = get_current_draw_service()
        batch_id = draw_service.draw(args, batch_size=batch_size, name=name, desc=desc)
        
        return batch_id
        
    except httpx.HTTPError as e:
        backend = app_settings.draw.backend
        raise HTTPException(status_code=502, detail=f"{backend} 连接失败: {e}") from e
    except Exception as e:
        import traceback
        logger.exception(f"创建绘图任务失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("", summary="获取绘图任务信息")
async def get_draw_job(job_id: str) -> Job:
    """
    获取单个绘图任务信息。
    
    Args:
        job_id: 任务ID（查询参数）
    
    Returns:
        任务对象
    
    Raises:
        HTTPException: 任务不存在时返回 404
    """
    job = JobService.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"任务不存在: {job_id}")
    return job


@router.delete("", summary="删除绘图任务")
async def delete_draw_job(job_id: str) -> dict:
    """
    删除单个绘图任务。
    
    Args:
        job_id: 任务ID（查询参数）
    
    Returns:
        删除的任务ID（job_id）
    
    Raises:
        HTTPException: 任务不存在时返回 404
    """
    success = JobService.delete(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"任务不存在: {job_id}")
    return {"job_id": job_id}


@router.get("/all", summary="获取所有绘图任务列表")
async def get_all_draw_jobs(
    limit: Optional[int] = None,
    offset: int = 0
) -> List[Job]:
    """
    获取所有绘图任务列表。
    
    Args:
        limit: 返回数量限制（None 表示无限制）
        offset: 跳过的记录数
    
    Returns:
        任务列表
    """
    return JobService.get_all(limit=limit, offset=offset)


@router.post("/batch/delete", summary="批量删除绘图任务")
async def delete_draw_jobs_batch(job_ids: list[str]) -> dict:
    """
    批量删除绘图任务。
    
    Args:
        job_ids: 任务ID列表（请求体，JSON数组）
    
    Returns:
        删除的任务数量
    """
    if not job_ids:
        raise HTTPException(status_code=400, detail="任务ID列表不能为空")
    count = JobService.delete_batch(job_ids)
    return {"count": count}


@router.delete("/clear", summary="清空所有绘图任务")
async def clear_draw_jobs() -> dict:
    """
    清空所有绘图任务。
    
    Returns:
        删除的任务数量
    """
    count = JobService.clear()
    return {"count": count}


@router.get("/image", response_class=FileResponse, summary="获取生成的图像")
async def get_image(
    project_id: str,
    batch_id: str,
    index: int = 0
) -> FileResponse:
    """
    获取生成的图像文件。
    
    Args:
        project_id: 项目ID
        batch_id: 批次ID
        index: 图像索引（默认0，即批次中的第一张）
    
    Returns:
        图像文件
    
    实现要点：
    - 返回 storage/sessions/{project_id}/batches/{batch_id}/{index}.png
    - 设置正确的 Content-Type
    - 如果文件不存在，返回404
    """
    file_path = project_home / project_id / "batches" / batch_id / f"{index}.png"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="图像不存在")
    return FileResponse(path=str(file_path), media_type="image/png")


@router.get("/job/status", summary="检查任务状态")
async def check_job_status(job_id: str) -> dict:
    """
    检查任务状态。
    
    Args:
        job_id: 任务ID
    
    Returns:
        包含任务状态的字典: {"completed": bool}
    
    Raises:
        HTTPException: 任务不存在时返回 404
    """
    # 检查任务是否存在
    job = JobService.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"任务不存在: {job_id}")
    
    # 获取当前绘图服务并检查状态
    try:
        draw_service = get_current_draw_service()
        
        # 对于 Civitai，需要从 job.data 中获取 civitai_job_token
        civitai_token = None
        if job.data and 'civitai_job_token' in job.data:
            civitai_token = job.data['civitai_job_token']
        
        # 如果还没有 token，说明后台任务还在创建中
        backend = app_settings.draw.backend
        if backend == "civitai" and not civitai_token:
            return {"completed": False, "pending": True}
        
        # 检查状态：对于 Civitai，使用 civitai_job_token；对于 SD-Forge，使用 job_id
        check_job_id = civitai_token if (backend == "civitai" and civitai_token) else job_id
        is_complete = await draw_service.get_job_status(check_job_id)
        
        # 如果任务已完成且 completed_at 未设置，更新它
        if is_complete and job.completed_at is None:
            from datetime import datetime
            JobService.update(job_id, completed_at=datetime.now())
        
        return {"completed": is_complete}
    except Exception as e:
        logger.exception(f"检查任务状态失败: {job_id}")
        raise HTTPException(status_code=500, detail=f"检查任务状态失败: {str(e)}") from e


@router.get("/job/image", response_class=FileResponse, summary="获取任务生成的图像")
async def get_job_image(job_id: str) -> FileResponse:
    """
    获取任务生成的图像文件。
    
    从 jobs/{job_id}.png 读取图像文件并返回。
    
    Args:
        job_id: 任务ID
    
    Returns:
        图像文件
    
    Raises:
        HTTPException: 任务不存在、未完成或图像文件不存在时返回相应错误
    """
    try:
        # 检查任务是否存在
        job = JobService.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"任务不存在: {job_id}")
        
        # 检查任务是否完成
        if job.completed_at is None:
            # 检查任务状态
            draw_service = get_current_draw_service()
            
            # 对于 Civitai，需要从 job.data 中获取 civitai_job_token
            civitai_token = None
            if job.data and 'civitai_job_token' in job.data:
                civitai_token = job.data['civitai_job_token']
            
            # 如果还没有 token，说明后台任务还在创建中
            backend = app_settings.draw.backend
            if backend == "civitai" and not civitai_token:
                raise HTTPException(status_code=400, detail=f"任务正在创建中: {job_id}")
            
            # 检查状态：对于 Civitai，使用 civitai_job_token；对于 SD-Forge，使用 job_id
            check_job_id = civitai_token if (backend == "civitai" and civitai_token) else job_id
            is_complete = await draw_service.get_job_status(check_job_id)
            if not is_complete:
                raise HTTPException(status_code=400, detail=f"任务未完成: {job_id}")
        
        # 从 jobs 文件夹读取图像文件
        job_image_path = jobs_home / f"{job_id}.png"
        
        if not job_image_path.exists():
            raise HTTPException(status_code=404, detail=f"任务图像文件不存在: {job_id}")
        
        return FileResponse(
            path=str(job_image_path),
            media_type="image/png",
            filename=f"job_{job_id}.png"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取任务图像失败: {job_id}")
        raise HTTPException(status_code=500, detail=f"获取图像失败: {str(e)}") from e


# ==================== Batch 管理 ====================

@router.get("/batch/{batch_id}", summary="获取批量绘图任务信息")
async def get_batch(batch_id: str) -> List[Job]:
    """
    获取批量绘图任务的所有 job 信息。
    
    Args:
        batch_id: 批次ID（路径参数）
    
    Returns:
        Job 列表
    
    Raises:
        HTTPException: 批次任务不存在时返回 404
    """
    batch_job = BatchJobService.get(batch_id)
    if not batch_job:
        raise HTTPException(status_code=404, detail=f"批次任务不存在: {batch_id}")
    
    # 获取所有 job
    jobs = []
    for job_id in batch_job.job_ids:
        job = JobService.get(job_id)
        if job:
            jobs.append(job)
    
    return jobs


@router.delete("/batch/{batch_id}", summary="删除批量绘图任务")
async def delete_batch(batch_id: str) -> dict:
    """
    删除批量绘图任务及其所有 job。
    
    Args:
        batch_id: 批次ID（路径参数）
    
    Returns:
        删除的批次ID（batch_id）
    
    Raises:
        HTTPException: 批次任务不存在时返回 404
    """
    batch_job = BatchJobService.get(batch_id)
    if not batch_job:
        raise HTTPException(status_code=404, detail=f"批次任务不存在: {batch_id}")
    
    # 删除所有 job
    for job_id in batch_job.job_ids:
        JobService.delete(job_id)
    
    # 删除 batch
    success = BatchJobService.delete(batch_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"批次任务不存在: {batch_id}")
    
    return {"batch_id": batch_id}


@router.get("/batch/all", summary="获取所有批量绘图任务列表")
async def get_all_batch_jobs(
    limit: Optional[int] = None,
    offset: int = 0
) -> List[BatchJob]:
    """
    获取所有批量绘图任务列表。
    
    Args:
        limit: 返回数量限制（None 表示无限制）
        offset: 跳过的记录数
    
    Returns:
        批次任务列表
    """
    return BatchJobService.get_all(limit=limit, offset=offset)


@router.delete("/batch/clear", summary="清空所有批量绘图任务")
async def clear_batch_jobs() -> dict:
    """
    清空所有批量绘图任务及其所有 job。
    
    Returns:
        删除的批次任务数量
    """
    batch_jobs = BatchJobService.get_all()
    # 删除所有 job
    for batch_job in batch_jobs:
        for job_id in batch_job.job_ids:
            JobService.delete(job_id)
    # 清空所有 batch
    count = BatchJobService.clear()
    return {"count": count}



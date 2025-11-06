"""
绘图管理的路由。

专注于绘图功能：创建绘图任务、接受结果、管理绘图任务。
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import httpx
from loguru import logger

from api.services.db import JobService, BatchJobService
from api.schemas.draw import Job, BatchJob, DrawArgs
from api.services.draw import get_current_draw_service
from api.services.draw.sd_forge import SdForgeDrawService
from api.utils.path import project_home
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
async def create_draw_job(
    model: str,
    prompt: str,
    negative_prompt: str = "",
    loras: Optional[Dict[str, float] | str] = None,  # 可以是字典或 JSON 字符串
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
) -> Dict[str, str]:
    """
    创建绘图任务（文生图），返回 job_id。
    
    注意：如果使用的是SD-Forge后端，会自动检查并设置model和vae选项。
    
    Args:
        model: SD模型名称（查询参数）
        prompt: 正向提示词（查询参数）
        negative_prompt: 负向提示词（查询参数）
        loras: LoRA 配置 {name: weight}（查询参数）
        seed: 随机种子（-1 表示随机，查询参数）
        sampler_name: 采样器名称（查询参数）
        steps: 采样步数（查询参数）
        cfg_scale: CFG Scale（查询参数）
        width: 图像宽度（查询参数）
        height: 图像高度（查询参数）
        clip_skip: CLIP skip（查询参数）
        vae: VAE 模型（查询参数）
        name: 任务名称（查询参数，可选）
        desc: 任务描述（查询参数，可选）
    
    Returns:
        包含 job_id 的字典
    
    实现要点：
    - 调用绘图服务的 draw() 方法
    - 如果使用SD-Forge后端，会自动检查当前加载的model和vae，如果不同则自动设置
    - 创建 Job 记录到数据库
    """
    try:
        import json
        # 解析 loras（如果是字符串，尝试解析为 JSON）
        loras_dict: Optional[Dict[str, float]] = None
        if loras:
            if isinstance(loras, str):
                try:
                    loras_dict = json.loads(loras)
                except json.JSONDecodeError:
                    # 如果解析失败，尝试作为单个键值对处理
                    logger.warning(f"LoRA 参数格式错误，尝试其他解析方式: {loras}")
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
            
            # 如果宽高超过 1024，自动调整为 1024（保持宽高比例）
            if args.width > 1024 or args.height > 1024:
                if args.width > args.height:
                    # 宽度更大，以宽度为基准缩放到 1024
                    scale = 1024 / args.width
                    args.width = 1024
                    args.height = int(args.height * scale)
                else:
                    # 高度更大，以高度为基准缩放到 1024
                    scale = 1024 / args.height
                    args.height = 1024
                    args.width = int(args.width * scale)
                
                # 确保调整后的宽高不超过 1024（由于舍入可能导致）
                if args.width > 1024:
                    args.width = 1024
                if args.height > 1024:
                    args.height = 1024
                
                logger.warning(
                    f"⚠️ Civitai 后端：图像尺寸已自动调整 "
                    f"（{original_width}x{original_height} → {args.width}x{args.height}，最大限制 1024）"
                )
        
        # 使用当前配置的绘图服务
        draw_service = get_current_draw_service()
        job_id = draw_service.draw(args)
        
        # 创建 Job 记录到数据库
        from datetime import datetime
        job = Job(
            job_id=job_id,
            name=name,
            desc=desc,
            created_at=datetime.now(),
            draw_args=args.model_dump(exclude_none=True)  # 保存 DrawArgs 到 Job，排除 None 值
        )
        JobService.create(job)
        
        return {"job_id": job_id}
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
        is_complete = draw_service.get_job_status(job_id)
        
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
    
    通过 job_id 从绘图服务获取图像并返回。
    
    Args:
        job_id: 任务ID
    
    Returns:
        图像文件
    
    Raises:
        HTTPException: 任务不存在、未完成或图像获取失败时返回相应错误
    """
    try:
        # 检查任务是否存在
        job = JobService.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"任务不存在: {job_id}")
        
        # 获取当前绘图服务
        draw_service = get_current_draw_service()
        
        # 检查任务是否完成
        is_complete = draw_service.get_job_status(job_id)
        if not is_complete:
            raise HTTPException(status_code=400, detail=f"任务未完成: {job_id}")
        
        # 如果任务已完成且 completed_at 未设置，更新它
        if job.completed_at is None:
            from datetime import datetime
            JobService.update(job_id, completed_at=datetime.now())
        
        # 获取图像（PIL Image）
        img = draw_service.get_image(job_id)
        
        # 转换为字节流
        import io
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # 返回文件响应
        from fastapi.responses import Response
        return Response(
            content=img_bytes.getvalue(),
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=job_{job_id}.png"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取任务图像失败: {job_id}")
        raise HTTPException(status_code=500, detail=f"获取图像失败: {str(e)}") from e


# ==================== Batch 管理 ====================

@router.post("/batch", summary="创建批量绘图任务")
async def create_batch(
    batch_size: int,
    model: str,
    prompt: str,
    negative_prompt: str = "",
    loras: Optional[Dict[str, float] | str] = None,  # 可以是字典或 JSON 字符串
    seed: int = -1,
    sampler_name: str = "DPM++ 2M Karras",
    steps: int = 30,
    cfg_scale: float = 7.0,
    width: int = 1024,
    height: int = 1024,
    clip_skip: Optional[int] = None,
    vae: Optional[str] = None,
) -> Dict[str, Any]:
    """
    创建批量绘图任务，返回 batch_id。
    
    Args:
        batch_size: 批量大小（查询参数）
        model: SD模型名称（查询参数）
        prompt: 正向提示词（查询参数）
        negative_prompt: 负向提示词（查询参数）
        loras: LoRA 配置 {name: weight}（查询参数）
        seed: 随机种子（-1 表示随机，查询参数）
        sampler_name: 采样器名称（查询参数）
        steps: 采样步数（查询参数）
        cfg_scale: CFG Scale（查询参数）
        width: 图像宽度（查询参数）
        height: 图像高度（查询参数）
        clip_skip: CLIP skip（查询参数）
        vae: VAE 模型（查询参数）
    
    Returns:
        包含 batch_id 和 job_ids 列表的字典
    
    实现要点：
    - 创建 batch_size 个绘图任务
    - 将所有 job_id 添加到 BatchJob
    """
    try:
        import uuid
        import json
        from datetime import datetime
        
        # 解析 loras（如果是字符串，尝试解析为 JSON）
        loras_dict: Optional[Dict[str, float]] = None
        if loras:
            if isinstance(loras, str):
                try:
                    loras_dict = json.loads(loras)
                except json.JSONDecodeError:
                    logger.warning(f"LoRA 参数格式错误，尝试其他解析方式: {loras}")
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
            
            # 如果宽高超过 1024，自动调整为 1024（保持宽高比例）
            if args.width > 1024 or args.height > 1024:
                if args.width > args.height:
                    # 宽度更大，以宽度为基准缩放到 1024
                    scale = 1024 / args.width
                    args.width = 1024
                    args.height = int(args.height * scale)
                else:
                    # 高度更大，以高度为基准缩放到 1024
                    scale = 1024 / args.height
                    args.height = 1024
                    args.width = int(args.width * scale)
                
                # 确保调整后的宽高不超过 1024（由于舍入可能导致）
                if args.width > 1024:
                    args.width = 1024
                if args.height > 1024:
                    args.height = 1024
                
                logger.warning(
                    f"⚠️ Civitai 后端：图像尺寸已自动调整 "
                    f"（{original_width}x{original_height} → {args.width}x{args.height}，最大限制 1024）"
                )
        
        # 使用当前配置的绘图服务
        draw_service = get_current_draw_service()
        
        # 生成 batch_id
        batch_id = str(uuid.uuid4())
        job_ids = []
        
        # 创建多个任务
        for i in range(batch_size):
            job_id = draw_service.draw(args)
            job_ids.append(job_id)
            
            # 创建 Job 记录到数据库
            job = Job(
                job_id=job_id,
                created_at=datetime.now(),
                draw_args=args.model_dump(exclude_none=True)  # 保存 DrawArgs 到 Job，排除 None 值
            )
            JobService.create(job)
        
        # 创建 BatchJob 记录
        batch_job = BatchJob(
            batch_id=batch_id,
            job_ids=job_ids,
            created_at=datetime.now()
        )
        BatchJobService.create(batch_job)
        
        return {
            "batch_id": batch_id,
            "job_ids": job_ids
        }
    except httpx.HTTPError as e:
        backend = app_settings.draw.backend
        raise HTTPException(status_code=502, detail=f"{backend} 连接失败: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/batch", summary="获取批量绘图任务信息")
async def get_batch(batch_id: str) -> List[Job]:
    """
    获取批量绘图任务的所有 job 信息。
    
    Args:
        batch_id: 批次ID（查询参数）
    
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


@router.delete("/batch", summary="删除批量绘图任务")
async def delete_batch(batch_id: str) -> dict:
    """
    删除批量绘图任务及其所有 job。
    
    Args:
        batch_id: 批次ID（查询参数）
    
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



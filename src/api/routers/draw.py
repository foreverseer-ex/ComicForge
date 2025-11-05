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
from api.services.draw.sd_forge import SdForgeDrawService, sd_forge_draw_service
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
    project_id: str,
    model: str,
    prompt: str,
    negative_prompt: str = "",
    loras: Optional[Dict[str, float]] = None,
    styles: Optional[List[str]] = None,
    seed: int = -1,
    sampler_name: str = "DPM++ 2M Karras",
    steps: int = 30,
    cfg_scale: float = 7.0,
    width: int = 1024,
    height: int = 1024,
    clip_skip: Optional[int] = None,
    vae: Optional[str] = None,
) -> Dict[str, str]:
    """
    创建绘图任务（文生图），返回 job_id。
    
    注意：如果使用的是SD-Forge后端，会自动检查并设置model和vae选项。
    
    Args:
        project_id: 项目ID（查询参数）
        model: SD模型名称（查询参数）
        prompt: 正向提示词（查询参数）
        negative_prompt: 负向提示词（查询参数）
        loras: LoRA 配置 {name: weight}（查询参数）
        styles: 样式预设列表（查询参数）
        seed: 随机种子（-1 表示随机，查询参数）
        sampler_name: 采样器名称（查询参数）
        steps: 采样步数（查询参数）
        cfg_scale: CFG Scale（查询参数）
        width: 图像宽度（查询参数）
        height: 图像高度（查询参数）
        clip_skip: CLIP skip（查询参数）
        vae: VAE 模型（查询参数）
    
    Returns:
        包含 job_id 的字典
    
    实现要点：
    - 调用 sd_forge_service.draw()
    - 如果使用SD-Forge后端，会自动检查当前加载的model和vae，如果不同则自动设置
    - 创建 Job 记录到数据库
    """
    try:
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
            loras=loras or {},
        )
        job_id = sd_forge_draw_service.draw(args)
        
        # 创建 Job 记录到数据库
        from datetime import datetime
        job = Job(
            job_id=job_id,
            created_at=datetime.now()
        )
        JobService.create(job)
        
        return {"job_id": job_id}
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"SD-Forge 连接失败: {e}") from e
    except Exception as e:
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


# ==================== Batch 管理 ====================

@router.post("/batch", summary="创建批量绘图任务")
async def create_batch(
    project_id: str,
    batch_size: int,
    model: str,
    prompt: str,
    negative_prompt: str = "",
    loras: Optional[Dict[str, float]] = None,
    styles: Optional[List[str]] = None,
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
        project_id: 项目ID（查询参数）
        batch_size: 批量大小（查询参数）
        model: SD模型名称（查询参数）
        prompt: 正向提示词（查询参数）
        negative_prompt: 负向提示词（查询参数）
        loras: LoRA 配置 {name: weight}（查询参数）
        styles: 样式预设列表（查询参数）
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
        from datetime import datetime
        
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
            loras=loras or {},
        )
        
        # 生成 batch_id
        batch_id = str(uuid.uuid4())
        job_ids = []
        
        # 创建多个任务
        for i in range(batch_size):
            job_id = sd_forge_draw_service.draw(args)
            job_ids.append(job_id)
            
            # 创建 Job 记录到数据库
            job = Job(
                job_id=job_id,
                created_at=datetime.now()
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
        raise HTTPException(status_code=502, detail=f"SD-Forge 连接失败: {e}") from e
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

"""
Actor 管理的路由。

Actor 可以是角色、地点、组织等小说要素。
提供 CRUD 操作、示例图管理和预定义标签查询。
"""
import uuid
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from loguru import logger
from pydantic import BaseModel
import asyncio

from api.schemas.actor import Actor, ActorExample
from api.schemas.draw import DrawArgs, Job
from api.constants.actor import character_tags_description
from api.services.db import ActorService
from api.services.draw.sd_forge import sd_forge_draw_service
from api.utils.path import project_home

router = APIRouter(
    prefix="/actor",
    tags=["Actor管理"],
    responses={404: {"description": "Actor不存在"}},
)


# ==================== Actor 基本操作 ====================
# 注意：非ID的API（create, list, tag-description等）必须放在路径参数API之前

@router.post("/create", summary="创建Actor")
async def create_actor(
    project_id: str,
    name: str,
    desc: str = "",
    color: str = "#808080",
    tags: Optional[Dict[str, str]] = None
) -> dict:
    """
    创建新 Actor。
    
    Args:
        project_id: 项目ID（查询参数）
        name: 名称
        desc: 描述
        color: 卡片颜色（如 #FF69B4，女性角色建议粉色）
        tags: 标签字典（可选，建议使用 constants.actor.character_tags_description 中定义的键）
    
    Returns:
        创建的 Actor ID（actor_id）
    """
    # 生成唯一 Actor ID
    actor_id = str(uuid.uuid4())
    
    # 创建 Actor 对象
    actor = Actor(
        actor_id=actor_id,
        project_id=project_id,
        name=name,
        desc=desc,
        color=color,
        tags=tags or {},
        examples=[]
    )
    
    # 保存到数据库
    ActorService.create(actor)
    logger.info(f"创建 Actor: {name} (project: {project_id})")
    
    return {"actor_id": actor_id}


@router.get("/list", response_model=List[Actor], summary="列出所有Actor")
async def list_actors(
    project_id: str,
    limit: int = 100,
    offset: int = 0
) -> List[Actor]:
    """
    列出项目的所有 Actor，支持分页。
    
    Args:
        project_id: 项目ID（查询参数）
        limit: 返回数量限制（默认100，最大1000）
        offset: 偏移量（默认0）
    
    Returns:
        Actor 列表
    """
    # 获取项目的所有 Actor
    actors = ActorService.list_by_session(project_id, limit=limit)
    
    # 应用偏移量（简单的内存分页）
    return actors[offset:offset + limit]


# ==================== 预定义标签查询 ====================
# 注意：这些路由必须在 /{actor_id} 之前定义，避免路径冲突

@router.get("/tag-description", summary="获取预定义标签的描述")
async def get_tag_description(
    tag: str
) -> Dict[str, str]:
    """
    获取预定义标签的描述。
    
    Args:
        tag: 标签名（查询参数）
    
    Returns:
        包含标签和描述的字典 {"tag": "...", "description": "..."}
    
    Raises:
        404: 标签名不在预定义列表中
    """
    if tag not in character_tags_description:
        raise HTTPException(status_code=404, detail=f"标签名 '{tag}' 不在预定义列表中")
    
    return {
        "tag": tag,
        "description": character_tags_description[tag]
    }


@router.get("/tag-descriptions", summary="获取所有预定义标签和描述")
async def get_all_tag_descriptions() -> Dict[str, str]:
    """
    获取所有预定义的 Actor 标签和描述。
    
    Returns:
        所有预定义的标签字典
    """
    return character_tags_description


# ==================== 基于ID的CRUD操作 ====================
# 注意：ID参数通过路径参数传递，权限验证在服务层进行

@router.get("/{actor_id}", response_model=Actor, summary="获取Actor信息")
async def get_actor(actor_id: str) -> Actor:
    """
    获取 Actor 详细信息。
    
    Args:
        actor_id: Actor ID（路径参数）
    
    Returns:
        Actor 对象
    
    Raises:
        404: Actor 不存在
    """
    actor = ActorService.get(actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail=f"Actor 不存在: {actor_id}")
    
    return actor


class ActorUpdateRequest(BaseModel):
    """Actor 更新请求"""
    name: Optional[str] = None
    desc: Optional[str] = None
    color: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


@router.put("/{actor_id}", response_model=Actor, summary="更新Actor")
async def update_actor(
    actor_id: str,
    request: ActorUpdateRequest
) -> Actor:
    """
    更新 Actor 信息。
    
    Args:
        actor_id: Actor ID（路径参数）
        request: 更新请求体
    
    Returns:
        更新后的 Actor 对象
    
    Raises:
        404: Actor 不存在
    """
    # 检查 Actor 是否存在
    actor = ActorService.get(actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail=f"Actor 不存在: {actor_id}")
    
    # 构建更新字典
    update_data = {}
    if request.name is not None:
        update_data["name"] = request.name
    if request.desc is not None:
        update_data["desc"] = request.desc
    if request.color is not None:
        update_data["color"] = request.color
    if request.tags is not None:
        update_data["tags"] = request.tags
    
    # 更新 Actor
    updated_actor = ActorService.update(actor_id, **update_data)
    if not updated_actor:
        raise HTTPException(status_code=404, detail=f"Actor 不存在: {actor_id}")
    
    return updated_actor


@router.delete("/{actor_id}", summary="删除Actor")
async def remove_actor(actor_id: str) -> dict:
    """
    删除 Actor。
    
    Args:
        actor_id: Actor ID（路径参数）
    
    Returns:
        删除的 Actor ID
    
    Raises:
        404: Actor 不存在
    """
    # 检查 Actor 是否存在
    actor = ActorService.get(actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail=f"Actor 不存在: {actor_id}")
    
    # 删除 Actor
    success = ActorService.delete(actor_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Actor 不存在: {actor_id}")
    
    logger.info(f"删除 Actor: {actor_id} (project: {actor.project_id})")
    return {"actor_id": actor_id}


# ==================== 示例图管理 ====================

@router.post("/{actor_id}/example", response_model=Actor, summary="添加示例图")
async def add_example(
    actor_id: str,
    project_id: str,
    title: str,
    desc: str,
    image_path: str,
    # DrawArgs 参数
    model: str,
    prompt: str,
    negative_prompt: str = "",
    steps: int = 20,
    cfg_scale: float = 7.0,
    sampler: str = "Euler a",
    seed: int = -1,
    width: int = 512,
    height: int = 512,
    clip_skip: Optional[int] = 2,
    vae: Optional[str] = None,
    loras: Optional[Dict[str, float]] = None
) -> Actor:
    """
    为 Actor 添加示例图。
    
    Args:
        actor_id: Actor ID（路径参数）
        project_id: 项目ID（查询参数，用于权限校验）
        title: 示例标题
        desc: 示例说明
        image_path: 图片相对路径
        model: 模型名称
        prompt: 正面提示词
        negative_prompt: 负面提示词
        steps: 采样步数
        cfg_scale: CFG 权重
        sampler: 采样器
        seed: 随机种子
        width: 图片宽度
        height: 图片高度
        clip_skip: CLIP skip
        vae: VAE 模型
        loras: LoRA 字典
    
    Returns:
        更新后的 Actor 对象
    
    Raises:
        404: Actor 不存在或不属于该项目
    """
    # 权限校验
    actor = ActorService.get(actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail=f"Actor 不存在: {actor_id}")
    if actor.project_id != project_id:
        raise HTTPException(status_code=403, detail=f"Actor 不属于该项目: {project_id}")
    
    # 构建 DrawArgs
    draw_args = DrawArgs(
        model=model,
        prompt=prompt,
        negative_prompt=negative_prompt,
        steps=steps,
        cfg_scale=cfg_scale,
        sampler=sampler,
        seed=seed,
        width=width,
        height=height,
        clip_skip=clip_skip,
        vae=vae,
        loras=loras
    )
    
    # 构建 ActorExample
    example = ActorExample(
        title=title,
        desc=desc,
        draw_args=draw_args,
        image_path=image_path
    )
    
    # 添加示例
    updated = ActorService.add_example(actor_id, example)
    if not updated:
        raise HTTPException(status_code=500, detail=f"添加示例失败: {actor_id}")
    
    logger.success(f"为 Actor 添加示例成功: {actor_id}, title={title}")
    return updated


@router.delete("/{actor_id}/example", response_model=Actor, summary="删除示例图")
async def remove_example(
    actor_id: str,
    example_index: int,
    project_id: Optional[str] = None
) -> Actor:
    """
    删除 Actor 的指定示例图。
    
    Args:
        actor_id: Actor ID（路径参数）
        example_index: 示例图索引（查询参数）
        project_id: 项目ID（查询参数，可选，用于权限校验）
    
    Returns:
        更新后的 Actor 对象
    
    Raises:
        404: Actor 不存在
        403: Actor 不属于该项目（如果提供了project_id）
    """
    # 权限校验
    actor = ActorService.get(actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail=f"Actor 不存在: {actor_id}")
    if project_id and actor.project_id != project_id:
        raise HTTPException(status_code=403, detail=f"Actor 不属于该项目: {project_id}")
    
    # 删除示例
    updated = ActorService.remove_example(actor_id, example_index)
    if not updated:
        raise HTTPException(status_code=500, detail=f"删除示例失败: {actor_id}, index={example_index}")
    
    logger.success(f"删除 Actor 示例成功: {actor_id}, index={example_index}")
    return updated


# ==================== 立绘生成 ====================

async def _monitor_job_and_add_portrait(
    job_id: str,
    actor_id: str,
    project_id: str,
    title: str,
    desc: str,
    draw_args: DrawArgs
):
    """
    监控 job 状态，完成后添加立绘到 Actor。
    
    这是一个后台任务函数，会轮询检查 job 状态，直到完成。
    """
    max_attempts = 300  # 最多尝试 300 次（5分钟，每秒一次）
    attempt = 0
    
    while attempt < max_attempts:
        try:
            # 检查 job 状态
            if sd_forge_draw_service.get_job_status(job_id):
                # Job 已完成，保存图片并添加到 Actor
                actor = ActorService.get(actor_id)
                if not actor:
                    logger.error(f"监控任务失败: Actor 不存在 {actor_id}")
                    return
                
                # 保存图片到 projects/{project_id}/actors/{actor_id}/{title}.png
                out_dir: Path = project_home / project_id / "actors" / actor_id
                out_dir.mkdir(parents=True, exist_ok=True)
                
                # 确保文件名安全（移除特殊字符）
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                if not safe_title:
                    safe_title = "portrait"
                filename = f"{safe_title}.png"
                out_path = out_dir / filename
                
                # 如果文件已存在，添加时间戳
                if out_path.exists():
                    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
                    filename = f"{safe_title}-{ts}.png"
                    out_path = out_dir / filename
                
                # 保存图片
                sd_forge_draw_service.save_image(job_id, out_path)
                
                # 生成相对路径（相对 projects 根）
                rel_path = out_path.relative_to(project_home).as_posix()
                
                # 创建 ActorExample
                example = ActorExample(
                    title=title,
                    desc=desc,
                    draw_args=draw_args,
                    image_path=rel_path,
                )
                
                # 添加到 Actor
                updated = ActorService.add_example(actor_id, example)
                if updated:
                    logger.success(f"监控任务完成: 为 Actor {actor.name} 添加立绘成功, title={title}, file={rel_path}")
                else:
                    logger.error(f"监控任务失败: 添加立绘示例失败 {actor_id}")
                return
            
            # Job 未完成，等待 1 秒后重试
            await asyncio.sleep(1)
            attempt += 1
            
        except Exception as e:
            logger.exception(f"监控任务出错 (attempt {attempt}): {e}")
            await asyncio.sleep(1)
            attempt += 1
    
    # 超时
    logger.error(f"监控任务超时: job_id={job_id}, actor_id={actor_id}")


@router.post("/{actor_id}/add_portrait_from_job", summary="从 job_id 添加立绘到 Actor")
async def add_portrait_from_job(
    actor_id: str,
    project_id: str,
    job_id: str,
    title: str,
    background_tasks: BackgroundTasks,
    desc: str = "",
) -> Dict[str, Any]:
    """
    从已存在的 job_id 添加立绘到 Actor。
    
    此函数会：
    1. 校验 Actor 归属
    2. 启动后台任务监控 job 状态
    3. 当 job 完成时，保存图片并添加到 Actor.examples
    
    Args:
        actor_id: Actor ID（路径参数）
        project_id: 项目ID（查询参数，用于权限校验）
        job_id: 绘图任务 ID（查询参数）
        title: 立绘标题（会用作文件名，即 {title}.png）
        desc: 立绘说明/描述
        background_tasks: FastAPI 后台任务管理器
    
    Returns:
        包含 job_id、actor_id、title 的字典
    
    Raises:
        404: Actor 不存在或 job 不存在
        403: Actor 不属于该项目
    """
    # 校验 actor 归属
    actor = ActorService.get(actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail=f"Actor 不存在: {actor_id}")
    if actor.project_id != project_id:
        raise HTTPException(status_code=403, detail=f"Actor 不属于该项目: {project_id}")
    
    # 检查 job 是否存在
    from api.services.db import JobService
    job = JobService.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"任务不存在: {job_id}")
    
    # 获取 job 的 draw_args（需要从 job 中获取，这里简化处理，假设可以从 job 中获取）
    # 注意：当前 Job 模型中没有存储 draw_args，这里需要后续扩展
    # 暂时使用一个空的 DrawArgs，实际使用时需要存储 draw_args
    draw_args = DrawArgs(
        model="",  # 需要从 job 中获取
        prompt="",  # 需要从 job 中获取
        negative_prompt="",
        steps=30,
        cfg_scale=7.0,
        sampler="DPM++ 2M Karras",
        seed=-1,
        width=1024,
        height=1024,
        clip_skip=None,
        vae=None,
        loras=None,
    )
    
    # 启动后台任务监控 job 状态
    background_tasks.add_task(
        _monitor_job_and_add_portrait,
        job_id=job_id,
        actor_id=actor_id,
        project_id=project_id,
        title=title,
        desc=desc,
        draw_args=draw_args
    )
    
    logger.info(f"已启动监控任务: job_id={job_id}, actor_id={actor_id}, title={title}")
    return {
        "job_id": job_id,
        "actor_id": actor_id,
        "title": title,
        "message": f"已启动监控任务，立绘将在 job 完成后自动添加到角色 {actor.name}"
    }
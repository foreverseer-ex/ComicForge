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
from api.utils.path import project_home, jobs_home

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


@router.get("/all", response_model=List[Actor], summary="列出所有Actor")
async def get_all_actors(
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
    
    # 在删除数据库记录前，先删除所有示例图的图片文件
    if actor.examples:
        for example in actor.examples:
            image_path = example.get('image_path')
            if image_path:
                try:
                    # 图片文件路径：projects/{project_id}/actor/{filename}
                    image_file_path = project_home / actor.project_id / "actor" / image_path
                    if image_file_path.exists():
                        image_file_path.unlink()
                        logger.info(f"已删除角色示例图文件: {image_file_path}")
                    else:
                        logger.warning(f"角色示例图文件不存在: {image_file_path}")
                except Exception as e:
                    logger.exception(f"删除角色示例图文件失败: {image_file_path}, 错误: {e}")
                    # 即使删除文件失败，也继续删除数据库记录
    
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
    
    # 在删除数据库记录前，先删除图片文件
    if 0 <= example_index < len(actor.examples):
        example = actor.examples[example_index]
        image_path = example.get('image_path')
        
        # 如果存在图片文件，删除它
        if image_path:
            try:
                # 图片文件路径：projects/{project_id}/actor/{filename}
                image_file_path = project_home / actor.project_id / "actor" / image_path
                if image_file_path.exists():
                    image_file_path.unlink()
                    logger.info(f"已删除示例图文件: {image_file_path}")
                else:
                    logger.warning(f"示例图文件不存在: {image_file_path}")
            except Exception as e:
                logger.exception(f"删除示例图文件失败: {image_file_path}, 错误: {e}")
                # 即使删除文件失败，也继续删除数据库记录
    
    # 删除数据库记录
    updated = ActorService.remove_example(actor_id, example_index)
    if not updated:
        raise HTTPException(status_code=500, detail=f"删除示例失败: {actor_id}, index={example_index}")
    
    logger.success(f"删除 Actor 示例成功: {actor_id}, index={example_index}")
    return updated


@router.post("/{actor_id}/example/swap", response_model=Actor, summary="交换示例图位置")
async def swap_examples(
    actor_id: str,
    index1: int,
    index2: int,
    project_id: Optional[str] = None
) -> Actor:
    """
    交换两个示例图的位置。
    
    Args:
        actor_id: Actor ID（路径参数）
        index1: 第一个示例图索引（查询参数）
        index2: 第二个示例图索引（查询参数）
        project_id: 项目ID（查询参数，可选，用于权限校验）
    
    Returns:
        更新后的 Actor 对象
    
    Raises:
        404: Actor 不存在
        403: Actor 不属于该项目（如果提供了project_id）
        400: 索引无效
    """
    # 权限校验
    actor = ActorService.get(actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail=f"Actor 不存在: {actor_id}")
    if project_id and actor.project_id != project_id:
        raise HTTPException(status_code=403, detail=f"Actor 不属于该项目: {project_id}")
    
    # 验证索引
    if index1 == index2:
        # 如果两个索引相同，直接返回，不需要交换
        logger.debug(f"示例图索引相同，无需交换: {actor_id}, index={index1}")
        return actor
    
    if not (0 <= index1 < len(actor.examples) and 0 <= index2 < len(actor.examples)):
        raise HTTPException(
            status_code=400,
            detail=f"示例图索引越界: index1={index1}, index2={index2}, 总数={len(actor.examples)}"
        )
    
    # 交换示例图
    updated = ActorService.swap_examples(actor_id, index1, index2)
    if not updated:
        raise HTTPException(status_code=500, detail=f"交换示例失败: {actor_id}, index1={index1}, index2={index2}")
    
    logger.success(f"交换 Actor 示例成功: {actor_id}, index1={index1}, index2={index2}")
    return updated


# ==================== 立绘生成 ====================

async def _monitor_job_and_add_portrait(
    job_id: str,
    actor_id: str,
    project_id: str,
    title: str,
    desc: str,
    draw_args: DrawArgs,
    example_index: int
):
    """
    监控 job 状态，完成后从 jobs 文件夹复制图片到 actor 文件夹并更新 ActorExample。
    
    这是一个后台任务函数，会轮询检查 job 状态，直到完成或超时。
    如果超时或失败，会删除之前创建的 ActorExample。
    """
    from api.services.db import JobService
    from api.settings import app_settings
    from datetime import datetime
    import shutil
    
    # 根据后端类型设置超时时间
    backend = app_settings.draw.backend
    if backend == "civitai":
        # Civitai 超时时间（秒），从配置中读取
        timeout_seconds = app_settings.civitai.draw_timeout
        max_attempts = int(timeout_seconds)  # 每秒检查一次
    else:
        # SD-Forge 默认超时时间：5分钟
        max_attempts = 300
    
    attempt = 0
    last_error = None
    
    while attempt < max_attempts:
        try:
            # 检查 jobs 文件夹中是否存在图片文件（说明任务已完成）
            job_image_path = jobs_home / f"{job_id}.png"
            
            if job_image_path.exists():
                # 图片已缓存，可以复制到 actor 文件夹
                
                # 设置完成时间（如果未设置）
                job = JobService.get(job_id)
                if job and job.completed_at is None:
                    JobService.update(job_id, completed_at=datetime.now())
                
                # 检查 Actor 是否存在
                actor = ActorService.get(actor_id)
                if not actor:
                    logger.error(f"监控任务失败: Actor 不存在 {actor_id}")
                    # 删除 ActorExample
                    ActorService.remove_example(actor_id, example_index)
                    return
                
                # 验证示例索引是否有效
                if example_index >= len(actor.examples):
                    logger.error(f"监控任务失败: 示例索引越界 {actor_id}, index={example_index}")
                    return
                
                # 复制图片到 projects/{project_id}/actor/{filename}.png
                out_dir: Path = project_home / project_id / "actor"
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
                
                # 从 jobs 文件夹复制图片到 actor 文件夹
                shutil.copy2(job_image_path, out_path)
                logger.info(f"已复制任务图像: {job_image_path} -> {out_path}")
                
                # image_path 只保存文件名（不包含路径）
                # 实际文件保存在 projects/{project_id}/actor/{filename}
                
                # 更新 ActorExample 的 image_path（只保存文件名）
                example = ActorExample(
                    title=title,
                    desc=desc,
                    draw_args=draw_args,
                    image_path=filename,  # 只保存文件名
                )
                
                updated = ActorService.update_example(actor_id, example_index, example)
                if updated:
                    logger.success(f"监控任务完成: 为 Actor {actor.name} 更新立绘成功, title={title}, file={filename}")
                else:
                    logger.error(f"监控任务失败: 更新立绘示例失败 {actor_id}")
                return
            
            # 图片文件不存在，等待 1 秒后重试
            await asyncio.sleep(1)
            attempt += 1
            
        except Exception as e:
            logger.exception(f"监控任务出错 (attempt {attempt}): {e}")
            last_error = e
            await asyncio.sleep(1)
            attempt += 1
    
    # 超时或失败，删除 ActorExample
    logger.error(f"监控任务超时/失败: job_id={job_id}, actor_id={actor_id}, attempt={attempt}, error={last_error}")
    try:
        ActorService.remove_example(actor_id, example_index)
        logger.info(f"已删除失败的 ActorExample: {actor_id}, index={example_index}")
    except Exception as e:
        logger.exception(f"删除失败的 ActorExample 时出错: {e}")


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
    
    # 检查 job 是否存在，并获取 draw_args
    from api.services.db import JobService
    job = JobService.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"任务不存在: {job_id}")
    
    # 从 job 中获取 draw_args
    if not job.draw_args:
        raise HTTPException(status_code=400, detail=f"任务没有保存绘图参数: {job_id}")
    
    # 解析 DrawArgs
    draw_args = DrawArgs(**job.draw_args)
    
    # 立即创建 ActorExample（image_path 为 None，表示正在生成中）
    example = ActorExample(
        title=title,
        desc=desc,
        draw_args=draw_args,
        image_path=None  # 正在生成中
    )
    
    # 添加到 Actor
    updated = ActorService.add_example(actor_id, example)
    if not updated:
        raise HTTPException(status_code=500, detail=f"添加示例失败: {actor_id}")
    
    # 获取刚添加的示例的索引（最后一个）
    example_index = len(updated.examples) - 1
    
    # 启动后台任务监控 job 状态
    background_tasks.add_task(
        _monitor_job_and_add_portrait,
        job_id=job_id,
        actor_id=actor_id,
        project_id=project_id,
        title=title,
        desc=desc,
        draw_args=draw_args,
        example_index=example_index  # 传递示例索引
    )
    
    logger.info(f"已启动监控任务: job_id={job_id}, actor_id={actor_id}, title={title}")
    return {
        "job_id": job_id,
        "actor_id": actor_id,
        "title": title,
        "message": f"已启动监控任务，立绘将在 job 完成后自动添加到角色 {actor.name}"
    }


async def add_portrait_from_job_tool(
    actor_id: str,
    project_id: str,
    job_id: str,
    title: str,
    desc: str = "",
) -> Dict[str, Any]:
    """
    从已存在的 job_id 添加立绘到 Actor（工具函数版本，不包含 BackgroundTasks）。
    
    这是 add_portrait_from_job 的工具函数包装版本，移除了 BackgroundTasks 参数，
    直接使用 asyncio 创建后台任务。
    
    Args:
        actor_id: Actor ID
        project_id: 项目ID（用于权限校验）
        job_id: 绘图任务 ID
        title: 立绘标题（会用作文件名，即 {title}.png）
        desc: 立绘说明/描述
    
    Returns:
        包含 job_id、actor_id、title 的字典
    """
    # 校验 actor 归属
    actor = ActorService.get(actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail=f"Actor 不存在: {actor_id}")
    if actor.project_id != project_id:
        raise HTTPException(status_code=403, detail=f"Actor 不属于该项目: {project_id}")
    
    # 检查 job 是否存在，并获取 draw_args
    from api.services.db import JobService
    job = JobService.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"任务不存在: {job_id}")
    
    # 从 job 中获取 draw_args
    if not job.draw_args:
        raise HTTPException(status_code=400, detail=f"任务没有保存绘图参数: {job_id}")
    
    # 解析 DrawArgs
    draw_args = DrawArgs(**job.draw_args)
    
    # 立即创建 ActorExample（image_path 为 None，表示正在生成中）
    example = ActorExample(
        title=title,
        desc=desc,
        draw_args=draw_args,
        image_path=None  # 正在生成中
    )
    
    # 添加到 Actor
    updated = ActorService.add_example(actor_id, example)
    if not updated:
        raise HTTPException(status_code=500, detail=f"添加示例失败: {actor_id}")
    
    # 获取刚添加的示例的索引（最后一个）
    example_index = len(updated.examples) - 1
    
    # 使用 asyncio 创建后台任务（不依赖 FastAPI 的 BackgroundTasks）
    asyncio.create_task(
        _monitor_job_and_add_portrait(
            job_id=job_id,
            actor_id=actor_id,
            project_id=project_id,
            title=title,
            desc=desc,
            draw_args=draw_args,
            example_index=example_index
        )
    )
    
    logger.info(f"已启动监控任务: job_id={job_id}, actor_id={actor_id}, title={title}")
    return {
        "job_id": job_id,
        "actor_id": actor_id,
        "title": title,
        "message": f"已启动监控任务，立绘将在 job 完成后自动添加到角色 {actor.name}"
    }
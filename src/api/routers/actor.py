"""
Actor 管理的路由。

Actor 可以是角色、地点、组织等小说要素。
提供 CRUD 操作、示例图管理和预定义标签查询。
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel
import asyncio

from api.schemas.actor import Actor
from api.schemas.draw import Example
from api.schemas.draw import DrawArgs, Job
from api.constants.actor import character_tags_description
from api.services.db import ActorService
from api.services.db.base import normalize_project_id
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
    project_id: Optional[str] = None,
    name: str = "",
    desc: str = "",
    color: str = "#808080",
    tags: Optional[Dict[str, str]] = None
) -> str:
    """
    创建新 Actor。
    
    Args:
        project_id: 项目ID（查询参数，None 表示默认工作空间）
        name: 名称
        desc: 描述
        color: 卡片颜色（如 #FF69B4，女性角色建议粉色）
        tags: 标签字典（可选，建议使用 constants.actor.character_tags_description 中定义的键）
    
    Returns:
        创建的 Actor ID（actor_id）字符串
    """
    project_id = normalize_project_id(project_id)
    # 创建 Actor 对象（ID 会自动生成）
    actor = Actor(
        project_id=project_id,
        name=name,
        desc=desc,
        color=color,
        tags=tags or {},
        examples=[]
    )
    
    # 保存到数据库
    actor = ActorService.create(actor)
    logger.info(f"创建 Actor: {name} (project: {project_id}, actor_id: {actor.actor_id})")
    
    return actor.actor_id


@router.get("/all", response_model=List[Actor], summary="列出所有Actor")
async def get_all_actors(
    project_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Actor]:
    """
    列出项目的所有 Actor，支持分页。
    
    """
    project_id = normalize_project_id(project_id)
    return ActorService.list_by_session(project_id, limit=limit, offset=offset)


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
            filename = example.get('filename')
            if filename:
                try:
                    # 图片文件路径：projects/{project_id}/actors/{actor_name}/{filename}
                    # 如果 project_id 为 None，使用 "default" 作为目录名
                    actual_project_id = actor.project_id if actor.project_id is not None else "default"
                    image_file_path = project_home / actual_project_id / "actors" / actor.name / filename
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
    # 支持 project_id=None（默认工作空间）
    if (project_id is None and actor.project_id is not None) or (project_id is not None and actor.project_id != project_id):
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
    
    # 构建 Example
    # 文件名需要在调用时提供，这里使用 image_path 作为 filename
    example = Example(
        title=title,
        desc=desc,
        draw_args=draw_args,
        filename=image_path,
        extra={}
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
    
    # 验证索引
    if not (0 <= example_index < len(actor.examples)):
        raise HTTPException(
            status_code=400,
            detail=f"示例图索引越界: index={example_index}, 总数={len(actor.examples)}"
        )
    
    # 记录删除前的状态（用于调试）
    logger.debug(f"[Router] 删除前 examples 列表: {[ex.get('title', '未命名') for ex in actor.examples]}")
    logger.debug(f"[Router] 要删除的索引: {example_index}, 对应的标题: {actor.examples[example_index].get('title', '未命名')}")
    
    # 在删除数据库记录前，先删除图片文件
    # 注意：必须在删除数据库记录之前获取要删除的示例信息
    example = actor.examples[example_index]
    filename = example.get('filename')
    
    # 如果存在图片文件，删除它
    if filename:
        try:
            # 图片文件路径：projects/{project_id}/actors/{actor_name}/{filename}
            # 如果 project_id 为 None，使用 "default" 作为目录名
            actual_project_id = actor.project_id if actor.project_id is not None else "default"
            image_file_path = project_home / actual_project_id / "actors" / actor.name / filename
            if image_file_path.exists():
                image_file_path.unlink()
                logger.info(f"已删除示例图文件: {image_file_path}")
            else:
                logger.warning(f"示例图文件不存在: {image_file_path}")
        except Exception as e:
            logger.exception(f"删除示例图文件失败: {image_file_path}, 错误: {e}")
            # 即使删除文件失败，也继续删除数据库记录
    
    # 删除数据库记录（重新获取 actor 以确保数据是最新的）
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


@router.delete("/{actor_id}/examples/clear", response_model=Actor, summary="清空所有示例图")
async def clear_examples(
    actor_id: str,
    project_id: Optional[str] = None
) -> Actor:
    """
    清空 Actor 的所有示例图。
    
    Args:
        actor_id: Actor ID（路径参数）
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
    
    # 在清空数据库记录前，先删除所有示例图的图片文件
    if actor.examples:
        for example in actor.examples:
            filename = example.get('filename')
            if filename:
                try:
                    # 图片文件路径：projects/{project_id}/actors/{actor_name}/{filename}
                    # 如果 project_id 为 None，使用 "default" 作为目录名
                    actual_project_id = actor.project_id if actor.project_id is not None else "default"
                    image_file_path = project_home / actual_project_id / "actors" / actor.name / filename
                    if image_file_path.exists():
                        image_file_path.unlink()
                        logger.info(f"已删除示例图文件: {image_file_path}")
                    else:
                        logger.warning(f"示例图文件不存在: {image_file_path}")
                except Exception as e:
                    logger.exception(f"删除示例图文件失败: {image_file_path}, 错误: {e}")
                    # 即使删除文件失败，也继续清空数据库记录
    
    # 清空数据库记录
    updated = ActorService.clear_examples(actor_id)
    if not updated:
        raise HTTPException(status_code=500, detail=f"清空示例失败: {actor_id}")
    
    logger.success(f"清空 Actor 所有示例成功: {actor_id}")
    return updated


@router.post("/{actor_id}/examples/batch-remove", response_model=Actor, summary="批量删除示例图")
async def batch_remove_examples(
    actor_id: str,
    example_indices: list[int],
    project_id: Optional[str] = None
) -> Actor:
    """
    批量删除 Actor 的示例图。
    
    Args:
        actor_id: Actor ID（路径参数）
        example_indices: 要删除的示例图索引列表（请求体）
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
    
    if not actor.examples:
        logger.debug(f"Actor 没有示例图，无需删除: {actor_id}")
        return actor
    
    # 验证索引有效性
    valid_indices = [idx for idx in example_indices if 0 <= idx < len(actor.examples)]
    if not valid_indices:
        raise HTTPException(
            status_code=400,
            detail=f"没有有效的示例图索引: indices={example_indices}, 总数={len(actor.examples)}"
        )
    
    # 在删除数据库记录前，先删除所有要删除的示例图的图片文件
    for idx in valid_indices:
        example = actor.examples[idx]
        filename = example.get('filename')
        if filename:
            try:
                # 图片文件路径：projects/{project_id}/actors/{actor_name}/{filename}
                # 如果 project_id 为 None，使用 "default" 作为目录名
                actual_project_id = actor.project_id if actor.project_id is not None else "default"
                image_file_path = project_home / actual_project_id / "actors" / actor.name / filename
                if image_file_path.exists():
                    image_file_path.unlink()
                    logger.info(f"已删除示例图文件: {image_file_path}")
                else:
                    logger.warning(f"示例图文件不存在: {image_file_path}")
            except Exception as e:
                logger.exception(f"删除示例图文件失败: {image_file_path}, 错误: {e}")
                # 即使删除文件失败，也继续删除数据库记录
    
    # 批量删除数据库记录
    updated = ActorService.batch_remove_examples(actor_id, valid_indices)
    if not updated:
        raise HTTPException(status_code=500, detail=f"批量删除示例失败: {actor_id}, indices={valid_indices}")
    
    logger.success(f"批量删除 Actor 示例成功: {actor_id}, 删除了 {len(valid_indices)} 个示例")
    return updated


# ==================== 立绘生成 ====================

async def _monitor_single_job_and_update_portrait(
    job_id: str,
    actor_id: str,
    project_id: Optional[str],
    title: str,
    desc: str,
    draw_args: DrawArgs,
    example_index: int
):
    """
    监控单个 job 状态，完成后更新对应的 ActorExample。
    
    这是一个后台任务函数，会轮询检查 job 状态，直到完成或超时。
    如果超时或失败，会删除对应的 ActorExample。
    
    Args:
        job_id: 要监控的 job ID
        actor_id: Actor ID
        project_id: 项目 ID
        title: 立绘标题
        desc: 立绘描述
        draw_args: 绘图参数
        example_index: 要更新的 example 索引
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
            # 检查 job 状态，而不是文件是否存在
            # 只有当 job.status == "completed" 时，才说明文件已经完全写入
            job = JobService.get(job_id)
            if not job:
                logger.error(f"监控任务失败: Job 不存在 {job_id}")
                try:
                    ActorService.remove_example(actor_id, example_index)
                except Exception:
                    pass
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
                
                # 检查 Actor 是否存在
                actor = ActorService.get(actor_id)
                if not actor:
                    logger.error(f"监控任务失败: Actor 不存在 {actor_id}")
                    try:
                        ActorService.remove_example(actor_id, example_index)
                    except Exception:
                        pass
                    return
                
                # 复制图片到 projects/{project_id}/actors/{actor_name}/{filename}.png
                # 如果 project_id 为 None，使用 "default" 作为目录名
                actual_project_id = project_id if project_id is not None else "default"
                out_dir: Path = project_home / actual_project_id / "actors" / actor.name
                out_dir.mkdir(parents=True, exist_ok=True)
                
                # 获取 job 名称（如果不存在则使用默认值）
                job_name = job.name if job and job.name else "portrait"
                
                # 确保文件名安全（移除特殊字符，只保留字母数字、空格、连字符和下划线）
                safe_job_name = "".join(c for c in job_name if c.isalnum() or c in (' ', '-', '_')).strip()
                if not safe_job_name:
                    safe_job_name = "portrait"
                
                # 生成时间戳（格式：YYYYMMDDHHMMSS，例如：20231201123453）
                ts = datetime.now().strftime("%Y%m%d%H%M%S")
                
                # 为了确保文件名唯一性，添加 job_id 的前8位（即使 job 名称和时间戳相同，job_id 也不同）
                job_id_short = job_id[:8]
                
                # 文件名格式：{job名称}_{时间字符串}_{job_id前8位}.png
                filename = f"{safe_job_name}_{ts}_{job_id_short}.png"
                out_path = out_dir / filename
                
                # 从 jobs 文件夹复制图片到 actors 文件夹
                shutil.copy2(job_image_path, out_path)
                logger.info(f"已复制任务图像: {job_image_path} -> {out_path}")
                
                # 如果 title 为空或为 'portrait'，且 job.name 存在，使用 job.name
                # 如果 desc 为空，且 job.desc 存在，使用 job.desc
                final_title = title
                if (not final_title or final_title.strip() == '' or final_title == 'portrait') and job.name:
                    final_title = job.name
                elif not final_title or final_title.strip() == '':
                    final_title = 'portrait'
                
                final_desc = desc
                if (not final_desc or final_desc.strip() == '') and job.desc:
                    final_desc = job.desc
                
                # 更新对应的 Example（使用最终的 title 和 desc）
                example = Example(
                    title=final_title,
                    desc=final_desc,
                    draw_args=draw_args,
                    filename=filename,
                    extra={"job_id": job_id}  # 保存 job_id 到 extra
                )
                
                updated = ActorService.update_example(actor_id, example_index, example)
                if updated:
                    logger.success(f"监控任务完成: 为 Actor {actor.name} 更新立绘成功, title={final_title}, file={filename}, job_id={job_id}, example_index={example_index}")
                else:
                    logger.error(f"监控任务失败: 更新立绘示例失败 {actor_id}, example_index={example_index}")
                
                return  # 成功完成，退出循环
            
            # Job 未完成，等待 1 秒后重试
            await asyncio.sleep(1)
            attempt += 1
            
        except Exception as e:
            logger.exception(f"监控任务出错 (attempt {attempt}): {e}")
            last_error = e
            await asyncio.sleep(1)
            attempt += 1
    
    # 超时或失败，删除对应的 ActorExample
    logger.error(f"监控任务超时/失败: job_id={job_id}, actor_id={actor_id}, example_index={example_index}, attempt={attempt}, error={last_error}")
    try:
        ActorService.remove_example(actor_id, example_index)
        logger.info(f"已删除失败的 ActorExample: {actor_id}, index={example_index}")
    except Exception as e:
        logger.exception(f"删除失败的 ActorExample 时出错: {e}")


@router.post("/{actor_id}/add_portrait_from_batch", summary="从 batch_id 添加立绘到 Actor")
async def add_portrait_from_batch(
    actor_id: str,
    batch_id: str = Query(..., description="批量绘图任务 ID"),
    title: str = Query(..., description="立绘标题"),
    desc: str = Query("", description="立绘说明/描述"),
    project_id: Optional[str] = Query(None, description="项目ID（None 表示默认工作空间，用于权限校验）"),
) -> Dict[str, Any]:
    """
    从已存在的 batch_id 添加立绘到 Actor。
    
    此函数会：
    1. 校验 Actor 归属
    2. 立即创建 N 个 placeholder Example（N = batch 中的 job 数量）
    3. 为每个 job 启动独立的监控任务，当 job 完成时更新对应的 Example
    
    Args:
        actor_id: Actor ID（路径参数）
        project_id: 项目ID（查询参数，None 表示默认工作空间，用于权限校验）
        batch_id: 批量绘图任务 ID（查询参数）
        title: 立绘标题
        desc: 立绘说明/描述
    
    Returns:
        包含 batch_id、actor_id、title 的字典
    
    Raises:
        404: Actor 不存在或 batch 不存在
        403: Actor 不属于该项目
    
    Note:
        图片文件名格式为：{job名称}_{时间字符串}_{job_id前8位}.png（例如：角色立绘-南云_20231201123453_abc12345.png）
        会为 batch 中的每个 job 创建独立的监控任务，每个任务负责更新对应的 Example
    """
    project_id = normalize_project_id(project_id)
    # 校验 actor 归属
    actor = ActorService.get(actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail=f"Actor 不存在: {actor_id}")
    # 支持 project_id=None（默认工作空间）
    if (project_id is None and actor.project_id is not None) or (project_id is not None and actor.project_id != project_id):
        raise HTTPException(status_code=403, detail=f"Actor 不属于该项目: {project_id}")
    
    # 检查 batch 是否存在，并获取 draw_args
    from api.services.db import BatchJobService, JobService
    batch_job = BatchJobService.get(batch_id)
    if not batch_job:
        raise HTTPException(status_code=404, detail=f"批量任务不存在: {batch_id}")
    
    if not batch_job.job_ids:
        raise HTTPException(status_code=400, detail=f"批量任务中没有 job: {batch_id}")
    
    # 从第一个 job 中获取 draw_args（所有 job 使用相同的参数）
    first_job_id = batch_job.job_ids[0]
    job = JobService.get(first_job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"任务不存在: {first_job_id}")
    
    # 从 job 中获取 draw_args
    if not job.draw_args:
        raise HTTPException(status_code=400, detail=f"任务没有保存绘图参数: {first_job_id}")
    
    # 解析 DrawArgs
    draw_args = DrawArgs(**job.draw_args)
    
    # 获取 job 列表
    job_ids = batch_job.job_ids
    job_count = len(job_ids)
    
    # 立即创建 N 个 Example（使用临时 filename，表示正在生成中）
    # 每个 example 对应一个 job
    example_indices = []
    for i in range(job_count):
        # 使用临时 filename 占位，实际文件将在 job 完成后生成
        temp_filename = f"generating_{job_ids[i][:8]}.png"
        example = Example(
            title=title,
            desc=desc,
            draw_args=draw_args,
            filename=temp_filename,
            extra={"batch_id": batch_id, "job_id": job_ids[i]}
        )
        
        # 添加到 Actor
        updated = ActorService.add_example(actor_id, example)
        if not updated:
            # 如果添加失败，删除之前已创建的 example
            for idx in example_indices:
                try:
                    ActorService.remove_example(actor_id, idx)
                except Exception:
                    pass
            raise HTTPException(status_code=500, detail=f"添加示例失败: {actor_id}")
        
        # 获取刚添加的示例的索引（最后一个）
        example_index = len(updated.examples) - 1
        example_indices.append(example_index)
    
    # 为每个 job 启动独立的监控任务
    for i, job_id in enumerate(job_ids):
        asyncio.create_task(
            _monitor_single_job_and_update_portrait(
                job_id=job_id,
                actor_id=actor_id,
                project_id=project_id,
                title=title,
                desc=desc,
                draw_args=draw_args,
                example_index=example_indices[i]  # 每个 job 对应一个 example index
            )
        )
    
    logger.info(f"已启动 {job_count} 个监控任务: batch_id={batch_id}, actor_id={actor_id}, title={title}, job_count={job_count}")
    return {
        "batch_id": batch_id,
        "actor_id": actor_id,
        "title": title,
        "job_count": job_count,
        "message": f"已启动 {job_count} 个监控任务，立绘将在 job 完成后自动添加到角色 {actor.name}"
    }


@router.post("/{actor_id}/add_portrait_from_job", summary="从 job_id 添加立绘到 Actor")
async def add_portrait_from_job(
    actor_id: str,
    job_id: str = Query(..., description="绘图任务 ID"),
    title: str = Query(..., description="立绘标题"),
    desc: str = Query("", description="立绘说明/描述"),
    project_id: Optional[str] = Query(None, description="项目ID（None 表示默认工作空间，用于权限校验）"),
) -> Dict[str, Any]:
    """
    从已存在的 job_id 添加立绘到 Actor。
    
    此函数会：
    1. 校验 Actor 归属
    2. 检查 job 状态
    3. 如果 job 已完成（图片已存在），直接添加立绘
    4. 如果 job 未完成，创建 placeholder Example 并启动监控任务
    
    Args:
        actor_id: Actor ID（路径参数）
        project_id: 项目ID（查询参数，用于权限校验）
        job_id: 绘图任务 ID（查询参数）
        title: 立绘标题
        desc: 立绘说明/描述
    
    Returns:
        包含 job_id、actor_id、title 的字典
    
    Raises:
        404: Actor 不存在或 job 不存在
        403: Actor 不属于该项目
        400: job 没有保存绘图参数
    """
    project_id = normalize_project_id(project_id)
    # 校验 actor 归属
    actor = ActorService.get(actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail=f"Actor 不存在: {actor_id}")
    # 支持 project_id=None（默认工作空间）
    if (project_id is None and actor.project_id is not None) or (project_id is not None and actor.project_id != project_id):
        raise HTTPException(status_code=403, detail=f"Actor 不属于该项目: {project_id}")
    
    # 检查 job 是否存在，并获取 draw_args
    from api.services.db import JobService
    from api.utils.path import jobs_home
    
    job = JobService.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"任务不存在: {job_id}")
    
    # 从 job 中获取 draw_args
    if not job.draw_args:
        raise HTTPException(status_code=400, detail=f"任务没有保存绘图参数: {job_id}")
    
    # 解析 DrawArgs
    draw_args = DrawArgs(**job.draw_args)
    
    # 如果 title 为空或为 'portrait'，且 job.name 存在，使用 job.name
    # 如果 desc 为空，且 job.desc 存在，使用 job.desc
    final_title = title
    if (not final_title or final_title.strip() == '' or final_title == 'portrait') and job.name:
        final_title = job.name
    elif not final_title or final_title.strip() == '':
        final_title = 'portrait'
    
    final_desc = desc
    if (not final_desc or final_desc.strip() == '') and job.desc:
        final_desc = job.desc
    
    # 检查 job 是否已完成（图片是否存在）
    job_image_path = jobs_home / f"{job_id}.png"
    job_completed = job_image_path.exists()
    
    if job_completed:
        # Job 已完成，直接添加立绘
        from api.utils.path import project_home
        from datetime import datetime
        import shutil
        
        # 复制图片到 projects/{project_id}/actors/{actor_name}/{filename}.png
        # 如果 project_id 为 None，使用 "default" 作为目录名
        actual_project_id = project_id if project_id is not None else "default"
        out_dir: Path = project_home / actual_project_id / "actors" / actor.name
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取 job 名称（如果不存在则使用默认值）
        job_name = job.name if job.name else "portrait"
        
        # 确保文件名安全（移除特殊字符，只保留字母数字、空格、连字符和下划线）
        safe_job_name = "".join(c for c in job_name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_job_name:
            safe_job_name = "portrait"
        
        # 生成时间戳（格式：YYYYMMDDHHMMSS，例如：20231201123453）
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # 为了确保文件名唯一性，添加 job_id 的前8位
        job_id_short = job_id[:8]
        
        # 文件名格式：{job名称}_{时间字符串}_{job_id前8位}.png
        filename = f"{safe_job_name}_{ts}_{job_id_short}.png"
        out_path = out_dir / filename
        
        # 从 jobs 文件夹复制图片到 actors 文件夹
        shutil.copy2(job_image_path, out_path)
        logger.info(f"已复制任务图像: {job_image_path} -> {out_path}")
        
        # 创建 Example（使用最终的 title 和 desc）
        example = Example(
            title=final_title,
            desc=final_desc,
            draw_args=draw_args,
            filename=filename,
            extra={"job_id": job_id}
        )
        
        # 添加到 Actor
        updated = ActorService.add_example(actor_id, example)
        if not updated:
            raise HTTPException(status_code=500, detail=f"添加示例失败: {actor_id}")
        
        logger.success(f"已从已完成任务添加立绘: actor_id={actor_id}, title={final_title}, file={filename}, job_id={job_id}")
        return {
            "job_id": job_id,
            "actor_id": actor_id,
            "title": final_title,
            "message": f"已成功添加立绘到角色 {actor.name}",
            "completed": True
        }
    else:
        # Job 未完成，创建 placeholder 并启动监控任务
        temp_filename = f"generating_{job_id[:8]}.png"
        example = Example(
            title=final_title,
            desc=final_desc,
            draw_args=draw_args,
            filename=temp_filename,
            extra={"job_id": job_id}
        )
        
        # 添加到 Actor
        updated = ActorService.add_example(actor_id, example)
        if not updated:
            raise HTTPException(status_code=500, detail=f"添加示例失败: {actor_id}")
        
        # 获取刚添加的示例的索引（最后一个）
        example_index = len(updated.examples) - 1
        
        # 启动监控任务（传递最终的 title 和 desc）
        asyncio.create_task(
            _monitor_single_job_and_update_portrait(
                job_id=job_id,
                actor_id=actor_id,
                project_id=project_id,
                title=final_title,
                desc=final_desc,
                draw_args=draw_args,
                example_index=example_index
            )
        )
        
        logger.info(f"已启动监控任务: job_id={job_id}, actor_id={actor_id}, title={final_title}")
        return {
            "job_id": job_id,
            "actor_id": actor_id,
            "title": final_title,
            "message": f"已启动监控任务，立绘将在 job 完成后自动添加到角色 {actor.name}",
            "completed": False
        }


async def add_portrait_from_job_tool(
    actor_id: str,
    job_id: str,
    title: str,
    desc: str = "",
    project_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    从已存在的 job_id 添加立绘到 Actor（工具函数版本）。
    
    这是 add_portrait_from_job 的工具函数包装版本，用于 LLM 工具调用。
    
    此函数会：
    1. 校验 Actor 归属
    2. 检查 job 状态
    3. 如果 job 已完成，直接添加立绘
    4. 如果 job 未完成，创建 placeholder 并启动监控任务
    
    Args:
        actor_id: Actor ID
        job_id: 绘图任务 ID
        title: 立绘标题
        desc: 立绘说明/描述（可选，默认为空字符串）
        project_id: 项目ID（可选，None 表示默认工作空间，用于权限校验）
    
    Returns:
        包含 job_id、actor_id、title 的字典
    """
    # 直接调用原始函数
    return await add_portrait_from_job(
        actor_id=actor_id,
        job_id=job_id,
        title=title,
        desc=desc,
        project_id=project_id
    )


async def add_portrait_from_batch_tool(
    actor_id: str,
    batch_id: str,
    title: str,
    desc: str = "",
    project_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    从已存在的 batch_id 添加立绘到 Actor（工具函数版本）。
    
    这是 add_portrait_from_batch 的工具函数包装版本，使用 asyncio.create_task 来完成后台任务。
    
    此函数会：
    1. 校验 Actor 归属
    2. 立即创建 N 个 placeholder Example（N = batch 中的 job 数量）
    3. 为每个 job 启动独立的监控任务，当 job 完成时更新对应的 Example
    
    Args:
        actor_id: Actor ID
        batch_id: 批量绘图任务 ID
        title: 立绘标题
        desc: 立绘说明/描述（可选，默认为空字符串）
        project_id: 项目ID（可选，None 表示默认工作空间，用于权限校验）
    
    Returns:
        包含 batch_id、actor_id、title 的字典
    """
    project_id = normalize_project_id(project_id)
    # 校验 actor 归属
    actor = ActorService.get(actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail=f"Actor 不存在: {actor_id}")
    if actor.project_id != project_id:
        raise HTTPException(status_code=403, detail=f"Actor 不属于该项目: {project_id}")
    
    # 检查 batch 是否存在，并获取 draw_args
    from api.services.db import BatchJobService, JobService
    batch_job = BatchJobService.get(batch_id)
    if not batch_job:
        raise HTTPException(status_code=404, detail=f"批量任务不存在: {batch_id}")
    
    if not batch_job.job_ids:
        raise HTTPException(status_code=400, detail=f"批量任务中没有 job: {batch_id}")
    
    # 从第一个 job 中获取 draw_args（所有 job 使用相同的参数）
    first_job_id = batch_job.job_ids[0]
    job = JobService.get(first_job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"任务不存在: {first_job_id}")
    
    # 从 job 中获取 draw_args
    if not job.draw_args:
        raise HTTPException(status_code=400, detail=f"任务没有保存绘图参数: {first_job_id}")
    
    # 解析 DrawArgs
    draw_args = DrawArgs(**job.draw_args)
    
    # 获取 job 列表
    job_ids = batch_job.job_ids
    job_count = len(job_ids)
    
    # 立即创建 N 个 ActorExample（image_path 为 None，表示正在生成中）
    # 每个 example 对应一个 job
    example_indices = []
    for i in range(job_count):
        example = ActorExample(
            title=title,
            desc=desc,
            draw_args=draw_args,
            image_path=None  # 正在生成中
        )
        
        # 添加到 Actor
        updated = ActorService.add_example(actor_id, example)
        if not updated:
            # 如果添加失败，删除之前已创建的 example
            for idx in example_indices:
                try:
                    ActorService.remove_example(actor_id, idx)
                except Exception:
                    pass
            raise HTTPException(status_code=500, detail=f"添加示例失败: {actor_id}")
        
        # 获取刚添加的示例的索引（最后一个）
        example_index = len(updated.examples) - 1
        example_indices.append(example_index)
    
    # 为每个 job 启动独立的监控任务
    for i, job_id in enumerate(job_ids):
        asyncio.create_task(
            _monitor_single_job_and_update_portrait(
                job_id=job_id,
                actor_id=actor_id,
                project_id=project_id,
                title=title,
                desc=desc,
                draw_args=draw_args,
                example_index=example_indices[i]  # 每个 job 对应一个 example index
            )
        )
    
    logger.info(f"已启动 {job_count} 个监控任务: batch_id={batch_id}, actor_id={actor_id}, title={title}, job_count={job_count}")
    return {
        "batch_id": batch_id,
        "actor_id": actor_id,
        "title": title,
        "job_count": job_count,
        "message": f"已启动 {job_count} 个监控任务，立绘将在 job 完成后自动添加到角色 {actor.name}"
    }
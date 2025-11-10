"""
管理项目的路由。

每次将小说转换成漫画的任务都是一次项目。
维护项目基本信息：项目位置、project_id等。
依赖配置（SD后端、LLM后端）使用 settings 模块。
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from loguru import logger

from api.schemas.project import Project
from api.services.db import ProjectService
from api.services.db.base import normalize_project_id
from api.utils.path import project_home

router = APIRouter(
    prefix="/project",
    tags=["项目管理"],
    responses={404: {"description": "项目不存在"}},
)


# ==================== 项目管理 ====================

@router.post("/create", summary="创建新项目")
async def create_project(
    title: str,
    novel_path: Optional[str] = None
) -> dict:
    """
    创建新的小说转漫画项目。
    
    Args:
        title: 项目标题
        novel_path: 小说文件路径（可选）
    
    Returns:
        创建的项目ID（project_id）
    
    实现要点：
    - 生成唯一 project_id（UUID）
    - 创建项目目录结构
    - 初始化小说信息和状态
    - 如果提供了小说路径，触发小说解析
    - 依赖配置从 settings 模块读取
    """
    # 生成唯一项目ID
    # 创建项目对象（ID 会自动生成）
    project = Project(
        title=title,
        novel_path=novel_path,
        project_path="",  # 先创建空路径，创建后再设置
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    # 保存到数据库
    project = ProjectService.create(project)
    
    # 创建项目路径（使用生成的 project_id）
    project_path = str(project_home / project.project_id)
    project.project_path = project_path
    project = ProjectService.update(project.project_id, project_path=project_path)
    
    logger.info(f"创建项目: {project.project_id}, 标题: {title}")
    
    return {"project_id": project.project_id}


@router.get("/all", response_model=List[Project], summary="列出所有项目")
async def get_all_projects(
    limit: int = 50,
    offset: int = 0,

) -> List[Project]:
    """
    列出所有项目，支持分页。
    
    Args:
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        项目列表
    """
    # 获取所有项目
    projects = ProjectService.get_all(limit=limit, offset=offset)
    

    
    return projects


@router.get("/{project_id}", response_model=Project, summary="获取项目信息")
async def get_project(project_id: str) -> Project:
    """
    获取指定项目的详细信息。
    
    Args:
        project_id: 项目唯一标识
    
    Returns:
        完整的项目对象
    
    Raises:
        NotFoundError: 项目不存在
    """
    project = ProjectService.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
    
    return project


@router.put("/{project_id}", response_model=Project, summary="更新项目")
async def update_project(
    project_id: str,
    title: Optional[str] = None,
    total_lines: Optional[int] = None,
    total_chapters: Optional[int] = None,
    current_line: Optional[int] = None,
    current_chapter: Optional[int] = None,
) -> Project:
    """
    更新项目信息。
    
    Args:
        project_id: 项目ID
        title: 新标题（可选）
        total_lines: 总行数（可选）
        total_chapters: 总章节数（可选）
        current_line: 当前处理行（可选）
        current_chapter: 当前处理章节（可选）
    
    Returns:
        更新后的项目对象
    
    实现要点：
    - 只更新提供的字段
    - 自动更新 updated_at 时间戳
    """
    # 构建更新字典（只包含提供的字段）
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if total_lines is not None:
        update_data["total_lines"] = total_lines
    if total_chapters is not None:
        update_data["total_chapters"] = total_chapters
    if current_line is not None:
        update_data["current_line"] = current_line
    if current_chapter is not None:
        update_data["current_chapter"] = current_chapter
    
    # 自动更新时间戳
    update_data["updated_at"] = datetime.now()
    
    # 更新项目
    updated_project = ProjectService.update(project_id, **update_data)
    if not updated_project:
        raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
    
    return updated_project


@router.delete("/{project_id}", summary="删除项目")
async def delete_project(project_id: str) -> dict:
    """
    删除项目及其所有相关数据。

    Args:
        project_id: 项目ID（路径参数）
    
    Returns:
        删除的项目ID
    
    Raises:
        404: 项目不存在
    
    实现要点：
    - 删除项目记录
    - 可选：删除或归档项目文件
    - 清理关联的记忆、角色、图片等数据
    """
    success = ProjectService.delete(project_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
    
    logger.info(f"删除项目: {project_id}")
    return {"project_id": project_id}




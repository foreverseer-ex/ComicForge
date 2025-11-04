"""
LLM 相关的路由。

提供 LLM 交互过程中需要的辅助功能，如添加选项等。
"""
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from loguru import logger


from api.schemas.desperate.chat import IterationChatMessage, Choice, ImageChoice, TextChoice
from api.services.db.project_service import ProjectService
from api.settings import app_settings


router = APIRouter(
    prefix="/llm",
    tags=["LLM 辅助"],
    responses={404: {"description": "资源不存在"}},
)


# 全局项目选项存储（临时方案，后续可能需要改进）
_session_choices: Dict[str, List[Choice]] = {}


@router.post("/add_choices", summary="添加选项到当前消息")
async def add_choices(
    project_id: str,
    choices: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    为当前项目的最后一条助手消息添加选项。
    
    用于 LLM 工具调用后，添加用户可选的选项：
    - 图像选项：draw/draw_batch 工具调用后，展示生成的图像供用户选择
    - 文字选项：提供快捷回复按钮
    
    Args:
        project_id: 项目ID
        choices: 选项列表，每个选项包含 type 和相关字段
            - 图像选项: {"type": "image", "url": "...", "label": "...", "metadata": {...}}
            - 文字选项: {"type": "text", "text": "...", "label": "..."}
    
    Returns:
        操作结果
    
    示例:
        ```python
        # 图像选项
        add_choices(
            project_id="default",
            choices=[
                {"type": "image", "url": "http://...", "label": "图片1"},
                {"type": "image", "url": "http://...", "label": "图片2"}
            ]
        )
        
        # 文字选项
        add_choices(
            project_id="default",
            choices=[
                {"type": "text", "text": "继续生成", "label": "继续"},
                {"type": "text", "text": "重新生成", "label": "重新"}
            ]
        )
        ```
    """
    # 解析并验证 choices
    parsed_choices: List[Choice] = []
    for choice_data in choices:
        choice_type = choice_data.get("type")
        
        if choice_type == "image":
            parsed_choices.append(ImageChoice(**choice_data))
        elif choice_type == "text":
            parsed_choices.append(TextChoice(**choice_data))
        else:
            raise ValueError(f"不支持的选项类型: {choice_type}")
    
    # 存储到全局字典（临时方案）
    _session_choices[project_id] = parsed_choices
    
    return {
        "success": True,
        "project_id": project_id,
        "choices_count": len(parsed_choices),
        "message": f"已为项目 {project_id} 添加 {len(parsed_choices)} 个选项"
    }


@router.get("/get_choices", summary="获取项目的选项")
async def get_choices(project_id: str) -> Dict[str, Any]:
    """
    获取指定项目的选项。
    
    Args:
        project_id: 项目ID
    
    Returns:
        选项列表
    """
    choices = _session_choices.get(project_id, [])
    return {
        "project_id": project_id,
        "choices": [choice.model_dump() for choice in choices]
    }


@router.delete("/clear_choices", summary="清除项目的选项")
async def clear_choices(project_id: str) -> Dict[str, Any]:
    """
    清除指定项目的选项。
    
    Args:
        project_id: 项目ID
    
    Returns:
        操作结果
    """
    if project_id in _session_choices:
        del _session_choices[project_id]
    
    return {
        "success": True,
        "project_id": project_id,
        "message": f"已清除项目 {project_id} 的选项"
    }


@router.post("/iteration/start", summary="启动迭代模式")
async def start_iteration(
    project_id: str,
    target: str,
    index: int = 0,
    stop: int | None = None,
    step: int = 100,
    summary: str = ""
) -> Dict[str, Any]:
    """
    启动迭代模式。
    
    当LLM判断需要处理全文或大量内容时，应该调用此工具函数。
    
    Args:
        project_id: 项目ID
        target: 迭代目标（如："提取全文角色"、"生成章节摘要"）
        index: 起始索引。全文迭代时设为0，部分迭代时设为起始行号
        stop: 终止条件。如果为None，自动设置为project.total_lines
        step: 迭代步长（默认100行）
        summary: 初始摘要（通常为空字符串）
    
    Returns:
        包含迭代消息ID的字典
    
    示例:
        ```python
        # 全文迭代
        start_iteration(
            project_id="default",
            target="提取全文角色",
            index=0,
            stop=None,  # 自动设置为project.total_lines
            step=100
        )
        
        # 部分迭代
        start_iteration(
            project_id="default",
            target="生成章节摘要",
            index=100,
            stop=500,
            step=50
        )
        ```
    """
    # 如果stop未指定，从project获取total_lines
    if stop is None:
        project = ProjectService.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
        stop = project.total_lines
    
    # 验证参数
    if stop <= index:
        raise HTTPException(
            status_code=400,
            detail=f"参数不合法：stop({stop}) 必须大于 index({index})"
        )
    if step <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"参数不合法：step({step}) 必须大于0"
        )
    
    # 创建迭代消息
    iteration_msg = IterationChatMessage(
        target=target,
        index=index,
        stop=stop,
        step=step,
        summary=summary
    )
    
    # 将迭代消息存储到LlmSettings（全局可访问）
    app_settings.llm.pending_iteration = iteration_msg.model_dump()
    logger.info(f"已启动迭代模式：{target}，范围：{index}-{stop}，步长：{step}")
    
    return {
        "iteration_id": iteration_msg.id,
        "target": target,
        "index": index,
        "stop": stop,
        "step": step,
        "message": f"已启动迭代模式：{target}，将从第{index}行开始，每{step}行处理一次，直到第{stop}行"
    }


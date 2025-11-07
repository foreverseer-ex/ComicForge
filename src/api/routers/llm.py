"""
LLM 相关的路由。

提供 LLM 交互过程中需要的辅助功能，如添加选项等。
"""
import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Body
from loguru import logger

from api.schemas.chat import ChatMessage, ChatIteration
from api.services.db.project_service import ProjectService
from api.services.db import HistoryService
from api.services.llm import get_current_llm_service
from api.schemas.draw import DrawArgs
from api.constants.llm import (
    GENERATE_DRAW_PARAMS_BASE_TEMPLATE,
    GENERATE_DRAW_PARAMS_DESC_SECTION,
    GENERATE_DRAW_PARAMS_NO_DESC,
    GENERATE_DRAW_PARAMS_STEPS_WITHOUT_PROJECT,
    GENERATE_DRAW_PARAMS_STEPS_WITH_PROJECT,
    GENERATE_DRAW_PARAMS_ACTOR_CONTEXT_TEMPLATE
)

router = APIRouter(
    prefix="/llm",
    tags=["LLM 辅助"],
    responses={404: {"description": "资源不存在"}},
)

# 全局项目选项存储（临时方案，后续可能需要改进）
# 存储格式：Dict[str, List[Dict[str, Any]]]
# 每个选项字典格式：
# - 图像选项: {"type": "image", "url": "...", "label": "...", "metadata": {...}}
# - 文字选项: {"type": "text", "text": "...", "label": "..."}
_session_choices: Dict[str, List[Dict[str, Any]]] = {}


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
    # 验证 choices 格式
    validated_choices: List[Dict[str, Any]] = []
    for choice_data in choices:
        choice_type = choice_data.get("type")

        if choice_type == "image":
            # 验证图像选项必需字段
            if "url" not in choice_data:
                raise ValueError("图像选项必须包含 'url' 字段")
            validated_choices.append(choice_data)
        elif choice_type == "text":
            # 验证文字选项必需字段
            if "text" not in choice_data:
                raise ValueError("文字选项必须包含 'text' 字段")
            validated_choices.append(choice_data)
        else:
            raise ValueError(f"不支持的选项类型: {choice_type}")

    # 存储到全局字典（临时方案）
    _session_choices[project_id] = validated_choices

    return {
        "success": True,
        "project_id": project_id,
        "choices_count": len(validated_choices),
        "message": f"已为项目 {project_id} 添加 {len(validated_choices)} 个选项"
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
        "choices": choices
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


@router.post("/invoke", summary="调用 LLM（非流式，用于工具）")
async def chat_invoke(
        message: str,
        project_id: str | None = None,
        output_schema: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """
    调用 LLM 并返回结果（非流式，用于工具调用）。
    
    与 chat_streamed 相比：
    - project_id 是可选的（可以不关联特定项目）
    - 不产生任何 ChatMessage，不读取历史消息或摘要
    - 可以使用工具（但某些工具需要 project_id）
    - 非流式，运行完成后返回结果
    - 可以指定输出 schemas（默认返回文本）
    
    Args:
        message: 用户消息
        project_id: 项目 ID（可选）
        output_schema: 输出模式（可选，JSON Schema 格式，默认返回文本）
    
    Returns:
        包含 LLM 回复内容的字典
        
    示例:
        ```python
        # 基本调用
        chat_invoke(message="请分析这个文本：...")
        
        # 关联项目的调用
        chat_invoke(message="请分析项目的角色", project_id="xxx")
        
        # 指定输出格式
        chat_invoke(
            message="提取关键信息",
            output_schema={
                "type": "object",
                "properties": {
                    "key_points": {"type": "array", "items": {"type": "string"}},
                    "summary": {"type": "string"}
                }
            }
        )
        ```
    """
    try:
        llm_service = get_current_llm_service()
        if not llm_service:
            raise HTTPException(status_code=503, detail="LLM 服务未初始化")

        # 调用 chat_invoke（异步）
        # output_schema 目前暂不支持，传递 None
        # TODO: 实现结构化输出支持
        result = await llm_service.chat_invoke(
            message=message,
            project_id=project_id,
            output_schema=None  # 暂时不支持结构化输出
        )

        return {
            "success": True,
            "content": result,
            "project_id": project_id,
            "message": "LLM 调用成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"调用 LLM 失败: {e}")
        raise HTTPException(status_code=500, detail=f"调用 LLM 失败: {str(e)}")


@router.post("/generate-draw-params", summary="文生图参数生成（使用 LLM）")
async def generate_draw_params(
        name: str = Body(...),
        desc: str | None = Body(None),
        project_id: str | None = Body(None)
) -> Dict[str, Any]:
    """
    使用 LLM 生成文生图参数。
    
    根据任务名称和描述，使用 LLM 生成合适的绘图参数（包括 prompt、negative_prompt、
    model、sampler、steps、cfg_scale、width、height、seed、loras 等）。
    
    LLM 会先查看可用的模型和 LoRA，学习示例图像的生成参数，然后根据任务需求生成参数。
    
    如果提供了 project_id，LLM 可以查询项目中的角色信息，包括已生成的立绘参数，
    以保持前后生成图像的一致性。
    
    Args:
        name: 任务名称（图像名称）
        desc: 任务描述（可选）
        project_id: 项目ID（可选），如果提供，LLM 可以查询角色信息和已生成的立绘参数
    
    Returns:
        生成的绘图参数字典，格式与 DrawArgs 一致
    """
    try:
        llm_service = get_current_llm_service()
        if not llm_service:
            raise HTTPException(status_code=503, detail="LLM 服务未初始化")

        # 构建 LLM 提示消息
        # 注意：DrawArgs 的生成规范已定义在 MCP_TOOLS_GUIDE 中，这里使用模板构建提示词
        desc_section = GENERATE_DRAW_PARAMS_DESC_SECTION.format(desc=desc) if desc else GENERATE_DRAW_PARAMS_NO_DESC
        
        # 根据是否有 project_id 选择不同的步骤说明
        if project_id:
            steps_section = GENERATE_DRAW_PARAMS_STEPS_WITH_PROJECT
            # 添加角色查询要求
            actor_context = GENERATE_DRAW_PARAMS_ACTOR_CONTEXT_TEMPLATE.format(project_id=project_id)
            prompt = GENERATE_DRAW_PARAMS_BASE_TEMPLATE.format(
                name=name,
                desc_section=desc_section,
                steps_section=steps_section
            ) + actor_context
        else:
            steps_section = GENERATE_DRAW_PARAMS_STEPS_WITHOUT_PROJECT
            prompt = GENERATE_DRAW_PARAMS_BASE_TEMPLATE.format(
                name=name,
                desc_section=desc_section,
                steps_section=steps_section
            )

        # 导入 DrawArgs 模型

        # 调用 LLM（异步），使用结构化输出
        result = await llm_service.chat_invoke(
            message=prompt,
            project_id=project_id,  # 传递 project_id，让 LLM 可以查询角色信息
            output_schema=DrawArgs  # 使用 DrawArgs 作为输出 schema
        )

        # 打印原始返回内容用于调试
        logger.info(f"LLM 返回的原始内容（前1000字符）: {result[:1000] if result else '(空)'}")
        logger.info(f"LLM 返回内容长度: {len(result) if result else 0}")

        # 检查是否是错误消息
        if not result or len(result.strip()) == 0:
            logger.error("LLM 返回空内容")
            raise HTTPException(status_code=500, detail="LLM 返回空内容，无法生成参数")

        if result.startswith("错误：") or result.startswith("错误:"):
            logger.error(f"LLM 返回错误: {result}")
            raise HTTPException(status_code=500, detail=result)

        # 解析 JSON 结果（结构化输出应该直接返回 JSON）
        import json
        import re

        # 尝试提取 JSON 部分（可能 LLM 返回了包含其他文本的内容）
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            json_str = json_match.group(0)
            try:
                params = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"解析提取的 JSON 失败: {e}, JSON字符串: {json_str[:500]}")
                raise HTTPException(status_code=500, detail=f"解析 LLM 返回的 JSON 失败: {str(e)}")
        else:
            # 如果没有找到 JSON，尝试直接解析整个结果
            try:
                params = json.loads(result)
            except json.JSONDecodeError as e:
                logger.error(f"解析 LLM 返回的 JSON 失败: {e}, 原始结果: {result[:500]}")
                raise HTTPException(status_code=500, detail=f"LLM 返回的内容不包含有效的 JSON。LLM 返回: {result[:200]}")

        # 处理字段名不一致：DrawArgs 使用 sampler，但 API 使用 sampler_name
        if "sampler_name" in params and "sampler" not in params:
            params["sampler"] = params.pop("sampler_name")
        elif "sampler" in params and "sampler_name" not in params:
            params["sampler_name"] = params["sampler"]

        # 验证参数是否符合 DrawArgs 格式
        try:
            draw_args = DrawArgs(**params)
            params = draw_args.model_dump() if hasattr(draw_args, 'model_dump') else draw_args.dict()
        except Exception as e:
            logger.warning(f"参数验证失败，使用原始参数: {e}")
            # 如果验证失败，继续使用原始参数

        # 验证并补充缺失的参数（注意：API 使用 sampler_name）
        validated_params: Dict[str, Any] = {
            "model": params.get("model", ""),
            "prompt": params.get("prompt", ""),
            "negative_prompt": params.get("negative_prompt", "bad quality, worst quality"),
            "sampler_name": params.get("sampler_name") or params.get("sampler", "Euler a"),
            "steps": params.get("steps", 30),
            "cfg_scale": params.get("cfg_scale", 7.0),
            "width": params.get("width", 1024),
            "height": params.get("height", 1024),
            "seed": params.get("seed", -1),
            "clip_skip": params.get("clip_skip", 2),
        }

        # LoRA 是可选的
        if "loras" in params and isinstance(params["loras"], dict):
            validated_params["loras"] = params["loras"]
        else:
            validated_params["loras"] = {}

        # VAE 是可选的
        if "vae" in params and params["vae"]:
            validated_params["vae"] = params["vae"]

        logger.info(
            f"✅ 已生成绘图参数：model={validated_params.get('model')}, prompt长度={len(validated_params.get('prompt', ''))}")

        return {
            "success": True,
            "params": validated_params
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"生成绘图参数失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成绘图参数失败: {str(e)}")


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

    # 创建 ChatIteration 对象
    iteration_data = ChatIteration(
        target=target,
        index=index,
        stop=stop,
        step=step,
        summary=summary
    )

    # 创建 ChatMessage 并存储到数据库
    message_id = str(uuid.uuid4())
    iteration_message = ChatMessage(
        message_id=message_id,
        project_id=project_id,
        role="assistant",
        context="",
        status="thinking",
        message_type="iteration",
        data=iteration_data.model_dump(),
        tools=[],
        suggests=[]
    )
    HistoryService.create(iteration_message)

    logger.info(f"已启动迭代模式：{target}，范围：{index}-{stop}，步长：{step}")

    return {
        "iteration_id": message_id,
        "message_id": message_id,
        "target": target,
        "index": index,
        "stop": stop,
        "step": step,
        "message": f"已启动迭代模式：{target}，将从第{index}行开始，每{step}行处理一次，直到第{stop}行"
    }

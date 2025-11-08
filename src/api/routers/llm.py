"""
LLM 相关的路由。

提供 LLM 交互过程中需要的辅助功能，如添加选项等。
"""
import json
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Body
from loguru import logger

from api.schemas.chat import ChatMessage, ChatIteration
from api.services.db.project_service import ProjectService
from api.services.db import HistoryService
from api.services.llm import get_current_llm_service
from api.schemas.draw import DrawArgs
from api.routers.model_meta import get_checkpoints, get_loras
from api.routers.actor import get_all_actors
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
    - 图像选项：draw 工具调用后，展示生成的图像供用户选择
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
) -> DrawArgs:
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
        生成的绘图参数（DrawArgs 对象）
    
    Raises:
        HTTPException: 如果 LLM 服务未初始化、LLM 返回错误或参数验证失败
    """
    try:
        llm_service = get_current_llm_service()
        if not llm_service:
            raise HTTPException(status_code=503, detail="LLM 服务未初始化")

        # 1. 直接调用函数获取可用资源
        logger.info("正在获取可用模型和角色信息...")
        checkpoints = await get_checkpoints()
        loras = await get_loras()
        # 查询 actor（支持 project_id=None，表示默认工作空间）
        actors = await get_all_actors(project_id=project_id, limit=1000)
        
        # 2. 格式化资源信息为 JSON 字符串
        resources_info = {
            "checkpoints": checkpoints,
            "loras": loras,
        }
        # 将 Actor 对象转换为字典（包括 examples），支持 project_id=None
        if actors:
            actors_dict = [actor.model_dump() for actor in actors]
            resources_info["actors"] = actors_dict
        
        resources_json = json.dumps(resources_info, ensure_ascii=False, indent=2)
        logger.info(f"已获取资源信息：{len(checkpoints)} 个 Checkpoint，{len(loras)} 个 LoRA，{len(actors)} 个角色")

        # 3. 构建 LLM 提示消息
        desc_section = GENERATE_DRAW_PARAMS_DESC_SECTION.format(desc=desc) if desc else GENERATE_DRAW_PARAMS_NO_DESC
        
        # 根据是否有 project_id 选择不同的步骤说明
        # 如果有 actor 信息，使用带项目的步骤说明（即使 project_id=None）
        has_actors = len(actors) > 0
        if project_id or has_actors:
            steps_section = GENERATE_DRAW_PARAMS_STEPS_WITH_PROJECT
            # 添加角色查询要求（支持 project_id=None）
            actual_project_id = project_id if project_id is not None else "默认工作空间"
            actor_context = GENERATE_DRAW_PARAMS_ACTOR_CONTEXT_TEMPLATE.format(project_id=actual_project_id)
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
        
        # 4. 将资源信息添加到系统提示词中
        resources_prompt = f"""
## 可用资源信息（已自动获取，无需调用工具）

以下是当前可用的模型和角色信息，请直接使用这些信息生成参数：

```json
{resources_json}
```

**重要提示**：
- 必须使用 `version_name` 作为模型和 LoRA 名称（不是 `name`）
- 所有 LoRA 的 `ecosystem` 和 `base_model` 必须与 Checkpoint 完全匹配
- 如果提供了角色信息，请参考角色的 `examples` 中的 `draw_args` 保持一致性
- LoRA 的 `trained_words` 必须在 prompt 中包含
"""

        # 5. 调用 LLM（异步），使用结构化输出
        # 注意：我们需要将资源信息作为系统消息的一部分传递
        # 由于 chat_invoke 会构建系统消息，我们需要通过自定义方式添加资源信息
        # 这里我们将资源信息添加到用户消息的开头
        full_prompt = resources_prompt + "\n\n" + prompt
        
        result = await llm_service.chat_invoke(
            message=full_prompt,
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

        # 验证参数是否符合 DrawArgs 格式，如果失败则报错
        try:
            draw_args = DrawArgs(**params)
        except Exception as e:
            logger.error(f"参数验证失败: {e}, 参数: {params}")
            raise HTTPException(status_code=500, detail=f"LLM 返回的参数不符合 DrawArgs 格式: {str(e)}")

        logger.info(
            f"✅ 已生成绘图参数：model={draw_args.model}, prompt长度={len(draw_args.prompt)}")

        return draw_args

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

    # 创建 ChatMessage 并存储到数据库（ID 会自动生成）
    iteration_message = ChatMessage(
        project_id=project_id,
        role="assistant",
        context="",
        status="thinking",
        message_type="iteration",
        data=iteration_data.model_dump(),
        tools=[],
        suggests=[]
    )
    iteration_message = HistoryService.create(iteration_message)
    message_id = iteration_message.message_id

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

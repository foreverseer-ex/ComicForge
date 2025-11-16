"""
LLM 相关的路由。

提供 LLM 交互过程中需要的辅助功能，如添加选项等。
"""
import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Body
from loguru import logger
from pydantic import TypeAdapter

from api.schemas.chat import ChatMessage, ChatIteration
from api.services.db.project_service import ProjectService
from api.services.db import HistoryService, SummaryService, MemoryService, ContentService
from api.services.llm import get_current_llm_service
from api.schemas.draw import DrawArgs, DrawIterationResult
from api.services.db.base import normalize_project_id
from api.routers.model_meta import get_checkpoints, get_loras
from api.routers.actor import get_all_actors, _monitor_single_job_and_update_portrait
from api.schemas.memory import ChapterSummary
from api.schemas.actor import Actor, ActorList
from api.schemas.draw import Example
from api.services.db.actor_service import ActorService
from api.services.draw import get_current_draw_service
import asyncio

router = APIRouter(
    prefix="/llm",
    tags=["LLM 辅助"],
    responses={404: {"description": "资源不存在"}},
)

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
        checkpoints = await get_checkpoints(only_preferred=True)
        loras = await get_loras(only_preferred=True)
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
        desc_line = f"任务描述：{desc}" if desc else "无任务描述"
        prompt = f"""请根据以下信息生成文生图参数：

任务名称：{name}
{desc_line}

请按照 MCP 工具使用指南中的"DrawArgs 生成流程"生成参数，并返回符合 DrawArgs 格式的 JSON 对象。"""
        
        # 4. 将资源信息添加到系统提示词中
        resources_prompt = f"""
## 可用资源信息（已自动获取，无需调用工具）

以下是当前可用的模型和角色信息，请直接使用这些信息生成参数：

```json
{resources_json}
```

⚠️ 请按照 MCP 工具使用指南中的"DrawArgs 生成流程"生成参数。
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


# ==================== 摘要生成 ====================

@router.post("/generate-full-summary", summary="生成全文摘要")
async def generate_full_summary(
    project_id: str = Body(..., description="项目ID"),
    direct_mode: bool = Body(True, description="直接模式（True=输入全文内容，False=总结模式，基于其他章节摘要生成）")
) -> Dict[str, Any]:
    """
    生成全文摘要。
    
    调用 LLM 的 chat_invoke 生成全文摘要，输入包括：
    - 系统提示词
    - 全文内容（直接模式）或所有章节摘要（总结模式）
    - 所有 memory
    - 所有 actor
    - 所有其他 ChapterSummary 条目
    
    Args:
        project_id: 项目ID
        direct_mode: 直接模式（True=输入全文内容，False=总结模式，基于其他章节摘要生成）
    
    Returns:
        包含摘要内容的字典
    
    Raises:
        HTTPException: 如果项目不存在、LLM 服务未初始化或生成失败
    """
    try:
        project_id = normalize_project_id(project_id)
        
        # 验证项目是否存在
        project = ProjectService.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
        
        # 获取 LLM 服务
        llm_service = get_current_llm_service()
        if not llm_service:
            raise HTTPException(status_code=503, detail="LLM 服务未初始化")
        
        # 1. 获取所有 memory
        memories = MemoryService.get_all(project_id)
        memory_text = "\n".join([f"- {m.key}: {m.value}" for m in memories]) if memories else "无"
        
        # 2. 获取所有 actor
        actors = await get_all_actors(project_id=project_id, limit=1000)
        actor_text = "\n".join([f"- {a.name}: {a.desc}" for a in actors]) if actors else "无"
        
        # 3. 获取所有其他 ChapterSummary 条目（除了全文摘要）
        all_summaries = SummaryService.get_all(project_id)
        chapter_summaries = [s for s in all_summaries if s.chapter_index >= 0]
        summary_text = "\n".join([f"第{s.chapter_index}章 ({s.title}): {s.summary or '无摘要'}" for s in chapter_summaries]) if chapter_summaries else "无"
        
        # 4. 获取全文内容（仅直接模式）
        full_content = ""
        if direct_mode:
            novel_contents = ContentService.get_by_session(project_id)
            # 只输入文本内容，不包含章节和行号信息
            full_content = "\n".join([content.content for content in novel_contents])
            if not full_content:
                raise HTTPException(status_code=404, detail=f"项目没有小说内容: {project_id}")
        
        # 5. 构建系统提示词和用户消息
        system_prompt = """你是一个专业的小说分析助手。请根据提供的信息生成文章的全文摘要。

要求：
1. 摘要应该简洁明了，概括文章的主要情节、主题和关键信息
2. 摘要长度适中（建议200-500字）
3. 重点关注故事的核心冲突、主要角色关系和重要情节转折点
4. **重要**：必须返回纯文本格式，不要使用 Markdown 格式（不要使用标题符号、列表符号、粗体、斜体等格式）"""
        
        user_message = f"""请生成以下文章的全文摘要：

项目标题：{project.title}

## 项目记忆信息
{memory_text}

## 角色信息
{actor_text}

## 已有章节摘要
{summary_text}
"""
        
        if direct_mode:
            user_message += f"""
## 全文内容
{full_content}

请根据全文内容生成摘要。**注意：请返回纯文本格式，不要使用 Markdown 格式。**"""
        else:
            user_message += """
请基于以上章节摘要生成全文摘要（总结模式，不包含全文内容）。**注意：请返回纯文本格式，不要使用 Markdown 格式。**"""
        
        # 6. 调用 LLM 生成摘要
        result = await llm_service.chat_invoke(
            message=user_message,
            project_id=project_id,
            output_schema=None  # 返回纯文本摘要
        )
        
        if not result or len(result.strip()) == 0:
            raise HTTPException(status_code=500, detail="LLM 返回空内容，无法生成摘要")
        
        # 7. 获取或创建全文摘要记录
        summary_obj = SummaryService.get(project_id, -1)
        
        # 获取全文的行号范围
        novel_contents = ContentService.get_by_session(project_id)
        start_line = 0
        end_line = max([content.line for content in novel_contents]) if novel_contents else 0
        
        if summary_obj:
            # 更新现有摘要
            summary_obj.summary = result
            summary_obj.end_line = end_line
            updated = SummaryService.update(project_id, -1, summary=result, end_line=end_line)
            logger.info(f"更新全文摘要: project_id={project_id}")
        else:
            # 创建新摘要
            summary_obj = ChapterSummary(
                project_id=project_id,
                chapter_index=-1,
                title=project.title,
                summary=result,
                start_line=start_line,
                end_line=end_line
            )
            SummaryService.create(summary_obj)
            logger.info(f"创建全文摘要: project_id={project_id}")
        
        return {
            "success": True,
            "project_id": project_id,
            "summary": result,
            "direct_mode": direct_mode,
            "message": "全文摘要生成成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"生成全文摘要失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成全文摘要失败: {str(e)}")


@router.post("/generate-chapter-summary", summary="生成章节摘要")
async def generate_chapter_summary(
    project_id: str = Body(..., description="项目ID"),
    chapter_index: int = Body(..., ge=0, description="章节索引（>=0）")
) -> Dict[str, Any]:
    """
    生成章节摘要。
    
    调用 LLM 的 chat_invoke 生成章节摘要，输入包括：
    - 系统提示词
    - 章节全文内容
    - 所有 memory
    - 所有 actor
    - 所有其他 ChapterSummary 条目
    
    Args:
        project_id: 项目ID
        chapter_index: 章节索引（>=0）
    
    Returns:
        包含摘要内容的字典
    
    Raises:
        HTTPException: 如果项目不存在、章节不存在、LLM 服务未初始化或生成失败
    """
    try:
        project_id = normalize_project_id(project_id)
        
        # 验证项目是否存在
        project = ProjectService.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
        
        # 获取 LLM 服务
        llm_service = get_current_llm_service()
        if not llm_service:
            raise HTTPException(status_code=503, detail="LLM 服务未初始化")
        
        # 1. 获取章节内容
        chapter_contents = ContentService.get_by_chapter(project_id, chapter_index)
        if not chapter_contents:
            raise HTTPException(status_code=404, detail=f"章节不存在或为空: project_id={project_id}, chapter_index={chapter_index}")
        
        # 只输入文本内容，不包含行号信息
        chapter_text = "\n".join([content.content for content in chapter_contents])
        
        # 2. 获取所有 memory
        memories = MemoryService.get_all(project_id)
        memory_text = "\n".join([f"- {m.key}: {m.value}" for m in memories]) if memories else "无"
        
        # 3. 获取所有 actor
        actors = await get_all_actors(project_id=project_id, limit=1000)
        actor_text = "\n".join([f"- {a.name}: {a.desc}" for a in actors]) if actors else "无"
        
        # 4. 获取所有其他 ChapterSummary 条目
        all_summaries = SummaryService.get_all(project_id)
        summary_text = "\n".join([f"第{s.chapter_index}章 ({s.title}): {s.summary or '无摘要'}" for s in all_summaries if s.chapter_index != chapter_index]) if all_summaries else "无"
        
        # 5. 构建系统提示词和用户消息
        system_prompt = """你是一个专业的小说分析助手。请根据提供的章节内容生成章节摘要。

要求：
1. 摘要应该简洁明了，概括章节的主要情节和关键信息
2. 摘要长度适中（建议100-300字）
3. 重点关注章节的核心事件、角色行为和重要转折点
4. **重要**：必须返回纯文本格式，不要使用 Markdown 格式（不要使用标题符号、列表符号、粗体、斜体等格式）"""
        
        user_message = f"""请生成第{chapter_index}章的摘要：

项目标题：{project.title}

## 项目记忆信息
{memory_text}

## 角色信息
{actor_text}

## 其他章节摘要
{summary_text}

## 第{chapter_index}章全文内容
{chapter_text}

请根据以上章节全文内容生成摘要。**注意：请返回纯文本格式，不要使用 Markdown 格式。**"""
        
        # 6. 调用 LLM 生成摘要
        result = await llm_service.chat_invoke(
            message=user_message,
            project_id=project_id,
            output_schema=None  # 返回纯文本摘要
        )
        
        if not result or len(result.strip()) == 0:
            raise HTTPException(status_code=500, detail="LLM 返回空内容，无法生成摘要")
        
        # 7. 获取或创建章节摘要记录
        summary_obj = SummaryService.get(project_id, chapter_index)
        
        # 获取章节的行号范围
        start_line = min([content.line for content in chapter_contents])
        end_line = max([content.line for content in chapter_contents])
        chapter_title = chapter_contents[0].content[:50] if chapter_contents else f"第{chapter_index}章"  # 使用第一行的前50个字符作为标题
        
        if summary_obj:
            # 更新现有摘要
            summary_obj.summary = result
            summary_obj.start_line = start_line
            summary_obj.end_line = end_line
            updated = SummaryService.update(project_id, chapter_index, summary=result, start_line=start_line, end_line=end_line)
            logger.info(f"更新章节摘要: project_id={project_id}, chapter_index={chapter_index}")
        else:
            # 创建新摘要
            summary_obj = ChapterSummary(
                project_id=project_id,
                chapter_index=chapter_index,
                title=chapter_title,
                summary=result,
                start_line=start_line,
                end_line=end_line
            )
            SummaryService.create(summary_obj)
            logger.info(f"创建章节摘要: project_id={project_id}, chapter_index={chapter_index}")
        
        return {
            "success": True,
            "project_id": project_id,
            "chapter_index": chapter_index,
            "summary": result,
            "message": f"第{chapter_index}章摘要生成成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"生成章节摘要失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成章节摘要失败: {str(e)}")


# ==================== 角色提取 ====================

@router.post("/generate-full-actors", summary="一键提取全文角色")
async def generate_full_actors(
    project_id: str = Body(..., description="项目ID"),
    direct_mode: bool = Body(True, description="直接模式（True=输入全文内容，False=总结模式，基于章节摘要生成）")
) -> Dict[str, Any]:
    """
    一键提取全文角色。
    
    调用 LLM 的 chat_invoke 提取全文角色，输入包括：
    - 系统提示词
    - 全文内容（直接模式）或所有章节摘要（总结模式）
    - 所有 memory
    - 所有现有 actor
    - 所有 ChapterSummary 条目
    
    LLM 返回 list[Actor] 格式的角色列表，然后通过名称匹配批量更新或创建角色。
    
    Args:
        project_id: 项目ID
        direct_mode: 直接模式（True=输入全文内容，False=总结模式，基于章节摘要生成）
    
    Returns:
        包含提取结果和统计信息的字典
    
    Raises:
        HTTPException: 如果项目不存在、LLM 服务未初始化或生成失败
    """
    try:
        project_id = normalize_project_id(project_id)
        
        # 验证项目是否存在
        project = ProjectService.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
        
        # 获取 LLM 服务
        llm_service = get_current_llm_service()
        if not llm_service:
            raise HTTPException(status_code=503, detail="LLM 服务未初始化")
        
        # 1. 获取所有 memory
        memories = MemoryService.get_all(project_id)
        memory_text = "\n".join([f"- {m.key}: {m.value}" for m in memories]) if memories else "无"
        
        # 2. 获取所有现有 actor
        existing_actors = await get_all_actors(project_id=project_id, limit=1000)
        actor_text = "\n".join([f"- {a.name}: {a.desc}" for a in existing_actors]) if existing_actors else "无"
        
        # 3. 获取所有 ChapterSummary 条目
        all_summaries = SummaryService.get_all(project_id)
        summary_text = "\n".join([f"第{s.chapter_index}章 ({s.title}): {s.summary or '无摘要'}" for s in all_summaries]) if all_summaries else "无"
        
        # 4. 获取全文内容（仅直接模式）
        full_content = ""
        if direct_mode:
            novel_contents = ContentService.get_by_session(project_id)
            # 只输入文本内容，不包含章节和行号信息
            full_content = "\n".join([content.content for content in novel_contents])
            if not full_content:
                raise HTTPException(status_code=404, detail=f"项目没有小说内容: {project_id}")
        
        # 5. 获取可用的 Checkpoint 和 LoRA 模型列表
        available_checkpoints = await get_checkpoints(only_preferred=True)
        available_loras = await get_loras(only_preferred=True)
        
        # 构建模型信息文本（直接转 JSON）
        checkpoint_text = ""
        if available_checkpoints:
            checkpoint_text = "## 可用 Checkpoint 模型\n\n```json\n" + json.dumps(available_checkpoints, ensure_ascii=False, indent=2) + "\n```\n"
        else:
            checkpoint_text = "## 可用 Checkpoint 模型\n无\n"
        
        lora_text = ""
        if available_loras:
            lora_text = "## 可用 LoRA 模型\n\n```json\n" + json.dumps(available_loras, ensure_ascii=False, indent=2) + "\n```\n"
        else:
            lora_text = "## 可用 LoRA 模型\n无\n"
        
        # 5. 构建系统提示词和用户消息
        system_prompt = """你是一个专业的小说分析助手。请根据提供的信息提取文章中的所有角色（Actor），并为每个角色生成立绘（portrait）。

重要原则：这是更新模式，不是创建模式！
- 如果角色列表中已经存在某个角色（通过名称匹配），你应该返回该角色并更新其描述（desc）和标签（tags）
- 你返回的 examples 会在现有角色的 examples 列表基础上添加新的立绘，不会删除或替换现有的立绘
- 因此，即使角色已有立绘，你也可以返回新的立绘示例

重要：不要使用迭代模式！
- 全文内容已经直接提供给你了，不需要调用 `_start_iteration` 工具
- 直接分析提供的全文内容，提取所有角色，并返回 JSON 格式的结果
- 不要调用任何工具，只需要返回 JSON 结果

要求：
1. **主角（叙述者）提取**（⚠️ 非常重要）：
   - 文章通常有一个主角，文章中的"我"通常表示主角（叙述者）
   - 例如：如果角色A是主角，那么文章中出现的"我心里想：她是个骗子吧"，实际上是指角色A在想这件事
   - 必须识别并提取主角，如果文章是以第一人称叙述，要提取出叙述者（主角）
   - 主角的身份必须在角色的 desc 第一行明确标注，或者在 tags 的"角色定位"字段中标注
   - 如果没有明确的主角或叙述者，可以不提取
2. **角色分类**（重要）：
   - 需要根据角色在故事中的重要性和地位进行分类
   - 可以使用以下分类：主角、配角、男1、男2、女1、女2等
   - 分类信息应该在 tags 的"角色定位"字段中体现，例如："主角"、"配角"、"男1"、"女1"等
   - 具体分类应该根据文章内容判断，例如：
     - 如果只有一个主要角色（主角），标注为"主角"
     - 如果有多个重要角色，可以标注为"男1"、"女1"等
     - 如果角色重要性较低，标注为"配角"
3. 角色不仅包括人物角色，也包括小说中出现的重要要素，如国家、组织、地点等
4. 为每个角色提供：
   - name: 角色名称（必需）
   - desc: 角色描述（必需，详细描述角色的故事、经历、背景、性格、关系等信息）
     - **重要**：如果是主角，必须在 desc 的第一行明确标注，例如："【主角】角色A是故事的叙述者和主角..."或"【叙述者】这是故事的主角..."
     - **重要**：角色的 desc 应该重点关注角色的故事经历和背景设定，包括：
       - 角色的身份、职业、地位
       - 角色在故事中的经历和重要事件
       - 角色与其他角色的关系
       - 角色的性格特点和成长变化
       - 角色在故事中的作用和意义
     - 可以简要提及外貌特征，但不应只关注外貌，而应重点描述角色的故事经历
     - 如果角色已存在，可以更新其描述
   - color: 卡片颜色（可选，默认 #808080，格式如 #FF69B4）
   - tags: 标签字典（可选，必须包含"角色定位"字段来标注角色分类，如 {"角色定位": "主角", "性别": "男", "年龄": "20"}。如果角色已存在，可以更新其标签）
   - examples: 立绘示例列表（按需添加，遵循以下原则）：
     - **一般情况下**：每个角色只添加 1 张立绘（如果没有重大形象转变）
     - **跨性别角色特殊处理**（⚠️ 重要）：跨性别角色必须绘制至少 2 张立绘（变性前和变性后），且**必须先绘制变性后的立绘，再绘制变性前的立绘**
     - **其他特殊情况**：如果角色在故事中有其他重大形象转变（如年龄显著变化、服装风格重大改变等），可以为每种形象创建 1 张立绘（最多 2-3 张）
     - **不要为每个角色都创建多张立绘**，只有当角色确实有重大形象变化时才创建多张
     - 新立绘会添加到现有的立绘列表中（不会替换现有的立绘）
3. 每个 example 应该包含：
   - title: 立绘标题（如："立绘1"、"全身像"、"变性后"、"变性前"等，可选）
   - desc: 立绘描述（可选）
   - draw_args: 绘图参数（必需），包括：
     - model: SD模型名称（必需，使用可用的模型版本名称，从下方提供的 Checkpoint 列表中选择）
     - prompt: 正向提示词（必需，详细描述角色的外观特征、服装、姿势等）
       - **重要**：prompt 只关注外貌特征，不包含故事背景和剧情
         - 只描述外貌/姿态/气质，如：身高、体型、发色、瞳色、服装、表情、姿势等
         - 不要包含角色的故事经历、背景设定、与其他角色的关系等非视觉信息
         - 这与角色的 desc 不同：desc 要详细描述故事经历，而 prompt 只关注视觉外观
       - **重要**：必须在 prompt 开头明确指定人物数量，如 `1girl`、`1boy`、`1woman`、`1man` 等，确保生成单人立绘
       - 正常情况下角色立绘应该只包含一个角色，除非明确强调需要多个角色
     - negative_prompt: 负向提示词（可选，默认空字符串）
     - sampler: 采样器名称（可选，默认 "DPM++ 2M Karras"）
     - steps: 采样步数（可选，默认 30）
     - cfg_scale: CFG Scale（可选，默认 7.0）
     - width: 图像宽度（可选，默认 1024）
     - height: 图像高度（可选，默认 1024）
     - seed: 随机种子（可选，默认 -1 表示随机）
     - loras: LoRA 字典（必需使用，格式：{"version_name": weight}，从下方提供的 LoRA 列表中选择）
     - vae: VAE 模型名称（可选）
     - clip_skip: CLIP skip（可选）
4. 返回格式必须是一个包含 "actors" 字段的 JSON 对象，actors 是一个数组
5. 如果角色列表中已经存在某个角色，LLM 仍然应该返回该角色（更新其描述和标签，添加新的立绘）
6. 提取的角色应该全面，包括主角、主要角色和重要配角
7. **主角识别方法**：
   - 如果文章以第一人称叙述（出现"我"），那么这个"我"就是主角（叙述者）
   - 如果文章以第三人称叙述，需要根据角色的出场频率、重要性、情节关联度等判断主角
   - 主角通常贯穿整个故事，是故事的核心视角或主要推动者
8. **角色描述与绘图提示词的区别**（重要）：
   - **角色的 desc（描述）**：应该详细描述角色的故事经历、背景设定、性格特点、与其他角色的关系等，重点在故事内容，不要只关注外貌
   - **draw_args 的 prompt（绘图提示词）**：只关注视觉外观，如外貌、服装、姿势等，不包含故事背景和剧情
   - 两者的侧重点不同：desc 用于理解角色在故事中的意义，prompt 用于生成视觉图像
9. 立绘的 draw_args 应该包含详细的 prompt，描述角色的外观特征、服装风格、姿势等
   - **重要**：prompt 必须在开头明确指定人物数量，如 `1girl`、`1boy`、`1woman`、`1man` 等，确保生成单人立绘
   - 正常情况下角色立绘应该只包含一个角色，除非明确强调需要多个角色
10. **立绘数量原则**（重要）：
   - 大多数角色：只创建 1 张立绘（默认形象）
   - 跨性别角色：必须创建至少 2 张立绘（变性前和变性后），**先绘制变性后的，再绘制变性前的**
   - 其他特殊情况：角色有明显形象转变时，才为每种形象创建 1 张（最多 2-3 张）
   - 不要为所有角色都创建多张立绘，按需添加
11. **LoRA 使用要求**（重要）：
   - 必须为每个立绘的 draw_args 中的 loras 字段填充实际的 LoRA 模型（不能为空或 null）
   - 从下方提供的 LoRA 列表中选择合适的 LoRA，根据角色特征和风格选择
   - 如果 LoRA 有 trained_words，必须在 prompt 中包含相关的 trained_words
   - LoRA 权重通常在 0.8-1.2 之间"""
        
        user_message = f"""请提取以下文章中的所有角色：

项目标题：{project.title}

## 项目记忆信息
{memory_text}

## 现有角色信息
{actor_text}

## 已有章节摘要
{summary_text}

{checkpoint_text}

{lora_text}
"""
        
        if direct_mode:
            user_message += f"""
## 全文内容
{full_content}

请根据全文内容提取所有角色，并为每个角色生成立绘（portrait）。

重要提示：
- **不要调用任何工具**，特别是不要调用 `_start_iteration` 工具。全文内容已经直接提供给你了，直接分析即可。
- 这是更新模式：如果角色已存在，会更新其描述（desc）和标签（tags），并在现有立绘列表基础上添加新的立绘
- **主角（叙述者）提取**（⚠️ 极其重要）：
  - 文章中的"我"通常表示主角（叙述者），必须识别并提取出来
  - 例如：如果角色A是主角，文章中"我心里想：她是个骗子吧"指的是角色A的想法
  - 主角的身份必须在 desc 第一行标注（如"【主角】..."或"【叙述者】..."），或在 tags 的"角色定位"中标注为"主角"
  - 如果没有明确的主角或叙述者，可以不提取
- **角色分类**（重要）：
  - 必须在 tags 的"角色定位"字段中标注角色分类，如"主角"、"配角"、"男1"、"女1"等
  - 根据角色重要性和地位分类，例如：主角标注"主角"，重要配角可标注"男1"、"女1"等，次要角色标注"配角"
- **角色描述与绘图提示词的区别**（⚠️ 非常重要）：
  - **角色的 desc（描述）**：必须详细描述角色的故事经历、背景设定、性格特点、与其他角色的关系等
    - 重点关注角色在故事中的身份、职业、经历、重要事件、性格成长、关系网络等
    - 可以简要提及外貌，但不应只关注外貌，要重点描述角色的故事内容
    - 描述应该足够详细，让读者能够理解角色在故事中的意义和作用
  - **draw_args 的 prompt（绘图提示词）**：只关注视觉外观，不包含故事背景
    - 只描述外貌/姿态/气质，如：身高、体型、发色、瞳色、服装、表情、姿势等
    - 不要包含角色的故事经历、背景设定、与其他角色的关系等非视觉信息
- **立绘数量原则**（重要）：
  - 大多数角色：只创建 1 张立绘（默认形象），不要为每个角色都创建多张
  - 特殊情况：只有当角色在故事中有重大形象转变时（如跨性别角色变性前后、年龄显著变化、服装风格重大改变等），才为每种形象创建 1 张立绘（最多 2-3 张）
  - 按需添加，不要过度创建立绘
- **立绘人物数量原则**（⚠️ 极其重要）：
  - 每个立绘的 prompt 必须在开头明确指定人物数量，如 `1girl`、`1boy`、`1woman`、`1man` 等
  - 正常情况下角色立绘应该只包含一个角色，必须使用 `1girl`/`1boy`/`1woman`/`1man` 等标签确保单人立绘
  - 除非明确强调需要多个角色，否则不要省略人物数量标签
  - 人物数量标签应该放在 prompt 的开头位置
- 返回格式必须是一个 JSON 对象，包含 "actors" 字段，actors 是一个数组
- 每个 Actor 应该包含 name、desc、color、tags，以及 examples 数组（立绘列表，新立绘会添加到现有的立绘列表中）
- 每个 example 应该包含 title（可选）、desc（可选）和 draw_args（必需，包含 model、prompt 等绘图参数）"""
        else:
            user_message += """
请基于以上章节摘要提取所有角色（总结模式，不包含全文内容），并为每个角色生成立绘（portrait）。

重要提示：
- **不要调用任何工具**，特别是不要调用 `_start_iteration` 工具。章节摘要已经直接提供给你了，直接分析即可。
- 这是更新模式：如果角色已存在，会更新其描述（desc）和标签（tags），并在现有立绘列表基础上添加新的立绘
- **主角（叙述者）提取**（⚠️ 极其重要）：
  - 文章中的"我"通常表示主角（叙述者），必须识别并提取出来
  - 例如：如果角色A是主角，文章中"我心里想：她是个骗子吧"指的是角色A的想法
  - 主角的身份必须在 desc 第一行标注（如"【主角】..."或"【叙述者】..."），或在 tags 的"角色定位"中标注为"主角"
  - 如果没有明确的主角或叙述者，可以不提取
- **角色分类**（重要）：
  - 必须在 tags 的"角色定位"字段中标注角色分类，如"主角"、"配角"、"男1"、"女1"等
  - 根据角色重要性和地位分类，例如：主角标注"主角"，重要配角可标注"男1"、"女1"等，次要角色标注"配角"
- **角色描述与绘图提示词的区别**（⚠️ 非常重要）：
  - **角色的 desc（描述）**：必须详细描述角色的故事经历、背景设定、性格特点、与其他角色的关系等
    - 重点关注角色在故事中的身份、职业、经历、重要事件、性格成长、关系网络等
    - 可以简要提及外貌，但不应只关注外貌，要重点描述角色的故事内容
    - 描述应该足够详细，让读者能够理解角色在故事中的意义和作用
  - **draw_args 的 prompt（绘图提示词）**：只关注视觉外观，不包含故事背景
    - 只描述外貌/姿态/气质，如：身高、体型、发色、瞳色、服装、表情、姿势等
    - 不要包含角色的故事经历、背景设定、与其他角色的关系等非视觉信息
- **立绘数量原则**（重要）：
  - 大多数角色：只创建 1 张立绘（默认形象），不要为每个角色都创建多张
  - 特殊情况：只有当角色在故事中有重大形象转变时（如跨性别角色变性前后、年龄显著变化、服装风格重大改变等），才为每种形象创建 1 张立绘（最多 2-3 张）
  - 按需添加，不要过度创建立绘
- **立绘人物数量原则**（⚠️ 极其重要）：
  - 每个立绘的 prompt 必须在开头明确指定人物数量，如 `1girl`、`1boy`、`1woman`、`1man` 等
  - 正常情况下角色立绘应该只包含一个角色，必须使用 `1girl`/`1boy`/`1woman`/`1man` 等标签确保单人立绘
  - 除非明确强调需要多个角色，否则不要省略人物数量标签
  - 人物数量标签应该放在 prompt 的开头位置
- 返回格式必须是一个 JSON 对象，包含 "actors" 字段，actors 是一个数组
- 每个 Actor 应该包含 name、desc、color、tags，以及 examples 数组（立绘列表，新立绘会添加到现有的立绘列表中）
- 每个 example 应该包含 title（可选）、desc（可选）和 draw_args（必需，包含 model、prompt 等绘图参数）"""
        
        # 6. 调用 LLM 提取角色（使用结构化输出）
        result = await llm_service.chat_invoke(
            message=user_message,
            project_id=project_id,
            output_schema=ActorList  # 使用 ActorList 作为输出 schema
        )
        
        if not result or len(result.strip()) == 0:
            raise HTTPException(status_code=500, detail="LLM 返回空内容，无法提取角色")
        
        # 7. 解析 LLM 返回的 JSON
        try:
            import re
            # 尝试提取 JSON 部分（可能 LLM 返回了包含其他文本的内容）
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                json_str = json_match.group(0)
                parsed_data = json.loads(json_str)
            else:
                parsed_data = json.loads(result)
            
            # 验证返回格式
            if "actors" not in parsed_data:
                raise ValueError("LLM 返回的 JSON 中缺少 'actors' 字段")
            
            actors_data = parsed_data["actors"]
            if not isinstance(actors_data, list):
                raise ValueError("LLM 返回的 'actors' 字段不是数组")
            
            # 转换为 Actor 对象列表，并处理 examples（创建绘图任务）
            extracted_actors = []
            portrait_job_count = 0
            
            for actor_dict in actors_data:
                try:
                    # 创建 Actor 对象（不包含 actor_id，examples 会在批量更新后处理）
                    actor = Actor(
                        project_id=project_id,
                        name=actor_dict.get("name", ""),
                        desc=actor_dict.get("desc", ""),
                        color=actor_dict.get("color", "#808080"),
                        tags=actor_dict.get("tags", {}),
                        examples=[]  # 先设置为空，后续处理
                    )
                    if not actor.name:
                        logger.warning(f"跳过无效角色（缺少名称）: {actor_dict}")
                        continue
                    
                    # 保存 examples 数据（稍后处理）
                    actor_dict['_examples_data'] = actor_dict.get("examples", [])
                    extracted_actors.append(actor)
                except Exception as e:
                    logger.warning(f"解析角色数据失败: {actor_dict}, 错误: {e}")
                    continue
            
            if not extracted_actors:
                raise HTTPException(status_code=500, detail="LLM 未提取到任何有效角色")
            
            # 8. 批量更新或创建角色（通过名称匹配）
            # 注意：此方法会更新 desc、tags、color，但保留现有的 examples
            batch_result = ActorService.batch_update_by_name(project_id, extracted_actors)
            
            # 9. 处理每个角色的 examples，创建绘图任务（仅在现有基础上添加新的）
            draw_service = get_current_draw_service()
            for actor_data in actors_data:
                actor_name = actor_data.get("name", "")
                if not actor_name:
                    continue
                
                # 获取角色（通过名称，确保获取到更新后的角色）
                actor = ActorService.get_by_name(project_id, actor_name)
                if not actor:
                    logger.warning(f"角色不存在，跳过处理 examples: {actor_name}")
                    continue
                
                # 处理 examples：只在现有基础上添加新的，不删除或替换现有的
                examples_data = actor_data.get("examples", [])
                if not examples_data:
                    # LLM 没有返回 examples，跳过
                    continue
                
                for example_dict in examples_data:
                    try:
                        # 解析 draw_args
                        draw_args_dict = example_dict.get("draw_args", {})
                        if not draw_args_dict:
                            logger.warning(f"跳过无效 example（缺少 draw_args）: {actor_name}")
                            continue
                        
                        # 验证必需的字段
                        if "model" not in draw_args_dict or "prompt" not in draw_args_dict:
                            logger.warning(f"跳过无效 example（缺少 model 或 prompt）: {actor_name}")
                            continue
                        
                        # 创建 DrawArgs 对象
                        draw_args = DrawArgs(
                            model=draw_args_dict.get("model"),
                            prompt=draw_args_dict.get("prompt", ""),
                            negative_prompt=draw_args_dict.get("negative_prompt", ""),
                            sampler=draw_args_dict.get("sampler", "DPM++ 2M Karras"),
                            steps=draw_args_dict.get("steps", 30),
                            cfg_scale=draw_args_dict.get("cfg_scale", 7.0),
                            width=draw_args_dict.get("width", 1024),
                            height=draw_args_dict.get("height", 1024),
                            seed=draw_args_dict.get("seed", -1),
                            loras=draw_args_dict.get("loras"),
                            vae=draw_args_dict.get("vae"),
                            clip_skip=draw_args_dict.get("clip_skip")
                        )
                        
                        # 创建绘图任务
                        example_title = example_dict.get("title") or f"{actor_name}的立绘"
                        example_desc = example_dict.get("desc", "")
                        
                        # 如果角色已有立绘，使用第一个立绘作为 ControlNet reference_only 参考
                        # 这样可以保持同一角色的多张立绘在面部、身材、肤色等方面的一致性
                        if actor.examples and len(actor.examples) > 0:
                            # 查找第一个有效的立绘（filename 存在且不是正在生成的）
                            for existing_example_dict in actor.examples:
                                existing_filename = existing_example_dict.get('filename') or existing_example_dict.get('image_path')
                                if existing_filename and not str(existing_filename).startswith('generating_'):
                                    # 构建立绘的完整文件路径
                                    actual_project_id = actor.project_id if actor.project_id is not None else "default"
                                    from api.utils.path import project_home
                                    existing_portrait_path = project_home / actual_project_id / "actors" / actor.name / existing_filename
                                    
                                    # 检查文件是否存在
                                    if existing_portrait_path.exists() and existing_portrait_path.is_file():
                                        # 将立绘路径添加到 draw_args
                                        draw_args.reference_image_path = str(existing_portrait_path)
                                        draw_args.reference_weight = 0.8  # 默认权重 0.8
                                        logger.info(f"✅ 已为角色 {actor_name} 的新立绘添加 ControlNet reference_only 参考: {existing_portrait_path}")
                                    break  # 只使用第一个有效的立绘
                        
                        job_id = draw_service.draw(
                            args=draw_args,
                            name=example_title,
                            desc=example_desc
                        )
                        
                        # 创建 placeholder example（正在生成中）
                        temp_filename = f"generating_{job_id[:8]}.png"
                        example = Example(
                            title=example_title,
                            desc=example_desc,
                            draw_args=draw_args,
                            filename=temp_filename,
                            extra={"job_id": job_id}
                        )
                        
                        # 添加到 Actor
                        updated = ActorService.add_example(actor.actor_id, example)
                        if not updated:
                            logger.warning(f"添加 example 失败: {actor.actor_id}")
                            continue
                        
                        # 获取刚添加的示例的索引（最后一个）
                        example_index = len(updated.examples) - 1
                        
                        # 启动监控任务
                        asyncio.create_task(
                            _monitor_single_job_and_update_portrait(
                                job_id=job_id,
                                actor_id=actor.actor_id,
                                project_id=project_id,
                                title=example_title,
                                desc=example_desc,
                                draw_args=draw_args,
                                example_index=example_index
                            )
                        )
                        
                        portrait_job_count += 1
                        logger.info(f"已创建立绘任务: actor={actor_name}, job_id={job_id}, title={example_title}")
                        
                    except Exception as e:
                        logger.exception(f"处理 example 失败: actor={actor_name}, error={e}")
                        continue
            
            logger.info(f"一键提取角色完成: project_id={project_id}, 提取 {len(extracted_actors)} 个角色, 更新 {batch_result['updated']} 个, 创建 {batch_result['created']} 个, 创建 {portrait_job_count} 个立绘任务")
            
            return {
                "success": True,
                "project_id": project_id,
                "extracted_count": len(extracted_actors),
                "updated": batch_result["updated"],
                "created": batch_result["created"],
                "portrait_jobs": portrait_job_count,
                "direct_mode": direct_mode,
                "actors": [{"name": a.name, "desc": a.desc, "color": a.color, "tags": a.tags} for a in extracted_actors],
                "message": f"成功提取 {len(extracted_actors)} 个角色，更新 {batch_result['updated']} 个，创建 {batch_result['created']} 个，创建 {portrait_job_count} 个立绘任务"
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"解析 LLM 返回的 JSON 失败: {e}, 原始结果: {result[:500]}")
            raise HTTPException(status_code=500, detail=f"解析 LLM 返回的 JSON 失败: {str(e)}")
        except ValueError as e:
            logger.error(f"验证 LLM 返回格式失败: {e}, 原始结果: {result[:500]}")
            raise HTTPException(status_code=500, detail=f"LLM 返回格式不正确: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"一键提取角色失败: {e}")
        raise HTTPException(status_code=500, detail=f"一键提取角色失败: {str(e)}")


@router.post("/bind-paragraph-images", summary="绑定段落图像")
async def bind_paragraph_images(
    project_id: str = Body(..., description="项目ID"),
    start_index: int | None = Body(None, description="起始行号（从0开始，None表示自动查找）"),
    end_index: int = Body(..., description="结束行号（从0开始，包含）")
) -> Dict[str, Any]:
    """
    绑定段落图像。
    
    基于上下文（包括当前段落内容、前文摘要、角色信息等）生成绘图参数并创建绘图任务。
    
    工作原理：
    1. 如果 start_index 为 None，自动查找比 end_index 小的最大 index，设置 start_index = index + 1
    2. 删除 start_index 到 end_index 之间的所有 DrawIteration（包括对应的图片文件）
    3. 创建从 start_index 到 end_index 之间的所有 DrawIteration，状态为 pending（初始化）
    4. 创建循环，从 start_index 开始迭代到 end_index
    5. 每次迭代：
       - 更新 DrawIteration 状态为 drawing
       - 调用 chat_invoke，要求返回 DrawIterationResult（draw_args + 更新后的 summary）
       - 更新 DrawIteration（summary 和 draw_args）
       - 创建绘图任务
       - 调用 bind_image_from_job 绑定图像（完成后更新状态为 completed）
    
    Args:
        project_id: 项目ID
        start_index: 起始行号（从0开始，None表示自动查找比 end_index 小的最大 index，然后设置 start_index = index + 1）
        end_index: 结束行号（从0开始，包含）
    
    Returns:
        包含生成结果信息的字典
    
    Raises:
        HTTPException: 如果项目不存在、LLM 服务未初始化或生成失败
    """
    try:
        project_id = normalize_project_id(project_id)
        
        # 验证项目是否存在
        project = ProjectService.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
        
        # 获取 LLM 服务
        llm_service = get_current_llm_service()
        if not llm_service:
            raise HTTPException(status_code=503, detail="LLM 服务未初始化")
        
        # 1. 如果 start_index 为 None，自动查找比 end_index 小的最大 index
        from api.services.db import DrawIterationService
        from api.schemas.memory import DrawIteration
        from api.utils.path import project_home
        import os
        
        if start_index is None:
            prev_iteration = DrawIterationService.get_max_index_before(project_id, end_index)
            if prev_iteration:
                start_index = prev_iteration.index + 1
            else:
                start_index = 0
        
        # 验证索引范围
        if start_index < 0:
            start_index = 0
        if end_index < start_index:
            raise HTTPException(status_code=400, detail=f"end_index ({end_index}) 必须 >= start_index ({start_index})")
        
        logger.info(f"开始绑定段落图像: project_id={project_id}, start_index={start_index}, end_index={end_index}")
        
        # 2. 删除 start_index 到 end_index 之间的所有 DrawIteration（包括对应的图片文件）
        actual_project_id = project_id if project_id is not None else "default"
        images_dir = project_home / actual_project_id / "images"
        
        deleted_count = DrawIterationService.delete_range(project_id, start_index, end_index)
        logger.info(f"已删除 {deleted_count} 个 DrawIteration 记录: start_index={start_index}, end_index={end_index}")
        
        # 删除对应的图片文件
        for idx in range(start_index, end_index + 1):
            image_path = images_dir / f"{idx}.png"
            if image_path.exists():
                try:
                    os.remove(image_path)
                    logger.info(f"已删除图片文件: {image_path}")
                except Exception as e:
                    logger.warning(f"删除图片文件失败: {image_path}, 错误: {e}")
        
        # 3. 创建从 start_index 到 end_index 之间的所有 DrawIteration，状态为 pending（初始化）
        for idx in range(start_index, end_index + 1):
            iteration = DrawIteration(
                project_id=project_id,
                index=idx,
                status="pending",
                summary=None,
                draw_args=None
            )
            DrawIterationService.create(iteration)
        
        logger.info(f"已创建 {end_index - start_index + 1} 个 DrawIteration 记录（状态：pending）")
        
        # 4. 获取前文摘要（用于迭代）
        prev_iteration = DrawIterationService.get_max_index_before(project_id, start_index)
        if prev_iteration:
            prev_summary = prev_iteration.summary or ""
        else:
            prev_summary = ""
        
        # 2. 获取上下文信息（一次性获取，循环内复用）
        # 2.1 获取所有 memory
        memories = MemoryService.get_all(project_id)
        memory_text = "\n".join([f"- {m.key}: {m.value}" for m in memories]) if memories else "无"
        
        # 2.2 获取所有 actor
        actors = await get_all_actors(project_id=project_id, limit=1000)
        actor_text = "\n".join([f"- {a.name}: {a.desc}" for a in actors]) if actors else "无"
        
        # 2.3 获取可用的 checkpoints 和 loras
        try:
            checkpoints = await get_checkpoints()
        except Exception as e:
            logger.warning(f"获取 checkpoints 失败（可能是 SD-Forge 后端未启动）: {e}")
            checkpoints = []
        
        try:
            loras = await get_loras()
        except Exception as e:
            logger.warning(f"获取 loras 失败（可能是 SD-Forge 后端未启动）: {e}")
            loras = []
        
        checkpoint_text = "\n".join([f"- {c['version_name']} (ecosystem: {c.get('ecosystem', 'unknown')}, base_model: {c.get('base_model', 'unknown')})" for c in checkpoints]) if checkpoints else "无"
        lora_text = "\n".join([f"- {l['version_name']} (ecosystem: {l.get('ecosystem', 'unknown')}, base_model: {l.get('base_model', 'unknown')}, trained_words: {', '.join(l.get('trained_words', []))})" for l in loras]) if loras else "无"
        
        # 2.4 获取全文摘要
        full_summary_obj = SummaryService.get(project_id, -1)
        full_summary_text = full_summary_obj.summary if full_summary_obj and full_summary_obj.summary else "无"
        
        # 3. 构建 DrawIterationResult 的 JSON Schema
        draw_iteration_result_schema = TypeAdapter(DrawIterationResult).json_schema()
        
        # 5. 创建循环，从 start_index 开始迭代到 end_index
        created_jobs = []
        for current_index in range(start_index, end_index + 1):
            # 检查当前索引的 DrawIteration 状态，如果是 cancelled，提前退出
            current_iteration = DrawIterationService.get(project_id, current_index)
            if current_iteration and current_iteration.status == "cancelled":
                logger.info(f"检测到 cancelled 状态，提前退出迭代: project_id={project_id}, index={current_index}")
                break
            
            try:
                # 4.1 获取当前段落内容
                current_content = ContentService.get_by_index(project_id, current_index)
                if not current_content:
                    logger.warning(f"行内容不存在: project_id={project_id}, index={current_index}")
                    continue
                
                # 4.2 获取当前段落所在章节的摘要
                chapter_summary_obj = SummaryService.get(project_id, current_content.chapter)
                chapter_summary_text = chapter_summary_obj.summary if chapter_summary_obj and chapter_summary_obj.summary else "无"
                
                user_message = f"""请为以下段落生成绘图参数和更新摘要：

## ⚠️ 重要要求

### 1. 摘要（summary）生成要求（⚠️ 极其重要）
**摘要必须只反映"当前状态"，不能包含未来的剧透信息！**

**正确的做法：**
- ✅ 摘要应该描述"当前段落发生的事"和"当前的场景状态"
- ✅ 例如："战士A出现在战场上，他手持武器准备战斗"
- ✅ 摘要应该包含具体的场景描述（如"耳鼻喉诊室里有一个医生一个患者"、"坐满学生的教室里"等）
- ✅ 场景描述要具体，方便后续生成图像背景

**错误的做法：**
- ❌ 摘要中不能包含"他后来失去了双腿"这类未来的剧透信息
- ❌ 即使全文摘要或角色信息中提到角色未来会发生什么，也不能写进当前摘要
- ❌ 例如错误示例："战士A是一个战士，他在后来的战争中失去了双腿"（这是错误的，因为当前他还没有失去双腿）

**全文摘要和角色信息的作用：**
- 全文摘要和角色信息只是为了让 LLM 了解整个剧情脉络
- 这些信息帮助 LLM 更好地理解"当前状态"
- 但摘要本身必须只反映"当前情况"，不能包含未来的剧透

**场景描述要求：**
- 摘要必须包含当前场景的具体描述
- 场景描述要足够具体，以便生成图像背景
- 例如："耳鼻喉诊室里有一个医生一个患者"、"坐满学生的教室里"、"战火纷飞的战场"等
- 场景描述应该包括地点、环境、氛围等元素

### 2. 角色识别和绘图参数生成要求（⚠️ 极其重要）
**必须先识别角色，再生成绘图参数！**

**步骤1：识别当前段落中出现的所有角色和人物**
- 仔细分析当前段落内容，识别出现的所有角色
- 区分主要角色（有名字的角色）和路人（无名角色）
- 统计总出现人物的数量（包括角色和路人）
- **重要**：不是所有场景都有人物！有些场景可以只有场景没有人
  - 例如：空无一人的教室、背景设定介绍、环境描写等
  - 如果当前段落只是描述场景或背景设定，没有人物出现，则应该生成只有场景的图像
- 例如："当前段落出现了角色A（主角）、角色B（配角）、3个路人，总共5个人物"
- 或者："当前段落只描述了空无一人的教室，没有人物出现"

**步骤2：判断段落类型和绘图方式**
根据段落内容判断绘图方式：
- **大标题**：出现章节内主要人物，并绘制出主要场景
- **小标题**：所属内容的关键剧情场景（包括关键剧情的段落和人物）
- **普通段落**：根据段落内容决定是否包含人物

**步骤3：结合角色信息和场景生成绘图参数**
- 查询角色信息（actor_text），了解每个角色的特点
- 如果角色有立绘（examples），参考立绘的绘图参数（draw_args）来保持一致性
- **重要**：系统会自动使用角色的默认立绘（第一个立绘）作为 ControlNet reference_only 的参考图像，以保持人物的一致性（面部、身材、肤色等）
- 结合角色的特点（外貌、服装、当前状态）和场景信息生成绘图参数
- **人物数量词使用**：
  - 如果场景中有人物，必须准确使用数量词（如 `1girl`、`1boy`、`2girls`、`3people` 等）来限定出现的人物数量
  - 如果场景中没有人物（只有场景），则不需要使用人物数量词，直接描述场景即可
  - 数量词必须放在 prompt 的开头（如果有的话）

**绘图参数生成要求（遵循核心原则）：**
- **单镜头原则**（⚠️ 极其重要）：
  - 每张图应该只有一个镜头，不要生成包含多个子图的分镜图像
  - 不要在 prompt 中使用"分镜"、"多个画面"、"并排"、"组合"等词汇
  - 确保生成的图像是单一、连贯的场景
- **NSFW 内容处理**（⚠️ 重要）：
  - 如果故事包含 NSFW 内容，绘图应该更体现 NSFW 特色
  - 不要完全平铺直叙，应该根据内容特点生成相应的图像
  - 但必须遵循单镜头原则，不能生成分镜图像
- 角色描述聚焦形象：只描述外貌/姿态/气质，不要包含背景和剧情
- 背景描述：结合摘要中的场景描述，生成图像背景（如"诊室内"、"教室里"、"战场"等）
- 特殊情况：如果角色首次出现，出于介绍目的，背景可以是角色来源地或相关场景（如"战士A来自战火纷飞的非洲"时，背景可以是战火纷飞的感觉）
- 女性角色基准特性：fair skin 或 white skin、beautiful/attractive/elegant、slender body、D cup breasts/贫乳、long hair、detailed face、noble girl
- 画质提示词优先：精简使用 masterpiece、best quality、highres
- 画质反向提示词：worst quality、bad quality、lowres、blurry、ugly、deformed、unattractive、obese、muscular、bad anatomy、extra limbs、mutated hands、poorly drawn face、watermark、text
- 提示词格式：主要使用简单词和词组，避免长句子

### 3. 输出格式要求
必须返回 JSON 格式，包含：
- summary: 更新后的摘要（字符串，只反映当前状态，包含具体场景描述）
- draw_args: 绘图参数（对象，包含 model、prompt、negative_prompt、steps、cfg_scale、sampler、seed、width、height、clip_skip、vae、loras 等字段）
  - prompt 必须：
    - 在开头明确指定人物数量（如 `1girl`、`1boy`、`2girls` 等）
    - 包含角色外貌描述（参考角色信息中的立绘参数）
    - 包含场景背景描述（来自摘要中的场景）
    - 使用简单词和词组，避免长句子

## 上下文信息

## 前文摘要
{prev_summary if prev_summary else "（这是第一段）"}

## 全文摘要（⚠️ 仅供参考，了解剧情脉络，不要将未来的剧透写进当前摘要）
{full_summary_text}

## 当前章节摘要
{chapter_summary_text}

## 当前段落内容
{current_content.content}

## 项目记忆信息
{memory_text}

## 角色信息（包含每个角色的外貌特点和立绘绘图参数，用于保持图像一致性）
{actor_text}

## 可用 Checkpoint 模型
{checkpoint_text}

## 可用 LoRA 模型
{lora_text}

请按照以下步骤处理：
1. **识别角色**：分析当前段落，识别出现的所有角色、路人和总人数
2. **生成摘要**：在前文摘要基础上，结合当前段落内容生成更新后的摘要
   - 摘要必须只反映当前状态，不能包含未来剧透
   - 摘要必须包含具体的场景描述（如"耳鼻喉诊室里有一个医生一个患者"）
3. **生成绘图参数**：
   - 结合角色信息（包括立绘参数）和场景信息
   - 在 prompt 开头明确指定人物数量（如 `1girl`、`1boy` 等）
   - 包含角色外貌描述和场景背景描述

**重要**：必须返回 JSON 格式，包含：
- summary: 更新后的摘要（字符串，只反映当前状态，包含具体场景描述）
- draw_args: 绘图参数（对象，包含 model、prompt、negative_prompt、steps、cfg_scale、sampler、seed、width、height、clip_skip、vae、loras 等字段）"""
                
                # 4.4 调用 chat_invoke，要求返回 DrawIterationResult
                result = await llm_service.chat_invoke(
                    message=user_message,
                    project_id=project_id,
                    output_schema=draw_iteration_result_schema
                )
                
                # 4.5 解析结果
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except json.JSONDecodeError:
                        # 尝试提取 JSON 部分
                        import re
                        json_match = re.search(r'\{[\s\S]*\}', result)
                        if json_match:
                            result = json.loads(json_match.group(0))
                        else:
                            raise HTTPException(status_code=500, detail=f"LLM 返回的内容不包含有效的 JSON: {result[:200]}")
                
                # 4.6 验证并转换为 DrawIterationResult
                try:
                    iteration_result = DrawIterationResult(**result)
                except Exception as e:
                    logger.error(f"解析 DrawIterationResult 失败: {e}, 结果: {result}")
                    raise HTTPException(status_code=500, detail=f"解析 DrawIterationResult 失败: {str(e)}")
                
                # 4.7 更新 DrawIteration 状态为 drawing，并保存 summary 和 draw_args
                DrawIterationService.update(
                    project_id=project_id,
                    index=current_index,
                    status="drawing",
                    summary=iteration_result.summary,
                    draw_args=iteration_result.draw_args.model_dump()
                )
                logger.info(f"已更新 DrawIteration 状态为 drawing: project_id={project_id}, index={current_index}")
                
                # 4.8 创建绘图任务
                draw_args = iteration_result.draw_args
                
                # 4.8.1 识别段落中出现的角色，并添加默认立绘作为 ControlNet reference_only 参考
                # 分析段落内容和角色信息，找出出现的角色
                actors_in_content = []
                if actors and current_content.content:
                    # 简单的角色名称匹配：检查段落内容中是否包含角色名称
                    content_lower = current_content.content.lower()
                    for actor in actors:
                        # 检查角色名称是否出现在段落内容中
                        if actor.name and actor.name.lower() in content_lower:
                            # 检查角色是否有立绘（examples 不为空且有有效的 filename）
                            if actor.examples:
                                # 查找第一个有效的立绘（filename 存在且不是正在生成的）
                                for example_dict in actor.examples:
                                    example_filename = example_dict.get('filename') or example_dict.get('image_path')
                                    if example_filename and not str(example_filename).startswith('generating_'):
                                        actors_in_content.append({
                                            'actor': actor,
                                            'example_filename': example_filename,
                                            'example_index': actor.examples.index(example_dict)
                                        })
                                        break  # 只使用第一个有效的立绘
                
                # 如果找到角色，使用第一个角色的立绘作为参考（优先选择主角或重要角色）
                # 排序：优先选择主角（tags 中包含"主角"或"角色定位"为"主角"的）
                if actors_in_content:
                    # 按照重要性排序：主角 > 主要角色 > 配角
                    def get_role_priority(actor_info):
                        actor = actor_info['actor']
                        tags = actor.tags or {}
                        role = tags.get('角色定位', '')
                        if '主角' in role or role == '主角':
                            return 0
                        elif role in ['男1', '女1', '男2', '女2']:
                            return 1
                        else:
                            return 2
                    
                    actors_in_content.sort(key=get_role_priority)
                    selected_actor_info = actors_in_content[0]
                    selected_actor = selected_actor_info['actor']
                    example_filename = selected_actor_info['example_filename']
                    
                    # 构建立绘的完整文件路径
                    # 路径格式：projects/{project_id}/actors/{actor_name}/{filename}
                    actual_project_id = selected_actor.project_id if selected_actor.project_id is not None else "default"
                    from api.utils.path import project_home
                    portrait_path = project_home / actual_project_id / "actors" / selected_actor.name / example_filename
                    
                    # 检查文件是否存在
                    if portrait_path.exists() and portrait_path.is_file():
                        # 将立绘路径添加到 draw_args
                        draw_args.reference_image_path = str(portrait_path)
                        draw_args.reference_weight = 0.8  # 默认权重 0.8
                        logger.info(f"✅ 已为角色 {selected_actor.name} 添加 ControlNet reference_only 参考: {portrait_path}")
                    else:
                        logger.warning(f"⚠️ 角色 {selected_actor.name} 的立绘文件不存在: {portrait_path}")
                
                # 直接使用绘图服务（已在顶部导入）
                draw_service = get_current_draw_service()
                if not draw_service:
                    error_msg = "绘图服务未初始化（请检查 SD-Forge 后端是否已启动）"
                    logger.error(error_msg)
                    raise HTTPException(status_code=503, detail=error_msg)
                
                # 创建绘图任务
                try:
                    job_id = draw_service.draw(
                        args=draw_args,
                        name=f"段落图像-{current_index}",
                        desc=f"为第 {current_index} 行段落生成图像"
                    )
                    logger.info(f"已创建绘图任务: project_id={project_id}, index={current_index}, job_id={job_id}")
                except Exception as draw_error:
                    error_msg = f"创建绘图任务失败（可能是 SD-Forge 后端未启动或连接失败）: {str(draw_error)}"
                    logger.error(error_msg)
                    raise HTTPException(status_code=503, detail=error_msg) from draw_error
                
                # 4.9 调用 bind_image_from_job 绑定图像
                from api.routers.content import bind_image_from_job
                bind_result = await bind_image_from_job(
                    project_id=project_id,
                    job_id=job_id,
                    index=current_index
                )
                
                created_jobs.append({
                    "index": current_index,
                    "job_id": job_id,
                    "completed": bind_result.get("completed", False)
                })
                
                # 4.10 更新 prev_summary 用于下一轮迭代
                prev_summary = iteration_result.summary
                
            except Exception as e:
                logger.exception(f"处理段落失败: project_id={project_id}, index={current_index}, error={e}")
                # 继续处理下一个段落，不中断整个流程
                # 如果出错，将状态设置为 failed（可选，或者保持 drawing 状态）
                continue
        
        logger.info(f"绑定段落图像完成: project_id={project_id}, 处理了 {len(created_jobs)} 个段落")
        
        return {
            "success": True,
            "project_id": project_id,
            "start_index": start_index,
            "end_index": end_index,
            "processed_count": len(created_jobs),
            "jobs": created_jobs,
            "message": f"成功处理 {len(created_jobs)} 个段落"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"绑定段落图像失败: {e}")
        raise HTTPException(status_code=500, detail=f"绑定段落图像失败: {str(e)}")


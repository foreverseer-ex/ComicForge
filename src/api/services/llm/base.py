"""
LLM 服务基础抽象类。

定义所有 LLM 服务的统一接口。
"""
import functools
import json
from abc import ABC, abstractmethod
from typing import Optional, List, AsyncGenerator, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import ToolMessage, AIMessage
from langchain_core.tools import tool, BaseTool
from langgraph.graph.state import CompiledStateGraph
from loguru import logger
from pydantic_core import to_jsonable_python
from api.services.db.project_service import ProjectService
from api.constants.llm import (
    DEVELOP_MODE_PROMPTS, MCP_TOOLS_GUIDE,
    ERROR_SD_FORGE_CONNECTION, ERROR_CONNECTION_FAILED, ERROR_TOOL_CALL_FAILED,
    ERROR_TIMEOUT_TEMPLATE, ERROR_CONNECTION_TEMPLATE,
    SESSION_INFO_TEMPLATE,
    SUMMARY_MESSAGE_TEMPLATE, ITERATION_GUIDE, ITERATION_PROMPT_TEMPLATE, FINAL_OPERATION_PROMPT_TEMPLATE,
)
from api.routers.actor import (
    create_actor, get_actor, get_all_actors, update_actor,
    remove_actor, get_tag_description, get_all_tag_descriptions,
    add_example, remove_example, add_portrait_from_batch_tool, add_portrait_from_job_tool
)
from api.routers.draw import (
    create_draw_job, create_batch_job, batch_from_jobs,
    get_draw_job, delete_draw_job, get_image,
)
from api.routers.model_meta import (
    get_loras, get_checkpoints,
)

from api.routers.memory import (
    create_memory, get_memory, get_all_memories, update_memory,
    delete_memory, clear_memories, get_key_description, get_all_key_descriptions,
)
# ============================================================================
# ⚠️ 安全要求：所有MCP工具函数必须来自routers，不能直接调用服务函数
# ============================================================================
# 导入所有路由函数（这些函数经过路由层验证，确保安全性）
# 注意：绝对不能导入 services 层的函数，只能使用 routers 层的函数
from api.routers.project import (
    get_project, update_project,
)
from api.routers.context import (
    get_line, get_chapter_lines, get_lines_range, get_chapters,
    get_chapter, update_chapter, get_stats, get_project_content,
)
from api.schemas.chat import ChatMessage, ChatIteration
from api.services.db import MemoryService, HistoryService
from api.settings import app_settings


def tool_wrapper(func):
    """包装工具函数，确保返回值符合 OpenAI API 要求，并处理异常。"""

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            result = to_jsonable_python(result)
            if not isinstance(result, (list, dict)):
                # 基本类型，比如字符串
                return [result]
            if len(result) == 0:
                return ['无结果']
            return result
        except Exception as e:
            # 捕获工具调用中的异常，返回友好的错误消息
            error_str = str(e).lower()
            error_type = type(e).__name__

            # 检查是否是SD-Forge连接错误
            is_sd_forge_error = (
                    "sd-forge" in error_str or
                    "502" in error_str or
                    "bad gateway" in error_str or
                    "502 bad gateway" in error_str or
                    error_type == "HTTPException" and "502" in str(e)
            )

            if is_sd_forge_error:
                logger.warning(f"⚠️ SD-Forge 连接失败（工具: {func.__name__}）: {e}")
                return ERROR_SD_FORGE_CONNECTION

            # 检查是否是网络连接错误
            is_connection_error = (
                    "connection" in error_str or
                    "connect" in error_str or
                    "连接" in error_str or
                    "network" in error_str or
                    "网络" in error_str or
                    error_type in ("APIConnectionError", "ConnectError", "ConnectTimeout", "ReadTimeout",
                                   "HTTPException")
            )

            if is_connection_error:
                logger.warning(f"⚠️ 工具调用连接失败（工具: {func.__name__}）: {e}")
                return ERROR_CONNECTION_FAILED.format(error=str(e))

            # 其他错误
            logger.exception(f"❌ 工具调用失败（工具: {func.__name__}）: {e}")
            return ERROR_TOOL_CALL_FAILED.format(error=str(e))

    return async_wrapper


class AbstractLlmService(ABC):
    """
    LLM 服务抽象基类。
    
    定义统一的 LLM 接口，支持不同的提供商（OpenAI、Ollama 等）。
    """

    def __init__(self):
        """初始化服务。"""
        self.llm: Optional[BaseChatModel] = None
        self.agent: Optional[CompiledStateGraph] = None
        self.tools: List[BaseTool] = []
        self._initialize_tools()


    def _initialize_tools(self):
        """初始化工具函数列表。"""

        all_functions = [
            # Project 管理（只允许查询和更新，不允许创建和删除）
            get_project, update_project,
            # Actor 管理
            create_actor, get_actor, get_all_actors, update_actor,
            remove_actor, add_example, remove_example, add_portrait_from_batch_tool, add_portrait_from_job_tool,
            get_tag_description, get_all_tag_descriptions,
            # Memory 管理
            create_memory, get_memory, get_all_memories, update_memory,
            delete_memory, clear_memories, get_key_description, get_all_key_descriptions,
            # Reader / Context 功能（使用合并后的 context 接口）
            get_line, get_chapter_lines, get_lines_range, get_chapters,
            get_chapter, update_chapter, get_stats,
            # 项目/内容管理
            get_project_content,
            # 建议写入工具（支持负索引）
            self._add_suggestions,
            # Draw 功能
            get_loras, get_checkpoints, 
            create_draw_job, create_batch_job, batch_from_jobs,
            get_draw_job, delete_draw_job, get_image,
        ]
        # 先包装，再转换为工具
        self.tools = [tool(tool_wrapper(func)) for func in all_functions]
        logger.info(f"已初始化 {len(self.tools)} 个工具函数")

    @abstractmethod
    def initialize_llm(self, response_format: Optional[Any] = None) -> bool:
        """
        初始化 LLM 实例。
        
        由子类实现具体的 LLM 初始化逻辑（如 ChatOpenAI、ChatOllama 等）。
        
        :param response_format: 可选的响应格式（Pydantic 模型类），用于结构化输出
        :return: 初始化是否成功
        """
        raise NotImplementedError

    def get_session_context(self, project_id: Optional[str]) -> Optional[str]:
        """
        获取当前项目的上下文信息（包括项目基本信息和所有记忆条目）。
        
        :param project_id: 项目 ID（None 表示默认工作空间）
        :return: 格式化的项目信息（JSON 字符串），如果项目不存在则返回默认工作空间的记忆信息
        """
        try:
            # 查询所有记忆条目（支持 project_id 为 None）
            memories = MemoryService.get_all(project_id=project_id, limit=1000)

            # 构建记忆字典（按 key 分组）
            memories_dict = {}
            for memory in memories:
                memories_dict[memory.key] = {
                    "value": memory.value,
                    "description": memory.description,
                }



            # 查询项目信息（项目不存在时返回 None，不抛出异常）
            project = ProjectService.get(project_id)
            if not project:
                logger.debug(f"项目不存在: {project_id}，只返回记忆信息")
                # 项目不存在，但返回记忆信息
                default_context = {
                    'project_id': None,
                    "description": "目前在临时工作空间中，具有临时记忆和临时角色，但是没有项目内容"
                                   "注意project_id是python类型None，不是空字符串或者null什么都"
                }
                session_info = SESSION_INFO_TEMPLATE.format(
                    context_json=json.dumps(default_context, ensure_ascii=False, indent=2),
                    memories_count=len(memories),
                    memories_dict_json=json.dumps(memories_dict, ensure_ascii=False, indent=2),
                )
                return session_info

            # 构建项目上下文信息
            context = {
                "project_id": project.project_id,
                "title": project.title,
                "novel_path": project.novel_path,
                "total_lines": project.total_lines,
                "total_chapters": project.total_chapters,
                "current_line": project.current_line,
                "current_chapter": project.current_chapter,
            }

            # 格式化为 JSON 字符串，包含提示信息
            session_info = SESSION_INFO_TEMPLATE.format(
                context_json=json.dumps(context, ensure_ascii=False, indent=2),
                memories_count=len(memories),
                memories_dict_json=json.dumps(memories_dict, ensure_ascii=False, indent=2),
            )

            return session_info

        except Exception as e:
            logger.exception(f"获取项目上下文失败: {e}")
            return None

    def build_system_messages(self) -> list[tuple[str, str]]:
        """
        构建基础系统消息列表（不包含项目上下文）。

        :return: 包含系统提示词的元组列表
        """
        # 构建消息列表
        messages = []

        # 1. 如果启用开发者模式，添加开发者模式提示词
        if app_settings.llm.developer_mode:
            messages.append(("system", DEVELOP_MODE_PROMPTS))

        # 2. 如果配置了系统提示词（非空），添加系统提示词
        if app_settings.llm.system_prompt and app_settings.llm.system_prompt.strip():
            messages.append(("system", app_settings.llm.system_prompt))

        # 3. 添加 MCP 工具使用指南（已包含工具调用提示和建议功能要求）
        messages.append(("system", MCP_TOOLS_GUIDE))
        
        # 4. 添加建议条数配置
        suggestion_config = f"""
**建议条数配置**：
- **文字建议条数**：{app_settings.llm.text_suggestion_count} 条（每次对话后提供的文字操作建议数量）
- **图片建议条数**：{app_settings.llm.image_suggestion_count} 条（生成立绘等图像时提供的选项数量）
- **⚠️ 重要**：建议只能是纯文字或纯图片，不能同时返回文字建议和图片建议。如果生成了图片任务，必须只返回图片建议；否则只返回文字建议。
"""
        messages.append(("system", suggestion_config))

        # 合并记录所有系统提示词
        if len(messages) > 0:
            logger.debug(
                f"已添加 {len(messages)} 条基础系统提示词（开发者模式、系统提示词、MCP指南、建议配置）")
        return messages

    async def chat_invoke(self, message: str, project_id: Optional[str] = None,
                          output_schema: Optional[Any] = None) -> str:
        """
        调用 LLM 并返回结果（非流式，用于工具调用）。
        
        :param message: 用户消息
        :param project_id: 项目 ID（可选）
        :param output_schema: 输出模式（可选，Pydantic 模型类，如果不指定则默认返回文本）
        :return: LLM 的回复内容（如果是结构化输出，返回 JSON 字符串；否则返回文本）
        """
        logger.info(f"🔧 工具调用 LLM: {message[:1000]}{'...' if len(message) > 1000 else ''}")

        try:
            # 1. 构建系统消息（不包含历史消息和摘要）
            messages = self.build_system_messages()

            # 2. 添加项目上下文信息（支持 project_id=None，表示默认工作空间）
            session_info = self.get_session_context(project_id)
            if session_info:
                messages.append(("system", session_info))

            # 3. 如果 project_id 为 None，添加工具使用说明
            if project_id is None:
                from api.constants.llm import NO_PROJECT_ID_WARNING
                messages.append(("system", NO_PROJECT_ID_WARNING))

            # 4. 添加用户消息
            messages.append(("human", message))

            # 5. 如果有输出 schema，需要重新初始化 agent 以支持结构化输出
            if output_schema is not None:
                logger.info(
                    f"使用结构化输出，schema: {output_schema.__name__ if hasattr(output_schema, '__name__') else type(output_schema)}")
                # 重新初始化 agent 以支持结构化输出（同时保留工具调用能力）
            self.initialize_llm(response_format=output_schema)

            # 6. 调用 agent（使用异步调用）
            logger.info(f"开始调用 LLM，使用 {len(self.tools)} 个工具" + (
                f"，结构化输出: {output_schema.__name__ if output_schema else '无'}" if output_schema else ""))
            config = {"recursion_limit": app_settings.llm.recursion_limit}
            result: dict = await self.agent.ainvoke({"messages": messages}, config=config, stream_mode='values')
            result_message: AIMessage = result['messages'][-1]
            context = result_message.content  # json text

            # 7. 如果有结构化输出，直接返回文本（LLM 已经返回了 JSON）
            if output_schema is not None:
                logger.info(f"✅ LLM 调用完成，返回结构化输出，长度={len(context)}")
                return context

            # 8. 如果没有结构化输出，返回普通文本内容
            logger.info(f"✅ LLM 调用完成，返回长度={len(context)}")
            logger.debug(f"最终提取的内容: {context[:500] if context else '(空)'}")
            return context

        except Exception as e:
            logger.exception(f"LLM 调用失败: {e}")
            return f"错误：LLM 调用失败 - {str(e)}"

    def summary_history(self, project_id: Optional[str]):
        """
        自动生成聊天摘要（当消息数量达到 summary_epoch 的倍数时）。
        
        :param project_id: 项目ID（None 表示默认工作空间，不生成摘要）
        """
        # 无项目时不生成摘要（ChatSummary 的 project_id 是主键，不能为 None）
        if project_id is None:
            return
        count = HistoryService.count(project_id)
        res_round = count % app_settings.llm.summary_epoch

        if count > 0 and res_round == 0:
            try:
                # 获取最近的消息
                start_index = count - app_settings.llm.summary_epoch
                messages = self.build_system_messages()

                # 添加项目上下文信息
                session_info = self.get_session_context(project_id)
                if session_info:
                    messages.append(("system", session_info))

                recent_messages = HistoryService.get_all(project_id, start_index=start_index, end_index=count)

                # 获取现有摘要
                chat_summary = MemoryService.get_summary(project_id)
                summary_value = chat_summary.data if chat_summary and chat_summary.data else ""

                # 构建摘要提示词
                summary_message = SUMMARY_MESSAGE_TEMPLATE.format(
                    previous_rounds=count - app_settings.llm.summary_epoch,
                    summary_value=summary_value,
                    recent_rounds=app_settings.llm.summary_epoch,
                    recent_messages=json.dumps(
                        [{"role": msg.role, "context": msg.context} for msg in recent_messages],
                        ensure_ascii=False,
                        indent=2
                    ),
                )
                messages.append(("system", summary_message))

                # 调用 agent 生成摘要
                result = self.agent.invoke({"messages": messages})

                # 提取摘要文本
                summary_text = ""
                if hasattr(result, "messages") and result.messages:
                    last_msg = result.messages[-1]
                    if hasattr(last_msg, "content"):
                        summary_text = last_msg.content
                    elif isinstance(last_msg, dict) and "content" in last_msg:
                        summary_text = last_msg["content"]

                # 保存摘要
                if summary_text:
                    MemoryService.update_summary(project_id, summary_text)
                    logger.info(f"已生成聊天摘要: {project_id}, 长度={len(summary_text)}")
            except Exception as e:
                logger.exception(f"生成聊天摘要失败: {e}")

    async def chat_streamed(self, message: str, project_id: Optional[str] = None) -> AsyncGenerator[dict, None]:
        """
        增强的流式对话方法，返回结构化事件。
        
        :param message: 用户消息
        :param project_id: 项目 ID
        :yield: 事件字典，包含 type 和相应的数据
        """
        self.initialize_llm()
        logger.info(f"👤 用户消息: {message[:200]}{'...' if len(message) > 200 else ''}")

        # 创建助手消息的 ID（提前创建，用于实时更新）
        assistant_context = ""
        assistant_tools: list[dict] = []
        assistant_suggests: list[str] = []

        try:
            # 1. 构建系统消息和历史消息
            messages = self.build_system_messages()

            # 添加项目上下文信息
            session_info = self.get_session_context(project_id)
            if session_info:
                messages.append(("system", session_info))

            # 生成摘要（仅在有项目时）
            if project_id:
                self.summary_history(project_id)
                chat_summary_memory = MemoryService.get_summary(project_id)
            else:
                chat_summary_memory = None

            # 2. 创建用户消息并写入数据库（ID 会自动生成）
            user_message = ChatMessage(
                project_id=project_id,
                role="user",
                context=message,
                status="ready",
                message_type="normal"
            )
            user_message = HistoryService.create(user_message)

            # 3. 获取历史消息（用于上下文）
            start_index = max(0, HistoryService.count(project_id) - app_settings.llm.summary_epoch)
            messages_to_include = HistoryService.get_all(project_id, start_index=start_index)

            # 4. 如果有聊天摘要，添加到系统消息
            if chat_summary_memory and chat_summary_memory.data:
                summary_message = SUMMARY_MESSAGE_TEMPLATE.format(
                    previous_rounds=start_index,
                    summary_value=chat_summary_memory.data,
                    recent_rounds=len(messages_to_include),
                )
                messages.append(("system", summary_message))

            # 5. 添加历史消息到 langchain 消息列表
            for msg in messages_to_include:
                if msg.role == "user":
                    messages.append(("human", msg.context))
                elif msg.role == "assistant":
                    messages.append(("ai", msg.context))

            # 6. 创建初始助手消息（状态为 thinking，ID 会自动生成）
            assistant_message = ChatMessage(
                project_id=project_id,
                role="assistant",
                context="",
                status="thinking",
                message_type="normal",
                tools=[],
                suggests=[]
            )
            assistant_message = HistoryService.create(assistant_message)
            assistant_message_id = assistant_message.message_id

            # 发送消息ID
            yield {'type': 'message_id', 'message_id': assistant_message_id}
            yield {'type': 'status', 'status': 'thinking'}

            # 7. 实现流式对话逻辑
            logger.info(f"开始流式对话，使用 {len(self.tools)} 个工具")
            config = {"recursion_limit": app_settings.llm.recursion_limit}

            async for chunk in self.agent.astream_events(
                    {"messages": messages},
                    version="v2",
                    config=config
            ):
                event_type = chunk.get("event")

                # 处理文本流事件
                if event_type == "on_chat_model_stream":
                    message_chunk = chunk.get("data", {}).get("chunk")
                    if message_chunk and hasattr(message_chunk, "content") and message_chunk.content:
                        content = message_chunk.content
                        assistant_context += content

                        # 实时更新数据库中的助手消息
                        assistant_message.context = assistant_context
                        assistant_message.tools = assistant_tools.copy()
                        HistoryService.update(assistant_message)

                        yield {'type': 'content', 'content': content}

                # 处理工具调用开始事件
                elif event_type == "on_tool_start":
                    tool_name = chunk.get("name", "")
                    
                    # 处理工具调用（内部函数不会被添加到列表）
                    self._process_tool_start_event(chunk, assistant_tools)

                    # 更新数据库
                    assistant_message.tools = assistant_tools.copy()
                    HistoryService.update(assistant_message)

                    # 只为非内部函数发送工具调用事件
                    if not tool_name.startswith("_"):
                        tool_input = chunk.get("data", {}).get("input", {})
                        yield {
                            'type': 'tool_start',
                            'name': tool_name,
                            'args': tool_input if isinstance(tool_input, dict) else {}
                        }
                        # 发送完整的工具列表
                        yield {'type': 'tools', 'tools': assistant_tools.copy()}

                # 处理工具调用结束事件
                elif event_type == "on_tool_end":
                    tool_name = chunk.get("name", "")
                    tool_output: ToolMessage = chunk.get("data", {}).get("output")
                    logger.info(
                        f"✅ 工具调用完成: {tool_name}, 结果长度={len(str(tool_output.content)) if tool_output.content else 0}")

                    # 处理工具调用结束（内部函数不会被更新到列表）
                    self._process_tool_end_event(chunk, assistant_tools)

                    # 更新数据库
                    assistant_message.tools = assistant_tools.copy()
                    HistoryService.update(assistant_message)

                    # 只为非内部函数发送工具调用结束事件
                    if not tool_name.startswith("_"):
                        yield {
                            'type': 'tool_end',
                            'name': tool_name,
                            'result': tool_output.content
                        }
                        # 发送完整的工具列表
                        yield {'type': 'tools', 'tools': assistant_tools.copy()}

                    # 特殊处理：如果工具是 add_choices，更新 suggests
                    if tool_name == "add_choices":
                        from api.routers.llm import _session_choices
                        choices = _session_choices.get(project_id, [])
                        suggests = []
                        for choice in choices:
                            if isinstance(choice, dict):
                                if choice.get("type") == "image":
                                    suggests.append(f"image:{choice.get('url', '')}")
                                elif choice.get("type") == "text":
                                    suggests.append(choice.get("text", ""))
                            elif isinstance(choice, str):
                                suggests.append(choice)
                        assistant_message.suggests = suggests
                        assistant_suggests = suggests
                        HistoryService.update(assistant_message)

                        # 发送建议更新
                        yield {'type': 'suggests', 'suggests': suggests}

            # 8. 对话完成，更新助手消息状态为 ready
            assistant_message.status = "ready"
            assistant_message.context = assistant_context
            assistant_message.tools = assistant_tools.copy()
            HistoryService.update(assistant_message)

            yield {'type': 'status', 'status': 'ready'}
            logger.info(f"✅ 对话完成: {len(assistant_context)} 字符, {len(assistant_tools)} 个工具调用")

        except Exception as e:
            logger.exception(f"对话失败: {e}")

            # 检查是否是网络连接错误或超时错误
            error_type = type(e).__name__
            error_str = str(e).lower()

            is_connection_error = (
                    "connection" in error_str or
                    "connect" in error_str or
                    "连接" in error_str or
                    "network" in error_str or
                    "网络" in error_str or
                    error_type in ("APIConnectionError", "ConnectError", "ConnectTimeout", "ReadTimeout")
            )

            is_timeout_error = (
                    "timeout" in error_str or
                    "超时" in error_str or
                    error_type in ("TimeoutError", "ConnectTimeout", "ReadTimeout")
            )

            if is_connection_error or is_timeout_error:
                if is_timeout_error:
                    error_msg = ERROR_TIMEOUT_TEMPLATE.format(timeout=app_settings.llm.timeout)
                else:
                    error_msg = ERROR_CONNECTION_TEMPLATE
            else:
                error_msg = f"错误：{e}"

            # 更新助手消息为错误状态（如果已创建）
            if 'assistant_message' in locals() and assistant_message:
                try:
                    assistant_message.status = "error"
                    assistant_message.context = error_msg
                    HistoryService.update(assistant_message)
                except Exception as update_error:
                    logger.warning(f"更新助手消息失败: {update_error}")

            yield {'type': 'status', 'status': 'error'}
            yield {'type': 'error', 'error': error_msg}

    async def chat_text_only(self, message: str, project_id: str) -> AsyncGenerator[str, None]:
        """
        与 LLM 进行标准对话（流式返回）。
        
        这是 `chat_streamed` 的包装器，只返回文本内容片段。
        内部调用 `chat_streamed` 并提取 `content` 事件。
        
        :param message: 用户消息
        :param project_id: 项目 ID
        :yield: LLM 响应的文本片段
        """
        self.initialize_llm()
        async for event in self.chat_streamed(message, project_id):
            if event.get('type') == 'content':
                yield event.get('content', '')
            elif event.get('type') == 'error':
                yield event.get('error', '错误：未知错误')
                return

    async def chat_iteration(self, iteration_data: dict, project_id: str) -> AsyncGenerator[str, None]:
        """
        迭代模式专用方法。
        
        完全基于数据库操作：
        - 迭代数据存储在 ChatMessage 的 data 字段中（ChatIteration 对象）
        - 实时更新迭代进度到数据库
        - 最终操作的工具调用记录到 tools 字段
        
        通用迭代管理：
        1. 每次迭代，让 LLM 自行调用工具处理当前 index 的内容
        2. LLM 处理完成后，更新 index += step
        3. 累积 summary
        4. 当 index >= stop 时，执行最终操作并退出
        
        :param iteration_data: 迭代数据字典（包含 message_id 或完整的迭代信息）
        :param project_id: 项目ID
        :yield: LLM响应的文本片段
        """
        self.initialize_llm()
        # 1. 获取或创建迭代消息
        if "message_id" in iteration_data:
            # 从数据库读取现有迭代消息
            iteration_message = HistoryService.get(iteration_data["message_id"])
            if not iteration_message or iteration_message.project_id != project_id:
                logger.error(f"迭代消息不存在: {iteration_data['message_id']}")
                yield "错误：迭代消息不存在"
                return
            iteration = ChatIteration(**iteration_message.data)
        else:
            # 创建新的迭代消息（ID 会自动生成）
            iteration = ChatIteration(**iteration_data)
            iteration_message = ChatMessage(
                project_id=project_id,
                role="assistant",
                context="",
                status="thinking",
                message_type="iteration",
                data=iteration.model_dump(),
                tools=[],
                suggests=[]
            )
            iteration_message = HistoryService.create(iteration_message)

        # 2. 迭代循环
        while iteration.index < iteration.stop:
            # 构建迭代模式专用提示词
            iteration_prompt = self._build_iteration_prompt(iteration, project_id)

            # 调用LLM处理当前迭代（迭代过程中不记录工具调用，只累积summary）
            full_response = ""
            async for chunk in self._call_llm_in_iteration_mode(iteration_prompt, project_id):
                full_response += chunk
                yield chunk

            # 更新summary（将LLM的响应追加到summary）
            if iteration.summary:
                iteration.summary += "\n\n"
            iteration.summary += f"[第 {iteration.index // iteration.step + 1} 次迭代] {full_response}"

            # 更新index（将步长叠加到index）
            iteration.index += iteration.step

            # 更新数据库中的迭代消息
            iteration_message.data = iteration.model_dump()
            iteration_message.status = "thinking"
            HistoryService.update(iteration_message)

            logger.debug(
                f"已更新迭代消息进度: index={iteration.index}/{iteration.stop}, "
                f"summary长度={len(iteration.summary) if iteration.summary else 0}")

            # 检查是否迭代终止
            if iteration.index >= iteration.stop:
                break

        # 3. 迭代完成，执行最终操作
        logger.info(f"迭代完成，开始执行最终操作：{iteration.target}")
        final_prompt = self._build_final_operation_prompt(iteration)

        # 清空之前的工具调用（只保留最终操作的工具调用）
        final_tools: list[dict] = []
        final_context_ref = [""]  # 使用列表引用以便修改

        # 4. 调用LLM执行最终操作（记录工具调用）
        async for chunk in self._call_llm_final_operation(final_prompt, project_id, final_tools, final_context_ref):
            yield chunk

        # 5. 更新迭代消息（标记为完成，包含最终操作的工具调用）
        iteration_message.status = "ready"
        iteration_message.context = final_context_ref[0]
        iteration_message.tools = final_tools.copy()
        iteration_message.data = iteration.model_dump()
        HistoryService.update(iteration_message)

        logger.info(
            f"✅ 迭代完成: index={iteration.index}/{iteration.stop}, "
            f"summary长度={len(iteration.summary)}, 工具调用数={len(final_tools)}")

    def _build_iteration_prompt(self, iteration: ChatIteration, project_id: str) -> str:
        """构建迭代模式提示词"""
        progress_percent = iteration.index * 100 // iteration.stop if iteration.stop > 0 else 0
        is_near_completion = "是" if iteration.index + iteration.step >= iteration.stop else "否"
        summary_display = iteration.summary if iteration.summary else "（暂无）"

        return ITERATION_PROMPT_TEMPLATE.format(
            target=iteration.target,
            index=iteration.index,
            step=iteration.step,
            stop=iteration.stop,
            progress_percent=progress_percent,
            is_near_completion=is_near_completion,
            summary_display=summary_display,
        )

    def _build_final_operation_prompt(self, iteration: ChatIteration) -> str:
        """构建最终操作提示词"""
        iterations_count = iteration.stop // iteration.step if iteration.step > 0 else 0

        return FINAL_OPERATION_PROMPT_TEMPLATE.format(
            target=iteration.target,
            stop=iteration.stop,
            iterations_count=iterations_count,
            summary=iteration.summary,
        )

    async def _call_llm_in_iteration_mode(self, prompt: str, project_id: str) -> AsyncGenerator[str, None]:
        """
        在迭代模式下调用LLM（不记录到history，只用于累积summary）。
        """
        # 构建消息列表
        messages = []

        # 添加系统提示词
        if app_settings.llm.developer_mode:
            messages.append(("system", DEVELOP_MODE_PROMPTS))

        if app_settings.llm.system_prompt:
            messages.append(("system", app_settings.llm.system_prompt))

        # 添加迭代模式专用指南
        messages.append(("system", ITERATION_GUIDE))

        # 添加当前提示词
        messages.append(("human", prompt))

        # 配置递归限制（用于迭代模式等需要大量工具调用的场景）
        config = {"recursion_limit": app_settings.llm.recursion_limit}

        # 调用LLM（不记录到history）
        full_response = ""
        async for chunk in self.agent.astream_events({"messages": messages}, version="v2", config=config):
            event_type = chunk.get("event")

            if event_type == "on_chat_model_stream":
                message_chunk = chunk.get("data", {}).get("chunk")
                if message_chunk and hasattr(message_chunk, "content"):
                    content = message_chunk.content
                    if content:
                        full_response += content
                        yield content

        # 迭代过程中的工具调用不需要记录（用户要求）

    def _process_tool_start_event(self, chunk: dict, tools_list: list, log_prefix: str = "") -> None:
        """
        处理工具调用开始事件的通用方法。
        
        :param chunk: 事件 chunk
        :param tools_list: 工具调用列表（会被更新）
        :param log_prefix: 日志前缀（可选）
        """
        tool_name = chunk.get("name", "")
        tool_input = chunk.get("data", {}).get("input", {})
        prefix = f"[{log_prefix}] " if log_prefix else ""
        logger.info(f"✅ {prefix}工具调用: {tool_name}, 参数: {tool_input}")

        # 跳过以 _ 开头的内部函数（如 _add_suggestions）
        if tool_name.startswith("_"):
            logger.debug(f"跳过内部函数工具调用记录: {tool_name}")
            return

        args = tool_input if isinstance(tool_input, dict) else {}
        if 'request' in args and len(args) == 1:
            args = args['request']

        tool_call = {
            "name": tool_name,
            "args": args,
            "result": None
        }
        tools_list.append(tool_call)

    def _process_tool_end_event(self, chunk: dict, tools_list: list, log_prefix: str = "") -> None:
        """
        处理工具调用结束事件的通用方法。
        
        :param chunk: 事件 chunk
        :param tools_list: 工具调用列表（会被更新）
        :param log_prefix: 日志前缀（可选）
        """
        tool_name = chunk.get("name", "")
        tool_output: ToolMessage = chunk.get("data", {}).get("output")
        prefix = f"[{log_prefix}] " if log_prefix else ""
        logger.info(f"✅ {prefix}工具调用完成: {tool_name}")

        # 跳过以 _ 开头的内部函数（如 _add_suggestions）
        if tool_name.startswith("_"):
            logger.debug(f"跳过内部函数工具调用结果记录: {tool_name}")
            return

        if tools_list:
            try:
                result = json.loads(tool_output.content)
            except (json.JSONDecodeError, TypeError):
                # 可能是基本类型，比如字符串
                result = tool_output.content
            tools_list[-1]["result"] = result
            tools_list[-1]["status"] = tool_output.status
            tools_list[-1]["tool_call_id"] = tool_output.tool_call_id

    async def _add_suggestions(self, project_id: Optional[str], index: int, suggests: list) -> None:
        """
        将建议写入指定索引的消息（支持负索引）。

        说明：部分代码会以负索引表示从末尾倒数的位置（例如 -1 表示最后一条消息），
        这里需要将负索引转换为实际索引后再进行更新。

        :param project_id: 会话/项目 ID（None 表示默认工作空间）
        :param index: 消息索引，支持负数（-1 表示最后一条）
        :param suggests: 建议列表
        """
        if project_id=='null':
            project_id=None
        try:
            # 负索引支持：将 -1 表示最后一条转换为实际索引
            if index < 0:
                count = HistoryService.count(project_id)
                index = count + index

            # 获取目标消息并更新 suggests
            message = HistoryService.get_by_index(project_id, index)
            if not message:
                logger.debug(f"尝试为不存在的消息添加建议: project={project_id}, index={index}")
                return

            message.suggests = suggests or []
            HistoryService.update(message)
            logger.debug(f"已为消息添加建议: project={project_id}, index={index}, suggests_count={len(message.suggests)}")
        except Exception as e:
            logger.exception(f"添加建议失败: project={project_id}, index={index}, error={e}")

    async def _call_llm_final_operation(
            self,
            prompt: str,
            project_id: str,
            tools_list: list,
            context_ref: list
    ) -> AsyncGenerator[str, None]:
        """
        调用LLM执行最终操作（允许所有工具，记录到传入的列表）。
        
        这是 `chat_streamed` 的简化版本，使用自定义消息列表，不写入数据库。
        
        :param prompt: 提示词
        :param project_id: 项目ID
        :param tools_list: 工具调用列表（会被实时更新）
        :param context_ref: 上下文内容的引用（列表，用于修改字符串）
        """
        # 构建自定义消息列表（不包含历史消息和聊天摘要）
        messages = []

        # 添加系统提示词
        if app_settings.llm.developer_mode:
            messages.append(("system", DEVELOP_MODE_PROMPTS))

        if app_settings.llm.system_prompt:
            messages.append(("system", app_settings.llm.system_prompt))

        # 添加 MCP 工具使用指南
        messages.append(("system", MCP_TOOLS_GUIDE))

        # 添加当前项目信息
        session_info = self.get_session_context(project_id)
        if session_info:
            messages.append(("system", session_info))

        # 添加当前提示词
        messages.append(("human", prompt))

        # 配置递归限制
        config = {"recursion_limit": app_settings.llm.recursion_limit}

        # 调用LLM并处理事件
        async for chunk in self.agent.astream_events({"messages": messages}, version="v2", config=config):
            event_type = chunk.get("event")

            if event_type == "on_chat_model_stream":
                message_chunk = chunk.get("data", {}).get("chunk")
                if message_chunk and hasattr(message_chunk, "content") and message_chunk.content:
                    content = message_chunk.content
                    context_ref[0] += content
                    yield content

            elif event_type == "on_tool_start":
                self._process_tool_start_event(chunk, tools_list, "最终操作")

            elif event_type == "on_tool_end":
                self._process_tool_end_event(chunk, tools_list, "最终操作")

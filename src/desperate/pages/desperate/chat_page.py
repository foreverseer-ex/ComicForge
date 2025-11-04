"""
聊天页面

提供与 AI 交互的界面，帮助用户分析小说、优化提示词等。
"""

import flet as ft
from loguru import logger
from flet_toast import flet_toast
from flet_toast.Types import Position
from api.components.desperate.chat import ChatMessageDisplay, ChatInputArea
from api.components.desperate.chat.chat_message_display import MessageRole
from api.schemas.desperate.chat import ToolCall, IterationChatMessage, ChatMessage, TextMessage
from api.services.llm import get_current_llm_service
from api.services.db.desperate.chat_service import ChatService as ChatServiceDB


class ChatPage(ft.Container):
    """聊天页面主组件"""

    def __init__(self, page: ft.Page):
        """
        初始化聊天页面

        Args:
            page: Flet 页面对象
        """
        super().__init__()

        self.page = page
        self.expand = True
        self.padding = ft.padding.all(10)
        
        # 获取 LLM 服务
        self.llm_service = get_current_llm_service()
        
        # 使用当前选中的项目 ID，如果没有则使用 default
        from api.settings import app_settings
        self.project_id = app_settings.ui.current_project_id or "default"
        
        # 用于跟踪是否已显示SD-Forge错误Toast（避免重复显示）
        self._sd_forge_error_shown = False
        
        # 用于跟踪当前的 typing indicator（用于显示"AI思考中"）
        self._current_typing_indicator = None
        
        # 用于轮询的状态跟踪
        self._last_message_ids: list[str] = []  # 上次查询到的消息ID列表
        self._last_message_data: dict = {}  # 上次查询到的最后一条消息的data和tools
        self._polling_task = None  # 轮询任务

        # 创建组件
        self.message_display = ChatMessageDisplay(
            on_delete_message=self._handle_delete_message,
            on_reedit_message=self._handle_reedit_message
        )

        self.input_area = ChatInputArea(
            on_send_message=self._handle_send_message,
        )

        # 组装布局：垂直布局（标题栏 + 消息显示 + 输入框）
        self.content = ft.Column(
            [
                # 顶部标题栏
                self._create_header(),
                # 消息显示区
                self.message_display,
                # 输入区
                self.input_area,
            ],
            spacing=0,
            expand=True,
        )
    
    def did_mount(self):
        """组件挂载后加载历史记录并开始轮询"""
        # 更新 project_id（防止用户在主页切换了项目）
        from api.settings import app_settings
        self.project_id = app_settings.ui.current_project_id or "default"
        
        # 加载历史记录（必须在组件挂载到页面之后）
        self._load_history()
        
        # 开始轮询（每1秒查询一次数据库）
        self._start_polling()
    
    def will_unmount(self):
        """组件卸载时停止轮询"""
        self._stop_polling()
    
    def _load_history(self):
        """加载历史记录并显示在界面上"""
        try:
            # 从数据库加载消息
            db_messages = ChatServiceDB.list(self.project_id)
            
            # 转换为 Pydantic 模型
            messages = []
            for db_msg in db_messages:
                msg = ChatServiceDB.db_to_chat_message(db_msg)
                messages.append(msg)
            
            # 显示历史消息
            for msg in messages:
                if isinstance(msg, ChatMessage):
                    if msg.role == "user":
                        role = MessageRole.USER
                    elif msg.role == "assistant":
                        role = MessageRole.ASSISTANT
                    else:
                        role = MessageRole.SYSTEM
                    
                    # 将新格式的消息传递给渲染器（批量加载时不立即更新）
                    self.message_display.message_list.add_message_with_data(role, msg, update_ui=False)
                elif isinstance(msg, IterationChatMessage):
                    # 迭代消息
                    self.message_display.message_list.add_message_with_data(MessageRole.ASSISTANT, msg, update_ui=False)
            
            # 批量加载完成后，统一更新 UI
            try:
                self.message_display.message_list.update()
                # 自动滚动到底部，显示最新消息
                self.message_display.message_list.scroll_to_bottom()
            except (AssertionError, AttributeError):
                # 组件可能还未完全挂载，稍后会自动更新
                pass
            
            # 更新轮询状态
            self._last_message_ids = [msg.id for msg in messages]
            if messages:
                last_msg = messages[-1]
                if isinstance(last_msg, IterationChatMessage):
                    self._last_message_data = {
                        "message_id": last_msg.id,
                        "data": {
                            "index": last_msg.index,
                            "stop": last_msg.stop,
                            "step": last_msg.step,
                            "summary": last_msg.summary
                        },
                        "tools": [msg for msg in last_msg.messages if isinstance(msg, ToolCall)]
                    }
                else:
                    self._last_message_data = {
                        "message_id": last_msg.id,
                        "data": {},
                        "tools": [msg for msg in last_msg.messages if isinstance(msg, ToolCall)]
                    }
            
            logger.info(f"成功加载 {len(messages)} 条历史消息")
        except Exception as e:
            logger.exception(f"加载历史记录失败: {e}")

    def _create_header(self) -> ft.Container:
        """
        创建顶部标题栏

        Returns:
            标题栏容器
        """
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.BRUSH, size=24, color=ft.Colors.BLUE_400),
                    ft.Text(
                        "NovelPanel 助手",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Container(expand=True),
                    # 滚动到底部按钮
                    ft.IconButton(
                        icon=ft.Icons.ARROW_DOWNWARD,
                        tooltip="滚动到底部",
                        icon_size=20,
                        icon_color=ft.Colors.BLUE_400,
                        on_click=self._handle_scroll_to_bottom,
                    ),
                    # 清空对话按钮
                    ft.IconButton(
                        icon=ft.Icons.DELETE_SWEEP_ROUNDED,
                        tooltip="清空对话",
                        icon_size=20,
                        on_click=self._handle_clear_chat,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.all(15),
        )

    def _handle_scroll_to_bottom(self, _e: ft.ControlEvent):
        """处理滚动到底部按钮点击"""
        self.message_display.scroll_to_bottom()
    
    def _handle_clear_chat(self, _e: ft.ControlEvent):
        """处理清空对话"""
        # 清空数据库中的消息
        ChatServiceDB.clear(self.project_id)
        
        # 清空 LLM 服务的历史记录
        self.llm_service.clear_history()
        
        # 删除 JSON 历史记录文件（如果存在）
        from api.utils.path import chat_history_home
        history_file = chat_history_home / f"{self.project_id}.json"
        if history_file.exists():
            try:
                history_file.unlink()
                logger.debug(f"已删除历史记录文件: {history_file}")
            except Exception as e:
                logger.debug(f"删除历史记录文件失败: {e}")
        
        # 清空消息显示区
        self.message_display.message_list.clear_messages()
        
        # 更新轮询状态
        self._last_message_ids = []
        self._last_message_data = {}

        # 显示通知（使用 page.run_task 确保在主线程中执行）
        if self.page:
            try:
                async def show_toast():
                    try:
                        flet_toast.sucess(
                            page=self.page,
                            message="对话已清空",
                            position=Position.TOP_RIGHT,
                            duration=1
                        )
                    except Exception as e:
                        logger.debug(f"显示 Toast 失败: {e}")
                
                self.page.run_task(show_toast)
            except Exception as e:
                logger.debug(f"显示 Toast 失败: {e}")

    def _handle_delete_message(self, message_widget):
        """
        处理删除消息
        
        Args:
            message_widget: 要删除的消息组件
        """
        try:
            # 获取消息数据
            message_data = message_widget.message_data
            if not message_data:
                logger.warning("消息组件没有关联的数据，无法删除")
                return
            
            # 从数据库中删除该消息
            success = ChatServiceDB.delete(self.project_id, message_data.id)
            if success:
                logger.info(f"删除消息: {message_data.id}")
                
                # 也清空 LLM 服务的历史记录（保持同步）
                self.llm_service.clear_history()
                
                # 删除 JSON 历史记录文件（如果存在），确保重新加载时不会从文件恢复
                from api.utils.path import chat_history_home
                history_file = chat_history_home / f"{self.project_id}.json"
                if history_file.exists():
                    try:
                        history_file.unlink()
                        logger.debug(f"已删除历史记录文件: {history_file}")
                    except Exception as e:
                        logger.debug(f"删除历史记录文件失败: {e}")
                
                # 清空 UI 并重新加载（轮询会自动刷新）
                self.message_display.message_list.clear_messages()
                self._load_history()
                
                # 显示成功提示（使用 page.run_task 确保在主线程中执行）
                if self.page:
                    try:
                        async def show_toast():
                            try:
                                flet_toast.sucess(
                                    page=self.page,
                                    message="消息已删除",
                                    position=Position.TOP_RIGHT,
                                    duration=1
                                )
                            except Exception as e:
                                logger.debug(f"显示 Toast 失败: {e}")
                        
                        self.page.run_task(show_toast)
                    except Exception as e:
                        logger.debug(f"显示 Toast 失败: {e}")
            else:
                logger.warning(f"消息在数据库中不存在: {message_data.id}")
                if self.page:
                    try:
                        async def show_toast():
                            try:
                                flet_toast.error(
                                    page=self.page,
                                    message="删除失败：消息不存在",
                                    position=Position.TOP_RIGHT,
                                    duration=2
                                )
                            except Exception as e:
                                logger.debug(f"显示 Toast 失败: {e}")
                        
                        self.page.run_task(show_toast)
                    except Exception as e:
                        logger.debug(f"显示 Toast 失败: {e}")
        except Exception as e:
            logger.exception(f"删除消息失败: {e}")
            if self.page:
                try:
                    async def show_error_toast():
                        try:
                            flet_toast.error(
                                page=self.page,
                                message=f"删除失败: {str(e)}",
                                position=Position.TOP_RIGHT,
                                duration=2
                            )
                        except Exception as toast_error:
                            logger.debug(f"显示 Toast 失败: {toast_error}")
                    
                    self.page.run_task(show_error_toast)
                except Exception as toast_error:
                    logger.debug(f"显示 Toast 失败: {toast_error}")
    
    def _handle_reedit_message(self, message_widget):
        """
        处理重新编辑消息：删除这条消息和之后的所有对话记录，并将当前消息内容放到输入框
        
        Args:
            message_widget: 要重新编辑的消息组件
        """
        try:
            # 先提取消息数据（在删除之前）
            message_data = message_widget.message_data
            
            # 如果message_data不存在，尝试从历史记录中查找
            if not message_data:
                # 尝试通过消息ID查找
                if hasattr(message_widget, 'message_data') and hasattr(message_widget.message_data, 'id'):
                    msg_id = message_widget.message_data.id
                    for msg in self.llm_service.history.messages:
                        if hasattr(msg, 'id') and msg.id == msg_id:
                            message_data = msg
                            break
                
                # 如果还是找不到，尝试通过消息内容匹配（最后的手段）
                if not message_data:
                    # 尝试从消息组件的文本内容中提取
                    if hasattr(message_widget, 'message_content') and message_widget.message_content:
                        user_content = message_widget.message_content.strip()
                        # 在历史记录中查找匹配的用户消息
                        for msg in self.llm_service.history.messages:
                            if msg.role == "user":
                                for msg_content in msg.messages:
                                    if hasattr(msg_content, 'content') and msg_content.content.strip() == user_content:
                                        message_data = msg
                                        break
                                if message_data:
                                    break
                
                if not message_data:
                    logger.warning("消息组件没有关联的数据，无法重新编辑")
                    return
            
            # 只处理用户消息
            if message_data.role != "user":
                logger.warning("只能重新编辑用户消息")
                return
            
            # 找到消息在历史记录中的索引
            if message_data not in self.llm_service.history.messages:
                logger.warning("消息在历史记录中不存在")
                return
            
            message_index = self.llm_service.history.messages.index(message_data)
            
            # 提取用户消息内容（在删除之前保存）
            user_content = ""
            for msg_content in message_data.messages:
                if hasattr(msg_content, 'content'):
                    user_content = msg_content.content
                    break
            
            # 如果无法从message_data提取，使用message_content作为后备
            if not user_content and hasattr(message_widget, 'message_content'):
                user_content = message_widget.message_content.strip()
            
            if not user_content:
                logger.warning("无法提取用户消息内容")
                return
            
            # 删除这条消息及之后的所有消息
            self.llm_service.history.messages = self.llm_service.history.messages[:message_index]
            
            # 保存历史记录
            self.llm_service.save_history(self.project_id)
            
            # 清空 UI 并重新加载
            self.message_display.message_list.clear_messages()
            self._load_history()
            
            # 将消息内容放入输入框
            if self.input_area and self.input_area.input_field:
                self.input_area.input_field.value = user_content
                self.input_area.input_field.focus()
                self.input_area.update()
            
            logger.info(f"重新编辑消息: {user_content[:50]}...")
        except Exception as e:
            logger.exception(f"重新编辑消息失败: {e}")
            if self.page:
                try:
                    async def show_error_toast():
                        try:
                            flet_toast.error(
                                page=self.page,
                                message=f"重新编辑失败: {str(e)}",
                                position=Position.TOP_RIGHT,
                                duration=2
                            )
                        except Exception as toast_error:
                            logger.debug(f"显示 Toast 失败: {toast_error}")
                    
                    self.page.run_task(show_error_toast)
                except Exception as toast_error:
                    logger.debug(f"显示 Toast 失败: {toast_error}")

    def _handle_send_message(self, message: str):
        """
        处理发送消息（现在只负责发送用户消息，AI响应通过事件接收）
        
        Args:
            message: 用户消息内容
        """
        # 重置SD-Forge错误标志（新消息时重置）
        self._sd_forge_error_shown = False
        
        # 检查 LLM 服务是否就绪
        if not self.llm_service.is_ready():
            # 显示错误消息
            self.message_display.message_list.add_message(
                MessageRole.SYSTEM,
                "❌ LLM 服务未就绪，请在设置页面配置 LLM 参数并确保服务正常启动。"
            )
            return
        
        # 使用异步方式获取 AI 响应（后端会写入数据库，前端通过轮询更新）
        async def get_ai_response():
            try:
                # 流式获取响应（后端会自动写入数据库）
                async for chunk in self.llm_service.chat(message, self.project_id):
                    pass  # 响应已写入数据库，轮询会自动更新UI
                
                # 检查是否需要执行迭代模式
                # 从数据库查找是否有迭代消息需要执行迭代循环
                db_messages = ChatServiceDB.list(self.project_id)
                iteration_msg_to_execute = None
                for db_msg in reversed(db_messages):
                    if db_msg.message_type == "iteration":
                        msg = ChatServiceDB.db_to_chat_message(db_msg)
                        if isinstance(msg, IterationChatMessage):
                            if msg.index < msg.stop:
                                iteration_msg_to_execute = msg
                                break
                
                # 如果有迭代消息需要执行，执行迭代循环
                if iteration_msg_to_execute:
                    async for chunk in self.llm_service.chat_iteration(iteration_msg_to_execute, self.project_id):
                        pass  # 迭代进度已写入数据库，轮询会自动更新UI
            except Exception as e:
                logger.exception(f"获取 AI 响应失败: {e}")
                if self.page:
                    error_msg = ChatMessage(role="system", messages=[TextMessage(content=f"❌ 获取响应失败：{e}")])
                    ChatServiceDB.add(self.project_id, error_msg, status="error")
        
        if self.page:
            self.page.run_task(get_ai_response)
    
    def _start_polling(self):
        """开始轮询数据库"""
        if not self.page:
            return
        
        async def poll_messages():
            import asyncio
            while self.page and self.page.visible:
                try:
                    await asyncio.sleep(1)  # 每1秒查询一次
                    if not self.page or not self.page.visible:
                        break
                    self._check_messages_changes()
                except Exception as e:
                    logger.debug(f"轮询消息失败: {e}")
        
        if self.page:
            self._polling_task = self.page.run_task(poll_messages)
    
    def _stop_polling(self):
        """停止轮询"""
        self._polling_task = None
    
    def _check_messages_changes(self):
        """检查消息变化并更新UI"""
        if not self.page:
            return
        
        try:
            # 查询数据库中的所有消息ID
            current_message_ids = ChatServiceDB.get_message_ids(self.project_id)
            
            # 对比消息ID列表，检查是否有变化
            if current_message_ids != self._last_message_ids:
                # 消息数量或顺序发生变化，需要刷新整个列表
                self._refresh_all_messages()
            elif current_message_ids:
                # 消息ID列表相同，检查最后一条消息的data和tools是否有变化
                last_db_msg = ChatServiceDB.get_last(self.project_id)
                if last_db_msg:
                    last_msg = ChatServiceDB.db_to_chat_message(last_db_msg)
                    
                    # 提取当前消息的data和tools
                    if isinstance(last_msg, IterationChatMessage):
                        current_data = {
                            "index": last_msg.index,
                            "stop": last_msg.stop,
                            "step": last_msg.step,
                            "summary": last_msg.summary
                        }
                    else:
                        current_data = {}
                    current_tools = [msg for msg in last_msg.messages if isinstance(msg, ToolCall)]
                    
                    # 对比最后一条消息的data和tools
                    if (current_data != self._last_message_data.get("data", {}) or
                        len(current_tools) != len(self._last_message_data.get("tools", []))):
                        # 只有最后一条消息有变化，只更新这条消息
                        self._update_last_message(last_msg)
            else:
                # 没有消息了，清空UI
                if self._last_message_ids:
                    self.message_display.message_list.clear_messages()
                    self._last_message_ids = []
                    self._last_message_data = {}
                    if self.page:
                        self.page.update()
        except Exception as e:
            logger.debug(f"检查消息变化失败: {e}")
    
    def _refresh_all_messages(self):
        """刷新所有消息"""
        try:
            # 查询数据库中的所有消息
            db_messages = ChatServiceDB.list(self.project_id)
            
            # 转换为 Pydantic 模型
            messages = []
            for db_msg in db_messages:
                msg = ChatServiceDB.db_to_chat_message(db_msg)
                messages.append(msg)
            
            # 清空UI
            self.message_display.message_list.clear_messages()
            
            # 重新添加所有消息
            for msg in messages:
                if isinstance(msg, ChatMessage):
                    if msg.role == "user":
                        role = MessageRole.USER
                    elif msg.role == "assistant":
                        role = MessageRole.ASSISTANT
                    else:
                        role = MessageRole.SYSTEM
                    self.message_display.message_list.add_message_with_data(role, msg, update_ui=False)
                elif isinstance(msg, IterationChatMessage):
                    self.message_display.message_list.add_message_with_data(MessageRole.ASSISTANT, msg, update_ui=False)
            
            # 更新UI
            try:
                self.message_display.message_list.update()
            except (AssertionError, AttributeError):
                pass
            
            # 更新轮询状态
            self._last_message_ids = [msg.id for msg in messages]
            if messages:
                last_msg = messages[-1]
                if isinstance(last_msg, IterationChatMessage):
                    self._last_message_data = {
                        "message_id": last_msg.id,
                        "data": {
                            "index": last_msg.index,
                            "stop": last_msg.stop,
                            "step": last_msg.step,
                            "summary": last_msg.summary
                        },
                        "tools": [msg for msg in last_msg.messages if isinstance(msg, ToolCall)]
                    }
                else:
                    self._last_message_data = {
                        "message_id": last_msg.id,
                        "data": {},
                        "tools": [msg for msg in last_msg.messages if isinstance(msg, ToolCall)]
                    }
            
            # 更新"AI思考中"指示器
            if messages:
                last_msg = messages[-1]
                if isinstance(last_msg, ChatMessage) and last_msg.role == "assistant":
                    # 检查消息状态
                    last_db_msg = ChatServiceDB.get_by_message_id(self.project_id, last_msg.id)
                    if last_db_msg and last_db_msg.status == "thinking":
                        # 显示"AI思考中"指示器
                        if not self._current_typing_indicator:
                            self._current_typing_indicator = self.message_display.message_list.add_typing_indicator()
                    else:
                        # 移除"AI思考中"指示器
                        if self._current_typing_indicator:
                            self.message_display.message_list.remove_typing_indicator(self._current_typing_indicator)
                            self._current_typing_indicator = None
            
            if self.page:
                self.page.update()
        except Exception as e:
            logger.exception(f"刷新所有消息失败: {e}")
    
    def _update_last_message(self, message: ChatMessage | IterationChatMessage):
        """更新最后一条消息"""
        try:
            # 找到最后一条消息的索引
            if self._last_message_ids:
                last_message_id = self._last_message_ids[-1]
                message_index = len(self._last_message_ids) - 1
                
                # 更新消息
                if isinstance(message, IterationChatMessage):
                    role = MessageRole.ASSISTANT
                elif message.role == "user":
                    role = MessageRole.USER
                elif message.role == "assistant":
                    role = MessageRole.ASSISTANT
                else:
                    role = MessageRole.SYSTEM
                
                self.message_display.message_list.update_message_at_index(message_index, message)
                
                # 更新轮询状态
                if isinstance(message, IterationChatMessage):
                    self._last_message_data = {
                        "message_id": message.id,
                        "data": {
                            "index": message.index,
                            "stop": message.stop,
                            "step": message.step,
                            "summary": message.summary
                        },
                        "tools": [msg for msg in message.messages if isinstance(msg, ToolCall)]
                    }
                else:
                    self._last_message_data = {
                        "message_id": message.id,
                        "data": {},
                        "tools": [msg for msg in message.messages if isinstance(msg, ToolCall)]
                    }
                
                # 更新"AI思考中"指示器
                if isinstance(message, ChatMessage) and message.role == "assistant":
                    db_msg = ChatServiceDB.get_by_message_id(self.project_id, message.id)
                    if db_msg and db_msg.status == "thinking":
                        if not self._current_typing_indicator:
                            self._current_typing_indicator = self.message_display.message_list.add_typing_indicator()
                    else:
                        if self._current_typing_indicator:
                            self.message_display.message_list.remove_typing_indicator(self._current_typing_indicator)
                            self._current_typing_indicator = None
                
                if self.page:
                    self.page.update()
        except Exception as e:
            logger.exception(f"更新最后一条消息失败: {e}")
    
    def _handle_send_message_old(self, message: str):
        """
        处理发送消息

        Args:
            message: 用户消息内容
        """
        # 重置SD-Forge错误标志（新消息时重置）
        self._sd_forge_error_shown = False
        
        # 检查 LLM 服务是否就绪
        if not self.llm_service.is_ready():
            # 显示错误消息
            self.message_display.message_list.add_message(
                MessageRole.SYSTEM,
                "❌ LLM 服务未就绪，请在设置页面配置 LLM 参数并确保服务正常启动。"
            )
            return
        
        # 添加用户消息
        self.message_display.message_list.add_message(MessageRole.USER, message)

        # 检查是否会进入迭代模式（在 chat() 完成后）
        # 注意：迭代卡片会在 chat() 完成后根据历史记录中的迭代消息创建
        iteration_widget = None
        typing_indicator = None
        
        # 显示正在输入指示器
        typing_indicator = self.message_display.message_list.add_typing_indicator()
        
        # 使用异步方式获取 AI 响应
        async def get_ai_response():
            nonlocal iteration_widget, typing_indicator  # 声明为 nonlocal，以便在内部函数中修改
            response_text = ""
            assistant_message_widget = None
            last_update_time = 0
            update_interval = 0.1  # 最小更新间隔（秒）
            
            try:
                # 流式获取响应
                async for chunk in self.llm_service.chat(message, self.project_id):
                    response_text += chunk
                    
                    # 在主线程更新 UI（限流，避免过于频繁的更新）
                    if self.page:
                        import time
                        current_time = time.time()
                        
                        # 如果是第一个 chunk，移除指示器并创建助手消息占位符
                        if assistant_message_widget is None:
                            if typing_indicator:
                                self.message_display.message_list.remove_typing_indicator(typing_indicator)
                            assistant_message_widget = self.message_display.message_list.add_message(
                                MessageRole.ASSISTANT, ""  # 临时占位
                            )
                            last_update_time = current_time
                        
                        # 限流更新：只在间隔足够时才更新UI
                        if current_time - last_update_time >= update_interval:
                            # 实时获取历史记录中的最新助手消息并更新显示
                            if self.llm_service.history.messages:
                                last_msg = self.llm_service.history.messages[-1]
                                if last_msg.role == "assistant" and not isinstance(last_msg, IterationChatMessage):
                                    # 检查工具调用结果中是否有SD-Forge错误
                                    for msg_content in last_msg.messages:
                                        if isinstance(msg_content, ToolCall):
                                            tool_result = str(msg_content.result or "").lower()
                                            if "sd-forge" in tool_result or ("502" in tool_result and "bad gateway" in tool_result):
                                                # 显示Toast提示
                                                self._show_sd_forge_error_toast()
                                    # 找到并替换占位消息
                                    if assistant_message_widget in self.message_display.message_list.controls:
                                        idx = self.message_display.message_list.controls.index(assistant_message_widget)
                                        # 移除旧的占位消息和分隔线
                                        if idx + 1 < len(self.message_display.message_list.controls):
                                            self.message_display.message_list.controls.pop(idx + 1)  # 分隔线
                                        self.message_display.message_list.controls.pop(idx)  # 占位消息
                                        
                                        # 在相同位置插入完整消息
                                        new_widget = self.message_display.message_list._create_message_widget(
                                            MessageRole.ASSISTANT, last_msg
                                        )
                                        self.message_display.message_list.controls.insert(idx, new_widget)
                                        self.message_display.message_list.controls.insert(idx + 1, ft.Divider(height=1))
                                        
                                        # 更新引用
                                        assistant_message_widget = new_widget
                                        self.page.update()
                            
                            last_update_time = current_time
                
                # 流式输出完成后，检查是否需要执行迭代循环
                # 查找是否有迭代消息需要执行迭代循环
                iteration_msg_to_execute = None
                if self.llm_service.history.messages:
                    for msg in reversed(self.llm_service.history.messages):
                        if isinstance(msg, IterationChatMessage):
                            # 检查迭代是否还未完成
                            if msg.index < msg.stop:
                                iteration_msg_to_execute = msg
                                break
                            else:
                                # 迭代已完成，更新UI显示最终结果
                                if iteration_widget:
                                    self._update_iteration_widget(iteration_widget, msg)
                                    # 如果迭代完成，需要重新渲染迭代卡片以显示最终操作的工具调用
                                    if iteration_widget in self.message_display.message_list.controls:
                                        idx = self.message_display.message_list.controls.index(iteration_widget)
                                        if idx + 1 < len(self.message_display.message_list.controls):
                                            self.message_display.message_list.controls.pop(idx + 1)  # 分隔线
                                        self.message_display.message_list.controls.pop(idx)  # 旧卡片
                                        
                                        # 重新创建迭代卡片（包含最终操作的工具调用）
                                        new_iteration_widget = self.message_display.message_list.add_message_with_data(
                                            MessageRole.ASSISTANT, msg, update_ui=False
                                        )
                                        self.message_display.message_list.controls.insert(idx, new_iteration_widget)
                                        self.message_display.message_list.controls.insert(idx + 1, ft.Divider(height=1))
                                        iteration_widget = new_iteration_widget  # 更新引用
                                        if self.page:
                                            self.page.update()
                            break
                
                # 如果有迭代消息需要执行，创建迭代卡片（如果还没有创建），然后执行迭代循环
                if iteration_msg_to_execute:
                    # 创建迭代卡片（如果还没有创建）
                    if iteration_widget is None:
                        if self.page:
                            try:
                                iteration_widget = self.message_display.message_list.add_message_with_data(
                                    MessageRole.ASSISTANT, iteration_msg_to_execute, update_ui=True
                                )
                                self.page.update()
                                logger.debug(f"迭代卡片已创建: {iteration_msg_to_execute.target}")
                            except Exception as e:
                                logger.exception(f"创建迭代卡片失败: {e}")
                    
                    # 移除 typing indicator（如果存在）
                    if typing_indicator:
                        self.message_display.message_list.remove_typing_indicator(typing_indicator)
                        typing_indicator = None
                    
                    # 执行迭代循环
                    iteration_response_text = ""
                    if self.page:
                        import time
                        last_update_time = time.time()
                        update_interval = 0.1  # 最小更新间隔（秒）
                        
                        async for chunk in self.llm_service.chat_iteration(iteration_msg_to_execute, self.project_id):
                            iteration_response_text += chunk
                            
                            # 更新迭代卡片（限流更新）
                            if self.page:
                                current_time = time.time()
                                if current_time - last_update_time >= update_interval:
                                    # 查找最新的迭代消息
                                    if self.llm_service.history.messages:
                                        for msg in reversed(self.llm_service.history.messages):
                                            if isinstance(msg, IterationChatMessage) and msg.id == iteration_msg_to_execute.id:
                                                self._update_iteration_widget(iteration_widget, msg)
                                                last_update_time = current_time
                                                break
                        
                        # 迭代完成后，最后一次更新迭代卡片
                        if self.llm_service.history.messages:
                            for msg in reversed(self.llm_service.history.messages):
                                if isinstance(msg, IterationChatMessage) and msg.id == iteration_msg_to_execute.id:
                                    # 迭代完成，重新渲染迭代卡片以显示最终操作的工具调用
                                    if iteration_widget in self.message_display.message_list.controls:
                                        idx = self.message_display.message_list.controls.index(iteration_widget)
                                        if idx + 1 < len(self.message_display.message_list.controls):
                                            self.message_display.message_list.controls.pop(idx + 1)  # 分隔线
                                        self.message_display.message_list.controls.pop(idx)  # 旧卡片
                                        
                                        # 重新创建迭代卡片（包含最终操作的工具调用）
                                        new_iteration_widget = self.message_display.message_list.add_message_with_data(
                                            MessageRole.ASSISTANT, msg, update_ui=False
                                        )
                                        self.message_display.message_list.controls.insert(idx, new_iteration_widget)
                                        self.message_display.message_list.controls.insert(idx + 1, ft.Divider(height=1))
                                        iteration_widget = new_iteration_widget  # 更新引用
                                        self.page.update()
                                    break
                
                # 流式输出完成后，最后一次更新（非迭代模式）
                if self.page and not iteration_msg_to_execute:
                    if assistant_message_widget:
                        # 普通模式：更新助手消息
                        if self.llm_service.history.messages:
                            last_msg = self.llm_service.history.messages[-1]
                            if last_msg.role == "assistant" and not isinstance(last_msg, IterationChatMessage):
                                # 检查工具调用结果中是否有SD-Forge错误
                                for msg_content in last_msg.messages:
                                    if isinstance(msg_content, ToolCall):
                                        tool_result = str(msg_content.result or "").lower()
                                        if "sd-forge" in tool_result or ("502" in tool_result and "bad gateway" in tool_result):
                                            # 显示Toast提示
                                            self._show_sd_forge_error_toast()
                                # 最后一次更新
                                if assistant_message_widget in self.message_display.message_list.controls:
                                    idx = self.message_display.message_list.controls.index(assistant_message_widget)
                                    if idx + 1 < len(self.message_display.message_list.controls):
                                        self.message_display.message_list.controls.pop(idx + 1)
                                    self.message_display.message_list.controls.pop(idx)
                                    
                                    new_widget = self.message_display.message_list._create_message_widget(
                                        MessageRole.ASSISTANT, last_msg
                                    )
                                    self.message_display.message_list.controls.insert(idx, new_widget)
                                    self.message_display.message_list.controls.insert(idx + 1, ft.Divider(height=1))
                                    self.page.update()
                
                # 如果没有收到任何响应
                if not response_text:
                    if self.page:
                        if assistant_message_widget:
                            # 移除占位消息
                            if assistant_message_widget in self.message_display.message_list.controls:
                                idx = self.message_display.message_list.controls.index(assistant_message_widget)
                                if idx + 1 < len(self.message_display.message_list.controls):
                                    self.message_display.message_list.controls.pop(idx + 1)
                                self.message_display.message_list.controls.pop(idx)
                        else:
                            if typing_indicator:
                                self.message_display.message_list.remove_typing_indicator(typing_indicator)
                        
                        self.message_display.message_list.add_message(
                            MessageRole.SYSTEM,
                            "⚠️ 未收到响应，请检查 LLM 配置和网络连接。"
                        )
                        self.page.update()
                        
            except Exception as e:
                logger.exception(f"获取 AI 响应失败: {e}")
                if self.page:
                    if typing_indicator:
                        self.message_display.message_list.remove_typing_indicator(typing_indicator)
                    self.message_display.message_list.add_message(
                        MessageRole.SYSTEM,
                        f"❌ 获取响应失败：{e}"
                    )
        
        # 使用 page 的事件循环运行异步任务
        if self.page:
            self.page.run_task(get_ai_response)
    
    def _update_iteration_widget(self, iteration_widget: ft.Container, iteration_msg):
        """更新迭代卡片的进度和摘要"""
        if not iteration_widget or not iteration_widget.content:
            return
        
        try:
            # 检查是否是同一个迭代消息
            if hasattr(iteration_widget, 'data') and iteration_widget.data:
                widget_id = iteration_widget.data.get('iteration_msg_id')
                if widget_id and widget_id != iteration_msg.id:
                    # 不是同一个迭代消息，跳过
                    return
            
            # 计算进度
            progress = iteration_msg.index / iteration_msg.stop if iteration_msg.stop > 0 else 0.0
            is_completed = iteration_msg.index >= iteration_msg.stop
            
            # 使用存储的引用更新控件
            if hasattr(iteration_widget, 'data') and iteration_widget.data:
                progress_bar = iteration_widget.data.get('progress_bar')
                status_text = iteration_widget.data.get('status_text')
                summary_text = iteration_widget.data.get('summary_text')
                
                if progress_bar:
                    progress_bar.value = progress
                    progress_bar.color = ft.Colors.GREEN_400 if is_completed else ft.Colors.BLUE_400
                    progress_bar.update()
                
                if status_text:
                    status_text.value = f"{iteration_msg.index}/{iteration_msg.stop} 行" if not is_completed else "已完成"
                    status_text.update()
                
                if summary_text:
                    summary_text.value = iteration_msg.summary or "（暂无摘要）"
                    # summary_text.update()  # 不需要立即更新，用户点击展开时才会看到
            else:
                # 降级方案：通过遍历查找控件
                content_column = iteration_widget.content
                if isinstance(content_column, ft.Column):
                    for control in content_column.controls:
                        if isinstance(control, ft.ProgressBar):
                            control.value = progress
                            control.color = ft.Colors.GREEN_400 if is_completed else ft.Colors.BLUE_400
                            control.update()
                        elif isinstance(control, ft.Row):
                            for row_control in control.controls:
                                if isinstance(row_control, ft.Text) and row_control.size == 12:
                                    if "/" in row_control.value or "已完成" in row_control.value:
                                        row_control.value = f"{iteration_msg.index}/{iteration_msg.stop} 行" if not is_completed else "已完成"
                                        row_control.update()
                                elif isinstance(row_control, ft.Text) and hasattr(row_control, 'max_lines') and row_control.max_lines == 10:
                                    row_control.value = iteration_msg.summary or "（暂无摘要）"
            
            # 更新UI
            if self.page:
                iteration_widget.update()
        except Exception as e:
            logger.exception(f"更新迭代卡片失败: {e}")
    
    def _show_sd_forge_error_toast(self):
        """显示SD-Forge连接错误的Toast提示（每个消息只显示一次）"""
        if not self.page:
            return
        
        # 避免重复显示
        if self._sd_forge_error_shown:
            return
        
        try:
            self._sd_forge_error_shown = True
            
            async def show_toast():
                try:
                    flet_toast.warning(
                        page=self.page,
                        message="⚠️ SD-Forge 后端连接失败，请确保 SD-Forge 服务正在运行（http://127.0.0.1:7860）",
                        position=Position.TOP_RIGHT,
                        duration=5
                    )
                except Exception as e:
                    logger.debug(f"显示 Toast 失败: {e}")
                    print("Toast: ⚠️ SD-Forge 后端连接失败")
            
            self.page.run_task(show_toast)
        except Exception as e:
            logger.debug(f"显示 SD-Forge 错误 Toast 失败: {e}")
            print("Toast: ⚠️ SD-Forge 后端连接失败")



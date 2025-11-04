"""
主页 - 项目管理页面

管理和切换项目，显示项目基本信息。
"""
import flet as ft
from loguru import logger
from flet_toast import flet_toast
from flet_toast.Types import Position

from api.services.db import ProjectService, NovelContentService
from api.schemas.project import Project
from api.components import CreateProjectDialog, DeleteProjectDialog
from api.settings import app_settings


class HomePage(ft.Column):
    """
    主页 - 项目管理页面。
    
    页面结构：
    - 顶部 header：项目切换下拉列表
    - 中间 context：左右布局
      - 左侧：项目信息卡片
      - 右侧：上下两个卡片（暂未实现）
    - 底部 footer：快捷按钮（创建、删除）
    """
    
    # 统一的间距和样式常量
    PADDING_LARGE = 20    # 大内边距
    PADDING_MEDIUM = 15   # 中等内边距
    PADDING_SMALL = 10    # 小内边距
    SPACING_LARGE = 20    # 大间距
    SPACING_MEDIUM = 15   # 中等间距
    SPACING_SMALL = 10    # 小间距
    
    def __init__(self, page: ft.Page):
        """初始化主页"""
        super().__init__()
        self.page = page
        self.expand = True
        self.spacing = 0
        
        # 项目列表
        self.projects: list[Project] = []
        self.current_project: Project | None = None
        
        # UI 组件
        self.project_dropdown: ft.Dropdown | None = None
        self.content_area: ft.Container | None = None
        self.project_info_card: ft.Card | None = None
        self.create_button: ft.ElevatedButton | None = None
        self.delete_button: ft.ElevatedButton | None = None
        
        # 小说段落卡片组件
        self.novel_paragraph_text: ft.Text | None = None
        self.novel_line_info: ft.Text | None = None
        self.prev_button: ft.IconButton | None = None
        self.next_button: ft.IconButton | None = None
        
        # 构建 UI
        self._build_ui()
    
    def did_mount(self):
        """组件挂载后加载数据"""
        self._load_sessions()
        # 注册键盘事件（保留原有的键盘事件处理）
        original_handler = getattr(self.page, 'on_keyboard_event', None)
        
        def on_keyboard(e: ft.KeyboardEvent):
            # 检查组件是否已挂载到页面
            if not self.page:
                logger.debug("HomePage 尚未挂载到页面，跳过键盘事件处理")
                if original_handler:
                    original_handler(e)
                return
            
            # 先检查是否有打开的对话框
            if e.key == "Escape":
                for overlay_control in self.page.overlay:
                    if isinstance(overlay_control, ft.AlertDialog) and overlay_control.open:
                        # 找到打开的对话框，关闭它
                        if hasattr(overlay_control, '_on_cancel'):
                            overlay_control._on_cancel(None)
                        elif hasattr(overlay_control, '_close'):
                            overlay_control._close(None)
                        else:
                            overlay_control.open = False
                            self.page.update()
                        return  # 只关闭第一个找到的对话框
            
            # 处理原有的键盘事件（左右箭头）
            if e.key == "Arrow Left" and not e.shift and not e.ctrl and not e.alt:
                # 左箭头 - 上一段
                self._on_prev_paragraph(None)
            elif e.key == "Arrow Right" and not e.shift and not e.ctrl and not e.alt:
                # 右箭头 - 下一段
                self._on_next_paragraph(None)
            elif original_handler:
                # 如果有原始的键盘事件处理器，也调用它
                original_handler(e)
        
        self.page.on_keyboard_event = on_keyboard
    
    def will_unmount(self):
        """组件卸载时清理"""
        # 清理键盘事件处理器，恢复全局处理器
        if self.page:
            # 恢复全局键盘事件处理器（只处理ESC键关闭对话框）
            def on_keyboard_event(e: ft.KeyboardEvent):
                """处理键盘事件：ESC 键关闭对话框"""
                if e.key == "Escape":
                    # 检查页面上是否有打开的对话框
                    for overlay_control in self.page.overlay:
                        if isinstance(overlay_control, ft.AlertDialog) and overlay_control.open:
                            # 找到打开的对话框，尝试关闭它
                            if hasattr(overlay_control, '_on_cancel'):
                                overlay_control._on_cancel(None)
                            elif hasattr(overlay_control, '_close'):
                                overlay_control._close(None)
                            else:
                                # 否则直接关闭
                                overlay_control.open = False
                                self.page.update()
                            return  # 只关闭第一个找到的对话框
            
            self.page.on_keyboard_event = on_keyboard_event
    
    def _build_ui(self):
        """构建 UI 结构"""
        # 顶部 Header
        header = self._build_header()
        
        # 中间 Content
        self.content_area = ft.Container(
            expand=True,
            padding=self.PADDING_LARGE,
        )
        
        # 底部 Footer
        footer = self._build_footer()
        
        # 组装
        self.controls = [
            header,
            ft.Divider(height=1, color=ft.Colors.OUTLINE),
            self.content_area,
            ft.Divider(height=1, color=ft.Colors.OUTLINE),
            footer,
        ]
    
    def _build_header(self) -> ft.Container:
        """构建顶部 Header"""
        self.project_dropdown = ft.Dropdown(
            label="选择项目",
            hint_text="请选择一个项目",
            width=400,
            options=[],
            on_change=self._on_session_change,
        )
        
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.HOME_OUTLINED, size=24),
                    ft.Text("项目管理", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(width=self.SPACING_LARGE),
                    self.project_dropdown,
                ],
                spacing=self.SPACING_SMALL,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=self.PADDING_LARGE, vertical=self.PADDING_MEDIUM),
        )
    
    def _build_footer(self) -> ft.Container:
        """构建底部 Footer"""
        # 创建项目按钮
        self.create_button = ft.ElevatedButton(
            text="创建项目",
            icon=ft.Icons.ADD_CIRCLE_OUTLINE,
            on_click=self._on_create_session,
            height=50,
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=30, vertical=15),
                text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD),
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.PRIMARY,
                    ft.ControlState.HOVERED: ft.Colors.PRIMARY_CONTAINER,
                },
                color={
                    ft.ControlState.DEFAULT: ft.Colors.ON_PRIMARY,
                },
            ),
        )
        
        # 删除项目按钮
        self.delete_button = ft.ElevatedButton(
            text="删除项目",
            icon=ft.Icons.DELETE_OUTLINE,
            on_click=self._on_delete_session,
            disabled=True,  # 初始禁用
            height=50,
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=30, vertical=15),
                text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD),
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.ERROR,
                    ft.ControlState.HOVERED: ft.Colors.ERROR_CONTAINER,
                },
                color={
                    ft.ControlState.DEFAULT: ft.Colors.ON_ERROR,
                },
            ),
        )
        
        return ft.Container(
            content=ft.Row(
                [
                    self.create_button,
                    self.delete_button,
                ],
                spacing=self.SPACING_MEDIUM,
            ),
            padding=ft.padding.symmetric(horizontal=self.PADDING_LARGE, vertical=self.PADDING_MEDIUM),
        )
    
    def _build_empty_state(self) -> ft.Container:
        """构建空状态"""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.FOLDER_OPEN_OUTLINED,
                        size=100,
                        color=ft.Colors.OUTLINE,
                    ),
                    ft.Text(
                        "你还没有创建项目",
                        size=20,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=self.SPACING_SMALL),
                    ft.Text(
                        "点击下方的「创建项目」按钮开始你的项目",
                        size=14,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=self.SPACING_MEDIUM,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )
    
    def _build_session_content(self) -> ft.Container:
        """构建项目内容区域"""
        if not self.current_project:
            return self._build_empty_state()
        
        # 左侧：项目信息卡片
        session_info = self._build_session_info_card()
        
        # 右侧：小说段落和图片卡片
        right_content = ft.Container(
            content=ft.Column(
                [
                    # 上方：当前小说段落卡片（占据一半高度）
                    ft.Container(
                        content=self._build_novel_paragraph_card(),
                        expand=1,  # 占据一半高度
                    ),
                    ft.Container(height=self.SPACING_LARGE),
                    # 下方卡片占位（占据一半高度）
                    ft.Container(
                        content=ft.Card(
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("最近生成的图片", size=16, weight=ft.FontWeight.BOLD),
                                        ft.Container(height=self.SPACING_SMALL),
                                        ft.Text(
                                            "功能开发中...",
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        ),
                                    ],
                                ),
                                padding=self.PADDING_LARGE,
                                expand=True,
                            ),
                            elevation=2,
                            expand=True,
                            surface_tint_color=ft.Colors.GREEN,
                        ),
                        expand=1,  # 占据一半高度
                    ),
                ],
                spacing=0,
            ),
            expand=1,  # 占据一半宽度
        )
        
        # 左右布局 - 左右各占一半宽度
        return ft.Container(
            content=ft.Row(
                [
                    session_info,  # 左侧占一半
                    ft.Container(width=self.SPACING_LARGE),  # 间距
                    right_content,  # 右侧占一半
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
        )
    
    def _build_session_info_card(self) -> ft.Container:
        """构建项目信息卡片"""
        if not self.current_project:
            return ft.Container()
        
        project = self.current_project
        
        # 构建信息行
        info_rows = [
            self._build_info_row("项目 ID", project.project_id),
            self._build_info_row("标题", project.title),
            self._build_info_row("项目路径", project.project_path),
            self._build_info_row("小说路径", project.novel_path or "未设置"),
            self._build_info_row("作者", project.author or "未知"),
            ft.Divider(),
            self._build_info_row("总行数", str(project.total_lines)),
            self._build_info_row("总章节数", str(project.total_chapters)),
            self._build_info_row("当前行", str(project.current_line)),
            self._build_info_row("当前章节", str(project.current_chapter)),
            ft.Divider(),

            self._build_info_row("创建时间", project.created_at.strftime("%Y-%m-%d %H:%M:%S")),
            self._build_info_row("更新时间", project.updated_at.strftime("%Y-%m-%d %H:%M:%S")),
        ]
        
        self.project_info_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.INFO_OUTLINED, size=24),
                                ft.Text("项目信息", size=18, weight=ft.FontWeight.BOLD),
                            ],
                            spacing=self.SPACING_SMALL,
                        ),
                        ft.Container(height=self.SPACING_MEDIUM),
                        ft.Column(
                            info_rows,
                            spacing=self.SPACING_SMALL,
                            scroll=ft.ScrollMode.AUTO,  # 在Column上添加滚动
                            expand=True,  # 占据剩余空间
                        ),
                    ],
                ),
                padding=self.PADDING_LARGE,
            ),
            elevation=2,
            surface_tint_color=ft.Colors.PRIMARY,
        )
        
        return ft.Container(
            content=self.project_info_card,
            expand=1,  # 占据一半宽度
        )
    
    def _build_info_row(self, label: str, value: str) -> ft.Row:
        """构建信息行"""
        return ft.Row(
            [
                ft.Text(
                    label + ":",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    width=100,
                ),
                ft.Text(
                    value,
                    size=14,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    expand=True,
                ),
            ],
            spacing=self.SPACING_SMALL,
        )
    
    def _build_novel_paragraph_card(self) -> ft.Card:
        """构建当前小说段落卡片"""
        if not self.current_project:
            return ft.Card(
                content=ft.Container(
                    content=ft.Text(
                        "未选择项目",
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    padding=self.PADDING_LARGE,
                ),
                elevation=2,
                expand=True,
                surface_tint_color=ft.Colors.BLUE,
            )
        
        # 段落内容文本
        self.novel_paragraph_text = ft.Text(
            "",
            size=14,
            selectable=True,
            expand=True,
        )
        
        # 行号信息
        self.novel_line_info = ft.Text(
            "",
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )
        
        # 上一段按钮
        self.prev_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            tooltip="上一段 (←)",
            on_click=self._on_prev_paragraph,
        )
        
        # 下一段按钮
        self.next_button = ft.IconButton(
            icon=ft.Icons.ARROW_FORWARD,
            tooltip="下一段 (→)",
            on_click=self._on_next_paragraph,
        )
        
        # 加载当前段落内容（不更新控件，因为还未添加到页面）
        self._load_current_paragraph(update_controls=False)
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        # 标题栏
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.BOOK_OUTLINED, size=24),
                                ft.Text("当前小说段落", size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(expand=True),
                                self.novel_line_info,
                            ],
                            spacing=self.SPACING_SMALL,
                        ),
                        ft.Divider(height=1),
                        # 段落内容
                        ft.Container(
                            content=self.novel_paragraph_text,
                            padding=ft.padding.symmetric(vertical=self.PADDING_MEDIUM),
                            expand=True,
                        ),
                        # 控制按钮
                        ft.Row(
                            [
                                self.prev_button,
                                ft.Container(expand=True),
                                self.next_button,
                            ],
                            spacing=self.SPACING_SMALL,
                        ),
                    ],
                    expand=True,
                    spacing=self.SPACING_SMALL,
                ),
                padding=self.PADDING_LARGE,
                expand=True,
            ),
            elevation=2,
            expand=True,
            surface_tint_color=ft.Colors.BLUE,
        )
    
    def _load_current_paragraph(self, update_controls: bool = True):
        """
        加载当前段落内容
        
        :param update_controls: 是否调用控件的 update() 方法（如果控件还未添加到页面，应设为 False）
        """
        if not self.current_project:
            return
        
        try:
            # 从数据库获取当前行的内容
            novel_content = NovelContentService.get_by_line(
                self.current_project.project_id,
                self.current_project.current_chapter,
                self.current_project.current_line
            )
            
            if novel_content:
                # 更新段落文本
                if self.novel_paragraph_text:
                    self.novel_paragraph_text.value = novel_content.content
                    if update_controls and self.page:
                        # 检查控件是否已挂载
                        if hasattr(self.novel_paragraph_text, 'page') and self.novel_paragraph_text.page:
                            try:
                                self.novel_paragraph_text.update()
                            except (AssertionError, AttributeError):
                                # 控件未挂载，使用页面更新
                                self.page.update()
                        else:
                            # 控件未挂载，使用页面更新
                            self.page.update()
                
                # 更新行号信息
                if self.novel_line_info:
                    if self.current_project.total_chapters > 0:
                        self.novel_line_info.value = f"第 {self.current_project.current_chapter} 章 / 第 {self.current_project.current_line} 段"
                    else:
                        self.novel_line_info.value = f"第 {self.current_project.current_line} 段 / 共 {self.current_project.total_lines} 段"
                    if update_controls and self.page:
                        # 检查控件是否已挂载
                        if hasattr(self.novel_line_info, 'page') and self.novel_line_info.page:
                            try:
                                self.novel_line_info.update()
                            except (AssertionError, AttributeError):
                                # 控件未挂载，使用页面更新
                                self.page.update()
                        else:
                            # 控件未挂载，使用页面更新
                            self.page.update()
                
                # 更新按钮状态
                if self.prev_button:
                    self.prev_button.disabled = self.current_project.current_line == 0
                    if update_controls and self.page:
                        # 检查控件是否已挂载
                        if hasattr(self.prev_button, 'page') and self.prev_button.page:
                            try:
                                self.prev_button.update()
                            except (AssertionError, AttributeError):
                                # 控件未挂载，使用页面更新
                                self.page.update()
                        else:
                            # 控件未挂载，使用页面更新
                            self.page.update()
                
                if self.next_button:
                    self.next_button.disabled = self.current_project.current_line >= self.current_project.total_lines - 1
                    if update_controls and self.page:
                        # 检查控件是否已挂载
                        if hasattr(self.next_button, 'page') and self.next_button.page:
                            try:
                                self.next_button.update()
                            except (AssertionError, AttributeError):
                                # 控件未挂载，使用页面更新
                                self.page.update()
                        else:
                            # 控件未挂载，使用页面更新
                            self.page.update()
            else:
                # 没有找到内容
                if self.novel_paragraph_text:
                    self.novel_paragraph_text.value = "未找到段落内容"
                    if update_controls and self.page:
                        # 检查控件是否已挂载
                        if hasattr(self.novel_paragraph_text, 'page') and self.novel_paragraph_text.page:
                            try:
                                self.novel_paragraph_text.update()
                            except (AssertionError, AttributeError):
                                # 控件未挂载，使用页面更新
                                self.page.update()
                        else:
                            # 控件未挂载，使用页面更新
                            self.page.update()
                
                if self.novel_line_info:
                    self.novel_line_info.value = ""
                    if update_controls and self.page:
                        # 检查控件是否已挂载
                        if hasattr(self.novel_line_info, 'page') and self.novel_line_info.page:
                            try:
                                self.novel_line_info.update()
                            except (AssertionError, AttributeError):
                                # 控件未挂载，使用页面更新
                                self.page.update()
                        else:
                            # 控件未挂载，使用页面更新
                            self.page.update()
                
        except Exception as e:  # pylint: disable=broad-except
            logger.exception(f"加载段落内容失败: {e}")
            if self.novel_paragraph_text:
                self.novel_paragraph_text.value = f"加载失败: {e}"
                if update_controls and self.page:
                    # 检查控件是否已挂载
                    if hasattr(self.novel_paragraph_text, 'page') and self.novel_paragraph_text.page:
                        try:
                            self.novel_paragraph_text.update()
                        except (AssertionError, AttributeError):
                            # 控件未挂载，使用页面更新
                            self.page.update()
                    else:
                        # 控件未挂载，使用页面更新
                        self.page.update()
    
    def _on_prev_paragraph(self, _e):
        """上一段按钮点击"""
        # 检查组件是否已挂载到页面
        if not self.page:
            logger.debug("HomePage 尚未挂载到页面，跳过段落切换")
            return
        
        if not self.current_project or self.current_project.current_line <= 0:
            return
        
        try:
            # 更新当前行
            new_line = self.current_project.current_line - 1
            
            # 保存到数据库
            updated_session = ProjectService.update(
                self.current_project.project_id,
                current_line=new_line
            )
            
            if updated_session:
                self.current_project = updated_session
                
                # 重新加载段落
                self._load_current_paragraph()
                
                # 更新左侧信息卡片
                self._update_content()
                
                logger.info(f"切换到上一段: 行 {new_line}")
            
        except Exception as ex:  # pylint: disable=broad-except
            logger.exception(f"切换上一段失败: {ex}")
            self._show_toast(f"切换失败: {ex}", ft.Colors.RED_700)
    
    def _on_next_paragraph(self, _e):
        """下一段按钮点击"""
        # 检查组件是否已挂载到页面
        if not self.page:
            logger.debug("HomePage 尚未挂载到页面，跳过段落切换")
            return
        
        if not self.current_project or self.current_project.current_line >= self.current_project.total_lines - 1:
            return
        
        try:
            # 更新当前行
            new_line = self.current_project.current_line + 1
            
            # 保存到数据库
            updated_session = ProjectService.update(
                self.current_project.project_id,
                current_line=new_line
            )
            
            if updated_session:
                self.current_project = updated_session
                
                # 重新加载段落
                self._load_current_paragraph()
                
                # 更新左侧信息卡片
                self._update_content()
                
                logger.info(f"切换到下一段: 行 {new_line}")
            
        except Exception as ex:  # pylint: disable=broad-except
            logger.exception(f"切换下一段失败: {ex}")
            self._show_toast(f"切换失败: {ex}", ft.Colors.RED_700)
    
    def _load_sessions(self):
        """加载项目列表"""
        try:
            self.projects = ProjectService.list()
            logger.info(f"加载了 {len(self.projects)} 个项目")
            
            # 更新下拉列表选项
            if self.project_dropdown:
                self.project_dropdown.options = [
                    ft.dropdown.Option(key=s.project_id, text=s.title)
                    for s in self.projects
                ]
            
                # 如果没有项目，立即清空下拉列表
            if len(self.projects) == 0:
                self.current_project = None
                if self.project_dropdown:
                    self.project_dropdown.value = None
                    self.project_dropdown.disabled = True
            else:
                # 有项目时，恢复或选择
                if self.project_dropdown:
                    self.project_dropdown.disabled = False
                
                # 恢复上次选中的项目
                if app_settings.ui.current_project_id:
                    self.current_project = ProjectService.get(app_settings.ui.current_project_id)
                    if self.current_project and self.project_dropdown:
                        self.project_dropdown.value = self.current_project.project_id
                
                # 如果没有选中项目但有项目列表，选中第一个
                if not self.current_project and self.projects:
                    self.current_project = self.projects[0]
                    if self.project_dropdown:
                        self.project_dropdown.value = self.current_project.project_id
                    app_settings.ui.current_project_id = self.current_project.project_id
                    app_settings.save()
            
            # 更新内容区域（会调用整个页面的 update）
            self._update_content()
            
            # 在页面更新后，再次确保下拉列表状态正确
            # 因为 self.update() 可能会重新渲染组件
            if self.project_dropdown:
                if len(self.projects) == 0:
                    self.project_dropdown.value = None
                    self.project_dropdown.disabled = True
                    self.project_dropdown.update()
                elif self.current_project:
                    self.project_dropdown.value = self.current_project.project_id
                    self.project_dropdown.update()
            
        except Exception as e:
            logger.exception(f"加载项目列表失败: {e}")
            self._show_toast("加载项目列表失败", ft.Colors.RED_700)
    
    def _update_content(self):
        """更新内容区域"""
        # 检查组件是否已挂载到页面
        if not self.page:
            logger.debug("HomePage 尚未挂载到页面，跳过内容更新")
            return
        
        if self.content_area:
            self.content_area.content = self._build_session_content()
            
            # 更新删除按钮状态
            if hasattr(self, 'delete_button') and self.delete_button:
                self.delete_button.disabled = self.current_project is None
            
            self.update()
    
    def _on_session_change(self, e: ft.ControlEvent):
        """项目切换事件"""
        project_id = e.control.value
        if project_id:
            self.current_project = ProjectService.get(project_id)
            app_settings.ui.current_project_id = project_id
            app_settings.save()
            logger.info(f"切换到项目: {project_id}")
            self._update_content()
            # 重新加载段落内容
            self._load_current_paragraph()
    
    def _on_create_session(self, e):
        """创建项目按钮点击事件 - 使用官方推荐的方式"""
        logger.info("点击创建项目按钮")
        
        def on_success(created_project):
            """创建成功回调"""
            logger.info(f"创建项目成功回调: {created_project.project_id}")
            # 重新加载项目列表
            self._load_sessions()
            # 切换到新项目
            self.current_project = created_project
            app_settings.ui.current_project_id = created_project.project_id
            app_settings.save()
            if self.project_dropdown:
                self.project_dropdown.value = created_project.project_id
            self._update_content()
        
        # 使用 Flet 官方推荐方式打开对话框
        dialog = CreateProjectDialog(self.page, on_success=on_success)
        self.page.open(dialog)
    
    def _on_delete_session(self, e):
        """删除项目按钮点击事件 - 使用官方推荐的方式"""
        if not self.current_project:
            logger.warning("没有选中的项目，无法删除")
            return
        
        logger.info(f"点击删除项目按钮: {self.current_project.project_id}")
        
        def on_success():
            """删除成功回调"""
            logger.info("删除项目成功回调")
            # 清空当前项目
            self.current_project = None
            app_settings.ui.current_project_id = None
            app_settings.save()
            # 重新加载项目列表
            self._load_sessions()
        
        # 使用 Flet 官方推荐方式打开对话框
        dialog = DeleteProjectDialog(self.page, self.current_project, on_success=on_success)
        self.page.open(dialog)
    
    def _show_toast(self, message: str, bgcolor: str):
        """显示 Toast 提示"""
        if not self.page:
            # 如果没有页面对象，直接打印
            print(f"Toast: {message}")
            return
        
        try:
            duration_sec = 3  # 转换为秒
            if bgcolor == ft.Colors.GREEN_700:
                flet_toast.sucess(
                    page=self.page,
                    message=message,
                    position=Position.TOP_RIGHT,
                    duration=duration_sec
                )
            elif bgcolor == ft.Colors.RED_700:
                flet_toast.error(
                    page=self.page,
                    message=message,
                    position=Position.TOP_RIGHT,
                    duration=duration_sec
                )
            else:
                # 默认为 success
                flet_toast.sucess(
                    page=self.page,
                    message=message,
                    position=Position.TOP_RIGHT,
                    duration=duration_sec
                )
        except Exception:
            logger.exception("显示 Toast 失败")
            print(f"Toast: {message}")

"""
通用详情视图组件（非对话框版本）。

可以在对话框或其他容器中使用，提供统一的详情展示逻辑：
- 左右切换按钮固定在页面左右侧
- 支持上图下详情和左图右详情两种布局
- 根据页面剩余宽度自动切换布局模式
"""
import flet as ft
from typing import Dict, Callable, Optional
from api.constants.ui import (
    SPACING_SMALL,
)
from api.utils.responsive import ResponsiveHelper


class DetailView(ft.Container):
    """通用详情视图组件。
    
    支持统一的详情展示逻辑：
    - 左右切换按钮固定在页面左右侧
    - 支持上图下详情和左图右详情两种布局
    - 根据页面剩余宽度自动切换布局模式
    """
    
    def __init__(
        self,
        image_control: ft.Control,
        detail_items: Dict[str, ft.Control],
        current_index: int = 0,
        total_count: int = 1,
        on_previous: Optional[Callable] = None,
        on_next: Optional[Callable] = None,
        page: Optional[ft.Page] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        responsive: Optional[ResponsiveHelper] = None,
    ):
        """初始化通用详情视图。
        
        :param image_control: 图片控件
        :param detail_items: 详情项字典，格式为 {title: control}
        :param current_index: 当前索引
        :param total_count: 总数量
        :param on_previous: 上一页回调函数
        :param on_next: 下一页回调函数
        :param page: Flet 页面对象（用于响应式布局）
        :param width: 视图宽度（可选）
        :param height: 视图高度（可选）
        :param responsive: 响应式辅助类（可选，如果不提供则从page获取）
        """
        super().__init__()
        
        self.image_control = image_control
        self.detail_items = detail_items
        self.current_index = current_index
        self.total_count = total_count
        self.on_previous = on_previous
        self.on_next = on_next
        self.page = page
        
        # 获取响应式辅助类
        if responsive:
            self.responsive = responsive
        elif page:
            from api.utils.responsive import get_responsive_helper
            self.responsive = get_responsive_helper(page)
        else:
            self.responsive = ResponsiveHelper(1024)
        
        # 设置容器属性
        self.width = width
        self.height = height
        self.expand = width is None and height is None
        
        # 构建导航按钮
        self.prev_button = ft.ElevatedButton(
            content=ft.Icon(ft.Icons.CHEVRON_LEFT, size=40),
            on_click=self._go_previous,
            tooltip="上一个",
            disabled=current_index == 0,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.padding.symmetric(horizontal=15, vertical=80),
            ),
            width=70,
        )
        
        self.next_button = ft.ElevatedButton(
            content=ft.Icon(ft.Icons.CHEVRON_RIGHT, size=40),
            on_click=self._go_next,
            tooltip="下一个",
            disabled=current_index >= total_count - 1,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.padding.symmetric(horizontal=15, vertical=80),
            ),
            width=70,
        )
        
        # 构建内容
        self._build_content()
    
    def _build_content(self):
        """构建视图内容，根据页面宽度决定布局方式。
        
        布局判断逻辑：
        - 计算可用宽度（视图宽度减去左右按钮和间距）
        - 如果可用宽度能放下图片+分隔线+详情最小宽度，则使用左右布局
        - 否则使用上下布局
        """
        # 计算可用宽度（视图宽度减去左右按钮和间距）
        button_width = 70
        spacing = SPACING_SMALL * 2  # 左右按钮与内容之间的间距
        # 如果width未设置，使用响应式的对话框宽度
        view_width = self.width if self.width else self.responsive.dialog_wide_width
        available_width = view_width - button_width * 2 - spacing
        
        # 获取详情最小宽度和大图宽度
        detail_min_width = self.responsive.detail_info_min_width
        image_width = self.responsive.large_image_width
        divider_width = 1
        
        # 判断布局方式：如果可用宽度能放下图片+分隔线+详情，则左右布局，否则上下布局
        required_width = image_width + divider_width + detail_min_width + SPACING_SMALL * 2
        use_horizontal_layout = available_width >= required_width
        
        if use_horizontal_layout:
            # 左右布局：左图右详情
            self._build_horizontal_layout()
        else:
            # 上下布局：上图下详情
            self._build_vertical_layout()
    
    def _build_horizontal_layout(self):
        """构建左右布局（左图右详情）。"""
        # 详情部分：title和组件放在两行
        detail_rows = []
        for title, control in self.detail_items.items():
            detail_rows.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(f"{title}:", weight=ft.FontWeight.BOLD),
                            control,
                        ],
                        tight=True,
                        spacing=2,
                    ),
                    padding=ft.padding.symmetric(horizontal=SPACING_SMALL, vertical=2),
                )
            )
        
        detail_container = ft.Container(
            content=ft.Column(
                controls=detail_rows,
                tight=True,
                spacing=SPACING_SMALL,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            padding=ft.padding.symmetric(horizontal=SPACING_SMALL),
            width=self.responsive.detail_info_min_width,
        )
        
        # 图片容器
        image_container = ft.Container(
            content=self.image_control,
            width=self.responsive.large_image_width,
        )
        
        # 中间内容区域：图片、分隔线、详情
        content_area = ft.Row(
            controls=[
                image_container,
                ft.VerticalDivider(width=1),
                detail_container,
            ],
            spacing=SPACING_SMALL,
            expand=True,
        )
        
        # 整体布局：左按钮、内容区域、右按钮（按钮固定在页面左右侧）
        self.content = ft.Row(
            controls=[
                self.prev_button,
                content_area,
                self.next_button,
            ],
            spacing=SPACING_SMALL,
            expand=True,
        )
    
    def _build_vertical_layout(self):
        """构建上下布局（上图下详情）。
        
        布局顺序：左按钮、内容区域（上图下详情）、右按钮
        内容区域应该是可滚动的。
        """
        # 详情部分：title和组件放在一行（左title右组件）
        detail_rows = []
        for title, control in self.detail_items.items():
            detail_rows.append(
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(f"{title}:", weight=ft.FontWeight.BOLD),
                            width=self.responsive.detail_label_width,
                            padding=ft.padding.symmetric(horizontal=0, vertical=2),
                        ),
                        ft.Container(
                            content=control,
                            expand=True,
                            padding=ft.padding.symmetric(horizontal=5, vertical=2),
                        ),
                    ],
                    spacing=10,
                )
            )
        
        # 内容区域：图片、分隔线、详情（可滚动）
        content_area = ft.Column(
            controls=[
                ft.Container(
                    content=self.image_control,
                    alignment=ft.alignment.center,
                ),
                ft.Divider(),
                ft.Column(
                    controls=detail_rows,
                    tight=True,
                    spacing=SPACING_SMALL,
                ),
            ],
            tight=True,
            spacing=SPACING_SMALL,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        
        # 整体布局：左按钮、内容区域、右按钮（按钮固定在页面左右侧）
        self.content = ft.Row(
            controls=[
                self.prev_button,
                content_area,
                self.next_button,
            ],
            spacing=SPACING_SMALL,
            expand=True,
        )
    
    def _go_previous(self, e: ft.ControlEvent):
        """切换到上一项。"""
        if self.current_index > 0 and self.on_previous:
            self.on_previous(e)
    
    def _go_next(self, e: ft.ControlEvent):
        """切换到下一项。"""
        if self.current_index < self.total_count - 1 and self.on_next:
            self.on_next(e)
    
    def update_index(self, new_index: int):
        """更新当前索引并刷新UI。
        
        :param new_index: 新的索引值
        """
        self.current_index = new_index
        self.prev_button.disabled = new_index == 0
        self.next_button.disabled = new_index >= self.total_count - 1
        
        # 重新构建内容
        self._build_content()
        
        if self.page:
            self.update()
    
    def update_image(self, new_image_control: ft.Control):
        """更新图片控件。
        
        :param new_image_control: 新的图片控件
        """
        self.image_control = new_image_control
        self._build_content()
        
        if self.page:
            self.update()
    
    def update_details(self, new_detail_items: Dict[str, ft.Control]):
        """更新详情项。
        
        :param new_detail_items: 新的详情项字典
        """
        self.detail_items = new_detail_items
        self._build_content()
        
        if self.page:
            self.update()


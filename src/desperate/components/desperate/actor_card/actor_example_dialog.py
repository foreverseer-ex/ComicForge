"""
Actor 示例图（立绘）对话框。

以网格形式展示示例图，点击单项可查看大图和详细参数。
"""
import flet as ft

from api.schemas.actor import Actor, ActorExample
from api.components.desperate.detail_view import DetailView
from api.components.desperate.detail_dialog import create_copyable_text
from api.constants.ui import (
    THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT,
    SPACING_MEDIUM,
)
from api.utils.responsive import ResponsiveHelper, get_responsive_helper


class ActorExampleDialog(ft.AlertDialog):
    """Actor 示例图对话框类。"""
    
    def __init__(self, actor: Actor, page: ft.Page = None):
        """初始化示例图对话框。
        
        :param actor: Actor 对象
        :param page: Flet 页面对象（可选，用于响应式布局）
        """
        super().__init__()
        self.actor = actor
        self.page = page
        
        # 获取响应式辅助类
        if page:
            self.responsive = get_responsive_helper(page)
        else:
            self.responsive = ResponsiveHelper(1024)  # 默认中等尺寸
        
        # 状态管理
        self._view = 0  # 0: 网格视图, 1: 详情视图
        self._selected_index = -1
        self._total_examples = len(actor.examples) if actor.examples else 0
        
        # 配置对话框属性
        self.modal = True
        
        # 标题栏组件
        self.back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=self._back_to_list,
            visible=False,
            tooltip="返回",
        )
        self.title_text = ft.Text(f"{actor.name} - 示例图", size=18, weight=ft.FontWeight.BOLD)
        self.close_button = ft.IconButton(
            icon=ft.Icons.CLOSE,
            on_click=self._close,
            tooltip="关闭",
        )
        
        # 构建标题栏
        self.title = ft.Row(
            controls=[
                self.back_button,
                ft.Container(content=self.title_text, expand=True),
                self.close_button,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        # 构建内容容器（响应式尺寸）
        self.content_container = ft.Container(
            width=self.responsive.dialog_wide_width,
            height=self.responsive.dialog_wide_height
        )
        self.content = self.content_container
        
        # 移除底部按钮
        self.actions = []
        
        # 初始渲染
        self._render_grid()
    
    def _render_grid(self):
        """渲染图片网格视图。"""
        if not self.actor.examples:
            self.content_container.content = ft.Container(
                content=ft.Text("无示例图", size=16, color=ft.Colors.GREY_400),
                alignment=ft.alignment.center,
            )
            return
        
        # 为每个示例创建占位符
        tiles = []
        for idx, example_dict in enumerate(self.actor.examples):
            # 解析示例数据
            example = ActorExample(**example_dict)
            
            # 创建缩略图占位符
            tile = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.IMAGE, size=48, color=ft.Colors.GREY_400),
                        ft.Text(example.title, size=12, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                width=THUMBNAIL_WIDTH,
                height=THUMBNAIL_HEIGHT,
                bgcolor=ft.Colors.GREY_200,
                border_radius=8,
                alignment=ft.alignment.center,
                on_click=lambda e, i=idx: self._enter_detail(e, i),
            )
            tiles.append(tile)
        
        # 使用 Row + wrap=True 实现 flow layout
        flow_layout = ft.Row(
            controls=tiles,
            wrap=True,
            run_spacing=SPACING_MEDIUM,
            spacing=SPACING_MEDIUM,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        self.content_container.content = ft.Column(
            controls=[flow_layout],
            scroll=ft.ScrollMode.AUTO,
        )
    
    def _render_detail(self):
        """渲染详情视图：使用DetailView通用组件。"""
        idx = self._selected_index
        if 0 <= idx < len(self.actor.examples):
            example_dict = self.actor.examples[idx]
            example = ActorExample(**example_dict)
            
            # 创建大图占位符
            large_image = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.IMAGE, size=96, color=ft.Colors.GREY_400),
                        ft.Text(example.title, size=14),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                width=self.responsive.large_image_width,
                height=self.responsive.large_image_height,
                bgcolor=ft.Colors.GREY_200,
                border_radius=self.responsive.image_border_radius,
                alignment=ft.alignment.center,
            )
            
            # 构建详情项字典
            args = example.draw_args
            detail_items = {
                "标题": create_copyable_text(example.title, self.page),
                "说明": create_copyable_text(example.desc, self.page),
                "图片路径": create_copyable_text(example.image_path, self.page),
                "基础模型": create_copyable_text(args.model, self.page),
                "正面提示词": create_copyable_text(args.prompt if args.prompt else "无", self.page),
                "负面提示词": create_copyable_text(args.negative_prompt if args.negative_prompt else "无", self.page),
                "生成参数": create_copyable_text(
                    f"CFG: {args.cfg_scale} | 采样器: {args.sampler} | 步数: {args.steps} | 种子: {args.seed} | 尺寸: {args.width}×{args.height}",
                    self.page
                ),
            }
            
            # 使用DetailView组件
            self.detail_view = DetailView(
                image_control=large_image,
                detail_items=detail_items,
                current_index=idx,
                total_count=self._total_examples,
                on_previous=self._go_previous,
                on_next=self._go_next,
                page=self.page,
                width=self.responsive.dialog_wide_width,
                height=self.responsive.dialog_wide_height,
                responsive=self.responsive,
            )
            
            self.content_container.content = self.detail_view
        else:
            self.content_container.content = ft.Text("未选择示例")
    
    def _go_previous(self, e: ft.ControlEvent):
        """切换到上一张图片。"""
        if self._selected_index > 0:
            self._selected_index -= 1
            self._update_detail_content()
            if e.page:
                e.page.update()
    
    def _go_next(self, e: ft.ControlEvent):
        """切换到下一张图片。"""
        if self._selected_index < self._total_examples - 1:
            self._selected_index += 1
            self._update_detail_content()
            if e.page:
                e.page.update()
    
    def _update_detail_content(self):
        """更新详情视图的内容（切换图片时调用）。"""
        idx = self._selected_index
        if 0 <= idx < len(self.actor.examples):
            example_dict = self.actor.examples[idx]
            example = ActorExample(**example_dict)
            
            # 重新创建大图占位符
            large_image = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.IMAGE, size=96, color=ft.Colors.GREY_400),
                        ft.Text(example.title, size=14),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                width=self.responsive.large_image_width,
                height=self.responsive.large_image_height,
                bgcolor=ft.Colors.GREY_200,
                border_radius=self.responsive.image_border_radius,
                alignment=ft.alignment.center,
            )
            
            # 更新详情项
            args = example.draw_args
            detail_items = {
                "标题": create_copyable_text(example.title, self.page),
                "说明": create_copyable_text(example.desc, self.page),
                "图片路径": create_copyable_text(example.image_path, self.page),
                "基础模型": create_copyable_text(args.model, self.page),
                "正面提示词": create_copyable_text(args.prompt if args.prompt else "无", self.page),
                "负面提示词": create_copyable_text(args.negative_prompt if args.negative_prompt else "无", self.page),
                "生成参数": create_copyable_text(
                    f"CFG: {args.cfg_scale} | 采样器: {args.sampler} | 步数: {args.steps} | 种子: {args.seed} | 尺寸: {args.width}×{args.height}",
                    self.page
                ),
            }
            
            # 更新DetailView
            if hasattr(self, 'detail_view') and self.detail_view:
                self.detail_view.update_index(idx)
                self.detail_view.update_image(large_image)
                self.detail_view.update_details(detail_items)
            else:
                # 如果不存在，重新创建
                self._render_detail()
    
    def _enter_detail(self, e: ft.ControlEvent, index: int):
        """进入示例图片详情视图。"""
        self._selected_index = index
        self._view = 1
        self.title_text.value = f"{self.actor.name} - 示例详情"
        self.back_button.visible = True
        self._render_detail()
        if e.page:
            e.page.update()
    
    def _back_to_list(self, e: ft.ControlEvent):
        """返回示例图片列表视图。"""
        self._view = 0
        self._selected_index = -1
        self.title_text.value = f"{self.actor.name} - 示例图"
        self.back_button.visible = False
        self._render_grid()
        if e.page:
            e.page.update()
    
    def _close(self, e: ft.ControlEvent):
        """关闭对话框并重置状态。"""
        self._view = 0
        self._selected_index = -1
        self.back_button.visible = False
        
        if e.page:
            e.page.close(self)


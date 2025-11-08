"""
模型示例图片对话框。

以网格形式展示已缓存的示例图，点击单项可查看对应生成参数；
图片与参数均由 LocalModelMetaService 的本地缓存加载。
"""
import flet as ft
from api.schemas.model_meta import ModelMeta
from api.components.desperate.async_media import AsyncMedia
from api.components.desperate.detail_view import DetailView
from api.components.desperate.detail_dialog import create_copyable_text
from api.constants.ui import (
    THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT,
    SPACING_MEDIUM,
    LOADING_SIZE_MEDIUM,
)
from api.utils.responsive import ResponsiveHelper, get_responsive_helper


class ExampleImageDialog(ft.AlertDialog):
    """示例图片对话框类。"""
    
    def __init__(self, model_meta: ModelMeta, page: ft.Page = None):
        """初始化示例图片对话框。
        
        :param model_meta: 模型元数据对象
        :param page: Flet 页面对象（可选，用于响应式布局）
        """
        super().__init__()
        self.model_meta = model_meta
        self.page = page
        
        # 获取响应式辅助类
        if page:
            self.responsive = get_responsive_helper(page)
        else:
            self.responsive = ResponsiveHelper(1024)  # 默认中等尺寸
        
        # 状态管理
        self._view = 0  # 0: 网格视图, 1: 详情视图
        self._selected_index = -1
        self._image_containers = []  # 存储每张图片的 AsyncImage 控件
        self._total_examples = len(model_meta.examples) if model_meta.examples else 0
        
        # 配置对话框属性
        self.modal = True
        
        # 标题栏组件
        self.back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=self._back_to_list,
            visible=False,  # 初始不可见
            tooltip="返回",
        )
        self.title_text = ft.Text("示例图片", size=18, weight=ft.FontWeight.BOLD)
        self.close_button = ft.IconButton(
            icon=ft.Icons.CLOSE,
            on_click=self._close,
            tooltip="关闭",
        )
        
        # 构建标题栏：左侧返回按钮 + 中间标题 + 右侧关闭按钮
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
        
        # 初始渲染（直接显示网格占位）
        self._render_grid_with_placeholders()
    
    def _render_grid_with_placeholders(self):
        """渲染图片网格占位（使用 AsyncImage）。"""
        if not self.model_meta.examples:
            self.content_container.content = ft.Container(
                content=ft.Text("无示例图片", size=16, color=ft.Colors.GREY_400),
                alignment=ft.alignment.center,
            )
            return
        
        # 为每个示例创建 AsyncImage（大尺寸展示）
        self._image_containers = []
        tiles = []
        for idx in range(len(self.model_meta.examples)):
            # 使用 AsyncImage 组件
            async_img = AsyncMedia(
                model_meta=self.model_meta,
                index=idx,
                width=THUMBNAIL_WIDTH,
                height=THUMBNAIL_HEIGHT,
                on_click=lambda e, i=idx: self._enter_detail(e, i),
                border_radius=8,
                loading_size=LOADING_SIZE_MEDIUM,
                loading_text="加载中",
                loading_text_size=12,
            )
            self._image_containers.append(async_img)
            tiles.append(async_img)
        
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
        if 0 <= idx < len(self.model_meta.examples):
            ex = self.model_meta.examples[idx]
            
            # 创建大图预览（使用 AsyncImage，响应式尺寸）
            large_image_control = AsyncMedia(
                model_meta=self.model_meta,
                index=idx,
                width=self.responsive.large_image_width,
                height=self.responsive.large_image_height,
                border_radius=self.responsive.image_border_radius,
                loading_size=self.responsive.loading_size_large,
                loading_text="",
            )
            
            # 构建详情项字典
            args = ex.args
            detail_items = {
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
                image_control=large_image_control,
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
        if 0 <= idx < len(self.model_meta.examples):
            ex = self.model_meta.examples[idx]
            
            # 重新创建 AsyncImage 以刷新图片
            large_image_control = AsyncMedia(
                model_meta=self.model_meta,
                index=idx,
                width=self.responsive.large_image_width,
                height=self.responsive.large_image_height,
                border_radius=self.responsive.image_border_radius,
                loading_size=self.responsive.loading_size_large,
                loading_text="",
            )
            
            # 更新详情项
            args = ex.args
            detail_items = {
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
                self.detail_view.update_image(large_image_control)
                self.detail_view.update_details(detail_items)
            else:
                # 如果不存在，重新创建
                self._render_detail()
    
    def _enter_detail(self, e: ft.ControlEvent, index: int):
        """进入示例图片详情视图。
        
        :param e: 控件事件对象
        :param index: 选中的示例图片索引
        """
        self._selected_index = index
        self._view = 1
        self.title_text.value = "示例详情"
        self.back_button.visible = True  # 显示返回按钮
        self._render_detail()
        if e.page:
            e.page.update()
    
    def _back_to_list(self, e: ft.ControlEvent):
        """返回示例图片列表视图。
        
        :param e: 控件事件对象
        """
        self._view = 0
        self._selected_index = -1
        self.title_text.value = "示例图片"
        self.back_button.visible = False  # 隐藏返回按钮
        self._render_grid_with_placeholders()
        if e.page:
            e.page.update()
    
    def _close(self, e: ft.ControlEvent):
        """关闭对话框并重置状态。
        
        :param e: 控件事件对象
        """
        # 重置状态
        self._view = 0
        self._selected_index = -1
        self._image_containers = []
        self.back_button.visible = False  # 重置返回按钮
        
        if e.page:
            e.page.close(self)

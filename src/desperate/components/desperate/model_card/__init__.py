"""
模型卡片 UI 组件。

为给定模型提供预览图与基础信息徽章的卡片展示；
支持打开"示例图片"与"模型详情"对话框。
"""
import flet as ft

from api.schemas.model_meta import ModelMeta
from api.constants.color import BaseModelColor
from api.constants.ui import (
    CARD_TITLE_MAX_LINES,
    # 向后兼容的默认值
)
from api.components.desperate.async_media import AsyncMedia
from api.utils.responsive import ResponsiveHelper, get_responsive_helper
from .example_image_dialog import ExampleImageDialog
from .model_detail_dialog import ModelDetailDialog
from api.settings import app_settings


class ModelCard(ft.Column):
    """模型的可视化卡片，展示关键信息。"""
    def __init__(
        self, 
        model_meta: ModelMeta, 
        all_models: list[ModelMeta] = None, 
        index: int = 0,
        on_delete: callable = None,
        responsive: ResponsiveHelper = None,
        page: ft.Page = None
    ):
        """初始化模型卡片。
        
        :param model_meta: 模型元数据对象
        :param all_models: 所有模型列表（用于切换导航）
        :param index: 当前模型在列表中的索引
        :param on_delete: 删除回调函数，接收 model_meta 作为参数
        :param responsive: 响应式辅助类（可选，如果不提供则从 page 获取）
        :param page: Flet 页面对象（可选，用于获取响应式辅助类）
        """
        super().__init__()
        self.model_meta = model_meta
        self.all_models = all_models or [model_meta]
        self.index = index
        self.on_delete_callback = on_delete
        self.page = page
        self.delete_confirm_dialog = None  # 延迟创建
        
        # 获取响应式辅助类
        if responsive:
            self.responsive = responsive
        elif page:
            self.responsive = get_responsive_helper(page)
        else:
            # 默认使用中等尺寸
            self.responsive = ResponsiveHelper(1024)
        
        self.width = self.responsive.thumbnail_width  # 响应式宽度
        
        # 检查是否需要显示警告图标（sd-forge 后端且本地文件不存在）
        show_warning = (app_settings.draw.backend == "sd_forge" and not self._check_file_exists())
        
        # 使用 AsyncImage 组件
        self.preview_image = AsyncMedia(
            model_meta=model_meta,
            index=0,
            width=self.responsive.thumbnail_width,
            height=self.responsive.thumbnail_height,
            on_click=self._open_examples_dialog,
            border_radius=self.responsive.image_border_radius,
            loading_size=self.responsive.loading_size_medium,
            loading_text="加载中...",
            loading_text_size=self.responsive.font_caption,
            privacy_mode=app_settings.ui.privacy_mode,
        )
        
        # 图片容器：包含图片和警告图标（如果需要）
        image_container = ft.Stack(
            controls=[
                self.preview_image,
                # 警告图标（右上角）
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.WARNING_AMBER_ROUNDED,
                        size=20,
                        color=ft.Colors.ORANGE_700,
                    ),
                    tooltip="本地文件不存在（仅元数据）",
                    visible=show_warning,
                    top=5,
                    right=5,
                    bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
                    border_radius=15,
                    padding=3,
                ) if show_warning else ft.Container(width=0, height=0),
            ],
        )
        
        info_control = self._build_info()
        
        # 获取基础模型的颜色（用于边框）
        base_model_color = BaseModelColor.get(self.model_meta.base_model)
        
        self.controls = [
            ft.GestureDetector(
                content=ft.Container(
                    content=ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                controls=[
                                    image_container,
                                    ft.Container(
                                        content=info_control,
                                        on_click=self._open_detail_dialog
                                    ),
                                ],
                                spacing=self.responsive.spacing_small,
                            ),
                            padding=self.responsive.spacing_small,
                        ),
                        elevation=2,  # 轻微阴影
                    ),
                    # ✨ 添加边框，颜色和 chip 一致
                    border=ft.border.all(2, base_model_color),
                    border_radius=10,
                ),
                on_secondary_tap_down=self._on_right_click,  # 右键菜单
            )
        ]

    def _check_file_exists(self) -> bool:
        """检查模型文件是否在本地存在（仅对 sd-forge 后端有效）"""
        # 如果是 civitai 后端，总是返回 True（civitai 后端总是有模型）
        if app_settings.draw.backend == "civitai":
            return True
        
        # 对于 sd-forge 后端，检查文件是否存在
        if self.model_meta.type == "checkpoint":
            file_path = app_settings.sd_forge.checkpoint_home / self.model_meta.filename
        elif self.model_meta.type == "lora":
            file_path = app_settings.sd_forge.lora_home / self.model_meta.filename
        elif self.model_meta.type == "vae":
            file_path = app_settings.sd_forge.vae_home / self.model_meta.filename
        else:
            return True  # 未知类型，假设存在
        
        return file_path.exists()
    
    def _build_info(self):
        """构建标题与徽章，展示模型版本与基础类型。"""
        # 标题：固定高度容器，垂直居中，限制最多2行，超出部分显示省略号
        title = ft.Container(
            content=ft.Text(
                self.model_meta.version_name,
                size=self.responsive.font_subtitle,
                weight=ft.FontWeight.BOLD,
                max_lines=CARD_TITLE_MAX_LINES,
                overflow=ft.TextOverflow.ELLIPSIS,
                tooltip=self.model_meta.version_name,  # 鼠标悬停显示完整名称
            ),
            height=self.responsive.card_title_height,  # 响应式标题区域高度
            alignment=ft.alignment.center_left,  # 垂直居中，水平左对齐
        )
        
        # 获取基础模型的颜色
        base_model_color = BaseModelColor.get(self.model_meta.base_model)
        
        # 基础模型 chip：占据整行宽度
        base_model_chip = ft.Container(
            content=ft.Text(
                self.model_meta.base_model,
                size=self.responsive.chip_text_size,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=base_model_color,
            padding=ft.padding.symmetric(
                horizontal=self.responsive.chip_padding_h,
                vertical=self.responsive.chip_padding_v
            ),
            border_radius=self.responsive.chip_border_radius,
            border=ft.border.all(
                self.responsive.chip_border_width,
                ft.Colors.with_opacity(0.3, ft.Colors.WHITE)
            ),
            alignment=ft.alignment.center,
        )
        
        controls = [title, base_model_chip]
        
        # 信息区域：标题 + 基础模型 chip
        return ft.Column(
            controls=controls,
            spacing=self.responsive.spacing_small,
            tight=True,  # 紧凑排列，缩小底部间距
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,  # 子元素横向拉伸填充
        )

    def _open_detail_dialog(self, e: ft.ControlEvent | None = None):
        """打开展示模型详细元数据的对话框。
        
        :param e: 控件事件对象
        """
        page = e.page if e and e.page else self.page
        dlg = ModelDetailDialog(
            model_meta=self.model_meta,
            all_models=self.all_models,
            current_index=self.index,
            page=page
        )
        if page:
            # 打开对话框（AsyncImage 会自动加载）
            page.open(dlg)

    def _open_examples_dialog(self, e: ft.ControlEvent | None = None):
        """打开列出模型示例图片的对话框。
        
        :param e: 控件事件对象
        """
        page = e.page if e and e.page else self.page
        dlg = ExampleImageDialog(self.model_meta, page=page)
        if page:
            # 打开对话框（AsyncImage 会自动加载）
            page.open(dlg)
    
    
    
    def _on_right_click(self, e: ft.TapEvent):
        """右键菜单处理。
        
        :param e: 手势事件对象
        """
        if not self.on_delete_callback:
            return
        
        # 创建删除确认对话框
        self._open_delete_confirm_dialog(e)
    
    def _open_delete_confirm_dialog(self, e: ft.TapEvent):
        """打开删除确认对话框"""
        if not e.page:
            return
        
        # 创建删除确认对话框
        dialog = DeleteModelConfirmDialog(
            model_meta=self.model_meta,
            on_confirm=lambda: self.on_delete_callback(self.model_meta) if self.on_delete_callback else None,
        )
        
        e.page.open(dialog)


# ============================================================================
# Dialog 类定义
# ============================================================================

class DeleteModelConfirmDialog(ft.AlertDialog):
    """删除模型确认对话框"""
    
    def __init__(self, model_meta: 'ModelMeta', on_confirm: callable):
        """
        初始化删除模型确认对话框
        
        Args:
            model_meta: 要删除的模型元数据
            on_confirm: 确认回调函数，无参数
        """
        self.model_meta = model_meta
        self.on_confirm = on_confirm
        
        super().__init__(
            modal=True,
            title=ft.Text("确认删除", color=ft.Colors.RED_700),
            content=ft.Column([
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=48, color=ft.Colors.ORANGE_700),
                ft.Text("即将删除以下模型元数据：", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"名称：{model_meta.name}", size=14),
                ft.Text(f"版本：{model_meta.version_name}", size=14),
                ft.Text(f"类型：{model_meta.type}", size=14),
                ft.Text(f"基础模型：{model_meta.base_model}", size=14),
                ft.Divider(),
                ft.Text("⚠️ 此操作将删除：", size=14, color=ft.Colors.RED_700, weight=ft.FontWeight.BOLD),
                ft.Text("• metadata.json 文件", size=12),
                ft.Text(f"• {len(model_meta.examples)} 张示例图片", size=12),
                ft.Text("• 整个元数据目录", size=12),
                ft.Divider(),
                ft.Text("⚠️ 此操作不可恢复！", size=14, color=ft.Colors.RED_700, weight=ft.FontWeight.BOLD),
            ], tight=True, spacing=8, width=400, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.TextButton("取消", on_click=self._on_cancel),
                ft.ElevatedButton(
                    "确认删除",
                    bgcolor=ft.Colors.RED_700,
                    color=ft.Colors.WHITE,
                    on_click=self._on_confirm
                ),
            ],
        )
    
    def _on_confirm(self, e):
        """确认删除"""
        # 关闭对话框
        self.open = False
        self.update()
        
        # 调用确认回调
        if self.on_confirm:
            self.on_confirm()
    
    def _on_cancel(self, e):
        """取消删除"""
        self.open = False
        self.update()

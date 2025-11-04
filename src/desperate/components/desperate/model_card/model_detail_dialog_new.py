"""
模型详情对话框（使用通用组件重构）。

展示模型的详细元数据和大图预览。
"""
import flet as ft
from flet_toast import flet_toast
from flet_toast.Types import Position
from api.schemas.model_meta import ModelMeta
from api.components.desperate.async_media import AsyncMedia
from api.components.desperate.editable_text import EditableText
from api.components.desperate.detail_dialog import DetailDialog, create_copyable_text
from api.services.model_meta import local_model_meta_service
from api.utils.responsive import ResponsiveHelper, get_responsive_helper


class ModelDetailDialog(DetailDialog):
    """模型详情对话框类（使用通用组件）。"""
    
    def __init__(self, model_meta: ModelMeta, all_models: list[ModelMeta] = None, current_index: int = 0, page: ft.Page = None):
        """初始化模型详情对话框。
        
        :param model_meta: 模型元数据对象
        :param all_models: 所有模型列表（用于切换导航）
        :param current_index: 当前模型在列表中的索引
        :param page: Flet 页面对象（可选，用于响应式布局）
        """
        self.model_meta = model_meta
        self.all_models = all_models or [model_meta]
        self.page = page
        
        # 获取响应式辅助类
        if page:
            self.responsive = get_responsive_helper(page)
        else:
            self.responsive = ResponsiveHelper(1024)
        
        # 构建图片控件
        self.preview_image_control = AsyncMedia(
            model_meta=model_meta,
            index=0,
            width=self.responsive.large_image_width,
            height=self.responsive.large_image_height,
            border_radius=self.responsive.image_border_radius,
            loading_size=self.responsive.loading_size_large,
            loading_text="",
        )
        
        # 构建详情项
        detail_items = self._build_detail_items()
        
        # 调用父类初始化
        super().__init__(
            title="模型详情",
            image_control=self.preview_image_control,
            detail_items=detail_items,
            current_index=current_index,
            total_count=len(self.all_models),
            on_previous=self._go_previous,
            on_next=self._go_next,
            page=page,
            dialog_width=self.responsive.dialog_standard_width,
            dialog_height=self.responsive.dialog_standard_height,
        )
    
    def _build_detail_items(self) -> dict[str, ft.Control]:
        """构建详情项字典。
        
        :return: 详情项字典，格式为 {title: control}
        """
        meta = self.model_meta
        items = {}
        
        # 基础信息
        items["版本名称"] = create_copyable_text(meta.version_name, self.page)
        items["模型类型"] = create_copyable_text(meta.type, self.page)
        items["生态系统"] = create_copyable_text(meta.ecosystem.upper(), self.page)
        items["基础模型"] = create_copyable_text(meta.base_model if meta.base_model else "未知", self.page)
        items["AIR 标识符"] = create_copyable_text(meta.air, self.page)
        
        # 网页链接
        if meta.web_page_url:
            def _open_link(_e):
                if self.page:
                    self.page.launch_url(meta.web_page_url)
            
            items["网页链接"] = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.OPEN_IN_BROWSER, size=14, color=ft.Colors.BLUE_400),
                        ft.Text(
                            meta.web_page_url if len(meta.web_page_url) <= 50 else f"{meta.web_page_url[:47]}...",
                            color=ft.Colors.BLUE_400,
                            weight=ft.FontWeight.W_500,
                        ),
                    ],
                    spacing=4,
                    tight=True,
                ),
                on_click=_open_link,
                tooltip="点击打开浏览器",
                padding=ft.padding.symmetric(horizontal=5, vertical=2),
                ink=True,
                border_radius=4,
            )
        
        # 触发词
        if meta.trained_words:
            items["触发词"] = create_copyable_text(", ".join(meta.trained_words), self.page)
        
        # 可编辑的说明字段
        desc_editable = EditableText(
            value=meta.desc,
            placeholder="点击添加说明...",
            on_submit=lambda new_desc: self._handle_desc_update(new_desc),
            multiline=False,
        )
        items["说明"] = desc_editable
        
        return items
    
    def _handle_desc_update(self, new_desc: str):
        """处理描述更新。
        
        :param new_desc: 新的描述内容
        """
        import asyncio
        
        # 更新描述并保存
        self.model_meta.desc = new_desc if new_desc else None
        asyncio.run(local_model_meta_service.save(self.model_meta))
        
        # 显示提示
        if self.page:
            flet_toast.sucess(
                page=self.page,
                message="说明已保存",
                position=Position.TOP_RIGHT,
                duration=2
            )
    
    def _go_previous(self, e: ft.ControlEvent):
        """切换到上一个模型。"""
        if self.current_index > 0:
            new_index = self.current_index - 1
            self._update_content(new_index)
    
    def _go_next(self, e: ft.ControlEvent):
        """切换到下一个模型。"""
        if self.current_index < len(self.all_models) - 1:
            new_index = self.current_index + 1
            self._update_content(new_index)
    
    def _update_content(self, new_index: int):
        """更新对话框内容以显示当前索引的模型。
        
        :param new_index: 新的索引值
        """
        # 更新当前索引和模型
        self.current_index = new_index
        self.model_meta = self.all_models[new_index]
        
        # 更新图片控件
        self.preview_image_control = AsyncMedia(
            model_meta=self.model_meta,
            index=0,
            width=self.responsive.large_image_width,
            height=self.responsive.large_image_height,
            border_radius=self.responsive.image_border_radius,
            loading_size=self.responsive.loading_size_large,
            loading_text="",
        )
        
        # 更新详情项
        detail_items = self._build_detail_items()
        
        # 更新组件
        self.update_index(new_index)
        self.update_image(self.preview_image_control)
        self.update_details(detail_items)


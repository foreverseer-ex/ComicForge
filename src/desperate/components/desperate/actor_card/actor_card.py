"""
Actor 卡片组件。

展示 Actor 的基本信息和缩略图。
"""
import flet as ft

from api.schemas.actor import Actor
from api.constants.ui import CARD_WIDTH, SPACING_SMALL
from .actor_detail_dialog import ActorDetailDialog
from .actor_example_dialog import ActorExampleDialog


class ActorCard(ft.Card):
    """Actor 卡片组件。"""
    
    def __init__(self, actor: Actor, all_actors: list[Actor] = None, index: int = 0, on_delete: callable = None, page: ft.Page = None):
        """初始化 Actor 卡片。
        
        :param actor: Actor 对象
        :param all_actors: 所有 Actor 列表（用于详情对话框的切换）
        :param index: 当前 Actor 在列表中的索引
        :param on_delete: 删除回调函数，接收 actor 作为参数
        :param page: Flet 页面对象（用于打开对话框）
        """
        super().__init__()
        self.actor = actor
        self.all_actors = all_actors or [actor]
        self.index = index
        self.on_delete_callback = on_delete
        self.page = page
        
        # 配置卡片样式
        self.elevation = 2
        self.width = CARD_WIDTH
        # 移除固定高度，让卡片根据内容自适应
        
        # 使用 Actor 的颜色作为边框颜色
        try:
            border_color = actor.color if actor.color else "#808080"
            self.surface_tint_color = border_color
        except:
            self.surface_tint_color = "#808080"
        
        # 构建卡片内容
        self.content = self._build_content()
    
    def _build_content(self) -> ft.Container:
        """构建卡片内容。"""
        # Actor 名称
        name_text = ft.Text(
            self.actor.name,
            size=16,
            weight=ft.FontWeight.BOLD,
        )
        
        # Actor 描述
        desc_text = ft.Text(
            self.actor.desc if self.actor.desc else "无描述",
            size=12,
            color=ft.Colors.GREY_600,
        )
        
        # 示例图数量
        example_count = len(self.actor.examples) if self.actor.examples else 0
        example_info = ft.Row(
            controls=[
                ft.Icon(ft.Icons.IMAGE, size=16, color=ft.Colors.BLUE_400),
                ft.Text(f"{example_count} 张示例图", size=12, color=ft.Colors.GREY_600),
            ],
            spacing=5,
        )
        
        # 标签数量
        tag_count = len(self.actor.tags) if self.actor.tags else 0
        tag_info = ft.Row(
            controls=[
                ft.Icon(ft.Icons.LABEL, size=16, color=ft.Colors.GREEN_400),
                ft.Text(f"{tag_count} 个标签", size=12, color=ft.Colors.GREY_600),
            ],
            spacing=5,
        )
        
        # 缩略图或占位符
        if example_count > 0:
            # 显示第一张示例图的占位符
            thumbnail = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.IMAGE, size=48, color=ft.Colors.GREY_400),
                        ft.Text("点击查看", size=10, color=ft.Colors.GREY_500),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                width=CARD_WIDTH - 20,
                height=120,
                bgcolor=ft.Colors.GREY_200,
                border_radius=8,
                alignment=ft.alignment.center,
                on_click=self._open_example_dialog,
            )
        else:
            thumbnail = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.PERSON, size=48, color=ft.Colors.GREY_400),
                        ft.Text("无示例图", size=10, color=ft.Colors.GREY_500),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                width=CARD_WIDTH - 20,
                height=120,
                bgcolor=ft.Colors.GREY_200,
                border_radius=8,
                alignment=ft.alignment.center,
            )
        
        # 信息区域
        info_column = ft.Column(
            controls=[
                name_text,
                desc_text,
                ft.Divider(height=1),
                example_info,
                tag_info,
            ],
            spacing=SPACING_SMALL,
            tight=True,
        )
        
        # 使用 GestureDetector 包裹内容以支持右键点击
        # 点击卡片打开详情对话框
        content_container = ft.GestureDetector(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        thumbnail,
                        info_column,
                    ],
                    spacing=SPACING_SMALL,
                    tight=True,
                ),
                padding=10,
                on_click=self._open_detail_dialog,
            ),
            on_secondary_tap_down=self._on_right_click,  # 右键菜单
        )
        
        return content_container
    
    def _open_detail_dialog(self, e: ft.ControlEvent):
        """打开 Actor 详情对话框。"""
        if self.page:
            dialog = ActorDetailDialog(self.actor, self.all_actors, self.index)
            self.page.open(dialog)
    
    def _open_example_dialog(self, e: ft.ControlEvent):
        """打开 Actor 示例图对话框。"""
        e.control.disabled = True  # 防止重复点击
        
        if self.page:
            dialog = ActorExampleDialog(self.actor, self.page)
            self.page.open(dialog)
        
        e.control.disabled = False
    
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
        dialog = DeleteActorConfirmDialog(
            actor=self.actor,
            on_confirm=lambda: self.on_delete_callback(self.actor) if self.on_delete_callback else None,
        )
        
        e.page.open(dialog)


# ============================================================================
# Dialog 类定义
# ============================================================================

class DeleteActorConfirmDialog(ft.AlertDialog):
    """删除 Actor 确认对话框"""
    
    def __init__(self, actor: Actor, on_confirm: callable):
        """
        初始化删除 Actor 确认对话框
        
        Args:
            actor: 要删除的 Actor 对象
            on_confirm: 确认回调函数，无参数
        """
        self.actor = actor
        self.on_confirm = on_confirm
        
        # 统计信息
        example_count = len(actor.examples) if actor.examples else 0
        tag_count = len(actor.tags) if actor.tags else 0
        
        super().__init__(
            modal=True,
            title=ft.Text("确认删除", color=ft.Colors.RED_700),
            content=ft.Column([
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=48, color=ft.Colors.ORANGE_700),
                ft.Text("即将删除以下 Actor：", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"名称：{actor.name}", size=14),
                ft.Text(f"描述：{actor.desc if actor.desc else '无'}", size=14),
                ft.Text(f"颜色：{actor.color}", size=14),
                ft.Divider(),
                ft.Text("⚠️ 此操作将删除：", size=14, color=ft.Colors.RED_700, weight=ft.FontWeight.BOLD),
                ft.Text(f"• Actor 记录", size=12),
                ft.Text(f"• {example_count} 张示例图片", size=12),
                ft.Text(f"• {tag_count} 个标签", size=12),
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


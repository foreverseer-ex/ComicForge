"""
Actor 管理页面。

展示所有 Actor 卡片（包括角色、地点、组织等）。
"""
import flet as ft
from loguru import logger
from flet_toast import flet_toast
from flet_toast.Types import Position

from api.components.desperate.actor_card import ActorCard
from api.constants.ui import SPACING_SMALL, SPACING_MEDIUM
from api.services.db import ActorService
from api.settings import app_settings
from api.schemas.actor import Actor


class ActorManagePage(ft.Column):
    """Actor 管理页面。"""
    
    def __init__(self):
        """初始化 Actor 管理页面。"""
        super().__init__()
        
        # 当前项目 ID - 在初始化时就检查
        self.project_id: str | None = app_settings.ui.current_project_id
        
        # Actor 区域（占位，后面会动态填充）
        self.actor_section = ft.Column(spacing=SPACING_MEDIUM)
        
        # 右上角：创建 Actor 按钮
        self.create_button = ft.IconButton(
            icon=ft.Icons.ADD,
            tooltip="创建 Actor",
            on_click=self._open_create_dialog
        )
        
        
        # 组合布局
        self.controls = [
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(expand=True),  # 左侧留空
                        self.create_button,
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
                padding=ft.padding.only(top=SPACING_SMALL, bottom=SPACING_MEDIUM),
            ),
            self.actor_section,
        ]
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.alignment = ft.MainAxisAlignment.START
        self.spacing = SPACING_MEDIUM
        
        # 初始化时就设置初始状态，但不调用 update()（因为组件还没挂载）
        # 实际的加载和更新会在 did_mount() 中进行
        if self.project_id:
            # 只准备数据，不更新UI
            self._prepare_actors_data()
        else:
            # 只设置UI状态，不更新
            self._prepare_empty_state()
    
    def did_mount(self):
        """组件挂载后，重新检查项目状态（可能用户切换了项目）并更新UI。"""
        # 重新检查项目ID（可能在主页切换了项目）
        new_project_id = app_settings.ui.current_project_id
        if new_project_id != self.project_id:
            self.project_id = new_project_id
            if self.project_id:
                self._render_actors()
            else:
                self._show_empty_state()
        else:
            # 项目ID没变，但需要更新UI（因为初始化时没有调用update）
            if self.project_id:
                self._render_actors()
            else:
                self._show_empty_state()
    
    def _prepare_actors_data(self):
        """准备Actor数据（不更新UI，用于初始化）"""
        if not self.project_id:
            return
        
        try:
            # 只准备数据，不渲染UI
            logger.debug(f"预准备 Actor 数据 (session: {self.project_id})")
        except Exception as e:
            logger.exception(f"预准备Actor数据失败: {e}")
    
    def _prepare_empty_state(self):
        """准备空状态UI（不更新，用于初始化）"""
        self.actor_section.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=64, color=ft.Colors.GREY_400),
                        ft.Text(
                            "请先创建一个项目",
                            size=18,
                            color=ft.Colors.GREY_600,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "在主页创建项目后，才能管理角色",
                            size=14,
                            color=ft.Colors.GREY_500,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                ),
                alignment=ft.alignment.center,
                padding=40,
            ),
        ]
    
    def _open_create_dialog(self, _: ft.ControlEvent):
        """打开创建 Actor 对话框"""
        if not self.page:
            logger.error("self.page 为 None，无法打开对话框")
            return
        
        # 检查是否有项目
        if not self.project_id:
            self._show_toast("请先选择一个项目", ft.Colors.RED_700)
            return
        
        try:
            # 创建对话框
            dialog = CreateActorDialog(
                project_id=self.project_id,
                on_create=lambda name, desc, color: self.page.run_task(self._do_create, name, desc, color),
                on_error=lambda msg: self._show_toast(msg, ft.Colors.RED_700),
            )
            
            # 打开对话框
            self.page.open(dialog)
            logger.info("创建 Actor 对话框已打开")
        except Exception as e:
            logger.exception(f"打开创建对话框失败: {e}")
    
    async def _do_create(self, name: str, desc: str, color: str):
        """执行创建 Actor 任务。"""
        try:
            from api.schemas.actor import Actor
            import uuid
            
            # 检查是否有项目
            if not self.project_id:
                self._show_toast("❌ 请先选择一个会话", ft.Colors.RED_700)
                return
            
            # 创建 Actor
            actor = Actor(
                actor_id=str(uuid.uuid4()),
                project_id=self.project_id,
                name=name,
                desc=desc,
                color=color,
                tags={},
                examples=[]
            )
            
            created = ActorService.create(actor)
            logger.success(f"创建 Actor 成功: {name}")
            
            # 重新渲染
            self._render_actors()
            
            # 确保页面更新（在异步任务中需要明确调用 page.update，而不是 self.update）
            if self.page:
                # 先更新组件本身
                self.update()
                # 然后更新整个页面，确保UI刷新
                self.page.update()
            
            # 显示成功消息
            self._show_toast(f"✅ 创建成功: {name}", ft.Colors.GREEN_700)
        except Exception as ex:
            logger.exception(f"创建 Actor 失败: {ex}")
            self._show_toast(f"❌ 创建失败: {str(ex)}", ft.Colors.RED_700)
    
    def _show_toast(self, message: str, bgcolor=ft.Colors.GREEN_700, duration: int = 3000):
        """显示 Toast 提示。"""
        if self.page:
            duration_sec = duration / 1000
            
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
    
    def _render_actors(self):
        """渲染 Actor 卡。"""
        # 检查是否有项目
        if not self.project_id:
            self._show_empty_state()
            return
        
        # 获取当前 session 的所有 Actor
        all_actors = ActorService.list_by_session(self.project_id, limit=1000)
        
        logger.debug(f"渲染 Actor 列表: {len(all_actors)} 个 Actor (session: {self.project_id})")
        
        actor_cards = [
            ActorCard(
                actor, 
                all_actors=all_actors, 
                index=all_actors.index(actor),
                on_delete=self._on_actor_delete,
                page=self.page
            )
            for actor in all_actors
        ]
        
        actor_flow = ft.Row(
            controls=actor_cards,
            wrap=True,
            run_spacing=SPACING_SMALL,
            spacing=SPACING_SMALL,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        
        # 更新 Actor 区域
        self.actor_section.controls = [
            ft.Text("Actor", size=20, weight=ft.FontWeight.BOLD),
            actor_flow if actor_cards else ft.Text("暂无 Actor，点击右上角 + 创建", size=14, color=ft.Colors.GREY_500),
        ]
        
        # 只在组件已挂载时更新UI
        if self.page:
            self.update()
    
    def _show_empty_state(self):
        """显示空状态（没有项目时）"""
        self.actor_section.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=64, color=ft.Colors.GREY_400),
                        ft.Text(
                            "请先创建一个项目",
                            size=18,
                            color=ft.Colors.GREY_600,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "在主页创建项目后，才能管理角色",
                            size=14,
                            color=ft.Colors.GREY_500,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                ),
                alignment=ft.alignment.center,
                padding=40,
            ),
        ]
        # 只在组件已挂载时更新UI
        if self.page:
            self.update()
    
    def _on_actor_delete(self, actor: 'Actor'):
        """处理 Actor 删除回调。
        
        :param actor: 要删除的 Actor 对象
        """
        logger.info(f"开始删除 Actor: {actor.name}")
        
        try:
            # 调用服务删除 Actor
            success = ActorService.delete(actor.actor_id)
            
            if success:
                # 重新渲染视图
                self._render_actors()
                
                # 确保页面更新
                if self.page:
                    self.update()
                    self.page.update()
                
                # 显示成功消息
                self._show_toast(f"✅ 已删除: {actor.name}", ft.Colors.GREEN_700)
                logger.success(f"删除成功: {actor.name}")
            else:
                self._show_toast(f"❌ 删除失败: {actor.name}", ft.Colors.RED_700)
                logger.error(f"删除失败: {actor.name}")
        
        except Exception as e:
            logger.exception(f"删除 Actor 时出错: {e}")
            self._show_toast(f"❌ 删除出错: {str(e)}", ft.Colors.RED_700)


# ============================================================================
# Dialog 类定义
# ============================================================================

class CreateActorDialog(ft.AlertDialog):
    """创建 Actor 对话框"""
    
    def __init__(self, project_id: str, on_create: callable, on_error: callable):
        """
        初始化创建 Actor 对话框
        
        Args:
            project_id: 项目ID
            on_create: 创建回调函数，接收参数 (name: str, desc: str, color: str)
            on_error: 错误回调函数，接收参数 (message: str)
        """
        self.project_id = project_id
        self.on_create = on_create
        self.on_error = on_error
        
        # 创建输入字段
        self.name_field = ft.TextField(
            label="名称",
            hint_text="如：主角、帝国、纽约",
            autofocus=True,
        )
        
        self.desc_field = ft.TextField(
            label="描述",
            hint_text="简要描述",
            multiline=True,
            min_lines=2,
            max_lines=4,
        )
        
        self.color_field = ft.TextField(
            label="颜色",
            hint_text="如：#FF69B4（粉色）、#4169E1（蓝色）",
            value="#808080",
        )
        
        super().__init__(
            modal=True,
            title=ft.Text("创建 Actor"),
            content=ft.Column([
                ft.Text("提示：", size=12, weight=ft.FontWeight.BOLD),
                ft.Text("• Actor 可以是角色、地点、组织等小说要素", size=11, color=ft.Colors.GREY_600),
                ft.Text("• 颜色建议：女性→粉色 #FF69B4，男性→蓝色 #4169E1，地点→绿色 #228B22", size=11, color=ft.Colors.GREY_600),
                ft.Divider(),
                self.name_field,
                self.desc_field,
                self.color_field,
            ], tight=True, spacing=10, width=400),
            actions=[
                ft.TextButton("取消", on_click=self._on_cancel),
                ft.ElevatedButton("创建", on_click=self._on_confirm),
            ],
        )
    
    def _on_confirm(self, e):
        """确认创建"""
        # 验证输入
        name = self.name_field.value.strip()
        if not name:
            if self.on_error:
                self.on_error("❌ 请输入名称")
            return
        
        desc = self.desc_field.value.strip()
        color = self.color_field.value.strip()
        if not color:
            color = "#808080"
        
        # 验证颜色格式
        if not color.startswith("#") or len(color) != 7:
            if self.on_error:
                self.on_error("❌ 颜色格式错误，应为 #RRGGBB")
            return
        
        # 关闭对话框
        page = e.page if e and e.page else None
        self.open = False
        if page:
            page.update()
        
        # 调用创建回调
        if self.on_create:
            self.on_create(name, desc, color)
    
    def _on_cancel(self, e):
        """取消创建"""
        self.open = False
        self.update()


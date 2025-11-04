"""
设置页面：应用配置管理。

Flet 1.0 声明式 UI 风格。
使用 load/save 模式：State 类从 BaseSetting 加载，修改时自动保存。
"""
import flet as ft

from .civitai_settings import CivitaiSettingsSection
from .danger_section import DangerSection
from .draw_settings import DrawSettingsSection
from .llm_settings import LlmSettingsSection
from .sd_forge_settings import SdForgeSettingsSection


@ft.component
def SettingsPage():
    """设置页面组件。"""
    return ft.Column(
        controls=[
            ft.Text("应用设置", size=24, weight=ft.FontWeight.BOLD),
            ft.Text(
                "提示：修改后回车或点击其他地方自动保存",
                size=12,
                color=ft.Colors.GREY_600,
                italic=True,
            ),
            ft.Divider(),
            
            # 绘图设置
            DrawSettingsSection(),
            ft.Divider(),
            
            # LLM 设置
            LlmSettingsSection(),
            ft.Divider(),
            
            # Civitai 设置
            CivitaiSettingsSection(),
            ft.Divider(),
            
            # SD Forge 设置
            SdForgeSettingsSection(),
            ft.Divider(),
            
            # 危险操作
            DangerSection(),
        ],
        spacing=20,
        scroll=ft.ScrollMode.AUTO,
    )


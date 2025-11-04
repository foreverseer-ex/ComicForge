"""
绘图设置视图。
"""
from dataclasses import dataclass

import flet as ft
from api.settings import app_settings


@dataclass
@ft.observable
class DrawSettingsState:
    """绘图设置状态。"""
    backend: str = "sd_forge"
    
    def load(self):
        """从 app_settings.draw 加载数据。"""
        self.backend = app_settings.draw.backend
    
    def save(self):
        """保存数据到 app_settings.draw。"""
        if self.backend not in ("sd_forge", "civitai"):
            return False
        
        app_settings.draw.backend = self.backend
        app_settings.save(reason="修改绘图设置")
        return True


@ft.component
def DrawSettingsSection():
    """绘图设置区域组件。"""
    draw_state, _ = ft.use_state(DrawSettingsState())
    
    # 使用 use_effect 在组件首次挂载时加载配置
    def load_settings():
        if not draw_state.backend:
            draw_state.load()
    
    ft.use_effect(load_settings, [])
    
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("绘图服务设置", size=18, weight=ft.FontWeight.BOLD),
                ft.Dropdown(
                    label="绘图后端",
                    value=draw_state.backend,
                    options=[
                        ft.dropdown.Option(key="sd_forge", text="SD-Forge (本地)"),
                        ft.dropdown.Option(key="civitai", text="Civitai (云端)"),
                    ],
                    width=300,
                    on_select=lambda e: (
                        setattr(draw_state, "backend", e.control.value),
                        draw_state.save()
                    )[-1],
                ),
            ],
            spacing=10,
        ),
        padding=ft.padding.only(left=20),
    )


"""
UI 设置视图。
"""
from dataclasses import dataclass
import socket

import flet as ft
from api.settings import app_settings


@dataclass
@ft.observable
class UiSettingsState:
    """UI 设置状态。"""
    default_username: str = ""
    
    def load(self):
        """从 app_settings.ui 加载数据。"""
        self.default_username = app_settings.ui.default_username or socket.gethostname()
    
    def save(self):
        """保存数据到 app_settings.ui。"""
        value = self.default_username.strip()
        if not value:
            value = socket.gethostname()
            self.default_username = value
        
        app_settings.ui.default_username = value
        app_settings.save(reason="修改 UI 设置")


@ft.component
def UiSettingsSection():
    """UI 设置区域组件。"""
    ui_state, _ = ft.use_state(UiSettingsState())
    
    # 使用 use_effect 在组件首次挂载时加载配置
    def load_settings():
        if not ui_state.default_username:
            ui_state.load()
    
    ft.use_effect(load_settings, [])
    
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("界面设置", size=18, weight=ft.FontWeight.BOLD),
                ft.TextField(
                    label="默认用户名",
                    value=ui_state.default_username,
                    hint_text="留空将自动使用计算机名",
                    width=300,
                    on_blur=lambda e: (
                        setattr(ui_state, "default_username", e.control.value),
                        ui_state.save()
                    )[-1],
                    on_submit=lambda e: (
                        setattr(ui_state, "default_username", e.control.value),
                        ui_state.save()
                    )[-1],
                ),
            ],
            spacing=10,
        ),
        padding=ft.padding.only(left=20),
    )


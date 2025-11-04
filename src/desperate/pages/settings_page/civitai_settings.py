"""
Civitai 设置视图。
"""
from dataclasses import dataclass

import flet as ft
from api.settings import app_settings


@dataclass
@ft.observable
class CivitaiSettingsState:
    """Civitai 设置状态。"""
    api_token: str = ""
    timeout: str = "30.0"
    
    def load(self):
        """从 app_settings.civitai 加载数据。"""
        self.api_token = app_settings.civitai.api_token or ""
        self.timeout = str(app_settings.civitai.timeout)
    
    def save(self):
        """保存数据到 app_settings.civitai。"""
        try:
            timeout_val = float(self.timeout)
            if timeout_val <= 0:
                raise ValueError("超时时间必须大于 0")
            
            app_settings.civitai.api_token = self.api_token.strip() or None
            app_settings.civitai.timeout = timeout_val
            app_settings.save(reason="修改 Civitai 设置")
            return True
        except ValueError:
            return False


@ft.component
def CivitaiSettingsSection():
    """Civitai 设置区域组件。"""
    civitai_state, _ = ft.use_state(CivitaiSettingsState())
    
    # 使用 use_effect 在组件首次挂载时加载配置
    def load_settings():
        if not civitai_state.timeout:
            civitai_state.load()
    
    ft.use_effect(load_settings, [])
    
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Civitai 设置", size=18, weight=ft.FontWeight.BOLD),
                ft.TextField(
                    label="Civitai API Token",
                    value=civitai_state.api_token,
                    password=True,
                    can_reveal_password=True,
                    expand=True,
                    on_blur=lambda e: (
                        setattr(civitai_state, "api_token", e.control.value),
                        civitai_state.save()
                    )[-1],
                    on_submit=lambda e: (
                        setattr(civitai_state, "api_token", e.control.value),
                        civitai_state.save()
                    )[-1],
                ),
                ft.TextField(
                    label="Civitai 请求超时",
                    value=civitai_state.timeout,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    width=200,
                    on_blur=lambda e: (
                        setattr(civitai_state, "timeout", e.control.value),
                        civitai_state.save()
                    )[-1],
                    on_submit=lambda e: (
                        setattr(civitai_state, "timeout", e.control.value),
                        civitai_state.save()
                    )[-1],
                ),
                ft.ElevatedButton(
                    content=ft.Text("从 SD Forge 导入"),
                    icon=ft.Icons.SYNC,
                    on_click=lambda e: None,  # TODO: 实现从 SD Forge 导入模型功能
                ),
            ],
            spacing=10,
        ),
        padding=ft.padding.only(left=20),
    )


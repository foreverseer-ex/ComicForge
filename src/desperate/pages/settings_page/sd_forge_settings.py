"""
SD Forge 设置视图。
"""
from dataclasses import dataclass

import flet as ft
from api.settings import app_settings


@dataclass
@ft.observable
class SdForgeSettingsState:
    """SD Forge 设置状态。"""
    base_url: str = ""
    home: str = ""
    timeout: str = "30.0"
    generate_timeout: str = "120.0"

    def load(self):
        """从 app_settings.sd_forge 加载数据。"""
        self.base_url = app_settings.sd_forge.base_url
        self.home = app_settings.sd_forge.home
        self.timeout = str(app_settings.sd_forge.timeout)
        self.generate_timeout = str(app_settings.sd_forge.generate_timeout)

    def save(self):
        """保存数据到 app_settings.sd_forge。"""
        try:
            timeout_val = float(self.timeout)
            generate_timeout_val = float(self.generate_timeout)
            if timeout_val <= 0 or generate_timeout_val <= 0:
                raise ValueError("超时时间必须大于 0")

            base_url_val = self.base_url.strip()
            home_val = self.home.strip()
            if not base_url_val or not home_val:
                raise ValueError("Base URL 和安装目录不能为空")

            app_settings.sd_forge.base_url = base_url_val
            app_settings.sd_forge.home = home_val
            app_settings.sd_forge.timeout = timeout_val
            app_settings.sd_forge.generate_timeout = generate_timeout_val
            app_settings.save(reason="修改 SD Forge 设置")
            return True
        except ValueError:
            return False


@ft.component
def SdForgeSettingsSection():
    """SD Forge 设置区域组件。"""
    sd_forge_state, _ = ft.use_state(SdForgeSettingsState())
    
    # 使用 use_effect 在组件首次挂载时加载配置
    def load_settings():
        if not sd_forge_state.base_url:
            sd_forge_state.load()
    
    ft.use_effect(load_settings, [])
    
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("SD Forge 设置", size=18, weight=ft.FontWeight.BOLD),
                ft.TextField(
                    label="SD Forge Base URL",
                    value=sd_forge_state.base_url,
                    expand=True,
                    on_blur=lambda e: (
                        setattr(sd_forge_state, "base_url", e.control.value),
                        sd_forge_state.save()
                    )[-1],
                    on_submit=lambda e: (
                        setattr(sd_forge_state, "base_url", e.control.value),
                        sd_forge_state.save()
                    )[-1],
                ),
                ft.TextField(
                    label="SD Forge 安装目录",
                    value=sd_forge_state.home,
                    expand=True,
                    on_blur=lambda e: (
                        setattr(sd_forge_state, "home", e.control.value),
                        sd_forge_state.save()
                    )[-1],
                    on_submit=lambda e: (
                        setattr(sd_forge_state, "home", e.control.value),
                        sd_forge_state.save()
                    )[-1],
                ),
                ft.Row(
                    controls=[
                        ft.TextField(
                            label="SD Forge 请求超时",
                            value=sd_forge_state.timeout,
                            keyboard_type=ft.KeyboardType.NUMBER,
                            width=200,
                            on_blur=lambda e: (
                                setattr(sd_forge_state, "timeout", e.control.value),
                                sd_forge_state.save()
                            )[-1],
                            on_submit=lambda e: (
                                setattr(sd_forge_state, "timeout", e.control.value),
                                sd_forge_state.save()
                            )[-1],
                        ),
                        ft.TextField(
                            label="SD Forge 生成超时",
                            value=sd_forge_state.generate_timeout,
                            keyboard_type=ft.KeyboardType.NUMBER,
                            width=200,
                            on_blur=lambda e: (
                                setattr(sd_forge_state, "generate_timeout", e.control.value),
                                sd_forge_state.save()
                            )[-1],
                            on_submit=lambda e: (
                                setattr(sd_forge_state, "generate_timeout", e.control.value),
                                sd_forge_state.save()
                            )[-1],
                        ),
                    ],
                    spacing=20,
                ),
            ],
            spacing=10,
        ),
        padding=ft.padding.only(left=20),
    )

"""
LLM 设置视图。
"""
from dataclasses import dataclass

import flet as ft
from api.constants.llm import (
    LlmProvider,
    get_base_url_for_provider,
    get_models_for_provider,
)
from api.settings import app_settings


@dataclass
@ft.observable
class LlmSettingsState:
    """LLM 设置状态。"""
    provider: str = LlmProvider.XAI
    model: str = ""
    model_custom: str = ""  # 自定义模型输入
    api_key: str = ""
    base_url: str = ""
    temperature: str = "0.7"
    timeout: str = "60.0"
    developer_mode: bool = True
    system_prompt: str = ""
    summary_epoch: str = "2"
    
    def load(self):
        """从 app_settings.llm 加载数据。"""
        self.provider = app_settings.llm.provider
        self.model = app_settings.llm.model
        self.api_key = app_settings.llm.api_key
        self.base_url = app_settings.llm.base_url
        self.temperature = str(app_settings.llm.temperature)
        self.timeout = str(app_settings.llm.timeout)
        self.developer_mode = app_settings.llm.developer_mode
        self.system_prompt = app_settings.llm.system_prompt
        self.summary_epoch = str(app_settings.llm.summary_epoch)
        
        # 检查模型是否在推荐列表中
        models = get_models_for_provider(self.provider)
        if models and self.model in models:
            self.model_custom = ""
        else:
            self.model_custom = self.model
    
    def save(self):
        """保存数据到 app_settings.llm。"""
        try:
            # 验证数值字段
            temperature_val = float(self.temperature)
            if not (0.0 <= temperature_val <= 2.0):
                raise ValueError("Temperature 必须在 0.0 到 2.0 之间")
            
            timeout_val = float(self.timeout)
            if timeout_val <= 0:
                raise ValueError("超时时间必须大于 0")
            
            summary_epoch_val = int(self.summary_epoch)
            if not (2 <= summary_epoch_val <= 1000):
                raise ValueError("对话总结周期必须在 2-1000 之间")
            
            # 验证字符串字段
            if not self.api_key.strip():
                raise ValueError("API Key 不能为空")
            if not self.base_url.strip():
                raise ValueError("Base URL 不能为空")
            if not self.system_prompt.strip():
                raise ValueError("系统提示词不能为空")
            
            # 确定模型名称
            models = get_models_for_provider(self.provider)
            if models and self.model in models:
                model_val = self.model
            else:
                model_val = self.model_custom.strip()
                if not model_val:
                    raise ValueError("模型名称不能为空")
            
            # 保存
            app_settings.llm.provider = self.provider
            app_settings.llm.model = model_val
            app_settings.llm.api_key = self.api_key.strip()
            app_settings.llm.base_url = self.base_url.strip()
            app_settings.llm.temperature = temperature_val
            app_settings.llm.timeout = timeout_val
            app_settings.llm.developer_mode = self.developer_mode
            app_settings.llm.system_prompt = self.system_prompt.strip()
            app_settings.llm.summary_epoch = summary_epoch_val
            app_settings.save(reason="修改 LLM 设置")
            return True
        except ValueError:
            return False


@ft.component
def LlmSettingsSection():
    """LLM 设置区域组件。"""
    llm_state, _ = ft.use_state(LlmSettingsState())
    
    # 使用 use_effect 在组件首次挂载时加载配置
    def load_settings():
        if not llm_state.provider:
            llm_state.load()
    
    ft.use_effect(load_settings, [])
    
    # 根据 provider 获取模型列表
    models = get_models_for_provider(llm_state.provider)
    show_model_dropdown = bool(models and llm_state.model in models)
    
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("AI 大模型设置", size=18, weight=ft.FontWeight.BOLD),
                ft.Row(
                    controls=[
                        ft.Dropdown(
                            label="提供商",
                            value=llm_state.provider,
                            options=[
                                ft.dropdown.Option(key=LlmProvider.XAI, text="xAI (Grok)"),
                                ft.dropdown.Option(key=LlmProvider.OPENAI, text="OpenAI (GPT)"),
                                ft.dropdown.Option(key=LlmProvider.OLLAMA, text="Ollama (本地)"),
                                ft.dropdown.Option(key=LlmProvider.ANTHROPIC, text="Anthropic (Claude)"),
                                ft.dropdown.Option(key=LlmProvider.GOOGLE, text="Google (Gemini)"),
                                ft.dropdown.Option(key=LlmProvider.CUSTOM, text="自定义"),
                            ],
                            width=250,
                            on_select=lambda e: (
                                setattr(llm_state, "provider", e.control.value),
                                setattr(llm_state, "base_url", get_base_url_for_provider(e.control.value)),
                                (lambda new_models: (
                                    setattr(llm_state, "model", new_models[0] if new_models else ""),
                                    setattr(llm_state, "model_custom", "" if new_models else ""),
                                    llm_state.save()
                                ))(get_models_for_provider(e.control.value))
                            )[-1],
                        ),
                        ft.Dropdown(
                            label="模型",
                            value=llm_state.model if show_model_dropdown else None,
                            options=[ft.dropdown.Option(key=m, text=m) for m in models] if models else [],
                            width=350,
                            visible=show_model_dropdown,
                            on_select=lambda e: (
                                setattr(llm_state, "model", e.control.value),
                                llm_state.save()
                            )[-1],
                        ),
                    ],
                    spacing=20,
                ),
                ft.TextField(
                    label="自定义模型名称",
                    value=llm_state.model_custom,
                    hint_text="手动输入模型名称",
                    expand=True,
                    visible=not show_model_dropdown,
                    on_blur=lambda e: (
                        setattr(llm_state, "model_custom", e.control.value),
                        llm_state.save()
                    )[-1],
                    on_submit=lambda e: (
                        setattr(llm_state, "model_custom", e.control.value),
                        llm_state.save()
                    )[-1],
                ),
                ft.TextField(
                    label="API Key",
                    value=llm_state.api_key,
                    password=True,
                    can_reveal_password=True,
                    expand=True,
                    on_blur=lambda e: (
                        setattr(llm_state, "api_key", e.control.value),
                        llm_state.save()
                    )[-1],
                    on_submit=lambda e: (
                        setattr(llm_state, "api_key", e.control.value),
                        llm_state.save()
                    )[-1],
                ),
                ft.TextField(
                    label="API Base URL",
                    value=llm_state.base_url,
                    expand=True,
                    on_blur=lambda e: (
                        setattr(llm_state, "base_url", e.control.value),
                        llm_state.save()
                    )[-1],
                    on_submit=lambda e: (
                        setattr(llm_state, "base_url", e.control.value),
                        llm_state.save()
                    )[-1],
                ),
                ft.Row(
                    controls=[
                        ft.TextField(
                            label="Temperature",
                            value=llm_state.temperature,
                            width=200,
                            on_blur=lambda e: (
                                setattr(llm_state, "temperature", e.control.value),
                                llm_state.save()
                            )[-1],
                            on_submit=lambda e: (
                                setattr(llm_state, "temperature", e.control.value),
                                llm_state.save()
                            )[-1],
                        ),
                        ft.TextField(
                            label="请求超时",
                            value=llm_state.timeout,
                            keyboard_type=ft.KeyboardType.NUMBER,
                            width=200,
                            on_blur=lambda e: (
                                setattr(llm_state, "timeout", e.control.value),
                                llm_state.save()
                            )[-1],
                            on_submit=lambda e: (
                                setattr(llm_state, "timeout", e.control.value),
                                llm_state.save()
                            )[-1],
                        ),
                    ],
                    spacing=20,
                ),
                ft.Switch(
                    label="开发者模式",
                    value=llm_state.developer_mode,
                    on_change=lambda e: (
                        setattr(llm_state, 'developer_mode', e.control.value),
                        llm_state.save()
                    )[-1],
                ),
                ft.Container(
                    content=ft.TextField(
                        label="系统提示词",
                        value=llm_state.system_prompt,
                        multiline=True,
                        min_lines=5,
                        max_lines=10,
                        width=800,  # 固定宽度，占屏幕约3/4
                        on_blur=lambda e: (
                            setattr(llm_state, "system_prompt", e.control.value),
                            llm_state.save()
                        )[-1],
                    ),
                    alignment=ft.Alignment.TOP_LEFT,
                ),
                ft.TextField(
                    label="对话总结周期",
                    value=llm_state.summary_epoch,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    width=200,
                    on_blur=lambda e: (
                        setattr(llm_state, "summary_epoch", e.control.value),
                        llm_state.save()
                    )[-1],
                    on_submit=lambda e: (
                        setattr(llm_state, "summary_epoch", e.control.value),
                        llm_state.save()
                    )[-1],
                ),
                ft.ElevatedButton(
                    content=ft.Text("重新初始化 LLM"),
                    icon=ft.Icons.REFRESH,
                    on_click=lambda e: None,  # TODO: 实现重新初始化 LLM 功能
                ),
            ],
            spacing=10,
        ),
        padding=ft.padding.only(left=20),
    )


"""
创作页面：AI对话。

Flet 1.0 声明式 UI 风格。
"""
import flet as ft


@ft.component
def ChatPage():
    """创作页面组件。

    用于与AI进行对话。
    """
    # 使用基本类型的状态
    input_text, set_input_text = ft.use_state("")

    return ft.Container(
        key="chat_page_component",
        content=ft.Column(
            controls=[
                ft.Text("创作页面（测试状态持久化）", size=20, weight=ft.FontWeight.BOLD),
                ft.Text("请在输入框中输入一些文字，然后切换页面，再回来看看是否保留"),
                ft.TextField(
                    label="输入框（测试状态）",
                    value=input_text,
                    on_change=lambda e: set_input_text(e.control.value),
                    hint_text="输入一些文字，切换页面后再回来...",
                ),
                ft.Text(
                    value=f"当前输入内容: {input_text}",
                    size=14,
                    color=ft.Colors.GREY_600,
                ),
                ft.Text("TODO: 实现聊天页面功能", size=16),
            ],
            spacing=10,
        ),
        padding=20,
        alignment=ft.Alignment.TOP_LEFT,
    )

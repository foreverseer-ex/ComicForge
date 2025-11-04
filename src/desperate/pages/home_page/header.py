"""
顶部项目选择器。

显示项目选择下拉框和标题。
"""
import flet as ft


@ft.component
def ProjectSelector():
    """项目选择器组件。
    
    显示项目选择下拉框和标题。
    """
    # TODO: 临时占位，等待修复状态传递问题
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.HOME_OUTLINED, size=24),
                ft.Text("项目管理", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(width=20),  # 间距
                ft.Dropdown(
                    label="选择项目",
                    hint_text="请选择一个项目",
                    width=400,
                    options=[],
                    disabled=True,
                ),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=20, vertical=15),
    )


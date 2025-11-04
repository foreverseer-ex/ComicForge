"""
空状态视图。

当没有项目时显示的提示视图。
"""
import flet as ft


@ft.component
def EmptyState():
    """空状态组件。
    
    当没有项目时显示的提示视图。
    """
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(
                    ft.Icons.FOLDER_OPEN_OUTLINED,
                    size=100,
                    color=ft.Colors.OUTLINE,
                ),
                ft.Text(
                    "你还没有创建项目",
                    size=20,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=10),
                ft.Text(
                    "点击下方的「创建项目」按钮开始你的项目",
                    size=14,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        ),
        alignment=ft.Alignment.CENTER,
        expand=True,
    )


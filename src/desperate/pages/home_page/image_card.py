"""
图片卡片。

显示最近生成的图片（暂未实现）。
"""
import flet as ft


@ft.component
def ImageCard():
    """图片卡片组件。
    
    显示最近生成的图片（暂未实现）。
    """
    # TODO: 临时占位，等待修复状态传递问题
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("最近生成的图片", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    ft.Text(
                        "功能开发中...",
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
            ),
            padding=ft.padding.all(20),
            expand=True,
        ),
        elevation=2,
        expand=True,
        surface_tint_color=ft.Colors.GREEN,
    )


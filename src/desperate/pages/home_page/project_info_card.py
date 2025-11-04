"""
项目信息卡片。

显示项目的详细信息。
"""
import flet as ft


@ft.component
def ProjectInfoCard():
    """项目信息卡片组件。
    
    显示项目的详细信息。
    """
    # TODO: 临时占位，等待修复状态传递问题
    return ft.Container(
        content=ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.INFO_OUTLINED, size=24),
                                ft.Text("项目信息", size=18, weight=ft.FontWeight.BOLD),
                            ],
                            spacing=10,
                        ),
                        ft.Container(height=15),
                        ft.Text("请选择一个项目", color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                ),
                padding=ft.padding.all(20),
            ),
            elevation=2,
            surface_tint_color=ft.Colors.PRIMARY,
        ),
        expand=1,
    )


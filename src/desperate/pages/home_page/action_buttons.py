"""
操作按钮。

显示创建和删除项目的按钮。
"""
import flet as ft


@ft.component
def ActionButtons():
    """操作按钮组件。
    
    显示创建和删除项目的按钮。
    """
    # TODO: 临时占位，等待修复状态传递问题
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.ElevatedButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE),
                            ft.Text("创建项目"),
                        ],
                        spacing=10,
                    ),
                    height=50,
                    style=ft.ButtonStyle(
                        padding=ft.padding.symmetric(horizontal=30, vertical=15),
                        text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD),
                        bgcolor={
                            ft.ControlState.DEFAULT: ft.Colors.PRIMARY,
                            ft.ControlState.HOVERED: ft.Colors.PRIMARY_CONTAINER,
                        },
                        color={
                            ft.ControlState.DEFAULT: ft.Colors.ON_PRIMARY,
                        },
                    ),
                ),
                ft.ElevatedButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.DELETE_OUTLINE),
                            ft.Text("删除项目"),
                        ],
                        spacing=10,
                    ),
                    disabled=True,
                    height=50,
                    style=ft.ButtonStyle(
                        padding=ft.padding.symmetric(horizontal=30, vertical=15),
                        text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD),
                        bgcolor={
                            ft.ControlState.DEFAULT: ft.Colors.ERROR,
                            ft.ControlState.HOVERED: ft.Colors.ERROR_CONTAINER,
                        },
                        color={
                            ft.ControlState.DEFAULT: ft.Colors.ON_ERROR,
                        },
                    ),
                ),
            ],
            spacing=15,
        ),
        padding=ft.padding.symmetric(horizontal=20, vertical=15),
    )


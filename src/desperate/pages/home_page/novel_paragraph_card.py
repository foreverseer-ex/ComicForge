"""
小说段落卡片。

显示当前段落内容和导航按钮。
"""
import flet as ft


@ft.component
def NovelParagraphCard():
    """小说段落卡片组件。
    
    显示当前段落内容和导航按钮。
    """
    # TODO: 临时占位，等待修复状态传递问题
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.BOOK_OUTLINED, size=24),
                            ft.Text("当前小说段落", size=16, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                        ],
                        spacing=10,
                    ),
                    ft.Divider(height=1),
                    ft.Container(
                        content=ft.Text(
                            "请选择一个项目",
                            size=14,
                            selectable=True,
                        ),
                        padding=ft.padding.symmetric(vertical=15),
                        expand=True,
                    ),
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                tooltip="上一段 (←)",
                                disabled=True,
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.Icons.ARROW_FORWARD,
                                tooltip="下一段 (→)",
                                disabled=True,
                            ),
                        ],
                        spacing=10,
                    ),
                ],
                expand=True,
                spacing=10,
            ),
            padding=ft.padding.all(20),
            expand=True,
        ),
        elevation=2,
        expand=True,
        surface_tint_color=ft.Colors.BLUE,
    )


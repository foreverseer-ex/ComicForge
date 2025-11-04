"""
危险操作视图。
"""
import flet as ft


@ft.component
def DangerSection():
    """危险操作区域组件。"""
    def on_reset_click(e):
        """重置应用（功能待实现）。"""
        # TODO: 实现重置确认对话框和逻辑
        pass
    
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "危险操作",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED_700,
                ),
                ft.Text(
                    "⚠️ 以下操作不可逆，请谨慎操作",
                    size=14,
                    color=ft.Colors.RED_400,
                    italic=True,
                ),
                ft.ElevatedButton(
                    content=ft.Text("重置应用"),
                    icon=ft.Icons.RESTART_ALT,
                    on_click=on_reset_click,
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.RED_700,
                    width=200,
                ),
                ft.Text(
                    "将删除所有数据和配置，重启应用",
                    size=12,
                    color=ft.Colors.GREY_600,
                    italic=True,
                ),
            ],
            spacing=10,
        ),
        padding=ft.padding.only(left=20),
    )


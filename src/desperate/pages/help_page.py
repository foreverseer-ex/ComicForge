"""
帮助页面。

Flet 1.0 声明式 UI 风格。
"""
from pathlib import Path

import flet as ft
from api.utils.url_util import launch_url_or_file


def _load_readme(filename: str) -> str:
    """加载 README 文件内容。"""
    try:
        # README 文件在项目根目录
        readme_path = Path(__file__).parent.parent.parent / filename
        if readme_path.exists():
            return readme_path.read_text(encoding="utf-8")
        else:
            return f"# {filename} 未找到\n\nREADME 文件不存在。"
    except Exception as e:
        # 使用标准库的 logging 记录错误
        import logging
        logging.exception(f"加载文档失败: {filename}")
        return f"# 加载失败\n\n无法加载 {filename}: {str(e)}"


# 文件顶部加载 README 内容（只加载一次）
README_ZH = _load_readme("README.md")
README_EN = _load_readme("README.en.md")


@ft.component
def HelpPage():
    """帮助页面组件。
    
    显示应用的使用说明和文档。
    """
    # 使用基本类型的状态
    current_lang, set_current_lang = ft.use_state(1)  # zh 或 en
    
    # 切换语言函数
    def toggle_language():
        set_current_lang("en" if current_lang == "zh" else "zh")
    
    # 处理链接点击
    def handle_link_click(link: str):
        if not link:
            return
        
        link = link.strip()
        
        # 1. 检查是否是 README 链接（切换语言）
        if link in ("README.en.md", "README.md"):
            if link == "README.en.md" and current_lang != "en":
                toggle_language()
            elif link == "README.md" and current_lang != "zh":
                toggle_language()
            return
        
        # 2. 使用通用工具函数打开链接或文件
        project_root = Path(__file__).parent.parent.parent
        launch_url_or_file(link, project_root)
    
    # 计算当前内容（使用文件顶部的常量）
    current_content = README_EN if current_lang == "en" else README_ZH
    title_text = "Help" if current_lang == "en" else "帮助文档"
    
    return ft.Container(
        key="help_page_component",
        content=ft.Column(
            controls=[
                # 顶部标题
                ft.Container(
                    content=ft.Text(
                        title_text,
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),
                    padding=ft.padding.only(bottom=20),
                ),
                # Markdown 内容
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Markdown(
                                value=current_content,
                                selectable=True,
                                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                                on_tap_link=lambda e: handle_link_click(e.data),
                            ),
                        ],
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    expand=True,
                    border=ft.border.all(1, ft.Colors.OUTLINE),
                    border_radius=ft.border_radius.all(8),
                    padding=ft.padding.all(20),
                ),
            ],
            expand=True,
            spacing=0,
        ),
        padding=ft.padding.all(20),
        expand=True,
    )

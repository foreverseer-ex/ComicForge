"""
主页：项目管理。

Flet 1.0 声明式 UI 风格。
"""
# from .action_buttons import ActionButtons
# from .empty_state import EmptyState
# from .header import ProjectSelector
# from .image_card import ImageCard
# from .novel_paragraph_card import NovelParagraphCard
# from .project_info_card import ProjectInfoCard
# from .state import HomePageState

import flet as ft


@ft.component
def HomePage():
    """主页组件。
    
    用于管理会话（项目）列表和显示项目信息。
    """
    # TODO: 实现主页功能
    # state, _ = ft.use_state(HomePageState())
    # 
    # # 首次加载时从数据库和配置加载数据
    # if not state.projects:
    #     state.load()
    # 
    # # 判断是否显示空状态
    # has_projects = len(state.projects) > 0
    # has_current_project = state.current_project is not None
    # 
    # return ft.Container(
    #     key="home_page_component",
    #     content=ft.Column(
    #         controls=[
    #             # 顶部 Header
    #             ProjectSelector(),
    #             ft.Divider(height=1, color=ft.Colors.OUTLINE),
    #             # 中间 Content
    #             ft.Container(
    #                 content=(
    #                     EmptyState()
    #                     if not has_projects
    #                     else (
    #                         ft.Row(
    #                             controls=[
    #                                 # 左侧：项目信息卡片
    #                                 ProjectInfoCard(),
    #                                 ft.Container(width=20),  # 间距
    #                                 # 右侧：上下布局
    #                                 ft.Container(
    #                                     content=ft.Column(
    #                                         controls=[
    #                                             # 上方：小说段落卡片
    #                                             NovelParagraphCard(),
    #                                             ft.Container(height=20),  # 间距
    #                                             # 下方：图片卡片
    #                                             ImageCard(),
    #                                         ],
    #                                         spacing=0,
    #                                     ),
    #                                     expand=1,
    #                                 ),
    #                             ],
    #                             expand=True,
    #                             spacing=0,
    #                         )
    #                         if has_current_project
    #                         else ft.Container(
    #                             content=ft.Text("请选择一个项目"),
    #                             alignment=ft.Alignment.CENTER,
    #                             expand=True,
    #                         )
    #                     )
    #                 ),
    #                 expand=True,
    #                 padding=ft.padding.all(20),
    #             ),
    #             ft.Divider(height=1, color=ft.Colors.OUTLINE),
    #             # 底部 Footer
    #             ActionButtons(),
    #         ],
    #         expand=True,
    #         spacing=0,
    #     ),
    #     expand=True,
    # )
    
    return ft.Container(
        key="home_page_component",
        content=ft.Text("主页（待实现）"),
        alignment=ft.Alignment.CENTER,
    )


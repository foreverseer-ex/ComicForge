"""应用页面包。

包含组装应用 UI 的顶层 Flet 视图（Flet 1.0 声明式 UI）。
"""
# Flet 1.0 声明式 UI 页面组件
from api.pages.home_page import HomePage
from api.pages.chat_page import ChatPage
from api.pages.memory_manage_page import MemoryManagePage
from api.pages.actor_manage_page import ActorManagePage
from api.pages.content_manage_page import ContentManagePage
from api.pages.model_manage_page import ModelManagePage
from api.pages.settings_page import SettingsPage
from api.pages.help_page import HelpPage

__all__ = [
    'HomePage',
    'ChatPage',
    'MemoryManagePage',
    'ActorManagePage',
    'ContentManagePage',
    'ModelManagePage',
    'SettingsPage',
    'HelpPage',
]

# 注意：旧的 imperative UI 页面已移动到 pages.desperate 目录

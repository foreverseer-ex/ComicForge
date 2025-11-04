"""
对话框基类和辅助函数，提供 ESC 键关闭功能。
"""
import flet as ft
from typing import Optional, Callable


def setup_dialog_esc_handler(page: ft.Page, dialog: ft.AlertDialog):
    """
    为对话框设置 ESC 键关闭功能。
    
    这个方法应该在打开对话框之后调用。
    对话框应该在关闭时（通过 on_dismiss 或手动关闭）调用返回的清理函数。
    
    Args:
        page: Flet 页面对象
        dialog: 对话框对象
    
    Returns:
        清理函数，应该在对话框关闭时调用
    """
    # 保存原始的键盘事件处理器
    original_handler = getattr(page, 'on_keyboard_event', None)
    
    def on_keyboard(e: ft.KeyboardEvent):
        # 如果按下 ESC 键且对话框是打开的，关闭对话框
        if e.key == "Escape" and hasattr(dialog, 'open') and dialog.open:
            # 尝试调用取消方法
            if hasattr(dialog, '_on_cancel'):
                dialog._on_cancel(None)
            elif hasattr(dialog, '_close'):
                dialog._close(None)
            else:
                # 否则直接关闭
                dialog.open = False
                page.update()
        # 如果有原始的键盘事件处理器，也调用它
        elif original_handler:
            original_handler(e)
    
    # 设置键盘事件处理器
    page.on_keyboard_event = on_keyboard
    
    # 返回清理函数
    def cleanup():
        if page.on_keyboard_event == on_keyboard:
            if original_handler is not None:
                page.on_keyboard_event = original_handler
            else:
                page.on_keyboard_event = None
    
    return cleanup





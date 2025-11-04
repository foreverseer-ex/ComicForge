"""
响应式工具类。

提供根据窗口宽度动态获取 UI 尺寸的功能。
"""
import flet as ft
from api.constants.ui import (
    # 映射字典
    THUMBNAIL_WIDTH_MAP, THUMBNAIL_HEIGHT_MAP,
    LARGE_IMAGE_WIDTH_MAP, LARGE_IMAGE_HEIGHT_MAP,
    IMAGE_BORDER_RADIUS_MAP,
    DIALOG_STANDARD_WIDTH_MAP, DIALOG_STANDARD_HEIGHT_MAP,
    DIALOG_WIDE_WIDTH_MAP, DIALOG_WIDE_HEIGHT_MAP,
    SPACING_SMALL_MAP, SPACING_MEDIUM_MAP, SPACING_LARGE_MAP,
    LOADING_SIZE_SMALL_MAP, LOADING_SIZE_MEDIUM_MAP, LOADING_SIZE_LARGE_MAP,
    CHIP_PADDING_H_MAP, CHIP_PADDING_V_MAP,
    CHIP_BORDER_RADIUS_MAP, CHIP_BORDER_WIDTH_MAP, CHIP_TEXT_SIZE_MAP,
    CARD_WIDTH_MAP, CARD_HEIGHT_MAP, CARD_INFO_HEIGHT_MAP, CARD_TITLE_HEIGHT_MAP,
    DETAIL_LABEL_WIDTH_MAP, DETAIL_INFO_MIN_WIDTH_MAP,
    FONT_DISPLAY_MAP, FONT_TITLE_MAP, FONT_SUBTITLE_MAP, FONT_BODY_MAP, FONT_CAPTION_MAP,
    # 工具函数
    get_scale, pick,
)


class ResponsiveHelper:
    """响应式辅助类，用于根据窗口宽度获取对应的 UI 尺寸。"""
    
    def __init__(self, window_width: int = 1024):
        """
        初始化响应式辅助类。
        
        Args:
            window_width: 窗口宽度（像素）
        """
        self.window_width = window_width
        self.scale = get_scale(window_width)
    
    def update_width(self, window_width: int):
        """更新窗口宽度并重新计算断点。"""
        self.window_width = window_width
        self.scale = get_scale(window_width)
    
    # ==================== 图片尺寸 ====================
    
    @property
    def thumbnail_width(self) -> int:
        """缩略图宽度"""
        return pick(THUMBNAIL_WIDTH_MAP, self.window_width)
    
    @property
    def thumbnail_height(self) -> int:
        """缩略图高度"""
        return pick(THUMBNAIL_HEIGHT_MAP, self.window_width)
    
    @property
    def large_image_width(self) -> int:
        """大图宽度"""
        return pick(LARGE_IMAGE_WIDTH_MAP, self.window_width)
    
    @property
    def large_image_height(self) -> int:
        """大图高度"""
        return pick(LARGE_IMAGE_HEIGHT_MAP, self.window_width)
    
    @property
    def image_border_radius(self) -> int:
        """图片边框圆角"""
        return pick(IMAGE_BORDER_RADIUS_MAP, self.window_width)
    
    # ==================== 对话框尺寸 ====================
    
    @property
    def dialog_standard_width(self) -> int:
        """标准对话框宽度"""
        return pick(DIALOG_STANDARD_WIDTH_MAP, self.window_width)
    
    @property
    def dialog_standard_height(self) -> int:
        """标准对话框高度"""
        return pick(DIALOG_STANDARD_HEIGHT_MAP, self.window_width)
    
    @property
    def dialog_wide_width(self) -> int:
        """宽对话框宽度"""
        return pick(DIALOG_WIDE_WIDTH_MAP, self.window_width)
    
    @property
    def dialog_wide_height(self) -> int:
        """宽对话框高度"""
        return pick(DIALOG_WIDE_HEIGHT_MAP, self.window_width)
    
    # ==================== 间距 ====================
    
    @property
    def spacing_small(self) -> int:
        """小间距"""
        return pick(SPACING_SMALL_MAP, self.window_width)
    
    @property
    def spacing_medium(self) -> int:
        """中间距"""
        return pick(SPACING_MEDIUM_MAP, self.window_width)
    
    @property
    def spacing_large(self) -> int:
        """大间距"""
        return pick(SPACING_LARGE_MAP, self.window_width)
    
    # ==================== Loading 尺寸 ====================
    
    @property
    def loading_size_small(self) -> int:
        """小加载图标尺寸"""
        return pick(LOADING_SIZE_SMALL_MAP, self.window_width)
    
    @property
    def loading_size_medium(self) -> int:
        """中等加载图标尺寸"""
        return pick(LOADING_SIZE_MEDIUM_MAP, self.window_width)
    
    @property
    def loading_size_large(self) -> int:
        """大加载图标尺寸"""
        return pick(LOADING_SIZE_LARGE_MAP, self.window_width)
    
    # ==================== Chip 样式 ====================
    
    @property
    def chip_padding_h(self) -> int:
        """Chip 水平内边距"""
        return pick(CHIP_PADDING_H_MAP, self.window_width)
    
    @property
    def chip_padding_v(self) -> int:
        """Chip 垂直内边距"""
        return pick(CHIP_PADDING_V_MAP, self.window_width)
    
    @property
    def chip_border_radius(self) -> int:
        """Chip 边框圆角"""
        return pick(CHIP_BORDER_RADIUS_MAP, self.window_width)
    
    @property
    def chip_border_width(self) -> int:
        """Chip 边框宽度"""
        return pick(CHIP_BORDER_WIDTH_MAP, self.window_width)
    
    @property
    def chip_text_size(self) -> int:
        """Chip 文字大小"""
        return pick(CHIP_TEXT_SIZE_MAP, self.window_width)
    
    # ==================== 卡片尺寸 ====================
    
    @property
    def card_width(self) -> int:
        """卡片宽度"""
        return pick(CARD_WIDTH_MAP, self.window_width)
    
    @property
    def card_height(self) -> int:
        """卡片高度"""
        return pick(CARD_HEIGHT_MAP, self.window_width)
    
    @property
    def card_info_height(self) -> int:
        """卡片信息区域高度"""
        return pick(CARD_INFO_HEIGHT_MAP, self.window_width)
    
    @property
    def card_title_height(self) -> int:
        """卡片标题高度"""
        return pick(CARD_TITLE_HEIGHT_MAP, self.window_width)
    
    # ==================== 详情页尺寸 ====================
    
    @property
    def detail_label_width(self) -> int:
        """详情页标签宽度"""
        return pick(DETAIL_LABEL_WIDTH_MAP, self.window_width)
    
    @property
    def detail_info_min_width(self) -> int:
        """详情页信息最小宽度"""
        return pick(DETAIL_INFO_MIN_WIDTH_MAP, self.window_width)
    
    # ==================== 字体大小 ====================
    
    @property
    def font_display(self) -> int:
        """Display 字体大小"""
        return pick(FONT_DISPLAY_MAP, self.window_width)
    
    @property
    def font_title(self) -> int:
        """Title 字体大小"""
        return pick(FONT_TITLE_MAP, self.window_width)
    
    @property
    def font_subtitle(self) -> int:
        """Subtitle 字体大小"""
        return pick(FONT_SUBTITLE_MAP, self.window_width)
    
    @property
    def font_body(self) -> int:
        """Body 字体大小"""
        return pick(FONT_BODY_MAP, self.window_width)
    
    @property
    def font_caption(self) -> int:
        """Caption 字体大小"""
        return pick(FONT_CAPTION_MAP, self.window_width)


def get_responsive_helper(page: ft.Page) -> ResponsiveHelper:
    """
    从页面对象获取响应式辅助类。
    
    Args:
        page: Flet 页面对象
    
    Returns:
        ResponsiveHelper 实例
    """
    if page and hasattr(page, 'window_width'):
        return ResponsiveHelper(page.window_width)
    # 默认返回中等尺寸
    return ResponsiveHelper(1024)


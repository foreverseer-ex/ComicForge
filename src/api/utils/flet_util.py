"""
Flet 工具函数和基类。

提供 Flet 相关的通用工具类和函数。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


import flet as ft


@dataclass
class BaseObservableState(ft.Observable, ABC):
    """可观察状态基类。
    
    自动处理加载和保存逻辑：
    - 初始化时自动调用 load() 加载数据
    - 属性改变时自动调用 save() 保存数据
    
    子类需要：
    1. 实现 load() 方法：从配置加载数据到属性
    2. 实现 save() 方法：将属性保存到配置
    """
    _loading: bool = False  # 标记是否正在加载数据
    _saving: bool = False  # 标记是否正在保存数据
    
    def __post_init__(self):
        """初始化时自动加载数据。"""
        self._loading = True
        try:
            self.load()
        finally:
            self._loading = False
    
    @abstractmethod
    def load(self) -> None:
        """从配置加载数据到属性。
        
        子类必须实现此方法，用于将配置数据加载到 State 对象的属性中。
        在 load() 执行期间，属性改变不会触发自动保存。
        """
        raise NotImplementedError
    
    @abstractmethod
    def save(self) -> None:
        """将属性保存到配置。
        
        子类必须实现此方法，用于将 State 对象的属性保存到配置中。
        """
        raise NotImplementedError
    
    def __setattr__(self, name: str, value: Any):
        """设置属性后自动保存。"""
        # 私有属性或加载/保存期间，直接设置并通知，不触发自动保存
        if name.startswith("_") or self._loading or self._saving:
            # 使用 object.__setattr__ 设置属性
            old = object.__getattribute__(self, name) if hasattr(self, name) else None
            object.__setattr__(self, name, value)
            # 手动包装集合类型并通知观察者（如果值改变）
            if not name.startswith("_"):
                value = self._wrap_if_collection(name, value)
                object.__setattr__(self, name, value)
                if old != value:
                    self._notify(name)
            return
        
        # 普通属性设置：先获取旧值
        old_value = object.__getattribute__(self, name) if hasattr(self, name) else None
        # 包装集合类型
        value = self._wrap_if_collection(name, value)
        # 设置新值
        object.__setattr__(self, name, value)
        # 通知观察者
        if old_value != value:
            self._notify(name)
            # 只有在非加载状态下，且属性确实改变时才保存
            if not self._loading:
                self._saving = True
                try:
                    self.save()
                finally:
                    self._saving = False
    
    def __eq__(self, other):
        """比较两个状态对象是否相等。
        
        只有当类型相同且所有字段都相等时才返回 True。
        这有助于 Flet 正确区分不同的状态类型。
        """
        if type(self) is not type(other):
            return False
        return super().__eq__(other)



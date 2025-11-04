"""
简单的发布-订阅机制。

用于聊天服务的事件通知。
"""
from typing import Dict, List, Callable
from loguru import logger


class PubSub:
    """
    简单的发布-订阅系统。
    
    支持主题订阅和事件发布。
    """
    
    def __init__(self):
        """初始化发布-订阅系统。"""
        # 订阅者：{topic: [callback1, callback2, ...]}
        self._subscribers: Dict[str, List[Callable]] = {}
    
    def publish(self, topic: str, data: dict):
        """
        发布事件。
        
        Args:
            topic: 主题名称
            data: 事件数据
        """
        if topic not in self._subscribers:
            logger.debug(f"主题无订阅者: {topic}")
            return
        
        # 通知所有订阅者
        for callback in self._subscribers[topic]:
            try:
                callback(data)
            except (BrokenPipeError, ConnectionError, OSError) as e:
                # 忽略 socket 连接错误（通常是应用关闭时产生的）
                logger.debug(f"发布事件时连接已关闭 (topic={topic}): {e}")
            except Exception as e:
                logger.exception(f"执行回调失败 (topic={topic}): {e}")
    
    def subscribe(self, topic: str, callback: Callable):
        """
        订阅事件。
        
        Args:
            topic: 主题名称
            callback: 回调函数，接收一个 dict 参数
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        
        self._subscribers[topic].append(callback)
        logger.debug(f"订阅主题: {topic}")
    
    def unsubscribe(self, topic: str, callback: Callable):
        """
        取消订阅。
        
        Args:
            topic: 主题名称
            callback: 回调函数
        """
        if topic in self._subscribers:
            if callback in self._subscribers[topic]:
                self._subscribers[topic].remove(callback)
                logger.debug(f"取消订阅: {topic}")
    
    def clear(self):
        """清空所有订阅。"""
        self._subscribers.clear()


# 全局发布-订阅实例
_pubsub = PubSub()


def publish(topic: str, data: dict):
    """
    发布事件。
    
    Args:
        topic: 主题名称
        data: 事件数据
    """
    _pubsub.publish(topic, data)


def subscribe(topic: str, callback: Callable):
    """
    订阅事件。
    
    Args:
        topic: 主题名称
        callback: 回调函数
    """
    _pubsub.subscribe(topic, callback)


def unsubscribe(topic: str, callback: Callable):
    """
    取消订阅。
    
    Args:
        topic: 主题名称
        callback: 回调函数
    """
    _pubsub.unsubscribe(topic, callback)


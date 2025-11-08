"""
重试工具函数。

提供通用的重试机制，支持同步和异步函数。
"""
import asyncio
import time
from typing import Callable, TypeVar, Any, Optional, Tuple
from loguru import logger

T = TypeVar('T')


def retry(
    func: Callable[[], T],
    max_attempts: int = 5,
    delay: float = 5.0,
    exceptions: Tuple[type[Exception], ...] = (Exception,),
    operation_name: str = "操作"
) -> T:
    """
    同步函数重试装饰器。
    
    :param func: 要执行的函数
    :param max_attempts: 最大重试次数
    :param delay: 重试延迟（秒）
    :param exceptions: 需要重试的异常类型元组
    :param operation_name: 操作名称（用于日志）
    :return: 函数返回值
    :raises: 最后一次尝试的异常
    """
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:
                logger.warning(
                    f"{operation_name} 失败（尝试 {attempt + 1}/{max_attempts}），"
                    f"{delay}秒后重试... 错误: {e}"
                )
                time.sleep(delay)
            else:
                logger.error(f"{operation_name} 失败，已重试 {max_attempts} 次，放弃")
                raise
        except Exception as e:
            # 非指定异常类型，直接抛出
            raise
    
    # 理论上不会到达这里
    if last_exception:
        raise last_exception
    raise RuntimeError(f"{operation_name} 失败")


async def retry_async(
    func: Callable[[], Any],
    max_attempts: int = 5,
    delay: float = 5.0,
    exceptions: Tuple[type[Exception], ...] = (Exception,),
    operation_name: str = "操作"
) -> Any:
    """
    异步函数重试装饰器。
    
    :param func: 要执行的协程函数
    :param max_attempts: 最大重试次数
    :param delay: 重试延迟（秒）
    :param exceptions: 需要重试的异常类型元组
    :param operation_name: 操作名称（用于日志）
    :return: 协程返回值
    :raises: 最后一次尝试的异常
    """
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:
                logger.warning(
                    f"{operation_name} 失败（尝试 {attempt + 1}/{max_attempts}），"
                    f"{delay}秒后重试... 错误: {e}"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"{operation_name} 失败，已重试 {max_attempts} 次，放弃")
                raise
        except Exception as e:
            # 非指定异常类型，直接抛出
            raise
    
    # 理论上不会到达这里
    if last_exception:
        raise last_exception
    raise RuntimeError(f"{operation_name} 失败")


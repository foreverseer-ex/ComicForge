"""
超时工具函数。

提供通用的超时机制，支持同步和异步函数。
"""
import asyncio
from typing import Callable, TypeVar, Any
from loguru import logger

T = TypeVar('T')


def with_timeout(
    func: Callable[[], T],
    timeout_seconds: float,
    operation_name: str = "操作"
) -> T:
    """
    同步函数超时包装器。
    
    注意：对于同步函数，超时机制可能不够精确，建议使用异步版本。
    
    :param func: 要执行的函数
    :param timeout_seconds: 超时时间（秒）
    :param operation_name: 操作名称（用于日志）
    :return: 函数返回值
    :raises TimeoutError: 超时时抛出
    """
    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(func)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            logger.error(f"{operation_name} 超时（{timeout_seconds}秒）")
            raise TimeoutError(f"{operation_name} 超时（{timeout_seconds}秒）")


async def with_timeout_async(
    func: Callable[[], Any],
    timeout_seconds: float,
    operation_name: str = "操作"
) -> Any:
    """
    异步函数超时包装器。
    
    :param func: 要执行的协程函数
    :param timeout_seconds: 超时时间（秒）
    :param operation_name: 操作名称（用于日志）
    :return: 协程返回值
    :raises TimeoutError: 超时时抛出
    """
    try:
        return await asyncio.wait_for(func(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.error(f"{operation_name} 超时（{timeout_seconds}秒）")
        raise TimeoutError(f"{operation_name} 超时（{timeout_seconds}秒）")


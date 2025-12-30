"""
异步装饰器

包含异常处理、断点续传等装饰器
"""
import asyncio
import functools
import os
from pathlib import Path
from typing import Callable, TypeVar

from loguru import logger

T = TypeVar("T")


def async_except_handler(message: str = "Operation failed", max_retries: int = 5):
    """
    异步异常处理装饰器，支持指数退避重试

    Args:
        message: 错误消息
        max_retries: 最大重试次数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"{message} (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"{message} after {max_retries} attempts: {e}")
            raise last_error
        return wrapper
    return decorator


def async_check_file_exists(output_path: str | Path):
    """
    异步断点续传装饰器

    如果输出文件已存在，则跳过执行

    Args:
        output_path: 输出文件路径（可以是字符串或返回路径的函数）
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # 解析输出路径
            if callable(output_path):
                path = output_path(*args, **kwargs)
            else:
                path = output_path

            # 检查文件是否存在
            if os.path.exists(path):
                logger.info(f"Skipping {func.__name__}, output file exists: {path}")
                # 如果可能，返回已存在的文件内容
                return None

            # 执行函数
            result = await func(*args, **kwargs)
            return result
        return wrapper
    return decorator

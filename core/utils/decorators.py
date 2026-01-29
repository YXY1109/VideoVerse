"""Async decorators for pipeline steps."""
import asyncio
import functools
import os
from pathlib import Path
from typing import Callable, TypeVar, Union
from loguru import logger

T = TypeVar("T")


def async_except_handler(message: str = "Operation failed", max_retries: int = 5):
    """
    Async exception handler decorator with exponential backoff retry.

    Args:
        message: Error message prefix
        max_retries: Maximum number of retries
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
                        logger.warning(
                            f"{message} (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {wait_time} seconds..."
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"{message} after {max_retries} attempts: {e}")
            raise last_error
        return wrapper
    return decorator


def async_check_file_exists(output_path: Union[str, Path, Callable[..., Union[str, Path]]]):
    """
    Async checkpoint decorator - skip execution if output file exists.

    Args:
        output_path: Output file path (string, Path, or callable that returns path)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Resolve output path
            if callable(output_path):
                path = output_path(*args, **kwargs)
            else:
                path = output_path

            # Check if file exists
            if os.path.exists(path):
                logger.info(f"Skipping {func.__name__}, output file exists: {path}")
                return str(path)

            # Execute function
            result = await func(*args, **kwargs)
            return result
        return wrapper
    return decorator

"""
装饰器模块测试

测试异步装饰器功能
"""
import asyncio
import os
from pathlib import Path
from typing import Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAsyncExceptHandler:
    """测试 async_except_handler 装饰器"""

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """测试成功执行"""
        from src.utils.decorators import async_except_handler

        @async_except_handler("Test failed")
        async def test_func():
            return "success"

        result = await test_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_on_exception(self):
        """测试异常重试"""
        from src.utils.decorators import async_except_handler

        call_count = 0

        @async_except_handler("Test failed", max_retries=3)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        from src.utils.decorators import async_except_handler

        @async_except_handler("Test failed", max_retries=2)
        async def test_func():
            raise ValueError("Permanent error")

        with pytest.raises(ValueError, match="Permanent error"):
            await test_func()

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """测试指数退避"""
        from src.utils.decorators import async_except_handler
        import time

        sleep_times = []

        @async_except_handler("Test failed", max_retries=3)
        async def test_func():
            if len(sleep_times) < 2:
                raise ValueError("Error")
            return "success"

        # 模拟 asyncio.sleep 以记录时间
        original_sleep = asyncio.sleep

        async def mock_sleep(delay):
            sleep_times.append(delay)

        with patch('asyncio.sleep', side_effect=mock_sleep):
            await test_func()

        # 验证退避时间: 1s, 2s (2^0, 2^1)
        assert sleep_times == [1, 2]

    @pytest.mark.asyncio
    async def test_custom_message(self):
        """测试自定义错误消息"""
        from src.utils.decorators import async_except_handler

        @async_except_handler("Custom operation failed", max_retries=1)
        async def test_func():
            raise RuntimeError("Test error")

        with pytest.raises(RuntimeError):
            await test_func()

    @pytest.mark.asyncio
    async def test_no_retry(self):
        """测试不重试（max_retries=1）"""
        from src.utils.decorators import async_except_handler

        call_count = 0

        @async_except_handler("Test failed", max_retries=1)
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Error")

        with pytest.raises(ValueError):
            await test_func()

        # 应该只调用一次（没有重试）
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_different_exception_types(self):
        """测试不同类型的异常"""
        from src.utils.decorators import async_except_handler

        @async_except_handler("Test failed", max_retries=2)
        async def raise_value_error():
            raise ValueError("Value error")

        @async_except_handler("Test failed", max_retries=2)
        async def raise_type_error():
            raise TypeError("Type error")

        @async_except_handler("Test failed", max_retries=2)
        async def raise_runtime_error():
            raise RuntimeError("Runtime error")

        with pytest.raises(ValueError):
            await raise_value_error()

        with pytest.raises(TypeError):
            await raise_type_error()

        with pytest.raises(RuntimeError):
            await raise_runtime_error()

    @pytest.mark.asyncio
    async def test_preserve_function_attributes(self):
        """测试保留函数属性"""
        from src.utils.decorators import async_except_handler
        import functools

        @async_except_handler("Test failed")
        async def test_func():
            """Test function docstring"""
            return "result"

        # 验证函数属性被保留
        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test function docstring"

    @pytest.mark.asyncio
    async def test_with_arguments(self):
        """测试带参数的函数"""
        from src.utils.decorators import async_except_handler

        @async_except_handler("Test failed")
        async def test_func(a, b, c=None):
            return f"{a}-{b}-{c}"

        result = await test_func(1, 2, c=3)
        assert result == "1-2-3"

    @pytest.mark.asyncio
    async def test_exception_after_success(self):
        """测试成功后再次调用失败"""
        from src.utils.decorators import async_except_handler

        call_count = 0

        @async_except_handler("Test failed", max_retries=2)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "success"
            else:
                raise ValueError("Error")

        # 第一次调用成功
        result = await test_func()
        assert result == "success"

        # 第二次调用失败
        with pytest.raises(ValueError):
            await test_func()


class TestAsyncCheckFileExists:
    """测试 async_check_file_exists 装饰器"""

    @pytest.mark.asyncio
    async def test_file_not_exists(self, tmp_path: Path):
        """测试文件不存在时执行函数"""
        from src.utils.decorators import async_check_file_exists

        output_file = tmp_path / "output.txt"

        @async_check_file_exists(output_file)
        async def create_file():
            output_file.write_text("content")
            return "created"

        result = await create_file()
        assert result == "created"
        assert output_file.exists()
        assert output_file.read_text() == "content"

    @pytest.mark.asyncio
    async def test_file_exists_skip_execution(self, tmp_path: Path):
        """测试文件存在时跳过执行"""
        from src.utils.decorators import async_check_file_exists

        output_file = tmp_path / "output.txt"
        output_file.write_text("existing content")

        executed = False

        @async_check_file_exists(output_file)
        async def create_file():
            nonlocal executed
            executed = True
            output_file.write_text("new content")
            return "created"

        result = await create_file()
        assert result is None
        assert executed is False
        assert output_file.read_text() == "existing content"

    @pytest.mark.asyncio
    async def test_callable_output_path(self, tmp_path: Path):
        """测试可调用的输出路径"""
        from src.utils.decorators import async_check_file_exists

        def get_output_path(suffix):
            return tmp_path / f"output_{suffix}.txt"

        @async_check_file_exists(lambda: get_output_path("test"))
        async def create_file():
            output_file = get_output_path("test")
            output_file.write_text("content")
            return "created"

        # 第一次执行
        result = await create_file()
        assert result == "created"

        # 第二次应该跳过
        result = await create_file()
        assert result is None

    @pytest.mark.asyncio
    async def test_callable_with_function_args(self, tmp_path: Path):
        """测试使用函数参数的可调用路径"""
        from src.utils.decorators import async_check_file_exists

        def get_output_path(name):
            return tmp_path / f"{name}.txt"

        @async_check_file_exists(lambda name: get_output_path(name))
        async def create_file(name):
            output_file = get_output_path(name)
            output_file.write_text(f"content for {name}")
            return f"created {name}"

        # 创建 test1
        result = await create_file("test1")
        assert result == "created test1"

        # 跳过 test1
        result = await create_file("test1")
        assert result is None

        # 创建 test2
        result = await create_file("test2")
        assert result == "created test2"

    @pytest.mark.asyncio
    async def test_string_path(self, tmp_path: Path):
        """测试字符串路径"""
        from src.utils.decorators import async_check_file_exists

        output_path = str(tmp_path / "output.txt")

        @async_check_file_exists(output_path)
        async def create_file():
            Path(output_path).write_text("content")
            return "created"

        result = await create_file()
        assert result == "created"

    @pytest.mark.asyncio
    async def test_path_object(self, tmp_path: Path):
        """测试 Path 对象"""
        from src.utils.decorators import async_check_file_exists

        output_path = tmp_path / "output.txt"

        @async_check_file_exists(output_path)
        async def create_file():
            output_path.write_text("content")
            return "created"

        result = await create_file()
        assert result == "created"

    @pytest.mark.asyncio
    async def test_preserve_function_attributes(self):
        """测试保留函数属性"""
        from src.utils.decorators import async_check_file_exists

        @async_check_file_exists("output.txt")
        async def test_func():
            """Test function"""
            return "result"

        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test function"

    @pytest.mark.asyncio
    async def test_with_function_arguments(self, tmp_path: Path):
        """测试带函数参数的装饰器"""
        from src.utils.decorators import async_check_file_exists

        output_file = tmp_path / "output.txt"

        @async_check_file_exists(output_file)
        async def create_file(value: int):
            output_file.write_text(str(value))
            return value

        result = await create_file(42)
        assert result == 42

    @pytest.mark.asyncio
    async def test_empty_file_creation(self, tmp_path: Path):
        """测试创建空文件"""
        from src.utils.decorators import async_check_file_exists

        output_file = tmp_path / "empty.txt"

        @async_check_file_exists(output_file)
        async def create_empty():
            output_file.write_text("")
            return "created"

        result = await create_empty()
        assert result == "created"
        assert output_file.exists()


@pytest.mark.integration
class TestDecoratorsIntegration:
    """集成测试: 装饰器组合"""

    @pytest.mark.asyncio
    async def test_combined_decorators(self, tmp_path: Path):
        """测试装饰器组合"""
        from src.utils.decorators import async_except_handler, async_check_file_exists

        output_file = tmp_path / "output.txt"

        call_count = 0

        @async_check_file_exists(output_file)
        @async_except_handler("Operation failed", max_retries=3)
        async def create_with_retry():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            output_file.write_text(f"success after {call_count} tries")
            return "success"

        # 第一次调用（会重试）
        result = await create_with_retry()
        assert result == "success"
        assert call_count == 2

        # 第二次调用（文件已存在，跳过）
        call_count = 0
        result = await create_with_retry()
        assert result is None
        assert call_count == 0

    @pytest.mark.asyncio
    async def test_decorator_order(self, tmp_path: Path):
        """测试装饰器顺序"""
        from src.utils.decorators import async_except_handler, async_check_file_exists

        output_file = tmp_path / "output.txt"

        # 检查文件在外层，异常处理在内层
        @async_check_file_exists(output_file)
        @async_except_handler("Failed")
        async def func1():
            raise ValueError("Error")

        # 文件不存在时，应该执行函数并抛出异常
        with pytest.raises(ValueError):
            await func1()

        # 文件存在后，应该跳过执行
        output_file.write_text("content")
        result = await func1()
        assert result is None

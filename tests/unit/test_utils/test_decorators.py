"""Test async decorators."""
import pytest
import asyncio
import os
import tempfile
from pathlib import Path
from core.utils.decorators import async_except_handler, async_check_file_exists


@pytest.mark.asyncio
async def test_async_except_handler_success():
    """Test successful execution with exception handler."""
    @async_except_handler("Test operation", max_retries=2)
    async def successful_operation():
        return "success"

    result = await successful_operation()
    assert result == "success"


@pytest.mark.asyncio
async def test_async_except_handler_retry():
    """Test retry on failure."""
    call_count = 0

    @async_except_handler("Test operation", max_retries=3)
    async def failing_operation():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Temporary failure")
        return "success"

    result = await failing_operation()
    assert result == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_async_except_handler_max_retries():
    """Test exceeding max retries."""
    @async_except_handler("Test operation", max_retries=2)
    async def always_failing():
        raise ValueError("Always fails")

    with pytest.raises(ValueError, match="Always fails"):
        await always_failing()


@pytest.mark.asyncio
async def test_async_check_file_exists_skip():
    """Test skipping when file exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("content")

        executed = []

        @async_check_file_exists(str(test_file))
        async def create_file():
            executed.append(True)
            return "created"

        result = await create_file()
        assert result == str(test_file)
        assert len(executed) == 0  # Function was not executed


@pytest.mark.asyncio
async def test_async_check_file_exists_execute():
    """Test executing when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "new_file.txt"

        executed = []

        @async_check_file_exists(str(test_file))
        async def create_file():
            executed.append(True)
            test_file.write_text("created")
            return str(test_file)

        result = await create_file()
        assert result == str(test_file)
        assert len(executed) == 1  # Function was executed

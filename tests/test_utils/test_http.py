"""
HTTP 客户端模块测试

测试异步 HTTP 客户端功能
"""
import asyncio

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestAsyncHTTPClient:
    """测试 AsyncHTTPClient 类"""

    @pytest.mark.asyncio
    async def test_init(self):
        """测试初始化"""
        from src.utils.http import AsyncHTTPClient

        client = AsyncHTTPClient()
        assert client.base_url == ""
        assert client.timeout == 300.0
        assert client._max_connections == 100
        assert client._max_keepalive_connections == 20
        assert client._client is None

    @pytest.mark.asyncio
    async def test_init_with_params(self):
        """测试带参数初始化"""
        from src.utils.http import AsyncHTTPClient

        client = AsyncHTTPClient(
            base_url="https://api.example.com",
            timeout=60.0,
            max_connections=50,
            max_keepalive_connections=10,
        )

        assert client.base_url == "https://api.example.com"
        assert client.timeout == 60.0
        assert client._max_connections == 50
        assert client._max_keepalive_connections == 10

    @pytest.mark.asyncio
    async def test_base_url_trailing_slash(self):
        """测试 base_url 尾部斜杠处理"""
        from src.utils.http import AsyncHTTPClient

        client1 = AsyncHTTPClient(base_url="https://api.example.com/")
        client2 = AsyncHTTPClient(base_url="https://api.example.com")

        assert client1.base_url == "https://api.example.com"
        assert client2.base_url == "https://api.example.com"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """测试上下文管理器"""
        from src.utils.http import AsyncHTTPClient

        async with AsyncHTTPClient() as client:
            assert client._client is not None
            assert isinstance(client._client, httpx.AsyncClient)

        # 退出上下文后客户端应该被关闭
        # 但我们无法直接验证 _client 是否为 None

    @pytest.mark.asyncio
    async def test_get_request(self, mock_http_response):
        """测试 GET 请求"""
        from src.utils.http import AsyncHTTPClient

        async with AsyncHTTPClient() as client:
            with patch.object(client._client, 'get', new=AsyncMock(return_value=mock_http_response)):
                response = await client.get("https://api.example.com/test")

                # 验证响应
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_with_params(self, mock_http_response):
        """测试带参数的 GET 请求"""
        from src.utils.http import AsyncHTTPClient

        async with AsyncHTTPClient() as client:
            with patch.object(client._client, 'get', new=AsyncMock(return_value=mock_http_response)) as mock_get:
                await client.get(
                    "https://api.example.com/test",
                    params={"key": "value"},
                    headers={"X-Custom": "header"}
                )

                # 验证调用参数
                mock_get.assert_called_once()
                call_args = mock_get.call_args
                assert "params" in call_args.kwargs
                assert call_args.kwargs["params"] == {"key": "value"}
                assert "headers" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_post_request(self, mock_http_response):
        """测试 POST 请求"""
        from src.utils.http import AsyncHTTPClient

        async with AsyncHTTPClient() as client:
            with patch.object(client._client, 'post', new=AsyncMock(return_value=mock_http_response)) as mock_post:
                await client.post(
                    "https://api.example.com/test",
                    json={"data": "value"}
                )

                # 验证调用
                mock_post.assert_called_once()
                call_args = mock_post.call_args
                assert call_args.kwargs["json"] == {"data": "value"}

    @pytest.mark.asyncio
    async def test_post_with_data(self, mock_http_response):
        """测试带 data 的 POST 请求"""
        from src.utils.http import AsyncHTTPClient

        async with AsyncHTTPClient() as client:
            with patch.object(client._client, 'post', new=AsyncMock(return_value=mock_http_response)) as mock_post:
                await client.post(
                    "https://api.example.com/test",
                    data="raw data"
                )

                # 验证调用
                call_args = mock_post.call_args
                assert call_args.kwargs["data"] == "raw data"

    @pytest.mark.asyncio
    async def test_post_with_files(self, mock_http_response):
        """测试带文件的 POST 请求"""
        from src.utils.http import AsyncHTTPClient

        async with AsyncHTTPClient() as client:
            with patch.object(client._client, 'post', new=AsyncMock(return_value=mock_http_response)) as mock_post:
                files = {"file": ("test.txt", b"content")}
                await client.post(
                    "https://api.example.com/upload",
                    files=files
                )

                # 验证调用
                call_args = mock_post.call_args
                assert "files" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_put_request(self, mock_http_response):
        """测试 PUT 请求"""
        from src.utils.http import AsyncHTTPClient

        async with AsyncHTTPClient() as client:
            with patch.object(client._client, 'put', new=AsyncMock(return_value=mock_http_response)) as mock_put:
                await client.put(
                    "https://api.example.com/test",
                    json={"updated": "data"}
                )

                # 验证调用
                mock_put.assert_called_once()
                call_args = mock_put.call_args
                assert call_args.kwargs["json"] == {"updated": "data"}

    @pytest.mark.asyncio
    async def test_request_without_init(self):
        """测试未初始化的客户端请求"""
        from src.utils.http import AsyncHTTPClient

        client = AsyncHTTPClient()
        # 不使用上下文管理器，直接调用请求

        with pytest.raises(RuntimeError, match="HTTPClient not initialized"):
            await client.get("https://api.example.com/test")


class TestGlobalClient:
    """测试全局 HTTP 客户端"""

    @pytest.mark.asyncio
    async def test_get_global_client(self):
        """测试获取全局客户端"""
        from src.utils.http import get_global_client

        client = await get_global_client()
        assert client is not None
        assert isinstance(client, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_get_global_client_singleton(self):
        """测试全局客户端单例"""
        from src.utils.http import get_global_client

        client1 = await get_global_client()
        client2 = await get_global_client()

        assert client1 is client2

    @pytest.mark.asyncio
    async def test_close_global_client(self):
        """测试关闭全局客户端"""
        from src.utils.http import get_global_client, close_global_client, _global_client

        # 获取客户端
        client = await get_global_client()
        assert _global_client is not None

        # 关闭客户端
        await close_global_client()
        # 验证客户端被重置
        # 注意: _global_client 是模块级变量，需要重新导入
        from src.utils import http
        assert http._global_client is None

    @pytest.mark.asyncio
    async def test_global_client_recreation(self):
        """测试重新创建全局客户端"""
        from src.utils.http import get_global_client, close_global_client

        # 获取并关闭
        client1 = await get_global_client()
        await close_global_client()

        # 重新获取
        client2 = await get_global_client()

        # 应该是不同的实例
        assert client1 is not client2

    @pytest.mark.asyncio
    async def test_global_client_config(self):
        """测试全局客户端配置"""
        from src.utils.http import get_global_client

        client = await get_global_client()

        # 验证默认配置
        assert client.timeout == httpx.Timeout(300.0)
        # 验证连接池配置
        limits = client._limits
        assert limits.max_connections == 100
        assert limits.max_keepalive_connections == 20


@pytest.mark.integration
class TestAsyncHTTPClientIntegration:
    """集成测试: HTTP 客户端"""

    @pytest.mark.skip(reason="需要真实的 HTTP 服务器")
    @pytest.mark.asyncio
    async def test_real_http_request(self):
        """测试真实的 HTTP 请求（跳过）"""
        pass

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """测试并发请求"""
        from src.utils.http import AsyncHTTPClient

        async with AsyncHTTPClient() as client:
            # 模拟多个并发请求
            tasks = []
            for i in range(10):
                mock_response = MagicMock()
                mock_response.status_code = 200

                with patch.object(client._client, 'get', new=AsyncMock(return_value=mock_response)):
                    task = client.get(f"https://api.example.com/test{i}")
                    tasks.append(task)

            results = await asyncio.gather(*tasks)

            # 验证所有请求都成功
            assert len(results) == 10
            assert all(r.status_code == 200 for r in results)

    @pytest.mark.asyncio
    async def test_request_timeout(self):
        """测试请求超时"""
        from src.utils.http import AsyncHTTPClient

        client = AsyncHTTPClient(timeout=0.001)  # 非常短的超时

        # 这个测试依赖于实际的 HTTP 服务器
        # 在测试环境中应该被 mock
        async with client:
            # 模拟超时
            with patch.object(client._client, 'get', side_effect=asyncio.TimeoutError()):
                with pytest.raises(asyncio.TimeoutError):
                    await client.get("https://api.example.com/test")

    @pytest.mark.asyncio
    async def test_http_error_handling(self):
        """测试 HTTP 错误处理"""
        from src.utils.http import AsyncHTTPClient

        async with AsyncHTTPClient() as client:
            # 模拟 HTTP 错误
            with patch.object(client._client, 'get', side_effect=httpx.HTTPError("Connection error")):
                with pytest.raises(httpx.HTTPError):
                    await client.get("https://api.example.com/test")

    @pytest.mark.asyncio
    async def test_http_status_error(self):
        """测试 HTTP 状态码错误"""
        from src.utils.http import AsyncHTTPClient

        async with AsyncHTTPClient() as client:
            # 模拟 404 错误
            mock_response = MagicMock()
            mock_response.status_code = 404

            with patch.object(client._client, 'get', new=AsyncMock(return_value=mock_response)):
                response = await client.get("https://api.example.com/notfound")
                # get 方法不会自动抛出异常，需要手动检查状态码
                assert response.status_code == 404

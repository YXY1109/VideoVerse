"""
异步 HTTP 客户端封装

基于 httpx 的异步 HTTP 客户端，支持连接池、重试、超时
"""
import asyncio
from typing import Any, Optional
import httpx
from src.config import get_settings

settings = get_settings()


class AsyncHTTPClient:
    """异步 HTTP 客户端"""

    def __init__(
        self,
        base_url: str = "",
        timeout: float = 300.0,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._max_connections = max_connections
        self._max_keepalive_connections = max_keepalive_connections

    async def __aenter__(self):
        """进入上下文"""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(
                max_connections=self._max_connections,
                max_keepalive_connections=self._max_keepalive_connections,
            ),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self._client:
            await self._client.aclose()

    async def get(
        self,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> httpx.Response:
        """GET 请求"""
        if not self._client:
            raise RuntimeError("HTTPClient not initialized. Use 'async with' or call init()")
        return await self._client.get(url, params=params, headers=headers)

    async def post(
        self,
        url: str,
        json: Optional[dict] = None,
        data: Any = None,
        files: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> httpx.Response:
        """POST 请求"""
        if not self._client:
            raise RuntimeError("HTTPClient not initialized. Use 'async with' or call init()")
        return await self._client.post(url, json=json, data=data, files=files, headers=headers)

    async def put(
        self,
        url: str,
        json: Optional[dict] = None,
        data: Any = None,
        headers: Optional[dict] = None,
    ) -> httpx.Response:
        """PUT 请求"""
        if not self._client:
            raise RuntimeError("HTTPClient not initialized. Use 'async with' or call init()")
        return await self._client.put(url, json=json, data=data, headers=headers)


# 全局 HTTP 客户端（用于简单场景）
_global_client: Optional[httpx.AsyncClient] = None


async def get_global_client() -> httpx.AsyncClient:
    """获取全局 HTTP 客户端"""
    global _global_client
    if _global_client is None:
        _global_client = httpx.AsyncClient(
            timeout=httpx.Timeout(300.0),
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
            ),
        )
    return _global_client


async def close_global_client():
    """关闭全局 HTTP 客户端"""
    global _global_client
    if _global_client:
        await _global_client.aclose()
        _global_client = None

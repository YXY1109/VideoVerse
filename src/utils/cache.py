"""
异步缓存管理

使用 aiocache 进行内存缓存，支持 TTL
"""
import hashlib
from typing import Any, Optional

from aiocache.backends.memory import SimpleMemoryCache
from aiocache.serializers import PickleSerializer


class CacheManager:
    """缓存管理器"""

    def __init__(self, ttl: int = 86400 * 7):  # 默认 7 天
        serializer = PickleSerializer()
        self.llm_cache = SimpleMemoryCache(serializer=serializer, ttl=ttl, namespace="llm")
        self.translation_cache = SimpleMemoryCache(serializer=serializer, ttl=ttl, namespace="translation")

    def _make_key(self, *args: str) -> str:
        """生成缓存键（使用 SHA256 hash 避免键过长）"""
        content = ":".join(str(arg) for arg in args)
        return hashlib.sha256(content.encode()).hexdigest()

    async def get_llm_cache(self, prompt: str, resp_type: str = "default") -> Optional[Any]:
        """获取 LLM 缓存"""
        key = self._make_key(resp_type, prompt)
        return await self.llm_cache.get(key)

    async def set_llm_cache(self, prompt: str, result: Any, resp_type: str = "default") -> None:
        """设置 LLM 缓存"""
        key = self._make_key(resp_type, prompt)
        await self.llm_cache.set(key, result)

    async def get_translation_cache(self, text: str, target_lang: str) -> Optional[str]:
        """获取翻译缓存"""
        key = self._make_key(target_lang, text)
        return await self.translation_cache.get(key)

    async def set_translation_cache(self, text: str, translation: str, target_lang: str) -> None:
        """设置翻译缓存"""
        key = self._make_key(target_lang, text)
        await self.translation_cache.set(key, translation)

    async def clear(self) -> None:
        """清空所有缓存"""
        await self.llm_cache.clear()
        await self.translation_cache.clear()


# 全局缓存实例
cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """获取缓存管理器"""
    return cache_manager

"""
同步缓存管理

使用内存字典进行缓存，支持 TTL
"""

import hashlib
import time
from typing import Any


class _CacheEntry:
    """缓存条目"""

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.expires_at = time.time() + ttl

    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() > self.expires_at


class CacheManager:
    """缓存管理器"""

    def __init__(self, ttl: int = 86400 * 7):  # 默认 7 天
        self._llm_cache: dict[str, _CacheEntry] = {}
        self._translation_cache: dict[str, _CacheEntry] = {}
        self._ttl = ttl

    def _make_key(self, *args: str) -> str:
        """生成缓存键（使用 SHA256 hash 避免键过长）"""
        content = ":".join(str(arg) for arg in args)
        return hashlib.sha256(content.encode()).hexdigest()

    def _get(self, cache: dict[str, _CacheEntry], key: str) -> Any | None:
        """从缓存中获取值"""
        entry = cache.get(key)
        if entry is None:
            return None
        if entry.is_expired():
            del cache[key]
            return None
        return entry.value

    def _set(self, cache: dict[str, _CacheEntry], key: str, value: Any) -> None:
        """设置缓存值"""
        cache[key] = _CacheEntry(value, self._ttl)

    def get_llm_cache(self, prompt: str, resp_type: str = "default") -> Any | None:
        """获取 LLM 缓存"""
        key = self._make_key(resp_type, prompt)
        return self._get(self._llm_cache, key)

    def set_llm_cache(self, prompt: str, result: Any, resp_type: str = "default") -> None:
        """设置 LLM 缓存"""
        key = self._make_key(resp_type, prompt)
        self._set(self._llm_cache, key, result)

    def get_translation_cache(self, text: str, target_lang: str) -> str | None:
        """获取翻译缓存"""
        key = self._make_key(target_lang, text)
        result = self._get(self._translation_cache, key)
        return result

    def set_translation_cache(self, text: str, translation: str, target_lang: str) -> None:
        """设置翻译缓存"""
        key = self._make_key(target_lang, text)
        self._set(self._translation_cache, key, translation)

    def clear(self) -> None:
        """清空所有缓存"""
        self._llm_cache.clear()
        self._translation_cache.clear()


# 全局缓存实例
cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """获取缓存管理器"""
    return cache_manager

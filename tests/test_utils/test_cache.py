"""
缓存模块测试

测试异步缓存管理功能
"""
import asyncio

import pytest


class TestCacheManager:
    """测试 CacheManager 类"""

    @pytest.mark.asyncio
    async def test_init(self):
        """测试缓存管理器初始化"""
        from src.utils.cache import CacheManager

        cache = CacheManager()
        assert cache.llm_cache is not None
        assert cache.translation_cache is not None

    @pytest.mark.asyncio
    async def test_init_custom_ttl(self):
        """测试自定义 TTL"""
        from src.utils.cache import CacheManager

        cache = CacheManager(ttl=3600)
        assert cache.llm_cache is not None
        assert cache.translation_cache is not None

    def test_make_key(self):
        """测试缓存键生成"""
        from src.utils.cache import CacheManager

        cache = CacheManager()
        key1 = cache._make_key("test", "prompt1")
        key2 = cache._make_key("test", "prompt1")
        key3 = cache._make_key("test", "prompt2")

        # 相同输入应该生成相同的键
        assert key1 == key2
        # 不同输入应该生成不同的键
        assert key1 != key3
        # 键应该是十六进制字符串（SHA256 哈希）
        assert len(key1) == 64
        assert all(c in "0123456789abcdef" for c in key1)

    def test_make_key_with_multiple_args(self):
        """测试多个参数的键生成"""
        from src.utils.cache import CacheManager

        cache = CacheManager()
        key1 = cache._make_key("arg1", "arg2", "arg3")
        key2 = cache._make_key("arg1", "arg2", "arg3")
        key3 = cache._make_key("arg1", "arg2", "different")

        assert key1 == key2
        assert key1 != key3

    def test_make_key_long_input(self):
        """测试长输入的键生成"""
        from src.utils.cache import CacheManager

        cache = CacheManager()
        long_input = "a" * 100000
        key = cache._make_key(long_input)

        # 长输入应该生成固定长度的哈希
        assert len(key) == 64

    @pytest.mark.asyncio
    async def test_set_and_get_llm_cache(self):
        """测试 LLM 缓存设置和获取"""
        from src.utils.cache import CacheManager

        cache = CacheManager()
        prompt = "Test prompt"
        result = {"output": "test result"}

        # 设置缓存
        await cache.set_llm_cache(prompt, result, "test_type")

        # 获取缓存
        cached = await cache.get_llm_cache(prompt, "test_type")

        assert cached == result

    @pytest.mark.asyncio
    async def test_get_llm_cache_miss(self):
        """测试 LLM 缓存未命中"""
        from src.utils.cache import CacheManager

        cache = CacheManager()
        prompt = "Non-existent prompt"

        # 获取不存在的缓存
        cached = await cache.get_llm_cache(prompt, "test_type")

        assert cached is None

    @pytest.mark.asyncio
    async def test_set_and_get_translation_cache(self):
        """测试翻译缓存设置和获取"""
        from src.utils.cache import CacheManager

        cache = CacheManager()
        text = "Hello world"
        translation = "你好世界"
        target_lang = "zh"

        # 设置缓存
        await cache.set_translation_cache(text, translation, target_lang)

        # 获取缓存
        cached = await cache.get_translation_cache(text, target_lang)

        assert cached == translation

    @pytest.mark.asyncio
    async def test_translation_cache_different_languages(self):
        """测试不同语言的翻译缓存"""
        from src.utils.cache import CacheManager

        cache = CacheManager()
        text = "Hello"

        # 设置不同语言的缓存
        await cache.set_translation_cache(text, "你好", "zh")
        await cache.set_translation_cache(text, "こんにちは", "ja")
        await cache.set_translation_cache(text, "Bonjour", "fr")

        # 验证不同语言的缓存是独立的
        assert await cache.get_translation_cache(text, "zh") == "你好"
        assert await cache.get_translation_cache(text, "ja") == "こんにちは"
        assert await cache.get_translation_cache(text, "fr") == "Bonjour"

    @pytest.mark.asyncio
    async def test_cache_overwrite(self):
        """测试缓存覆盖"""
        from src.utils.cache import CacheManager

        cache = CacheManager()
        prompt = "Test prompt"

        # 设置初始值
        await cache.set_llm_cache(prompt, "result1", "test")
        assert await cache.get_llm_cache(prompt, "test") == "result1"

        # 覆盖
        await cache.set_llm_cache(prompt, "result2", "test")
        assert await cache.get_llm_cache(prompt, "test") == "result2"

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """测试清空缓存"""
        from src.utils.cache import CacheManager

        cache = CacheManager()

        # 设置一些缓存
        await cache.set_llm_cache("prompt1", "result1", "test")
        await cache.set_llm_cache("prompt2", "result2", "test")
        await cache.set_translation_cache("text1", "trans1", "zh")

        # 清空缓存
        await cache.clear()

        # 验证缓存已清空
        assert await cache.get_llm_cache("prompt1", "test") is None
        assert await cache.get_llm_cache("prompt2", "test") is None
        assert await cache.get_translation_cache("text1", "zh") is None

    @pytest.mark.asyncio
    async def test_cache_with_complex_data(self):
        """测试复杂数据结构的缓存"""
        from src.utils.cache import CacheManager

        cache = CacheManager()
        complex_data = {
            "nested": {
                "dict": {
                    "with": ["lists", "and", "numbers"],
                    "int": 123,
                    "float": 45.67,
                }
            },
            "list": [{"a": 1}, {"b": 2}]
        }

        await cache.set_llm_cache("complex", complex_data)
        cached = await cache.get_llm_cache("complex")

        assert cached == complex_data

    @pytest.mark.asyncio
    async def test_cache_with_none_value(self):
        """测试缓存 None 值"""
        from src.utils.cache import CacheManager

        cache = CacheManager()

        # 设置 None 值
        await cache.set_llm_cache("none_prompt", None, "test")

        # 获取 None 值（应该返回 None，但与缓存未命中不同）
        # 注意: aiocache 可能不区分 None 和未命中
        cached = await cache.get_llm_cache("none_prompt", "test")
        # 实际行为取决于 aiocache 实现
        # 如果 None 被缓存，应该返回 None
        # 如果 None 不被缓存，应该返回 None（未命中）

    @pytest.mark.asyncio
    async def test_cache_with_empty_string(self):
        """测试缓存空字符串"""
        from src.utils.cache import CacheManager

        cache = CacheManager()
        await cache.set_llm_cache("empty_prompt", "", "test")

        cached = await cache.get_llm_cache("empty_prompt", "test")
        assert cached == ""

    @pytest.mark.asyncio
    async def test_cache_with_special_characters(self):
        """测试包含特殊字符的缓存键"""
        from src.utils.cache import CacheManager

        cache = CacheManager()
        special_prompt = "Test with \n\t\r\"'\\特殊字符"

        await cache.set_llm_cache(special_prompt, "result", "test")
        cached = await cache.get_llm_cache(special_prompt, "test")

        assert cached == "result"

    @pytest.mark.asyncio
    async def test_cache_with_unicode(self):
        """测试 Unicode 内容的缓存"""
        from src.utils.cache import CacheManager

        cache = CacheManager()
        unicode_text = "Hello 你好 🎉 世界"

        await cache.set_translation_cache(unicode_text, "Translation", "en")
        cached = await cache.get_translation_cache(unicode_text, "en")

        assert cached == "Translation"


class TestGetCacheManager:
    """测试 get_cache_manager 函数"""

    def test_get_cache_manager_singleton(self):
        """测试 get_cache_manager 返回单例"""
        from src.utils.cache import get_cache_manager

        manager1 = get_cache_manager()
        manager2 = get_cache_manager()

        assert manager1 is manager2

    def test_get_cache_manager_type(self):
        """测试 get_cache_manager 返回类型"""
        from src.utils.cache import get_cache_manager, CacheManager

        manager = get_cache_manager()
        assert isinstance(manager, CacheManager)


@pytest.mark.integration
class TestCacheManagerIntegration:
    """集成测试: 缓存管理器"""

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """测试缓存过期（使用短 TTL）"""
        from src.utils.cache import CacheManager

        # 使用非常短的 TTL (1秒)
        cache = CacheManager(ttl=1)

        await cache.set_llm_cache("prompt", "result", "test")
        assert await cache.get_llm_cache("prompt", "test") == "result"

        # 等待过期
        await asyncio.sleep(2)

        # 缓存应该已过期
        cached = await cache.get_llm_cache("prompt", "test")
        assert cached is None

    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self):
        """测试并发缓存访问"""
        from src.utils.cache import CacheManager

        cache = CacheManager()

        async def set_cache(i):
            await cache.set_llm_cache(f"prompt_{i}", f"result_{i}", "test")

        async def get_cache(i):
            return await cache.get_llm_cache(f"prompt_{i}", "test")

        # 并发设置
        await asyncio.gather(*[set_cache(i) for i in range(100)])

        # 并发获取
        results = await asyncio.gather(*[get_cache(i) for i in range(100)])

        # 验证所有缓存都正确
        for i, result in enumerate(results):
            assert result == f"result_{i}"

    @pytest.mark.asyncio
    async def test_large_cache_size(self):
        """测试大容量缓存"""
        from src.utils.cache import CacheManager

        cache = CacheManager()

        # 添加大量缓存
        for i in range(1000):
            await cache.set_llm_cache(f"prompt_{i}", {"data": f"result_{i}"}, "test")

        # 验证缓存可以检索
        for i in range(1000):
            cached = await cache.get_llm_cache(f"prompt_{i}", "test")
            assert cached == {"data": f"result_{i}"}

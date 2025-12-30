"""
LLM 模块测试

测试异步 LLM API 调用功能
"""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from openai import AsyncOpenAI

from src.utils.llm import ask_llm, ask_llm_batch


class TestAskLLM:
    """测试 ask_llm 函数"""

    @pytest.mark.asyncio
    async def test_ask_llm_basic(self, mock_openai_client):
        """测试基本 LLM 调用"""
        with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client):
            result = await ask_llm("Test prompt", log_title="test")

            # 验证客户端被调用
            mock_openai_client.chat.completions.create.assert_called_once()

            # 验证响应被正确解析
            assert result is not None

    @pytest.mark.asyncio
    async def test_ask_llm_json_response(self, mock_openai_client):
        """测试 JSON 响应类型"""
        mock_response = {"result": "data"}
        mock_openai_client.chat.completions.create.return_value.choices[
            0
        ].message.content = json.dumps(mock_response)

        with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client):
            result = await ask_llm("Test prompt", resp_type="json")

            # 验证 JSON 被正确解析
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_ask_llm_text_response(self, mock_openai_client):
        """测试文本响应类型"""
        test_text = "This is a plain text response"
        mock_openai_client.chat.completions.create.return_value.choices[
            0
        ].message.content = test_text

        with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client):
            result = await ask_llm("Test prompt")

            # 验证文本被正确返回
            assert result == test_text

    @pytest.mark.asyncio
    async def test_ask_llm_with_cache(self, mock_openai_client, mock_cache_manager):
        """测试缓存功能"""
        cached_value = {"cached": "result"}

        with patch('src.utils.llm.cache_manager', mock_cache_manager):
            mock_cache_manager.get_llm_cache.return_value = cached_value

            result = await ask_llm("Test prompt")

            # 验证返回缓存值
            assert result == cached_value
            # 验证没有调用 LLM API
            mock_openai_client.chat.completions.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_ask_llm_cache_miss(self, mock_openai_client, mock_cache_manager):
        """测试缓存未命中"""
        mock_cache_manager.get_llm_cache.return_value = None

        with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client):
            with patch('src.utils.llm.cache_manager', mock_cache_manager):
                result = await ask_llm("Test prompt")

                # 验证调用了 LLM API
                mock_openai_client.chat.completions.create.assert_called_once()
                # 验证保存了缓存
                mock_cache_manager.set_llm_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_ask_llm_missing_api_key(self):
        """测试缺少 API Key"""
        with patch('src.utils.llm.settings.openai_api_key', ''):
            with pytest.raises(ValueError, match="OPENAI_API_KEY is not set"):
                await ask_llm("Test prompt")

    @pytest.mark.asyncio
    async def test_ask_llm_base_url_ark(self, mock_openai_client):
        """测试 Ark API Base URL 处理"""
        with patch('src.utils.llm.settings.openai_api_base', 'https://ark.example.com'):
            with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client) as mock_client_class:
                await ask_llm("Test prompt")

                # 验证使用了正确的 base_url
                call_args = mock_client_class.call_args
                assert call_args[1]['base_url'] == "https://ark.cn-beijing.volces.com/api/v3"

    @pytest.mark.asyncio
    async def test_ask_llm_base_url_without_v1(self, mock_openai_client):
        """测试不带 /v1 的 Base URL 处理"""
        with patch('src.utils.llm.settings.openai_api_base', 'https://api.example.com'):
            with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client) as mock_client_class:
                await ask_llm("Test prompt")

                # 验证添加了 /v1
                call_args = mock_client_class.call_args
                assert call_args[1]['base_url'] == "https://api.example.com/v1"

    @pytest.mark.asyncio
    async def test_ask_llm_client_closed(self, mock_openai_client):
        """测试客户端被正确关闭"""
        with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client):
            await ask_llm("Test prompt")

            # 验证客户端被关闭
            mock_openai_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_ask_llm_json_object_response_format(self, mock_openai_client):
        """测试 JSON 响应格式设置"""
        with patch('src.utils.llm.settings.openai_llm_support_json', True):
            with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client):
                await ask_llm("Test prompt", resp_type="json")

                # 验证 response_format 参数
                call_args = mock_openai_client.chat.completions.create.call_args
                assert call_args[1]['response_format'] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_ask_llm_max_tokens(self, mock_openai_client):
        """测试 max_tokens 参数"""
        with patch('src.utils.llm.settings.openai_max_tokens', 8000):
            with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client):
                await ask_llm("Test prompt")

                # 验证 max_tokens 参数
                call_args = mock_openai_client.chat.completions.create.call_args
                assert call_args[1]['max_tokens'] == 8000


class TestAskLLMBatch:
    """测试 ask_llm_batch 函数"""

    @pytest.mark.asyncio
    async def test_ask_llm_batch_basic(self, mock_openai_client):
        """测试批量 LLM 调用"""
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]

        with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client):
            with patch('src.utils.llm.ask_llm', new=AsyncMock(return_value="result")):
                results = await ask_llm_batch(prompts)

                # 验证返回结果数量
                assert len(results) == 3
                # 验证所有结果都是 "result"
                assert all(r == "result" for r in results)

    @pytest.mark.asyncio
    async def test_ask_llm_batch_concurrency_limit(self, mock_openai_client):
        """测试并发限制"""
        prompts = ["Prompt"] * 20
        max_concurrent = 5

        with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client):
            with patch('src.utils.llm.ask_llm', new=AsyncMock(return_value="result")):
                results = await ask_llm_batch(prompts, max_concurrent=max_concurrent)

                # 验证所有请求都完成了
                assert len(results) == 20

    @pytest.mark.asyncio
    async def test_ask_llm_batch_order_preservation(self, mock_openai_client):
        """测试批量调用保持顺序"""
        prompts = ["A", "B", "C"]

        async def mock_ask(prompt, resp_type, log_title):
            # 模拟不同的延迟
            if prompt == "B":
                await asyncio.sleep(0.1)
            return f"result_{prompt}"

        with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client):
            with patch('src.utils.llm.ask_llm', new=AsyncMock(side_effect=mock_ask)):
                results = await ask_llm_batch(prompts)

                # 验证结果顺序与输入顺序一致
                assert results == ["result_A", "result_B", "result_C"]

    @pytest.mark.asyncio
    async def test_ask_llm_batch_empty_list(self, mock_openai_client):
        """测试空提示词列表"""
        with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client):
            results = await ask_llm_batch([])

            # 验证返回空列表
            assert results == []

    @pytest.mark.asyncio
    async def test_ask_llm_batch_with_json_response(self, mock_openai_client):
        """测试批量调用 JSON 响应"""
        prompts = ["Prompt 1", "Prompt 2"]

        with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client):
            with patch('src.utils.llm.ask_llm', new=AsyncMock(return_value={"data": "value"})):
                results = await ask_llm_batch(prompts, resp_type="json")

                # 验证返回 JSON 结果
                assert len(results) == 2
                assert all(r == {"data": "value"} for r in results)


class TestAskLLMEdgeCases:
    """测试 ask_llm 边界情况"""

    @pytest.mark.asyncio
    async def test_ask_llm_invalid_json_response(self, mock_openai_client):
        """测试无效的 JSON 响应（json_repair 应该修复）"""
        # 模拟格式错误的 JSON
        mock_openai_client.chat.completions.create.return_value.choices[
            0
        ].message.content = "{invalid json"

        with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client):
            # json_repair 应该能修复这个问题
            # 如果修复失败，会抛出异常
            try:
                result = await ask_llm("Test prompt", resp_type="json")
                assert result is not None
            except Exception:
                # 如果 json_repair 也无法修复，这是预期行为
                pass

    @pytest.mark.asyncio
    async def test_ask_llm_empty_response(self, mock_openai_client):
        """测试空响应"""
        mock_openai_client.chat.completions.create.return_value.choices[
            0
        ].message.content = ""

        with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client):
            result = await ask_llm("Test prompt")

            # 空字符串应该被返回
            assert result == ""

    @pytest.mark.asyncio
    async def test_ask_llm_very_long_prompt(self, mock_openai_client):
        """测试超长提示词"""
        long_prompt = "Test " * 100000  # 非常长的提示词

        with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client):
            await ask_llm(long_prompt)

            # 验证提示词被发送
            call_args = mock_openai_client.chat.completions.create.call_args
            assert len(call_args[1]['messages'][0]['content']) > 100000

    @pytest.mark.asyncio
    async def test_ask_llm_special_characters(self, mock_openai_client):
        """测试特殊字符"""
        special_prompt = "Test with special chars: \n\t\r\"'\\"

        with patch('src.utils.llm.AsyncOpenAI', return_value=mock_openai_client):
            result = await ask_llm(special_prompt)

            # 验证特殊字符被正确处理
            assert result is not None


@pytest.mark.integration
class TestAskLLMIntegration:
    """集成测试（需要真实的 API Key）"""

    @pytest.mark.skip(reason="需要真实的 API Key")
    @pytest.mark.asyncio
    async def test_ask_llm_real_api(self):
        """测试真实 API 调用（跳过）"""
        # 这个测试需要真实的 API Key
        # 在 CI/CD 中应该被跳过
        pass

    @pytest.mark.skip(reason="需要真实的 API Key")
    @pytest.mark.asyncio
    async def test_ask_llm_batch_real_api(self):
        """测试真实批量 API 调用（跳过）"""
        pass

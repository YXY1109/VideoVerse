"""
Prompt 模板测试

测试各种 AI Prompt 生成函数
"""
import json
import re
from unittest.mock import patch

import pytest


class TestSplitPrompt:
    """测试 get_split_prompt 函数"""

    def test_get_split_prompt_basic(self):
        """测试基本分割提示词"""
        from src.tools.prompts import get_split_prompt

        prompt = get_split_prompt("This is a test sentence", num_parts=2, word_limit=20)

        assert "This is a test sentence" in prompt
        assert "2" in prompt
        assert "20" in prompt
        assert "[br]" in prompt
        assert "split" in prompt.lower()

    def test_get_split_prompt_different_params(self):
        """测试不同参数"""
        from src.tools.prompts import get_split_prompt

        prompt = get_split_prompt("Short", num_parts=3, word_limit=5)

        assert "3" in prompt
        assert "5" in prompt
        assert "Short" in prompt

    def test_get_split_prompt_contains_json_format(self):
        """测试包含 JSON 格式说明"""
        from src.tools.prompts import get_split_prompt

        prompt = get_split_prompt("Test")

        assert "```json" in prompt
        assert "```" in prompt
        assert '"analysis"' in prompt
        assert '"split1"' in prompt
        assert '"split2"' in prompt
        assert '"choice"' in prompt

    def test_get_split_prompt_language_placeholder(self):
        """测试语言占位符"""
        from src.tools.prompts import get_split_prompt

        with patch('src.tools.prompts.load_key', return_value='en'):
            prompt = get_split_prompt("Test")
            assert "en" in prompt or "English" in prompt


class TestSummaryPrompt:
    """测试 get_summary_prompt 函数"""

    def test_get_summary_prompt_basic(self):
        """测试基本摘要提示词"""
        from src.tools.prompts import get_summary_prompt

        content = "This is the video content."
        prompt = get_summary_prompt(content)

        assert content in prompt
        assert "summarize" in prompt.lower()
        assert "terms" in prompt.lower()

    def test_get_summary_prompt_with_custom_terms(self):
        """测试带自定义术语的摘要提示词"""
        from src.tools.prompts import get_summary_prompt

        content = "Video content"
        custom_terms = {
            "terms": [
                {"src": "AI", "tgt": "人工智能", "note": "Artificial Intelligence"},
                {"src": "ML", "tgt": "机器学习", "note": "Machine Learning"}
            ]
        }

        prompt = get_summary_prompt(content, custom_terms)

        assert "AI: 人工智能" in prompt
        assert "ML: 机器学习" in prompt
        assert "Existing Terms" in prompt

    def test_get_summary_prompt_json_structure(self):
        """测试 JSON 结构"""
        from src.tools.prompts import get_summary_prompt

        prompt = get_summary_prompt("Test content")

        assert '"theme"' in prompt
        assert '"terms"' in prompt
        assert '"src"' in prompt
        assert '"tgt"' in prompt
        assert '"note"' in prompt

    def test_get_summary_prompt_example(self):
        """测试包含示例"""
        from src.tools.prompts import get_summary_prompt

        prompt = get_summary_prompt("Test")

        # 验证包含示例部分
        assert "## Example" in prompt or "example" in prompt.lower()


class TestTranslationPrompts:
    """测试翻译相关提示词"""

    def test_generate_shared_prompt(self):
        """测试生成共享提示词"""
        from src.tools.prompts import generate_shared_prompt

        previous = "Previous content"
        after = "After content"
        summary = "Summary text"
        notes = "Notes"

        prompt = generate_shared_prompt(previous, after, summary, notes)

        assert previous in prompt
        assert after in prompt
        assert summary in prompt
        assert notes in prompt
        assert "Context Information" in prompt

    def test_get_prompt_faithfulness_basic(self):
        """测试直译提示词"""
        from src.tools.prompts import get_prompt_faithfulness

        lines = "Line 1\nLine 2\nLine 3"
        shared = "Shared context"

        with patch('src.tools.prompts.load_key', return_value='en'):
            prompt = get_prompt_faithfulness(lines, shared)

            assert lines in prompt
            assert shared in prompt
            assert "faithful" in prompt.lower() or "faith" in prompt.lower()
            assert "direct" in prompt.lower()

    def test_get_prompt_faithfulness_json_format(self):
        """测试直译 JSON 格式"""
        from src.tools.prompts import get_prompt_faithfulness

        lines = "Line 1\nLine 2"
        shared = "Context"

        with patch('src.tools.prompts.load_key', return_value='en'):
            prompt = get_prompt_faithfulness(lines, shared)

            # 验证 JSON 结构
            assert '"1"' in prompt
            assert '"2"' in prompt
            assert '"origin"' in prompt
            assert '"direct"' in prompt

    def test_get_prompt_expressiveness_basic(self):
        """测试意译提示词"""
        from src.tools.prompts import get_prompt_expressiveness

        lines = "Line 1\nLine 2"
        faithfulness_result = {
            "1": {"origin": "Line 1", "direct": "Direct 1"},
            "2": {"origin": "Line 2", "direct": "Direct 2"}
        }
        shared = "Context"

        with patch('src.tools.prompts.load_key', return_value='en'):
            prompt = get_prompt_expressiveness(faithfulness_result, lines, shared)

            assert lines in prompt
            assert shared in prompt
            assert "express" in prompt.lower() or "free" in prompt.lower()
            assert '"reflect"' in prompt
            assert '"free"' in prompt

    def test_get_prompt_expressiveness_with_faithfulness_result(self):
        """测试意译包含直译结果"""
        from src.tools.prompts import get_prompt_expressiveness

        faithfulness_result = {
            "1": {"origin": "Original", "direct": "Direct translation"},
        }
        lines = "Original"
        shared = "Shared"

        with patch('src.tools.prompts.load_key', return_value='en'):
            prompt = get_prompt_expressiveness(faithfulness_result, lines, shared)

            assert "Direct translation" in prompt
            assert "reflect" in prompt.lower()


class TestAlignPrompt:
    """测试字幕对齐提示词"""

    def test_get_align_prompt_basic(self):
        """测试基本对齐提示词"""
        from src.tools.prompts import get_align_prompt

        src_sub = "Original subtitle"
        tr_sub = "Translated subtitle"
        src_part = "Part 1\nPart 2"

        with patch('src.tools.prompts.load_key', side_effect=['en', 'zh']):
            prompt = get_align_prompt(src_sub, tr_sub, src_part)

            assert src_sub in prompt
            assert tr_sub in prompt
            assert "Part 1" in prompt or "Part 2" in prompt
            assert "[br]" in prompt
            assert "align" in prompt.lower()

    def test_get_align_prompt_json_structure(self):
        """测试对齐 JSON 结构"""
        from src.tools.prompts import get_align_prompt

        src_part = "Part 1\nPart 2"

        with patch('src.tools.prompts.load_key', side_effect=['en', 'zh']):
            prompt = get_align_prompt("src", "tr", src_part)

            assert '"analysis"' in prompt
            assert '"align"' in prompt
            assert '"src_part_1"' in prompt
            assert '"target_part_1"' in prompt


class TestSubtitleTrimPrompt:
    """测试字幕修剪提示词"""

    def test_get_subtitle_trim_prompt_basic(self):
        """测试基本修剪提示词"""
        from src.tools.prompts import get_subtitle_trim_prompt

        text = "This is a very long subtitle that needs to be trimmed"
        duration = 5.0

        prompt = get_subtitle_trim_prompt(text, duration)

        assert text in prompt
        assert "5.0" in prompt or "5" in prompt
        assert "trim" in prompt.lower() or "shorten" in prompt.lower()

    def test_get_subtitle_trim_prompt_contains_rules(self):
        """测试包含修剪规则"""
        from src.tools.prompts import get_subtitle_trim_prompt

        prompt = get_subtitle_trim_prompt("Test text", 3.0)

        assert "Processing Rules" in prompt or "rules" in prompt.lower()
        assert "analysis" in prompt.lower()
        assert "result" in prompt.lower()

    def test_get_subtitle_trim_prompt_json_format(self):
        """测试修剪 JSON 格式"""
        from src.tools.prompts import get_subtitle_trim_prompt

        prompt = get_subtitle_trim_prompt("Test", 2.5)

        assert '"analysis"' in prompt
        assert '"result"' in prompt


class TestCorrectTextPrompt:
    """测试文本清理提示词"""

    def test_get_correct_text_prompt_basic(self):
        """测试基本清理提示词"""
        from src.tools.prompts import get_correct_text_prompt

        text = "Text with @#$% special characters!!!"
        prompt = get_correct_text_prompt(text)

        assert text in prompt
        assert "clean" in prompt.lower()
        assert "punctuation" in prompt.lower()

    def test_get_correct_text_prompt_json_format(self):
        """测试清理 JSON 格式"""
        from src.tools.prompts import get_correct_text_prompt

        prompt = get_correct_text_prompt("Test")

        assert '"text"' in prompt


class TestPromptFormat:
    """测试提示词格式"""

    def test_all_prompts_end_with_json_note(self):
        """测试所有提示词以 JSON 说明结尾"""
        from src.tools.prompts import (
            get_split_prompt,
            get_summary_prompt,
            get_align_prompt,
            get_subtitle_trim_prompt,
            get_correct_text_prompt,
        )

        prompts = [
            get_split_prompt("Test"),
            get_summary_prompt("Test content"),
            get_align_prompt("src", "tr", "part"),
            get_subtitle_trim_prompt("text", 5.0),
            get_correct_text_prompt("text"),
        ]

        for prompt in prompts:
            # 验证包含 JSON 格式说明
            assert "```json" in prompt or "json" in prompt.lower()
            # 验证包含结束标记说明
            assert "Note:" in prompt or "note:" in prompt.lower()

    def test_prompts_are_trimmed(self):
        """测试提示词没有多余空白"""
        from src.tools.prompts import get_split_prompt

        prompt = get_split_prompt("Test")
        assert prompt == prompt.strip()

    def test_prompts_contain_instructions(self):
        """测试提示词包含说明"""
        from src.tools.prompts import (
            get_split_prompt,
            get_summary_prompt,
            get_subtitle_trim_prompt,
        )

        prompts = [
            get_split_prompt("Test"),
            get_summary_prompt("Test"),
            get_subtitle_trim_prompt("Test", 5.0),
        ]

        for prompt in prompts:
            # 验证包含 "Role" 或 "Task"
            assert "Role" in prompt or "Task" in prompt or "role" in prompt.lower() or "task" in prompt.lower()


@pytest.mark.integration
class TestPromptsIntegration:
    """集成测试: Prompt 模板"""

    def test_prompt_load_key_integration(self):
        """测试 load_key 函数集成"""
        from src.tools.prompts import load_key

        # 测试各种 key
        result = load_key("whisper.detected_language")
        assert isinstance(result, str)

        result = load_key("target_language")
        assert isinstance(result, str)

    def test_prompt_language_context(self):
        """测试语言上下文"""
        from src.tools.prompts import get_split_prompt

        with patch('src.tools.prompts.load_key', return_value='zh'):
            prompt = get_split_prompt("测试句子")
            # 应该包含语言相关信息
            assert "zh" in prompt or "Chinese" in prompt or "中文" in prompt

    def test_prompt_length_reasonable(self):
        """测试提示词长度合理"""
        from src.tools.prompts import (
            get_split_prompt,
            get_summary_prompt,
            get_align_prompt,
        )

        prompts = [
            get_split_prompt("Test"),
            get_summary_prompt("Test content"),
            get_align_prompt("src", "tr", "part"),
        ]

        for prompt in prompts:
            # 提示词应该在合理范围内（100-5000 字符）
            assert 100 < len(prompt) < 5000, f"Prompt length {len(prompt)} is out of range"

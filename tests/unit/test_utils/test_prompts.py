"""Test prompts module functionality."""
from core.utils.prompts import (
    get_split_prompt,
    # Add other prompt functions as needed
)


def test_get_split_prompt_basic():
    """Test basic split prompt generation."""
    prompt = get_split_prompt("测试文本", num_parts=2, word_limit=20, language="zh")
    assert "测试文本" in prompt
    assert "zh" in prompt
    assert isinstance(prompt, str)
    assert "20" in prompt


def test_get_split_prompt_chinese():
    """Test split prompt for Chinese."""
    prompt = get_split_prompt("这是一个测试句子", num_parts=2, word_limit=15, language="zh")
    assert "这是一个测试句子" in prompt
    assert "15" in prompt
    assert "characters" in prompt.lower()


def test_get_split_prompt_english():
    """Test split prompt for English."""
    prompt = get_split_prompt("This is a test sentence", num_parts=2, word_limit=10, language="en")
    assert "This is a test sentence" in prompt
    assert "10" in prompt
    assert "words" in prompt.lower()


def test_get_split_prompt_custom_parts():
    """Test split prompt with custom number of parts."""
    prompt = get_split_prompt("测试", num_parts=3, word_limit=20, language="zh")
    assert "3" in prompt
    assert "part 3" in prompt.lower()


def test_split_prompt_json_format():
    """Test that prompt requests JSON format."""
    prompt = get_split_prompt("test", language="en")
    assert "json" in prompt.lower()
    assert "```json" in prompt

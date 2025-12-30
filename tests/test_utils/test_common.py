"""
通用工具函数测试

测试 common 模块的工具函数
"""
import pytest
from unittest.mock import patch


class TestGetJoiner:
    """测试 get_joiner 函数"""

    def test_english_language(self):
        """测试英语返回空格"""
        from src.utils.common import get_joiner

        result = get_joiner("en")
        assert result == " "

    def test_spanish_language(self):
        """测试西班牙语返回空格"""
        from src.utils.common import get_joiner

        result = get_joiner("es")
        assert result == " "

    def test_french_language(self):
        """测试法语返回空格"""
        from src.utils.common import get_joiner

        result = get_joiner("fr")
        assert result == " "

    def test_german_language(self):
        """测试德语返回空格"""
        from src.utils.common import get_joiner

        result = get_joiner("de")
        assert result == " "

    def test_italian_language(self):
        """测试意大利语返回空格"""
        from src.utils.common import get_joiner

        result = get_joiner("it")
        assert result == " "

    def test_russian_language(self):
        """测试俄语返回空格"""
        from src.utils.common import get_joiner

        result = get_joiner("ru")
        assert result == " "

    def test_chinese_language(self):
        """测试中文返回空字符串"""
        from src.utils.common import get_joiner

        result = get_joiner("zh")
        assert result == ""

    def test_japanese_language(self):
        """测试日语返回空字符串"""
        from src.utils.common import get_joiner

        result = get_joiner("ja")
        assert result == ""

    def test_unknown_language_defaults_to_space(self):
        """测试未知语言默认返回空格"""
        from src.utils.common import get_joiner

        result = get_joiner("unknown")
        assert result == " "

    def test_case_sensitivity(self):
        """测试大小写敏感（未知语言应该默认为空格）"""
        from src.utils.common import get_joiner

        # 大写语言代码应该不在配置列表中，返回默认空格
        result = get_joiner("EN")
        assert result == " "

        result = get_joiner("ZH")
        assert result == " "

    def test_language_with_dialect(self):
        """测试带方言的语言代码"""
        from src.utils.common import get_joiner

        # zh-CN 应该匹配 zh 配置（如果支持）
        # 否则返回默认空格
        result = get_joiner("zh-CN")
        # 当前实现可能不支持带方言的代码
        assert result == " "  # 默认行为

    def test_all_supported_languages(self):
        """测试所有支持的语言"""
        from src.utils.common import get_joiner
        from src.config import get_settings

        settings = get_settings()

        # 测试所有需要空格的语言
        for lang in settings.language_split_with_space:
            result = get_joiner(lang)
            assert result == " ", f"Language {lang} should return space"

        # 测试所有不需要空格的语言
        for lang in settings.language_split_without_space:
            result = get_joiner(lang)
            assert result == "", f"Language {lang} should return empty string"


class TestCommonUtils:
    """测试其他通用工具函数"""

    def test_settings_export(self):
        """测试 settings 被导出"""
        from src.utils.common import settings
        from src.config import get_settings

        global_settings = get_settings()
        assert settings is global_settings

    def test_all_exports(self):
        """测试 __all__ 导出"""
        from src.utils.common import __all__ as exports

        expected = ["get_joiner", "settings"]
        assert set(exports) == set(expected)


@pytest.mark.integration
class TestGetJoinerIntegration:
    """集成测试: get_joiner 函数"""

    def test_joiner_in_text_concatenation(self):
        """测试连接符在文本拼接中的使用"""
        from src.utils.common import get_joiner

        # 英语应该用空格连接
        joiner = get_joiner("en")
        words = ["Hello", "world"]
        result = joiner.join(words)
        assert result == "Hello world"

        # 中文不应该有空格
        joiner = get_joiner("zh")
        words = ["你好", "世界"]
        result = joiner.join(words)
        assert result == "你好世界"

    def test_joiner_with_configuration(self):
        """测试连接符与配置的一致性"""
        from src.utils.common import get_joiner
        from src.config import get_settings

        settings = get_settings()

        # 验证配置中的语言映射
        for lang in settings.language_split_with_space:
            assert get_joiner(lang) == " "

        for lang in settings.language_split_without_space:
            assert get_joiner(lang) == ""

"""
VideoVerse 通用工具函数

提供与旧 core.utils 兼容的接口
"""
from rich import print as rprint
from ..config import get_settings

settings = get_settings()


def get_joiner(language: str) -> str:
    """
    根据语言返回连接符

    Args:
        language: 语言代码

    Returns:
        连接符（空格或空字符串）
    """
    if language in settings.language_split_with_space:
        return " "
    elif language in settings.language_split_without_space:
        return ""
    else:
        # 默认英语等语言使用空格
        return " "


# 导出常用函数
__all__ = ["rprint", "get_joiner", "settings"]

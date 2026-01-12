def get_joiner(language: str) -> str:
    """
    根据语言返回连接符

    Args:
        language: 语言代码

    Returns:
        连接符（空格或空字符串）
    """
    if language in ["en", "es", "fr", "de", "it", "ru"]:
        return " "
    elif language in ["zh", "ja"]:
        return ""
    else:
        # 默认英语等语言使用空格
        return " "

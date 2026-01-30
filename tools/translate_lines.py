"""
三步翻译逻辑模块

提供直译 → 反思 → 意译的三步翻译流程。
从 temp/tools/translate_lines.py 迁移并转换为同步架构。

关键改进：
- 转换为同步架构
- 从 core.utils.llm 导入 ask_llm
- 保留两步翻译逻辑（直译 + 可选的意译）
- 添加类型注解
"""

from loguru import logger

from core.config import get_settings
from core.utils.llm import ask_llm
from tools.prompts import (
    generate_shared_prompt,
    get_prompt_expressiveness,
    get_prompt_faithfulness,
)

settings = get_settings()


def valid_translate_result(
    result: dict,
    required_keys: list,
    required_sub_keys: list,
) -> dict:
    """验证翻译结果格式。

    Args:
        result: LLM 返回的结果
        required_keys: 必需的顶层键
        required_sub_keys: 必需的子键

    Returns:
        验证结果 {"status": "success/error", "message": "..."}
    """
    # 检查必需的顶层键
    if not all(key in result for key in required_keys):
        return {
            "status": "error",
            "message": f"Missing required key(s): {', '.join(set(required_keys) - set(result.keys()))}"
        }

    # 检查所有项目中的必需子键
    for key in result:
        if not all(sub_key in result[key] for sub_key in required_sub_keys):
            return {
                "status": "error",
                "message": f"Missing required sub-key(s) in item {key}: {', '.join(set(required_sub_keys) - set(result[key].keys()))}"
            }

    return {"status": "success", "message": "Translation completed"}


def translate_lines(
    lines: str,
    previous_content_prompt: str | None,
    after_content_prompt: str | None,
    things_to_note_prompt: str | None,
    summary_prompt: str | None,
    src_language: str = "zh",
    target_language: str = "en",
    index: int = 0,
) -> tuple[str, str]:
    """翻译文本行（同步版本）。

    Args:
        lines: 待翻译的文本行（用 \\n 分隔）
        previous_content_prompt: 前文内容
        after_content_prompt: 后文内容
        things_to_note_prompt: 注意事项
        summary_prompt: 摘要内容
        src_language: 源语言代码
        target_language: 目标语言代码
        index: 批次索引（用于日志）

    Returns:
        (翻译结果, 原始文本)
    """
    shared_prompt = generate_shared_prompt(
        previous_content_prompt or "",
        after_content_prompt or "",
        summary_prompt or "",
        things_to_note_prompt or "",
    )

    # 重试逻辑
    def retry_translation(prompt: str, length: int, step_name: str) -> dict:
        """重试翻译直到成功。"""
        for retry in range(3):
            if step_name == "faithfulness":
                result = ask_llm(
                    prompt + " " * retry,
                    log_title=f"translate_{step_name}_{index}",
                )
                # 验证结果
                validation = valid_translate_result(
                    result,
                    [str(i) for i in range(1, length + 1)],
                    ["direct"]
                )
                if validation["status"] == "success" and len(result) == length:
                    return result
            elif step_name == "expressiveness":
                result = ask_llm(
                    prompt + " " * retry,
                    log_title=f"translate_{step_name}_{index}",
                )
                # 验证结果
                validation = valid_translate_result(
                    result,
                    [str(i) for i in range(1, length + 1)],
                    ["free"]
                )
                if validation["status"] == "success" and len(result) == length:
                    return result

            if retry < 2:
                logger.warning(f"{step_name.capitalize()} translation of block {index} failed, retrying...")

        raise ValueError(f"{step_name.capitalize()} translation of block {index} failed after 3 retries")

    # 步骤 1: 直译
    logger.info(f"Step 1: Faithfulness translation for block {index}")
    prompt1 = get_prompt_faithfulness(
        lines,
        shared_prompt,
        src_language,
        target_language,
    )
    faith_result = retry_translation(prompt1, len(lines.split("\n")), "faithfulness")

    # 清理直译结果
    for i in faith_result:
        faith_result[i]["direct"] = faith_result[i]["direct"].replace("\n", " ")

    # 如果不启用反思翻译，直接返回直译结果
    if not settings.reflect_translate:
        translate_result = "\n".join([faith_result[i]["direct"].strip() for i in faith_result])

        logger.info("Translation Results (Direct):")
        for i, key in enumerate(faith_result):
            logger.info(f"Origin:  {faith_result[key]['origin']}")
            logger.info(f"Direct:  {faith_result[key]['direct']}")
            if i < len(faith_result) - 1:
                logger.debug("-" * 50)

        return translate_result, lines

    # 步骤 2: 意译
    logger.info(f"Step 2: Expressiveness translation for block {index}")
    prompt2 = get_prompt_expressiveness(
        faith_result,
        lines,
        shared_prompt,
        src_language,
        target_language,
    )
    express_result = retry_translation(prompt2, len(lines.split("\n")), "expressiveness")

    logger.info("Translation Results (Reflected):")
    for i, key in enumerate(express_result):
        logger.info(f"Origin:  {faith_result[key]['origin']}")
        logger.info(f"Direct:  {faith_result[key]['direct']}")
        logger.info(f"Free:    {express_result[key]['free']}")
        if i < len(express_result) - 1:
            logger.debug("-" * 50)

    translate_result = "\n".join([express_result[i]["free"].replace("\n", " ").strip() for i in express_result])

    # 验证行数一致
    if len(lines.split("\n")) != len(translate_result.split("\n")):
        logger.error(f"Translation of block {index} failed, Length Mismatch")
        raise ValueError(f'Origin:\n{lines}\nbut got:\n{translate_result}')

    return translate_result, lines


# 测试代码
if __name__ == "__main__":
    # 示例
    lines = """All of you know Andrew Ng as a famous computer science professor at Stanford.
He was really early on in the development of neural networks with GPUs.
Of course, a creator of Coursera and popular courses like deeplearning.ai.
Also the founder and creator and early lead of Google Brain."""

    previous_content_prompt = None
    after_content_prompt = None
    things_to_note_prompt = None
    summary_prompt = None

    result, original = translate_lines(
        lines,
        previous_content_prompt,
        after_content_prompt,
        things_to_note_prompt,
        summary_prompt,
        src_language="en",
        target_language="zh",
    )

    print(f"Original:\n{original}")
    print(f"\nTranslated:\n{result}")

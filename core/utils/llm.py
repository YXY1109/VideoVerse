"""LLM API client for synchronous calls."""

from collections.abc import Sequence
from functools import lru_cache
from typing import Final

import json_repair
from loguru import logger
from openai import APIConnectionError, APIError, APIStatusError, APITimeoutError, OpenAI

from core.config import settings
from core.utils.cache import cache_manager

# 常量定义
_DEFAULT_TIMEOUT: Final = 300.0
_MAX_RETRIES: Final = 2


@lru_cache(maxsize=1)
def _get_openai_client() -> OpenAI:
    """获取缓存的 OpenAI 客户端单例。"""
    return OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base,
        max_retries=_MAX_RETRIES,
        timeout=_DEFAULT_TIMEOUT,
    )


def ask_llm(
    prompt: str,
    log_title: str = "default",
) -> dict:
    """
    同步调用 LLM API。

    Args:
        prompt: 提示词
        log_title: 日志标题（用于缓存键）

    Returns:
        LLM 响应内容

    Raises:
        APIError: API 调用失败
        APITimeoutError: 请求超时
        APIConnectionError: 连接失败
        APIStatusError: API 返回错误状态码
    """
    # 检查缓存
    cached = cache_manager.get_llm_cache(prompt, log_title)
    if cached is not None:
        logger.info(f"Using cached LLM response for {log_title}")
        return cached

    client = _get_openai_client()

    # 构建请求参数
    request_params = {
        "model": settings.openai_model,
        "messages": [{"role": "user", "content": prompt}],
    }
    if settings.openai_max_tokens is not None:
        request_params["max_tokens"] = settings.openai_max_tokens

    # 发起请求
    try:
        response = client.chat.completions.create(**request_params)
    except (APIError, APITimeoutError, APIConnectionError, APIStatusError) as e:
        logger.error(f"LLM API call failed for {log_title}: {e}")
        raise

    # 处理响应
    resp_content = response.choices[0].message.content or ""
    logger.success(f"LLM response for {log_title}: {resp_content}")
    result_dict = json_repair.loads(resp_content)
    # 保存缓存
    cache_manager.set_llm_cache(prompt, result_dict, log_title)
    return result_dict


def ask_llm_batch(
    prompts: Sequence[str],
    log_title: str = "batch",
    max_workers: int = 5,
) -> list[str]:
    """
    批量同步调用 LLM API（使用线程池）。

    Args:
        prompts: 提示词列表
        log_title: 日志标题（用作缓存键前缀）
        max_workers: 最大线程数

    Returns:
        按原始顺序排列的 LLM 响应内容列表
    """
    import concurrent.futures

    def call_with_index(prompt: str, index: int) -> tuple[int, dict]:
        result_dict = ask_llm(prompt, f"{log_title}_{index}")
        return index, result_dict

    results: list[tuple[int, str]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(call_with_index, prompt, i): i for i, prompt in enumerate(prompts)}
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    # 按原始顺序排序
    return [r for _, r in sorted(results, key=lambda x: x[0])]


if __name__ == "__main__":
    response_dict = ask_llm("你是谁", log_title="split_by_meaning")
    print(response_dict)

    # response_data_list = ask_llm_batch(["你是谁", "你好", "我爱你"], log_title="split_by_meaning")
    # print(response_data_list)

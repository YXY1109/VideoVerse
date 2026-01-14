"""
同步 LLM API 调用模块
"""
import json
import json_repair
from typing import Any, Optional
from openai import OpenAI

from src.config import get_settings
from src.utils.cache import get_cache_manager
from src.utils.decorators import async_except_handler

from loguru import logger

settings = get_settings()
cache_manager = get_cache_manager()


@async_except_handler("LLM request failed", max_retries=5)
def ask_llm(
    prompt: str,
    resp_type: Optional[str] = None,
    log_title: str = "default",
    valid_def: Optional[callable] = None,
) -> Any:
    """
    同步调用 LLM API

    Args:
        prompt: 提示词
        resp_type: 响应类型 ("json" 或其他)
        log_title: 日志标题（用于缓存键）
        valid_def: 验证函数，用于验证响应格式

    Returns:
        LLM 响应结果
    """
    # 检查 API Key
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    # 检查缓存
    cached = cache_manager.get_llm_cache(prompt, resp_type or log_title)
    if cached is not None:
        logger.info(f"Using cached LLM response for {log_title}")
        return cached

    # 构建 Base URL
    base_url = settings.openai_api_base
    if 'ark' in base_url:
        base_url = "https://ark.cn-beijing.volces.com/api/v3"
    elif 'v1' not in base_url:
        base_url = base_url.rstrip('/') + '/v1'

    # 创建同步客户端
    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=base_url,
    )

    # 构建请求参数
    response_format = {"type": "json_object"} if resp_type == "json" and settings.openai_llm_support_json else None
    messages = [{"role": "user", "content": prompt}]

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            response_format=response_format,
            max_tokens=settings.openai_max_tokens,
            timeout=300.0,
        )
    finally:
        client.close()

    # 处理响应
    resp_content = response.choices[0].message.content
    if resp_type == "json":
        result = json_repair.loads(resp_content)
    else:
        result = resp_content

    # 验证响应格式
    if valid_def is not None:
        validation_result = valid_def(result)
        if validation_result.get("status") == "error":
            raise ValueError(f"LLM response validation failed: {validation_result.get('message')}")

    # 保存缓存
    cache_manager.set_llm_cache(prompt, result, resp_type or log_title)

    return result


def ask_llm_batch(
    prompts: list[str],
    resp_type: Optional[str] = None,
    log_title: str = "batch",
    max_workers: int = 5,
) -> list[Any]:
    """
    批量同步调用 LLM API (使用线程池)

    Args:
        prompts: 提示词列表
        resp_type: 响应类型
        log_title: 日志标题
        max_workers: 最大线程数

    Returns:
        LLM 响应结果列表
    """
    import concurrent.futures

    def call_with_index(prompt: str, index: int) -> tuple[int, Any]:
        result = ask_llm(prompt, resp_type, f"{log_title}_{index}")
        return index, result

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(call_with_index, prompt, i) for i, prompt in enumerate(prompts)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]

    # 按原始顺序排序
    sorted_results = [r for _, r in sorted(results, key=lambda x: x[0])]
    return sorted_results

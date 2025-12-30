"""
异步 LLM API 调用模块

使用 httpx 替代 requests，支持异步调用和缓存
"""
import asyncio
import json
import json_repair
from typing import Any, Optional
import httpx
from openai import AsyncOpenAI

from src.config import get_settings
from src.utils.cache import get_cache_manager
from src.utils.decorators import async_except_handler
from src.utils.http import get_global_client

from loguru import logger

settings = get_settings()
cache_manager = get_cache_manager()


@async_except_handler("LLM request failed", max_retries=5)
async def ask_llm(
    prompt: str,
    resp_type: Optional[str] = None,
    log_title: str = "default",
) -> Any:
    """
    异步调用 LLM API

    Args:
        prompt: 提示词
        resp_type: 响应类型 ("json" 或其他)
        log_title: 日志标题（用于缓存键）

    Returns:
        LLM 响应结果
    """
    # 检查 API Key
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    # 检查缓存
    cached = await cache_manager.get_llm_cache(prompt, resp_type or log_title)
    if cached is not None:
        logger.info(f"Using cached LLM response for {log_title}")
        return cached

    # 构建 Base URL
    base_url = settings.openai_api_base
    if 'ark' in base_url:
        base_url = "https://ark.cn-beijing.volces.com/api/v3"
    elif 'v1' not in base_url:
        base_url = base_url.rstrip('/') + '/v1'

    # 创建异步客户端
    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=base_url,
    )

    # 构建请求参数
    response_format = {"type": "json_object"} if resp_type == "json" and settings.openai_llm_support_json else None
    messages = [{"role": "user", "content": prompt}]

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            response_format=response_format,
            max_tokens=settings.openai_max_tokens,
            timeout=300.0,
        )
    finally:
        await client.close()

    # 处理响应
    resp_content = response.choices[0].message.content
    if resp_type == "json":
        result = json_repair.loads(resp_content)
    else:
        result = resp_content

    # 保存缓存
    await cache_manager.set_llm_cache(prompt, result, resp_type or log_title)

    return result


async def ask_llm_batch(
    prompts: list[str],
    resp_type: Optional[str] = None,
    log_title: str = "batch",
    max_concurrent: int = 10,
) -> list[Any]:
    """
    批量异步调用 LLM API

    Args:
        prompts: 提示词列表
        resp_type: 响应类型
        log_title: 日志标题
        max_concurrent: 最大并发数

    Returns:
        LLM 响应结果列表
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def call_with_semaphore(prompt: str, index: int) -> tuple[int, Any]:
        async with semaphore:
            result = await ask_llm(prompt, resp_type, f"{log_title}_{index}")
            return index, result

    tasks = [call_with_semaphore(prompt, i) for i, prompt in enumerate(prompts)]
    results = await asyncio.gather(*tasks)

    # 按原始顺序排序
    sorted_results = [r for _, r in sorted(results, key=lambda x: x[0])]
    return sorted_results

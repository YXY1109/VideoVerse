import asyncio

import httpx

from src.config import get_settings

from loguru import logger
settings = get_settings()


async def synthesize(text: str, save_path: str, voice: str = None) -> None:
    """
    异步合成语音（Azure TTS）

    Args:
        text: 要转换的文本
        save_path: 保存路径
        voice: 音色（可选，默认使用配置）
    """
    if voice is None:
        voice = settings.azure_tts_voice

    url = "https://api.302.ai/cognitiveservices/v1"
    api_key = settings.azure_tts_api_key

    payload = f"""<speak version='1.0' xml:lang='zh-CN'><voice name='{voice}'>{text}</voice></speak>"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'X-Microsoft-OutputFormat': 'riff-16khz-16bit-mono-pcm',
        'Content-Type': 'application/ssml+xml'
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, content=payload)

    # 异步写入文件
    with open(save_path, 'wb') as f:
        f.write(response.content)

    logger.info(f"Audio saved to {save_path}")


def synthesize_sync(text: str, save_path: str, voice: str = None) -> None:
    """同步包装器（用于兼容）"""
    return asyncio.run(synthesize(text, save_path, voice))

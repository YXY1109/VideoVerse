import logging

import httpx

from ...config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def synthesize(text: str, save_path: str, voice: str = None) -> None:
    """
    异步合成语音（Fish TTS）

    Args:
        text: 要转换的文本
        save_path: 保存路径
        voice: 音色（可选）
    """
    url = "https://api.302.ai/fish-audio/v1/tts"
    api_key = settings.fish_tts_api_key

    headers = {'Authorization': f'Bearer {api_key}'}
    json_data = {
        "text": text,
        "character": voice or "AD学姐"
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=json_data)

    # Fish TTS 返回音频 URL，需要下载
    result = response.json()
    audio_url = result.get("audio_url")

    if audio_url:
        async with httpx.AsyncClient() as download_client:
            audio_response = await download_client.get(audio_url)
            with open(save_path, 'wb') as f:
                f.write(audio_response.content)

    logger.info(f"Audio saved to {save_path}")

from openai import AsyncOpenAI

from src.config import get_settings

from loguru import logger
settings = get_settings()


async def synthesize(text: str, save_path: str, voice: str = None) -> None:
    """
    异步合成语音（OpenAI TTS）

    Args:
        text: 要转换的文本
        save_path: 保存路径
        voice: 音色（可选，默认使用配置）
    """
    if voice is None:
        voice = settings.openai_tts_voice

    client = AsyncOpenAI(
        api_key=settings.openai_tts_api_key,
        base_url="https://api.302.ai/v1"
    )

    try:
        response = await client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )

        # 流式写入文件
        with open(save_path, 'wb') as f:
            async for chunk in response.iter_bytes():
                f.write(chunk)

        logger.info(f"Audio saved to {save_path}")
    finally:
        await client.close()

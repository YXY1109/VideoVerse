import asyncio

import httpx

from src.config import get_settings

from loguru import logger
settings = get_settings()

GPT_SOVITS_HOST = "http://127.0.0.1:9880"


async def _ensure_server_running() -> None:
    """确保 GPT-SoVITS 服务器正在运行"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{GPT_SOVITS_HOST}/ping")
        if response.status_code != 200:
            raise RuntimeError("GPT-SoVITS server not responding")
    except Exception:
        # 启动服务器（Windows）
        import subprocess
        subprocess.Popen(
            ["python", "api.py"],
            cwd="core/tts_backend/GPT-SoVITS/api",
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        # 等待服务器启动
        for _ in range(50):
            await asyncio.sleep(1)
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{GPT_SOVITS_HOST}/ping")
                if response.status_code == 200:
                    break
            except:
                continue
        else:
            raise RuntimeError("Failed to start GPT-SoVITS server")


async def synthesize(text: str, save_path: str, reference_audio: str = None) -> None:
    """
    异步合成语音（GPT-SoVITS）

    Args:
        text: 要转换的文本
        save_path: 保存路径
        reference_audio: 参考音频路径（可选）
    """
    await _ensure_server_running()

    url = f"{GPT_SOVITS_HOST}/tts"
    data = {
        "text": text,
        "text_language": "auto",
    }

    if reference_audio:
        data["refer_audio_path"] = reference_audio

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=data)

    with open(save_path, 'wb') as f:
        f.write(response.content)

    logger.info(f"Audio saved to {save_path}")

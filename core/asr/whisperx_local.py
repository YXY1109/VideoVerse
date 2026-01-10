
from pathlib import Path

# import librosa
# import torch
import whisperx
from loguru import logger
from huggingface_hub import snapshot_download




def ensure_model_exists(model_name: str, model_cache_dir: str) -> str:
    """确保 WhisperX 模型已在缓存中，如果不存在则下载。

    Args:
        model_name: 模型名称，如 "large-v3" 或 "Huan69/Belle-whisper-large-v3-zh-punct-fasterwhisper"
        model_cache_dir: 模型缓存目录路径

    Returns:
        str: HuggingFace 返回 model_name，OpenAI 返回本地路径
    """
    if "/" in model_name:
        # HuggingFace 模型
        org, repo = model_name.split("/", 1)
        snapshot_path = Path(model_cache_dir) / f"models--{org}--{repo}" / "snapshots"
        model_exists = snapshot_path.exists() and any(snapshot_path.iterdir())

        if model_exists:
            snapshot_dir = next(snapshot_path.iterdir())
            logger.info(f"Found cached HuggingFace model at: {snapshot_dir}")
        else:
            # 模型不存在，使用 snapshot_download 下载
            logger.info(f"Model '{model_name}' not found in cache, downloading...")
            logger.info(f"Cache directory: {model_cache_dir}")

            snapshot_download(
                repo_id=model_name,
                cache_dir=model_cache_dir,
                resume_download=True,
            )
            logger.info(f"Model '{model_name}' downloaded successfully")
        # 返回 model_name 让 whisperx.load_model 处理
        return model_name
    else:
        # OpenAI 模型 (如 large-v3)
        # faster-whisper 存储格式: {model_cache_dir}/{model_name}/
        model_path = Path(model_cache_dir) / model_name
        required_files = ["config.json", "model.bin", "vocabulary.txt"]

        # 检查所有必需文件是否存在
        all_files_exist = all((model_path / f).exists() for f in required_files)

        if all_files_exist:
            logger.info(f"Found cached OpenAI model at: {model_path}")
            return str(model_path)

        # 模型不完整，需要下载
        logger.info(f"OpenAI model '{model_name}' not found in cache, downloading...")
        logger.info(f"Cache directory: {model_cache_dir}")

        # 创建缓存目录
        model_path.mkdir(parents=True, exist_ok=True)

        # 使用 faster-whisper 的 download_model
        from faster_whisper import download_model

        download_path = download_model(model_name, output_dir=str(model_path))
        logger.info(f"Model downloaded to: {download_path}")
        return str(download_path)


def transcribe_audio(raw_audio_file, vocal_audio_file, start, end):
    whisper_language = "zh"
    model_cache_dir = str(Path(__file__).parent.parent.parent / "models")
    model_name = "Huan69/Belle-whisper-large-v3-zh-punct-fasterwhisper" if whisper_language == 'zh' else "large-v3"

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        batch_size = 16 if gpu_mem > 8 else 2
        compute_type = "float16" if torch.cuda.is_bf16_supported() else "int8"
        logger.info(f"GPU memory: {gpu_mem:.2f} GB, Batch size: {batch_size}, Compute type: {compute_type}")
    else:
        batch_size = 1
        compute_type = "int8"
        logger.info(f"Batch size: {batch_size}, Compute type: {compute_type}")
    logger.info(f"Starting WhisperX for segment {start:.2f}s to {end:.2f}s")

    vad_options = {"vad_onset": 0.500, "vad_offset": 0.363}
    asr_options = {"temperatures": [0], "initial_prompt": ""}

    # 确保模型已下载，并获取本地路径
    local_model_path = ensure_model_exists(model_name, model_cache_dir)

    logger.info(f"Loading WhisperX model: {model_name}")
    model = whisperx.load_model(local_model_path, device, compute_type=compute_type, language=whisper_language,
                                vad_options=vad_options, asr_options=asr_options, download_root=model_cache_dir)

    def load_audio_segment(audio_file, start, end):
        audio, _ = librosa.load(audio_file, sr=16000, offset=start, duration=end - start, mono=True)
        return audio

    raw_audio_segment = load_audio_segment(raw_audio_file, start, end)
    vocal_audio_segment = load_audio_segment(vocal_audio_file, start, end)


if __name__ == '__main__':
    whisper_language = "zh1"
    model_cache_dir = str(Path(__file__).parent.parent.parent / "models")
    model_name = "Huan69/Belle-whisper-large-v3-zh-punct-fasterwhisper" if whisper_language == 'zh' else "large-v3"
    model_path = ensure_model_exists(model_name, model_cache_dir)
    print(f"Model path: {model_path}")

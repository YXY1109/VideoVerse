import os
import time
from pathlib import Path

import librosa
import torch
import whisperx
from huggingface_hub import snapshot_download
from loguru import logger
from whisperx.alignment import DEFAULT_ALIGN_MODELS_HF

# weights_only bug https://github.com/m-bain/whisperX/issues/1304
os.environ["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "true"


def setup_huggingface_cache(cache_dir: str) -> None:
    """设置 HuggingFace 缓存目录环境变量，确保模型直接存储在指定根目录下。
    模型目录格式: {cache_dir}/models--{org}--{repo}/
    """
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    # 直接设置为根目录，模型将存储为: models/models--xxx--xxx/snapshots/...
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(cache_path)
    os.environ["HF_HUB_CACHE"] = str(cache_path)
    logger.info(f"HuggingFace cache directory set to: {cache_path}")
    logger.info(f"Models will be stored as: {cache_path}/models--org--repo/snapshots/")


model_cache_dir = r"D:\PycharmProjects\VideoVerse\models"

# 在加载模型前设置 HuggingFace 缓存目录（必须在使用 whisperx 前调用）
setup_huggingface_cache(model_cache_dir)


# Fix encoding for Chinese text (faster-whisper bug)
def fix_text_encoding(text: str) -> str:
    """修复 faster-whisper 输出的乱码中文"""
    if not text or any("\u4e00" <= c <= "\u9fff" for c in text):
        return text

    # 尝试常见的编码修复
    for enc in ["latin-1", "iso-8859-1", "cp1252", "gbk", "gb2312"]:
        try:
            fixed = text.encode(enc).decode("utf-8")
            if any("\u4e00" <= c <= "\u9fff" for c in fixed):
                return fixed
        except (UnicodeError, LookupError):
            continue
    return text


def ensure_model_exists(model_name: str, model_cache_dir: str) -> str:
    """确保模型已下载（如不存在则自动下载），返回模型路径。

    Args:
        model_name: 模型名称，如 "large-v3" 或 "Huan69/Belle-whisper-large-v3-zh-punct-fasterwhisper"
        model_cache_dir: 模型缓存目录路径

    Returns:
        str: HuggingFace 模型返回 model_name，OpenAI 模型返回本地路径
    """
    if "/" in model_name:
        # HuggingFace 模型：snapshot_download 自动处理缓存，无需手动检查
        logger.info(f"Ensuring HuggingFace model '{model_name}' is available...")
        snapshot_download(repo_id=model_name, cache_dir=model_cache_dir)
        return model_name
    else:
        # OpenAI 模型 (如 large-v3)
        model_path = Path(model_cache_dir) / model_name
        required_files = ["config.json", "model.bin", "vocabulary.txt"]

        if all((model_path / f).exists() for f in required_files):
            logger.info(f"Found cached OpenAI model at: {model_path}")
            return str(model_path)

        logger.info(f"Downloading OpenAI model '{model_name}'...")
        model_path.mkdir(parents=True, exist_ok=True)

        from faster_whisper import download_model

        download_path = download_model(model_name, output_dir=str(model_path))
        logger.info(f"Model downloaded to: {download_path}")
        return str(download_path)


def transcribe_audio(raw_audio_file, vocal_audio_file, start, end):
    whisper_language = "zh"
    model_cache_dir = str(Path(__file__).parent.parent.parent / "models")

    # 在加载模型前设置 HuggingFace 缓存目录
    setup_huggingface_cache(model_cache_dir)

    model_name = "Huan69/Belle-whisper-large-v3-zh-punct-fasterwhisper" if whisper_language == "zh" else "large-v3"

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
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
    model = whisperx.load_model(
        local_model_path,
        device,
        compute_type=compute_type,
        language=whisper_language,
        vad_options=vad_options,
        asr_options=asr_options,
        download_root=model_cache_dir,
    )

    def load_audio_segment(audio_file, start, end):
        audio, _ = librosa.load(audio_file, sr=16000, offset=start, duration=end - start, mono=True)
        return audio

    raw_audio_segment = load_audio_segment(raw_audio_file, start, end)
    vocal_audio_segment = load_audio_segment(vocal_audio_file, start, end)

    # 语音转文本，比较耗时
    transcribe_start_time = time.time()
    logger.info("Starting transcribe (you will see progress bar)...")
    result = model.transcribe(raw_audio_segment, batch_size=batch_size, print_progress=True)
    transcribe_time = time.time() - transcribe_start_time
    logger.info(f"Transcribe time: {transcribe_time:.2f}s")

    # Free GPU resources
    del model
    torch.cuda.empty_cache()

    # 对齐
    align_start_time = time.time()
    # 预下载 alignment 模型（使用镜像）

    # 确保模型已下载，并获取本地路径
    model_name = DEFAULT_ALIGN_MODELS_HF.get(result["language"])
    local_model_path = ensure_model_exists(model_name, model_cache_dir)
    logger.success(f"对齐模型地址：{local_model_path}")
    # Align timestamps using vocal audio
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(
        result["segments"], model_a, metadata, vocal_audio_segment, device, return_char_alignments=False
    )

    align_time = time.time() - align_start_time
    logger.info(f"Align time: {align_time:.2f}s")

    # Free GPU resources again
    torch.cuda.empty_cache()
    del model_a

    # Adjust timestamps and fix encoding
    for segment in result["segments"]:
        segment["start"] += start
        segment["end"] += start
        for word in segment["words"]:
            if "start" in word:
                word["start"] += start
            if "end" in word:
                word["end"] += start
            # 修复单词文本的编码问题
            if "word" in word:
                word["word"] = fix_text_encoding(word["word"])
    return result


if __name__ == "__main__":
    raw_audio_file = r"D:\\PycharmProjects\\VideoVerse\\files\\demo\\demo_vocals_normalized.mp3"
    vocal_audio_file = r"D:\\PycharmProjects\\VideoVerse\\files\\demo\\demo_vocals.mp3"
    result = transcribe_audio(raw_audio_file, vocal_audio_file, 0, 364.852245)
    print(result)

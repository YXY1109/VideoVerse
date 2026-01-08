import torch
from loguru import logger


def transcribe_audio(raw_audio_file, vocal_audio_file, start, end):
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

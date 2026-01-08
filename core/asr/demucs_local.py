import os
import subprocess
import sys

from loguru import logger
from pydub import AudioSegment


def demucs_audio(input_audio: str) -> str:
    # python路径
    python_exe = sys.executable
    # todo 文件名称，有些文件名有特殊字符，需要处理
    audio_name = os.path.splitext(os.path.basename(input_audio))[0]
    # 人声分离后的文件名
    vocals_audio_name = audio_name + "_vocals.mp3"
    # 文件目录
    audio_dir = os.path.dirname(input_audio)
    # 保存人声路径
    output_path = os.path.join(audio_dir, vocals_audio_name)
    if os.path.exists(output_path):
        logger.warning(f"Demucs already exists:{output_path}")
        return output_path
    subprocess.run([
        python_exe, '-m', 'demucs.separate',
        '-n', 'htdemucs',
        '--two-stems', 'vocals',
        '--mp3',
        '--out', str(audio_dir),
        str(input_audio)
    ], check=True)
    # 人声输出路径
    demucs_vocals_path = os.path.join(audio_dir, "htdemucs", audio_name, "vocals.mp3")
    logger.success(f"Demucs complete:{demucs_vocals_path}")
    # 将demucs_vocals文件移动到output_path
    os.rename(demucs_vocals_path, output_path)
    return output_path


def normalize_audio_volume(audio_path: str, target_db: float = -20.0) -> str:
    """标准化音频音量"""
    name, ext = os.path.splitext(audio_path)
    output_path = name + "_normalized" + ext
    if os.path.exists(output_path):
        logger.warning(f"Normalized audio already exists: {output_path}")
        return output_path

    audio = AudioSegment.from_file(audio_path)
    change_in_dbfs = target_db - audio.dBFS
    normalized_audio = audio.apply_gain(change_in_dbfs)
    normalized_audio.export(output_path, format=ext[1:])
    logger.success(f"Audio normalized from {audio.dBFS:.1f}dB to {target_db:.1f}dB")
    return output_path

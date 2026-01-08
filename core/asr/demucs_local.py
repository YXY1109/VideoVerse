import os
import subprocess
import sys

from loguru import logger


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

    # 人声输出路径
    demucs_vocals_path = os.path.join(audio_dir, "htdemucs", audio_name, "vocals.mp3")
    if os.path.exists(demucs_vocals_path):
        logger.success(f"Demucs already exists:{demucs_vocals_path}")
    else:
        subprocess.run([
            python_exe, '-m', 'demucs.separate',
            '-n', 'htdemucs',
            '--two-stems', 'vocals',
            '--mp3',
            '--out', str(audio_dir),
            str(input_audio)
        ], check=True)
        logger.success(f"Demucs complete:{demucs_vocals_path}")
    # 将demucs_vocals文件移动到output_path
    os.rename(demucs_vocals_path, output_path)
    return output_path

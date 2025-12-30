"""
ASR 后端模块

包含各种语音识别后端
"""
from . import whisperx_api
from . import whisperx_local
from . import elevenlabs

__all__ = ["whisperx_api", "whisperx_local", "elevenlabs"]

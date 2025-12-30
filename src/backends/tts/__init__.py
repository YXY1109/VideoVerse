"""
TTS 后端模块

包含各种文本转语音后端
"""
from . import azure
from . import openai
from . import edge
from . import fish
from . import gpt_sovits

__all__ = ["azure", "openai", "edge", "fish", "gpt_sovits"]

"""
VideoVerse - AI 视频翻译和配音工具

此模块在包导入时尽早设置环境变量，以消除第三方库的警告。
"""
import os
import sys
import warnings

# 必须在导入任何 torch/torchaudio 相关模块之前设置
os.environ["TORCHAUDIO_USE_BACKEND_DISPATCHER"] = "1"

# 过滤 TorchAudio 全局 backend 废弃警告（多种模式确保覆盖）
warnings.filterwarnings("ignore", message=".*TorchAudio.*global backend.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*torchaudio.*backend.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*torchaudio._backend.*", category=UserWarning)
warnings.filterwarnings("ignore", module="demucs.*", category=UserWarning)
# 过滤 pyannote.audio 和 speechbrain 弃用警告
warnings.filterwarnings("ignore", message=".*speechbrain.pretrained.*deprecated.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*torchaudio.backend.common.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*AudioMetaData.*", category=UserWarning)
warnings.filterwarnings("ignore", module="pyannote.*", category=UserWarning)

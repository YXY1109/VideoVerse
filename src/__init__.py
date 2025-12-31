"""
VideoVerse - AI 视频翻译和配音工具

此模块在包导入时尽早设置环境变量和警告过滤，以消除第三方库的警告。
这是 Python 最佳实践：在包级别集中管理所有警告过滤，确保在整个应用生命周期中生效。

设计原则：
1. 尽早执行：在 __init__.py 中执行，确保在任何子模块导入前生效
2. 集中管理：所有警告过滤集中在一处，便于维护和审计
3. 精确匹配：使用 message/module 参数精确定位警告，避免过度抑制
"""
import os
import sys
import warnings
from io import StringIO
from contextlib import redirect_stdout

# =============================================================================
# 环境变量配置
# =============================================================================

# 必须在导入任何 torch/torchaudio 相关模块之前设置
# 解决 TorchAudio 2.1+ 的 backend dispatcher 弃用警告
os.environ["TORCHAUDIO_USE_BACKEND_DISPATCHER"] = "1"


# =============================================================================
# 警告过滤集中管理
# =============================================================================
# 最佳实践：在包导入时尽早执行警告过滤，确保所有子模块生效
# 参考：https://docs.python.org/3/library/warnings.html#the-warnings-module

# -----------------------------------------------------------------------------
# 1. TorchAudio/Demucs/Pyannote/SpeechBrain 相关警告
# -----------------------------------------------------------------------------
# 这些警告源于 PyTorch 2.1+ 与 TorchAudio 2.1+ 之间的兼容性问题
# 以及 Demucs/Pyannote/SpeechBrain 依赖的旧版 API

warnings.filterwarnings("ignore", message=".*TorchAudio.*global backend.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*torchaudio.*backend.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*torchaudio._backend.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*torchaudio.backend.common.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*AudioMetaData.*", category=UserWarning)
warnings.filterwarnings("ignore", module="demucs.*", category=UserWarning)
warnings.filterwarnings("ignore", module="pyannote.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*speechbrain.pretrained.*deprecated.*", category=UserWarning)

# -----------------------------------------------------------------------------
# 2. pkg_resources 废弃警告
# -----------------------------------------------------------------------------
# jieba 等库仍在使用已废弃的 pkg_resources（迁移到 importlib.metadata）
# 这是第三方库的遗留问题，暂时忽略
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

# -----------------------------------------------------------------------------
# 3. FutureWarning (Spacy/Pandas 等库)
# -----------------------------------------------------------------------------
# 这些库会发出 FutureWarning，提示未来版本的 API 变更
# 对于当前稳定版本，这些警告不影响功能
warnings.filterwarnings("ignore", category=FutureWarning)

# -----------------------------------------------------------------------------
# 4. WhisperX 相关警告
# -----------------------------------------------------------------------------
# WhisperX 和 faster-whisper 在处理音频时可能产生各种警告
# 这些警告通常不影响 ASR 结果，为保持输出整洁而忽略
warnings.filterwarnings("ignore", module="whisperx.*")
warnings.filterwarnings("ignore", module="faster_whisper.*")


# =============================================================================
# 特殊库预初始化（必须在所有子模块导入前执行）
# =============================================================================

# -----------------------------------------------------------------------------
# jieba 分词预初始化
# -----------------------------------------------------------------------------
# 问题：jieba 在首次使用时会输出 "Building prefix dict..." 等信息到 stdout
# 解决：在包导入时预先初始化 jieba，并使用 redirect_stdout 抑制输出
# 效果：后续使用 jieba 时不会再显示初始化信息
# 注意：必须尽早执行，确保在其他任何模块导入 jieba 之前完成
try:
    import jieba
    with redirect_stdout(StringIO()):
        jieba.lcut("初始化")
except ImportError:
    pass  # jieba 未安装，跳过

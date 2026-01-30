"""VideoVerse core modules.

提供流水线框架、配置管理、路径管理、工具函数等核心功能。
"""

# 配置管理
from core.config import Settings, get_settings, settings

# 路径管理
from core.paths import PathManager, paths

# 流水线框架
from core.pipeline import PipelineContext, PipelineEngine, PipelineStep, StepRegistry

# TTS 后端
from core.tts import (
    AzureTTSBackend,
    EdgeTTSBackend,
    FishTTSBackend,
    GPTSoVITSBackend,
    OpenAITTSBackend,
    TTSBackend,
    create_azure_backend,
    create_edge_backend,
    create_fish_backend,
    create_gpt_sovits_backend,
    create_openai_backend,
)

# 流水线步骤
from core.steps import ASRStep, DownloadStep, create_asr_step, create_download_step

# 工具函数
from core.utils.cache import CacheManager, cache_manager, get_cache_manager
from core.utils.common import get_joiner
from core.utils.decorators import async_check_file_exists, async_except_handler
from core.utils.llm import ask_llm, ask_llm_batch

# Prompts - 从 core.utils.prompts 导入基础函数
from core.utils.prompts import get_split_prompt, get_summary_prompt

# Prompts - 从 tools.prompts 导入完整函数（如果 tools 可用）
try:
    from tools.prompts import (
        get_align_prompt,
        get_correct_text_prompt,
        get_prompt_expressiveness,
        get_prompt_faithfulness,
        get_subtitle_trim_prompt,
    )
except ImportError:
    # tools 模块不可用时的占位符
    get_align_prompt = None
    get_correct_text_prompt = None
    get_prompt_expressiveness = None
    get_prompt_faithfulness = None
    get_subtitle_trim_prompt = None

__all__ = [
    # 配置
    "Settings",
    "get_settings",
    "settings",
    # 路径
    "PathManager",
    "paths",
    # 流水线
    "PipelineContext",
    "PipelineEngine",
    "PipelineStep",
    "StepRegistry",
    # TTS
    "TTSBackend",
    "EdgeTTSBackend",
    "AzureTTSBackend",
    "OpenAITTSBackend",
    "FishTTSBackend",
    "GPTSoVITSBackend",
    "create_edge_backend",
    "create_azure_backend",
    "create_openai_backend",
    "create_fish_backend",
    "create_gpt_sovits_backend",
    # 步骤
    "DownloadStep",
    "create_download_step",
    "ASRStep",
    "create_asr_step",
    # 工具
    "get_cache_manager",
    "cache_manager",
    "CacheManager",
    "get_joiner",
    "async_except_handler",
    "async_check_file_exists",
    "ask_llm",
    "ask_llm_batch",
    # Prompts
    "get_split_prompt",
    "get_summary_prompt",
    "get_prompt_faithfulness",
    "get_prompt_expressiveness",
    "get_align_prompt",
    "get_subtitle_trim_prompt",
    "get_correct_text_prompt",
]

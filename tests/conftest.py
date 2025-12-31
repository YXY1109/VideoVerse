"""
pytest 配置和共享 fixtures

提供测试所需的各种 mock 和 fixture
"""
import os

# 在导入任何 src 模块之前禁用 .env 文件加载
# 这必须在任何其他导入之前完成
os.environ["DOTENV_DISABLED"] = "1"

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pandas as pd
import pytest
import pytest_asyncio
from openai import AsyncOpenAI
from pydantic import ValidationError

from src.config import Settings, get_settings


# ==================== pytest 配置钩子 ====================

def pytest_configure(config):
    """
    在 pytest 启动时配置环境

    这个钩子在任何测试运行之前执行，用于设置测试环境
    """
    # 确保禁用 .env 文件加载（双重保险）
    os.environ["DOTENV_DISABLED"] = "1"

    # 设置 TorchAudio 后端调度器（消除 Demucs 警告）
    os.environ["TORCHAUDIO_USE_BACKEND_DISPATCHER"] = "1"

    # 过滤 TorchAudio 全局 backend 废弃警告
    import warnings
    warnings.filterwarnings("ignore", message=".*TorchAudio.*global backend.*", category=UserWarning)
    warnings.filterwarnings("ignore", message=".*torchaudio.*backend.*", category=UserWarning)
    warnings.filterwarnings("ignore", module="demucs.*", category=UserWarning)

    # 注册 pytest 标记
    config.addinivalue_line("markers", "asyncio: mark test as an async test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "skip_ci: skip test in CI environment")


# ==================== 自动清理环境变量 ====================

@pytest.fixture(autouse=True, scope="function")
def clean_env_vars(request, monkeypatch) -> None:
    """
    自动清理环境变量，确保测试在干净环境中运行

    这个 fixture 会自动应用于所有测试
    注意：会跳过标记了需要特定环境变量的测试
    """
    # 跳过某些需要特定环境变量的测试
    skip_clean = request.node.get_closest_marker("skip_env_clean")
    if skip_clean:
        return

    # 清除可能影响测试的环境变量
    env_keys_to_remove = [
        "OPENAI_API_KEY", "OPENAI_API_BASE", "OPENAI_MODEL",
        "WHISPER_RUNTIME", "WHISPER_MODEL", "WHISPER_LANGUAGE",
        "TTS_METHOD", "AZURE_TTS_VOICE", "EDGE_TTS_VOICE",
        "TARGET_LANGUAGE", "DEMUCS", "BURN_SUBTITLES",
        "YOUTUBE_RESOLUTION", "FFMPEG_GPU",
        "OPENAI_MAX_TOKENS", "SUBTITLE_MAX_LENGTH",
        "MAX_WORKERS", "SPEED_FACTOR_MIN", "SPEED_FACTOR_MAX",
    ]
    for key in env_keys_to_remove:
        monkeypatch.delenv(key, raising=False)


# ==================== 异步事件循环配置 ====================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建整个测试会话的事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def async_runner() -> Generator:
    """提供异步测试运行器"""

    def run_async(coro):
        return asyncio.run(coro)

    yield run_async


# ==================== 配置相关 fixtures ====================

@pytest.fixture
def mock_settings() -> Settings:
    """模拟配置对象"""
    # 使用 validation_alias 的名称作为参数
    return Settings(
        OPENAI_API_KEY="test_api_key",
        OPENAI_API_BASE="https://api.openai.com/v1",
        OPENAI_MODEL="gpt-4o",
        OPENAI_LLM_SUPPORT_JSON=True,
        OPENAI_MAX_TOKENS=16384,
        WHISPER_RUNTIME="local",
        WHISPER_MODEL="large-v3",
        WHISPER_LANGUAGE="zh",
        TTS_METHOD="edge",
        EDGE_TTS_VOICE="zh-CN-XiaoxiaoNeural",
        TARGET_LANGUAGE="en",
        DEMUCS=False,
        BURN_SUBTITLES=False,
        YOUTUBE_RESOLUTION="720",
        FFMPEG_GPU=False,
        SUBTITLE_MAX_LENGTH=75,
        SUBTITLE_TARGET_MULTIPLIER=1.2,
        MIN_SUBTITLE_DURATION=2.5,
        MIN_TRIM_DURATION=3.5,
        TOLERANCE=1.5,
        SPEED_FACTOR_MIN=1.0,
        SPEED_FACTOR_ACCEPT=1.2,
        SPEED_FACTOR_MAX=1.4,
        MAX_WORKERS=10,
        MAX_SPLIT_LENGTH=20,
        SUMMARY_LENGTH=8000,
        REFLECT_TRANSLATE=False,
        MODEL_CACHE_DIR="_test_model_cache",
        PAUSE_BEFORE_TRANSLATE=False,
    )


@pytest.fixture
def temp_env_vars(mock_settings: Settings, monkeypatch) -> Generator[dict, None, None]:
    """
    设置临时环境变量

    在测试前后保存和恢复环境变量
    """
    # 设置测试环境变量
    env_vars = {
        "OPENAI_API_KEY": mock_settings.openai_api_key,
        "OPENAI_API_BASE": mock_settings.openai_api_base,
        "OPENAI_MODEL": mock_settings.openai_model,
        "WHISPER_RUNTIME": mock_settings.whisper_runtime,
        "TTS_METHOD": mock_settings.tts_method,
        "TARGET_LANGUAGE": mock_settings.target_language,
    }

    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)

    yield env_vars


# ==================== 临时目录和文件 fixtures ====================

@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """
    创建临时输出目录

    包含所有必需的子目录结构
    """
    output_dir = tmp_path / "output"
    audio_dir = output_dir / "audio"
    log_dir = output_dir / "log"
    gpt_log_dir = output_dir / "gpt_log"
    refers_dir = audio_dir / "refers"
    segs_dir = audio_dir / "segs"
    tmp_dir = audio_dir / "tmp"

    for directory in [output_dir, audio_dir, log_dir, gpt_log_dir, refers_dir, segs_dir, tmp_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    yield output_dir


@pytest.fixture
def sample_video_path(temp_output_dir: Path) -> Path:
    """创建示例视频文件路径（不创建实际文件）"""
    return temp_output_dir / "sample_video.mp4"


@pytest.fixture
def sample_audio_path(temp_output_dir: Path) -> Path:
    """创建示例音频文件路径（不创建实际文件）"""
    return temp_output_dir / "audio" / "sample_audio.mp3"


@pytest.fixture
def create_sample_audio(temp_output_dir: Path) -> Path:
    """
    创建真实的示例音频文件

    注意: 这是一个空文件，仅用于路径测试
    """
    audio_file = temp_output_dir / "audio" / "test.mp3"
    audio_file.parent.mkdir(parents=True, exist_ok=True)
    audio_file.write_bytes(b"")
    return audio_file


@pytest.fixture
def create_sample_video(temp_output_dir: Path) -> Path:
    """
    创建真实的示例视频文件

    注意: 这是一个空文件，仅用于路径测试
    """
    video_file = temp_output_dir / "test_video.mp4"
    video_file.write_bytes(b"")
    return video_file


@pytest.fixture
def sample_transcription_df() -> pd.DataFrame:
    """
    创建示例转录数据 DataFrame

    模拟 WhisperX 输出的转录结果
    """
    return pd.DataFrame({
        'text': ['"Hello"', '"world"', '"This"', '"is"', '"a"', '"test"'],
        'start': [0.0, 0.5, 1.0, 1.5, 2.0, 2.5],
        'end': [0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
        'speaker_id': [None, None, None, None, None, None],
    })


@pytest.fixture
def sample_asr_result() -> dict:
    """创建示例 ASR 结果"""
    return {
        'segments': [
            {
                'start': 0.0,
                'end': 1.5,
                'text': 'Hello world',
                'speaker_id': None,
                'words': [
                    {'word': 'Hello', 'start': 0.0, 'end': 0.5},
                    {'word': 'world', 'start': 0.5, 'end': 1.5},
                ]
            },
            {
                'start': 1.5,
                'end': 3.0,
                'text': 'This is a test',
                'speaker_id': None,
                'words': [
                    {'word': 'This', 'start': 1.5, 'end': 2.0},
                    {'word': 'is', 'start': 2.0, 'end': 2.5},
                    {'word': 'a', 'start': 2.5, 'end': 2.7},
                    {'word': 'test', 'start': 2.7, 'end': 3.0},
                ]
            }
        ]
    }


@pytest.fixture
def sample_translation_result() -> dict:
    """创建示例翻译结果"""
    return {
        "theme": "This is a test video about AI.",
        "terms": [
            {
                "src": "Artificial Intelligence",
                "tgt": "人工智能",
                "note": "Computer systems that can perform tasks requiring human intelligence"
            }
        ]
    }


# ==================== LLM 相关 fixtures ====================

@pytest.fixture
def mock_llm_response(sample_translation_result: dict) -> dict:
    """模拟 LLM 响应"""
    return sample_translation_result


@pytest.fixture
def mock_openai_client() -> AsyncMock:
    """
    模拟 AsyncOpenAI 客户端

    模拟 chat.completions.create 调用
    """
    mock_client = AsyncMock(spec=AsyncOpenAI)

    # 模拟响应对象
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "theme": "Test theme",
        "terms": []
    })
    mock_response.choices[0].message.model = "gpt-4o"

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    mock_client.close = AsyncMock()

    return mock_client


@pytest.fixture
def mock_llm_ask(sample_translation_result: dict) -> AsyncMock:
    """模拟 ask_llm 函数"""
    async_mock = AsyncMock(return_value=sample_translation_result)
    return async_mock


# ==================== HTTP 相关 fixtures ====================

@pytest.fixture
def mock_httpx_client() -> AsyncMock:
    """模拟 httpx.AsyncClient"""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # 模拟响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={"result": "success"})
    mock_response.text = "Success"

    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.put = AsyncMock(return_value=mock_response)
    mock_client.aclose = AsyncMock()

    return mock_client


@pytest.fixture
def mock_http_response() -> MagicMock:
    """模拟 httpx.Response 对象"""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json = MagicMock(return_value={"data": "test"})
    mock_resp.text = "test response"
    mock_resp.content = b"test content"
    return mock_resp


# ==================== 缓存相关 fixtures ====================

@pytest.fixture
def mock_cache_manager() -> AsyncMock:
    """模拟缓存管理器"""
    mock_manager = AsyncMock()
    mock_manager.get_llm_cache = AsyncMock(return_value=None)
    mock_manager.set_llm_cache = AsyncMock()
    mock_manager.get_translation_cache = AsyncMock(return_value=None)
    mock_manager.set_translation_cache = AsyncMock()
    mock_manager.clear = AsyncMock()
    return mock_manager


# ==================== 文件系统相关 fixtures ====================

@pytest.fixture
def mock_file_exists() -> Mock:
    """模拟 os.path.exists"""
    return Mock(return_value=True)


@pytest.fixture
def mock_file_not_exists() -> Mock:
    """模拟文件不存在的情况"""
    return Mock(return_value=False)


@pytest.fixture
def temp_xlsx_file(tmp_path: Path) -> Path:
    """创建临时 Excel 文件"""
    import pandas as pd

    df = pd.DataFrame({
        'text': ['Hello', 'World'],
        'start': [0.0, 1.0],
        'end': [1.0, 2.0],
    })

    file_path = tmp_path / "test.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def temp_json_file(tmp_path: Path) -> Path:
    """创建临时 JSON 文件"""
    data = {"test": "data", "number": 123}

    file_path = tmp_path / "test.json"
    file_path.write_text(json.dumps(data, indent=2))
    return file_path


@pytest.fixture
def temp_txt_file(tmp_path: Path) -> Path:
    """创建临时文本文件"""
    content = "Line 1\nLine 2\nLine 3"

    file_path = tmp_path / "test.txt"
    file_path.write_text(content)
    return file_path


# ==================== 装饰器相关 fixtures ====================

@pytest.fixture
def mock_async_sleep() -> AsyncMock:
    """模拟 asyncio.sleep"""
    return AsyncMock()


@pytest.fixture
def retry_test_data() -> tuple:
    """
    提供重试测试的数据

    返回: (失败次数, 成功值)
    """
    return (3, "success")


# ==================== NLP 相关 fixtures ====================

@pytest.fixture
def sample_nlp_doc():
    """模拟 Spacy Doc 对象"""
    mock_doc = MagicMock()
    mock_doc.text = "This is a sample sentence."
    mock_doc.sents = [
        MagicMock(text="This is a sample sentence.", start=0, end=26)
    ]
    return mock_doc


@pytest.fixture
def sample_spacy_model():
    """模拟 Spacy 模型"""
    mock_model = MagicMock()
    mock_model.return_value = MagicMock(
        text="Test sentence",
        sents=[MagicMock(text="Test sentence")]
    )
    return mock_model


# ==================== TTS 相关 fixtures ====================

@pytest.fixture
def sample_tts_tasks() -> list[dict]:
    """创建示例 TTS 任务"""
    return [
        {
            "index": 0,
            "text": "Hello world",
            "start": 0.0,
            "end": 2.0,
            "audio_path": "audio/segs/0.mp3"
        },
        {
            "index": 1,
            "text": "This is a test",
            "start": 2.0,
            "end": 4.0,
            "audio_path": "audio/segs/1.mp3"
        }
    ]


# ==================== 字幕相关 fixtures ====================

@pytest.fixture
def sample_subtitle_data() -> list[dict]:
    """创建示例字幕数据"""
    return [
        {
            "index": 1,
            "start": 0.0,
            "end": 2.0,
            "text": "Hello world"
        },
        {
            "index": 2,
            "start": 2.0,
            "end": 4.0,
            "text": "This is a test"
        }
    ]


@pytest.fixture
def sample_srt_content() -> str:
    """创建示例 SRT 内容"""
    return """1
00:00:00,000 --> 00:00:02,000
Hello world

2
00:00:02,000 --> 00:00:04,000
This is a test
"""


# ==================== Pytest 配置 ====================
# 标记定义已移至第一个 pytest_configure 函数中（避免重复）

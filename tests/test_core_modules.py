"""VideoVerse 测试脚本。

测试核心模块的功能是否正常工作。
"""

import asyncio
from pathlib import Path

from loguru import logger

# 测试导入
def test_imports():
    """测试所有模块是否可以正常导入。"""
    logger.info("Testing imports...")

    try:
        from core import config, paths, pipeline
        from core.steps import (
            DownloadStep,
            ASRStep,
            NLPSplitStep,
            MeaningSplitStep,
            SummarizeStep,
            TranslateStep,
            SplitSubStep,
            GenSubStep,
            BurnSubStep,
            AudioTaskStep,
            GenAudioStep,
            MergeAudioStep,
            DubbingStep,
        )
        from core.tts import EdgeTTSBackend, AzureTTSBackend
        from core.utils import cache, llm, decorators, common, prompts
        from tools import prompts as tools_prompts, translate_lines, spacy_utils

        logger.success("✓ All imports successful")
        return True
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        return False


def test_config():
    """测试配置模块。"""
    logger.info("Testing config...")

    try:
        from core.config import get_settings
        settings = get_settings()

        # 验证关键配置项
        assert hasattr(settings, 'openai_api_key')
        assert hasattr(settings, 'tts_method')
        assert hasattr(settings, 'whisper_language')
        assert hasattr(settings, 'output_dir')
        assert hasattr(settings, 'model_cache_dir')

        logger.success(f"✓ Config loaded: output_dir={settings.output_dir}, model_cache_dir={settings.model_cache_dir}")
        return True
    except Exception as e:
        logger.error(f"✗ Config test failed: {e}")
        return False


def test_paths():
    """测试路径管理。"""
    logger.info("Testing paths...")

    try:
        from core.paths import paths

        # 验证路径属性
        assert paths.output_dir is not None
        assert paths.audio_dir is not None
        assert paths.log_dir is not None
        assert paths.cleaned_chunks is not None
        assert paths.split_by_nlp is not None
        assert paths.split_by_meaning is not None
        assert paths.terminology is not None

        # 尝试创建目录
        paths.ensure_directories()

        logger.success(f"✓ Paths initialized: output_dir={paths.output_dir}")
        return True
    except Exception as e:
        logger.error(f"✗ Paths test failed: {e}")
        return False


def test_pipeline_registry():
    """测试流水线注册表。"""
    logger.info("Testing pipeline registry...")

    try:
        from core.pipeline import StepRegistry, PipelineEngine
        from core.steps import create_download_step, create_asr_step

        registry = StepRegistry()

        # 注册步骤
        download_step = create_download_step()
        asr_step = create_asr_step()

        registry.register("step_01_download", download_step)
        registry.register("step_02_asr", asr_step)

        # 测试依赖解析
        execution_order = registry.resolve_execution_order(["step_02_asr"])

        logger.success(f"✓ Pipeline registry working: execution_order={execution_order}")
        return True
    except Exception as e:
        logger.error(f"✗ Pipeline registry test failed: {e}")
        return False


def test_tts_backends():
    """测试 TTS 后端。"""
    logger.info("Testing TTS backends...")

    try:
        from core.tts import EdgeTTSBackend, AzureTTSBackend

        # 创建后端实例
        edge_backend = EdgeTTSBackend()
        azure_backend = AzureTTSBackend()

        logger.success(f"✓ TTS backends created: EdgeTTSBackend(name={edge_backend.name}), AzureTTSBackend(name={azure_backend.name})")
        return True
    except Exception as e:
        logger.error(f"✗ TTS backend test failed: {e}")
        return False


def test_prompts():
    """测试 prompt 模块。"""
    logger.info("Testing prompts...")

    try:
        from tools.prompts import get_split_prompt, get_summary_prompt

        # 测试生成 prompt
        split_prompt = get_split_prompt("测试句子", num_parts=2, word_limit=10, language="zh")
        summary_prompt = get_summary_prompt("测试内容", src_lang="zh", tgt_lang="en")

        assert "测试句子" in split_prompt
        assert "测试内容" in summary_prompt

        logger.success("✓ Prompts generated successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Prompts test failed: {e}")
        return False


async def test_llm():
    """测试 LLM 模块（需要配置 API Key）。"""
    logger.info("Testing LLM module...")

    try:
        from core.utils.llm import ask_llm
        from core.config import get_settings

        settings = get_settings()
        if not settings.openai_api_key:
            logger.warning("✗ LLM test skipped: OPENAI_API_KEY not configured")
            return False

        # 简单测试
        result = ask_llm("你好", log_title="test")

        logger.success(f"✓ LLM test successful: response={result[:50]}...")
        return True
    except Exception as e:
        logger.error(f"✗ LLM test failed: {e}")
        return False


async def run_all_tests():
    """运行所有测试。"""
    logger.info("=" * 60)
    logger.info("VideoVerse Core Module Tests")
    logger.info("=" * 60)

    results = []

    # 同步测试
    results.append(("Imports", test_imports()))
    results.append(("Config", test_config()))
    results.append(("Paths", test_paths()))
    results.append(("Pipeline Registry", test_pipeline_registry()))
    results.append(("TTS Backends", test_tts_backends()))
    results.append(("Prompts", test_prompts()))

    # 异步测试
    results.append(("LLM", await test_llm()))

    # 汇总结果
    logger.info("=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")

    logger.info("=" * 60)
    logger.success(f"Tests completed: {passed}/{total} passed")

    return passed == total


if __name__ == "__main__":
    asyncio.run(run_all_tests())

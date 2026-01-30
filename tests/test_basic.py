"""VideoVerse 基础测试脚本。

测试核心模块的基本功能，跳过需要额外依赖的测试。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger


def test_basic_imports():
    """测试基本模块导入（不需要额外依赖）。"""
    logger.info("Testing basic imports...")

    try:
        # 测试配置
        from core.config import get_settings
        settings = get_settings()
        assert hasattr(settings, 'openai_api_key')
        assert hasattr(settings, 'tts_method')
        assert hasattr(settings, 'output_dir')
        logger.success(f"✓ Config loaded: output_dir={settings.output_dir}")

        # 测试路径
        from core.paths import paths
        paths.ensure_directories()
        assert paths.output_dir.exists()
        assert paths.audio_dir.exists()
        assert paths.log_dir.exists()
        logger.success(f"✓ Paths initialized: {paths.output_dir}")

        # 测试流水线框架
        from core.pipeline import StepRegistry, PipelineContext, PipelineEngine
        registry = StepRegistry()
        context = PipelineContext(
            video_source="test.mp4",
            source_language="zh",
            target_language="en",
            config=settings,
            storage={}
        )
        logger.success("✓ Pipeline framework imported")

        # 测试 TTS 后端基类
        from core.tts import TTSBackend
        logger.success("✓ TTS base class imported")

        # 测试工具模块
        from core.utils import cache, decorators, common, llm, prompts
        assert callable(cache.get_cache_manager)
        assert callable(decorators.async_except_handler)
        assert callable(common.get_joiner)
        logger.success("✓ Utils modules imported")

        logger.success("All basic imports successful!")
        return True

    except Exception as e:
        logger.error(f"Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_step_creation():
    """测试步骤创建（不需要额外依赖）。"""
    logger.info("Testing step creation...")

    try:
        from core.steps import create_download_step
        from core.pipeline import StepRegistry

        # 创建步骤
        download_step = create_download_step()

        # 验证步骤属性
        assert hasattr(download_step, 'name')
        assert hasattr(download_step, 'dependencies')
        assert hasattr(download_step, 'validate')
        assert hasattr(download_step, 'execute')

        logger.info(f"  ✓ DownloadStep: name={download_step.name}, dependencies={download_step.dependencies}")

        logger.success("Step creation test passed!")
        return True

    except Exception as e:
        logger.error(f"Step creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompts():
    """测试 prompt 模块。"""
    logger.info("Testing prompts...")

    try:
        from tools.prompts import get_split_prompt, get_summary_prompt

        # 测试生成 prompt
        split_prompt = get_split_prompt("测试句子", num_parts=2, word_limit=10, language="zh")
        assert "测试句子" in split_prompt
        assert "2" in split_prompt

        summary_prompt = get_summary_prompt("测试内容", src_lang="zh", tgt_lang="en")
        assert "测试内容" in summary_prompt

        logger.success("Prompts test passed!")
        return True

    except Exception as e:
        logger.error(f"Prompts test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_translate_lines():
    """测试翻译模块。"""
    logger.info("Testing translate_lines...")

    try:
        from tools.translate_lines import valid_translate_result

        # 测试验证函数
        result = {
            "1": {"origin": "Hello", "direct": "你好"},
            "2": {"origin": "World", "direct": "世界"}
        }
        validation = valid_translate_result(result, ["1", "2"], ["direct"])
        assert validation["status"] == "success"

        logger.success("Translate lines test passed!")
        return True

    except Exception as e:
        logger.error(f"Translate lines test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有基础测试。"""
    logger.info("=" * 60)
    logger.info("VideoVerse Basic Tests")
    logger.info("=" * 60)

    results = []

    # 运行测试
    results.append(("Basic Imports", test_basic_imports()))
    results.append(("Step Creation", test_step_creation()))
    results.append(("Prompts", test_prompts()))
    results.append(("Translate Lines", test_translate_lines()))

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

    if passed == total:
        logger.success("All tests passed! ✓")
    else:
        logger.warning(f"{total - passed} test(s) failed")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

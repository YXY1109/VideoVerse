"""
路径模块测试

测试路径常量和辅助函数
"""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPathConstants:
    """测试路径常量"""

    def test_project_root(self):
        """测试项目根目录"""
        from src.utils.paths import PROJECT_ROOT

        assert isinstance(PROJECT_ROOT, Path)
        assert PROJECT_ROOT.exists()
        # 验证 PROJECT_ROOT 指向项目根目录（包含 src 目录）
        assert (PROJECT_ROOT / "src").exists()

    def test_output_dir(self):
        """测试输出目录"""
        from src.utils.paths import OUTPUT_DIR

        assert isinstance(OUTPUT_DIR, Path)
        assert OUTPUT_DIR.name == "output"
        assert OUTPUT_DIR.parent == PROJECT_ROOT

    def test_audio_dir(self):
        """测试音频目录"""
        from src.utils.paths import AUDIO_DIR

        assert isinstance(AUDIO_DIR, Path)
        assert AUDIO_DIR.name == "audio"
        assert AUDIO_DIR.parent == OUTPUT_DIR

    def test_log_dir(self):
        """测试日志目录"""
        from src.utils.paths import LOG_DIR

        assert isinstance(LOG_DIR, Path)
        assert LOG_DIR.name == "log"
        assert LOG_DIR.parent == OUTPUT_DIR

    def test_gpt_log_dir(self):
        """测试 GPT 日志目录"""
        from src.utils.paths import GPT_LOG_DIR

        assert isinstance(GPT_LOG_DIR, Path)
        assert GPT_LOG_DIR.name == "gpt_log"
        assert GPT_LOG_DIR.parent == OUTPUT_DIR

    def test_audio_refers_dir(self):
        """测试音频参考目录"""
        from src.utils.paths import AUDIO_REFERS_DIR

        assert isinstance(AUDIO_REFERS_DIR, Path)
        assert AUDIO_REFERS_DIR.name == "refers"
        assert AUDIO_REFERS_DIR.parent == AUDIO_DIR

    def test_audio_segs_dir(self):
        """测试音频片段目录"""
        from src.utils.paths import AUDIO_SEGS_DIR

        assert isinstance(AUDIO_SEGS_DIR, Path)
        assert AUDIO_SEGS_DIR.name == "segs"
        assert AUDIO_SEGS_DIR.parent == AUDIO_DIR

    def test_audio_tmp_dir(self):
        """测试音频临时目录"""
        from src.utils.paths import AUDIO_TMP_DIR

        assert isinstance(AUDIO_TMP_DIR, Path)
        assert AUDIO_TMP_DIR.name == "tmp"
        assert AUDIO_TMP_DIR.parent == AUDIO_DIR


class TestIntermediateFilePaths:
    """测试中间产出文件路径"""

    def test_cleaned_chunks(self):
        """测试转录文本文件路径"""
        from src.utils.paths import CLEANED_CHUNKS

        assert isinstance(CLEANED_CHUNKS, Path)
        assert CLEANED_CHUNKS.name == "cleaned_chunks.xlsx"
        assert CLEANED_CHUNKS.parent == LOG_DIR

    def test_split_by_nlp(self):
        """测试 NLP 分割文件路径"""
        from src.utils.paths import SPLIT_BY_NLP

        assert isinstance(SPLIT_BY_NLP, Path)
        assert SPLIT_BY_NLP.name == "split_by_nlp.txt"
        assert SPLIT_BY_NLP.parent == LOG_DIR

    def test_split_by_meaning(self):
        """测试语义分割文件路径"""
        from src.utils.paths import SPLIT_BY_MEANING

        assert isinstance(SPLIT_BY_MEANING, Path)
        assert SPLIT_BY_MEANING.name == "split_by_meaning.txt"
        assert SPLIT_BY_MEANING.parent == LOG_DIR

    def test_terminology(self):
        """测试术语表文件路径"""
        from src.utils.paths import TERMINOLOGY

        assert isinstance(TERMINOLOGY, Path)
        assert TERMINOLOGY.name == "terminology.json"
        assert TERMINOLOGY.parent == LOG_DIR

    def test_translation_results(self):
        """测试翻译结果文件路径"""
        from src.utils.paths import TRANSLATION_RESULTS

        assert isinstance(TRANSLATION_RESULTS, Path)
        assert TRANSLATION_RESULTS.name == "translation_results.xlsx"
        assert TRANSLATION_RESULTS.parent == LOG_DIR

    def test_translation_for_subtitles(self):
        """测试字幕翻译结果文件路径"""
        from src.utils.paths import TRANSLATION_FOR_SUBTITLES

        assert isinstance(TRANSLATION_FOR_SUBTITLES, Path)
        assert TRANSLATION_FOR_SUBTITLES.name == "translation_results_for_subtitles.xlsx"
        assert TRANSLATION_FOR_SUBTITLES.parent == LOG_DIR

    def test_translation_remerged(self):
        """测试重新合并的翻译结果文件路径"""
        from src.utils.paths import TRANSLATION_REMERGED

        assert isinstance(TRANSLATION_REMERGED, Path)
        assert TRANSLATION_REMERGED.name == "translation_results_remerged.xlsx"
        assert TRANSLATION_REMERGED.parent == LOG_DIR

    def test_audio_tasks(self):
        """测试音频任务文件路径"""
        from src.utils.paths import AUDIO_TASKS

        assert isinstance(AUDIO_TASKS, Path)
        assert AUDIO_TASKS.name == "tts_tasks.xlsx"
        assert AUDIO_TASKS.parent == AUDIO_DIR


class TestAudioFilePaths:
    """测试音频文件路径"""

    def test_raw_audio_file(self):
        """测试原始音频文件路径"""
        from src.utils.paths import RAW_AUDIO_FILE

        assert isinstance(RAW_AUDIO_FILE, Path)
        assert RAW_AUDIO_FILE.name == "raw.mp3"
        assert RAW_AUDIO_FILE.parent == AUDIO_DIR

    def test_vocal_audio_file(self):
        """测试人声音频文件路径"""
        from src.utils.paths import VOCAL_AUDIO_FILE

        assert isinstance(VOCAL_AUDIO_FILE, Path)
        assert VOCAL_AUDIO_FILE.name == "vocal.mp3"
        assert VOCAL_AUDIO_FILE.parent == AUDIO_DIR

    def test_background_audio_file(self):
        """测试背景音频文件路径"""
        from src.utils.paths import BACKGROUND_AUDIO_FILE

        assert isinstance(BACKGROUND_AUDIO_FILE, Path)
        assert BACKGROUND_AUDIO_FILE.name == "background.mp3"
        assert BACKGROUND_AUDIO_FILE.parent == AUDIO_DIR


class TestVideoFilePaths:
    """测试视频文件路径"""

    def test_input_video_file(self):
        """测试输入视频文件路径"""
        from src.utils.paths import INPUT_VIDEO_FILE

        assert isinstance(INPUT_VIDEO_FILE, Path)
        assert INPUT_VIDEO_FILE.name == "input_video.mp4"
        assert INPUT_VIDEO_FILE.parent == OUTPUT_DIR

    def test_output_video_with_sub(self):
        """测试带字幕输出视频文件路径"""
        from src.utils.paths import OUTPUT_VIDEO_WITH_SUB

        assert isinstance(OUTPUT_VIDEO_WITH_SUB, Path)
        assert OUTPUT_VIDEO_WITH_SUB.name == "output_with_subtitles.mp4"
        assert OUTPUT_VIDEO_WITH_SUB.parent == OUTPUT_DIR

    def test_output_video_dubbed(self):
        """测试配音输出视频文件路径"""
        from src.utils.paths import OUTPUT_VIDEO_DUBBED

        assert isinstance(OUTPUT_VIDEO_DUBBED, Path)
        assert OUTPUT_VIDEO_DUBBED.name == "output_dubbed.mp4"
        assert OUTPUT_VIDEO_DUBBED.parent == OUTPUT_DIR


class TestEnsureDirectories:
    """测试 ensure_directories 函数"""

    def test_ensure_directories_creates_all(self, tmp_path: Path):
        """测试确保所有目录被创建"""
        from src.utils.paths import ensure_directories

        with patch('src.utils.paths.OUTPUT_DIR', tmp_path / "output"):
            ensure_directories()

            # 验证所有目录都被创建
            assert (tmp_path / "output").exists()
            assert (tmp_path / "output" / "audio").exists()
            assert (tmp_path / "output" / "log").exists()
            assert (tmp_path / "output" / "gpt_log").exists()
            assert (tmp_path / "output" / "audio" / "refers").exists()
            assert (tmp_path / "output" / "audio" / "segs").exists()
            assert (tmp_path / "output" / "audio" / "tmp").exists()

    def test_ensure_directories_idempotent(self, tmp_path: Path):
        """测试重复调用不会出错"""
        from src.utils.paths import ensure_directories

        with patch('src.utils.paths.OUTPUT_DIR', tmp_path / "output"):
            ensure_directories()
            ensure_directories()
            ensure_directories()

            # 验证目录存在
            assert (tmp_path / "output").exists()

    def test_ensure_directories_with_existing(self, tmp_path: Path):
        """测试部分目录已存在的情况"""
        from src.utils.paths import ensure_directories

        output_dir = tmp_path / "output"
        audio_dir = output_dir / "audio"

        # 预先创建部分目录
        audio_dir.mkdir(parents=True)

        with patch('src.utils.paths.OUTPUT_DIR', output_dir):
            ensure_directories()

            # 验证所有目录都存在
            assert (output_dir / "log").exists()
            assert (audio_dir / "refers").exists()
            assert (audio_dir / "segs").exists()
            assert (audio_dir / "tmp").exists()


class TestPathExports:
    """测试路径导出"""

    def test_all_exports(self):
        """测试 __all__ 导出列表"""
        from src.utils.paths import __all__ as exports

        expected_exports = [
            # 目录
            "PROJECT_ROOT",
            "OUTPUT_DIR",
            "AUDIO_DIR",
            "LOG_DIR",
            "GPT_LOG_DIR",
            "AUDIO_REFERS_DIR",
            "AUDIO_SEGS_DIR",
            "AUDIO_TMP_DIR",
            # 中间产出
            "CLEANED_CHUNKS",
            "SPLIT_BY_NLP",
            "SPLIT_BY_MEANING",
            "TERMINOLOGY",
            "TRANSLATION_RESULTS",
            "TRANSLATION_FOR_SUBTITLES",
            "TRANSLATION_REMERGED",
            "AUDIO_TASKS",
            # 音频文件
            "RAW_AUDIO_FILE",
            "VOCAL_AUDIO_FILE",
            "BACKGROUND_AUDIO_FILE",
            # 视频文件
            "INPUT_VIDEO_FILE",
            "OUTPUT_VIDEO_WITH_SUB",
            "OUTPUT_VIDEO_DUBBED",
            # 辅助函数
            "ensure_directories",
        ]

        assert set(exports) == set(expected_exports)

    def test_imported_constants_exist(self):
        """测试所有导出的常量都可以导入"""
        from src.utils.paths import __all__ as exports

        for name in exports:
            from src.utils import paths
            assert hasattr(paths, name)


class TestPathResolution:
    """测试路径解析"""

    def test_paths_are_absolute(self):
        """测试所有路径都是绝对路径"""
        from src.utils.paths import (
            PROJECT_ROOT, OUTPUT_DIR, AUDIO_DIR, LOG_DIR,
            CLEANED_CHUNKS, RAW_AUDIO_FILE, INPUT_VIDEO_FILE
        )

        assert PROJECT_ROOT.is_absolute()
        assert OUTPUT_DIR.is_absolute()
        assert AUDIO_DIR.is_absolute()
        assert LOG_DIR.is_absolute()
        assert CLEANED_CHUNKS.is_absolute()
        assert RAW_AUDIO_FILE.is_absolute()
        assert INPUT_VIDEO_FILE.is_absolute()

    def test_path_hierarchy(self):
        """测试路径层级关系"""
        from src.utils.paths import (
            PROJECT_ROOT, OUTPUT_DIR, AUDIO_DIR, LOG_DIR,
            RAW_AUDIO_FILE, CLEANED_CHUNKS
        )

        # OUTPUT_DIR 在 PROJECT_ROOT 下
        assert OUTPUT_DIR.parent == PROJECT_ROOT
        # AUDIO_DIR 和 LOG_DIR 在 OUTPUT_DIR 下
        assert AUDIO_DIR.parent == OUTPUT_DIR
        assert LOG_DIR.parent == OUTPUT_DIR
        # 文件在相应目录下
        assert RAW_AUDIO_FILE.parent == AUDIO_DIR
        assert CLEANED_CHUNKS.parent == LOG_DIR

    def test_path_str_conversion(self):
        """测试路径转换为字符串"""
        from src.utils.paths import OUTPUT_DIR, RAW_AUDIO_FILE

        output_str = str(OUTPUT_DIR)
        audio_str = str(RAW_AUDIO_FILE)

        assert isinstance(output_str, str)
        assert isinstance(audio_str, str)
        assert "output" in output_str
        assert "raw.mp3" in audio_str

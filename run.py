"""
VideoVerse 启动脚本

使用方式:
    python run.py <video_url_or_path> [options]

示例:
    # YouTube 视频 (仅字幕)
    python run.py "https://www.youtube.com/watch?v=xxx" -s zh -t en

    # 本地视频 (带配音)
    python run.py "D:/videos/demo.mp4" -s zh -t en -d

    # 使用默认设置
    python run.py "D:/videos/demo.mp4"
"""
import asyncio
import argparse

# 必须首先导入 src 包，以触发 src/__init__.py 中的警告过滤和 jieba 预初始化
import src  # noqa: F401

from src.pipeline import run_pipeline

# 默认值来自 pipeline.py 的 __main__
DEFAULT_VIDEO_SOURCE = r"D:\PycharmProjects\VideoVerse\files\demo.mp4"
DEFAULT_SOURCE_LANGUAGE = "zh"
DEFAULT_TARGET_LANGUAGE = "en"
DEFAULT_DUBBING = False


def main():
    parser = argparse.ArgumentParser(
        description="VideoVerse - AI 视频翻译和配音工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "video_source",
        nargs="?",  # 可选参数
        default=DEFAULT_VIDEO_SOURCE,
        help=f"YouTube URL 或本地视频路径 (默认: {DEFAULT_VIDEO_SOURCE})"
    )

    parser.add_argument(
        "-s", "--source-language",
        default=DEFAULT_SOURCE_LANGUAGE,
        help=f"源语言代码 (默认: {DEFAULT_SOURCE_LANGUAGE})"
    )

    parser.add_argument(
        "-t", "--target-language",
        default=DEFAULT_TARGET_LANGUAGE,
        help=f"目标语言代码 (默认: {DEFAULT_TARGET_LANGUAGE})"
    )

    parser.add_argument(
        "-d", "--dubbing",
        action="store_true",
        default=DEFAULT_DUBBING,
        help=f"是否生成配音 (默认: {DEFAULT_DUBBING})"
    )

    args = parser.parse_args()

    # 运行异步流水线
    output = asyncio.run(run_pipeline(
        video_source=args.video_source,
        source_language=args.source_language,
        target_language=args.target_language,
        dubbing=args.dubbing,
    ))

    print(f"\n完成! 输出文件: {output}")


if __name__ == "__main__":
    main()

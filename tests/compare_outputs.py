"""VideoVerse 输出对比脚本。

对比 temp 和 core 实现的输出差异，确保功能一致性。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger


def compare_file_contents(file1: Path, file2: Path) -> dict:
    """比较两个文件的内容差异。

    Args:
        file1: 第一个文件路径
        file2: 第二个文件路径

    Returns:
        包含比较结果的字典
    """
    result = {
        "both_exist": False,
        "identical": False,
        "size_diff": 0,
        "lines_diff": 0,
    }

    # 检查文件是否存在
    exists1 = file1.exists()
    exists2 = file2.exists()

    if not exists1 and not exists2:
        result["status"] = "neither_exists"
        return result

    if exists1 and not exists2:
        result["status"] = "only_file1"
        return result

    if not exists1 and exists2:
        result["status"] = "only_file2"
        return result

    result["both_exist"] = True

    try:
        # 比较文件大小
        size1 = file1.stat().st_size
        size2 = file2.stat().st_size
        result["size_diff"] = size2 - size1

        # 读取内容
        text1 = file1.read_text(encoding="utf-8")
        text2 = file2.read_text(encoding="utf-8")

        # 比较行数
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        result["lines_diff"] = len(lines2) - len(lines1)

        # 比较内容
        if text1 == text2:
            result["identical"] = True
            result["status"] = "identical"
        else:
            result["status"] = "different"

            # 计算相似度（简单的行对比）
            common_lines = set(lines1) & set(lines2)
            total_lines = set(lines1) | set(lines2)
            similarity = len(common_lines) / len(total_lines) if total_lines else 1.0
            result["similarity"] = similarity

    except Exception as e:
        result["status"] = f"error: {e}"

    return result


def compare_output_directories(temp_dir: Path, core_dir: Path) -> dict:
    """比较两个输出目录。

    Args:
        temp_dir: temp 实现的输出目录
        core_dir: core 实现的输出目录

    Returns:
        包含所有文件比较结果的字典
    """
    results = {}

    # 定义需要比较的关键文件
    key_files = [
        "log/cleaned_chunks.xlsx",
        "log/split_by_nlp.txt",
        "log/split_by_meaning.txt",
        "log/terminology.json",
        "log/translation_results.xlsx",
        "log/translation_for_subtitles.xlsx",
        "audio/tts_tasks.xlsx",
    ]

    for file_path in key_files:
        temp_file = temp_dir / file_path
        core_file = core_dir / file_path

        result = compare_file_contents(temp_file, core_file)
        results[file_path] = result

    # 比较生成的视频文件
    video_files = [
        "output_sub.mp4",
        "output_dub.mp4",
    ]

    for file_path in video_files:
        temp_file = temp_dir / file_path
        core_file = core_dir / file_path

        exists1 = temp_file.exists()
        exists2 = core_file.exists()

        if exists1 and exists2:
            # 对于视频文件，只比较文件大小
            size1 = temp_file.stat().st_size
            size2 = core_file.stat().st_size
            size_diff_pct = abs(size2 - size1) / size1 * 100 if size1 > 0 else 0

            results[file_path] = {
                "both_exist": True,
                "size1": size1,
                "size2": size2,
                "size_diff_pct": size_diff_pct,
                "status": "similar" if size_diff_pct < 5 else "different",
            }
        elif exists1 or exists2:
            results[file_path] = {
                "both_exist": False,
                "status": "only_one_exists",
                "temp_exists": exists1,
                "core_exists": exists2,
            }
        else:
            results[file_path] = {
                "both_exist": False,
                "status": "neither_exists",
            }

    return results


def print_comparison_results(results: dict) -> None:
    """打印对比结果。

    Args:
        results: compare_output_directories 返回的结果字典
    """
    logger.info("=" * 60)
    logger.info("Comparison Results")
    logger.info("=" * 60)

    identical = 0
    different = 0
    errors = 0

    for file_path, result in results.items():
        status = result.get("status", "unknown")

        if status == "identical":
            logger.success(f"  ✓ {file_path}: Identical")
            identical += 1
        elif status == "different":
            similarity = result.get("similarity", 0)
            lines_diff = result.get("lines_diff", 0)
            logger.warning(f"  ⚠ {file_path}: Different (similarity: {similarity:.1%}, lines_diff: {lines_diff})")
            different += 1
        elif status == "only_file1":
            logger.warning(f"  ⚠ {file_path}: Only in temp")
            different += 1
        elif status == "only_file2":
            logger.warning(f"  ⚠ {file_path}: Only in core")
            different += 1
        elif status == "similar":
            logger.success(f"  ✓ {file_path}: Similar (size diff: {result.get('size_diff_pct', 0):.1f}%)")
            identical += 1
        elif status == "neither_exists":
            logger.info(f"  - {file_path}: Neither exists")
        else:
            logger.error(f"  ✗ {file_path}: {status}")
            errors += 1

    logger.info("=" * 60)
    logger.info(f"Summary: {identical} identical, {different} different, {errors} errors")
    logger.info("=" * 60)


async def run_comparison(
    temp_output_dir: str | None = None,
    core_output_dir: str | None = None
) -> None:
    """运行对比脚本。

    Args:
        temp_output_dir: temp 实现的输出目录（默认为 output/temp）
        core_output_dir: core 实现的输出目录（默认为 output/core）
    """
    logger.info("=" * 60)
    logger.info("VideoVerse Output Comparison")
    logger.info("=" * 60)

    # 设置默认目录
    if temp_output_dir is None:
        temp_output_dir = "output/temp"
    if core_output_dir is None:
        core_output_dir = "output/core"

    temp_dir = Path(temp_output_dir)
    core_dir = Path(core_output_dir)

    logger.info(f"Comparing:")
    logger.info(f"  Temp output: {temp_dir}")
    logger.info(f"  Core output: {core_dir}")
    logger.info("")

    # 检查目录是否存在
    if not temp_dir.exists():
        logger.warning(f"Temp output directory does not exist: {temp_dir}")
        logger.info("Run temp implementation first to generate output files.")
        return

    if not core_dir.exists():
        logger.warning(f"Core output directory does not exist: {core_dir}")
        logger.info("Run core implementation first to generate output files.")
        return

    # 运行比较
    results = compare_output_directories(temp_dir, core_dir)

    # 打印结果
    print_comparison_results(results)


def main():
    """主函数。"""
    import argparse

    parser = argparse.ArgumentParser(description="Compare temp and core implementation outputs")
    parser.add_argument(
        "--temp-dir",
        default="output/temp",
        help="Path to temp implementation output directory"
    )
    parser.add_argument(
        "--core-dir",
        default="output/core",
        help="Path to core implementation output directory"
    )

    args = parser.parse_args()

    # 运行比较
    asyncio.run(run_comparison(args.temp_dir, args.core_dir))


if __name__ == "__main__":
    main()

"""
测试运行脚本

提供便捷的测试运行命令
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"\n❌ {description} failed!")
        return False
    else:
        print(f"\n✅ {description} passed!")
        return True


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="VideoVerse 测试运行器")
    parser.add_argument("--unit", action="store_true", help="只运行单元测试")
    parser.add_argument("--integration", action="store_true", help="只运行集成测试")
    parser.add_argument("--fast", action="store_true", help="跳过慢速测试")
    parser.add_argument("--cov", action="store_true", help="生成覆盖率报告")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--parallel", "-n", type=int, help="并行运行的进程数")
    parser.add_argument("--file", "-f", type=str, help="运行特定测试文件")
    parser.add_argument("--function", "-k", type=str, help="运行特定测试函数")

    args = parser.parse_args()

    # 构建基础命令
    cmd = ["pytest", "-x"]

    # 添加标记
    markers = []
    if args.unit:
        markers.append("unit")
    if args.integration:
        markers.append("integration")
    if args.fast:
        markers.append("not slow")

    if markers:
        cmd.extend(["-m", " and ".join(markers)])

    # 添加覆盖率
    if args.cov:
        cmd.extend(["--cov=src", "--cov-report=term-missing"])

    # 添加详细输出
    if args.verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")

    # 添加并行运行
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])

    # 添加特定文件或函数
    if args.file:
        cmd.append(args.file)
    if args.function:
        cmd.extend(["-k", args.function])

    # 运行测试
    success = run_command(cmd, "Tests")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    # 预定义的测试运行命令
    if len(sys.argv) == 1:
        print("""
VideoVerse 测试运行器

用法:
  python run_tests.py [选项]

选项:
  --unit              只运行单元测试
  --integration       只运行集成测试
  --fast              跳过慢速测试
  --cov               生成覆盖率报告
  --verbose, -v       详细输出
  --parallel N        并行运行 (N 个进程)
  --file FILE         运行特定测试文件
  --function NAME     运行特定测试函数

示例:
  # 运行所有测试
  python run_tests.py

  # 只运行单元测试
  python run_tests.py --unit

  # 生成覆盖率报告
  python run_tests.py --cov

  # 并行运行 (4 个进程)
  python run_tests.py --parallel 4

  # 运行特定文件
  python run_tests.py --file tests/test_config.py

  # 运行特定测试函数
  python run_tests.py -k test_settings_default_values

快捷命令:
  # 运行快速测试 (跳过集成测试和慢速测试)
  pytest -m "unit and not slow"

  # 运行特定模块
  pytest tests/test_utils/

  # 运行特定文件
  pytest tests/test_config.py -v

  # 生成 HTML 覆盖率报告
  pytest --cov=src --cov-report=html
        """)
    else:
        main()

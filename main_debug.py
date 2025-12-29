"""
独立调试脚本 - 不依赖 Streamlit
用法：
1. 将视频文件放到 output/ 目录下
2. 修改下面的 VIDEO_PATH 或 VIDEO_URL 变量
3. 选择要执行的处理模式
4. 直接在 PyCharm 中运行或调试

支持的处理模式：
- 'video_only': 仅下载/准备视频
- 'subtitle': 仅生成字幕
- 'audio': 仅生成配音
- 'full': 完整处理（字幕+配音）
- 'custom': 自定义步骤
"""
import os
import sys
import shutil
import subprocess

from core.st_utils.download_video_section import convert_audio_to_video

# 设置环境变量抑制警告
os.environ['TORCHAUDIO_USE_BACKEND_DISPATCHER'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'

import warnings
warnings.filterwarnings('ignore')

# ==================== 配置区域 ====================

# 方式1: 使用本地视频文件（推荐）
# 将你的视频文件路径填在这里，或者直接放到 output/ 目录下
VIDEO_PATH = r"D:\PycharmProjects\VideoVerse\files\demo.mp4"  # 修改为你的视频路径

# 方式2: 使用 YouTube URL
VIDEO_URL = ""  # 如果要从 YouTube 下载，填写 URL

# 处理模式选择: 'video_only', 'subtitle', 'audio', 'full', 'custom'
MODE = 'subtitle'

# 自定义步骤（仅当 MODE='custom' 时有效）
CUSTOM_STEPS = {
    'asr': True,           # ASR 转录
    'split_nlp': True,     # NLP 分割
    'split_meaning': True, # 语义分割
    'summarize': True,     # 摘要
    'translate': True,     # 翻译
    'split_sub': True,     # 字幕分割
    'align_sub': True,     # 字幕对齐
    'merge_sub': True,     # 字幕烧录
    'audio_task': True,    # 音频任务生成
    'dub_chunks': True,    # 配音分割
    'refer_audio': True,   # 参考音频提取
    'gen_audio': True,     # TTS 音频生成
    'merge_audio': True,   # 音频合并
    'dub_to_vid': True,    # 配音合成
}

# ==================== 初始化 ====================

current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] += os.pathsep + current_dir
sys.path.append(current_dir)

# 导入核心模块
from core import load_key
from core._1_ytdlp import download_video_ytdlp, find_video_files
from core._2_asr import transcribe
from core._3_1_split_nlp import split_by_spacy
from core._3_2_split_meaning import split_sentences_by_meaning
from core._4_1_summarize import get_summary
from core._4_2_translate import translate_all
from core._5_split_sub import split_for_sub_main
from core._6_gen_sub import align_timestamp_main
from core._7_sub_into_vid import merge_subtitles_to_video
from core._8_1_audio_task import gen_audio_task_main
from core._8_2_dub_chunks import gen_dub_chunks
from core._9_refer_audio import extract_refer_audio_main
from core._10_gen_audio import gen_audio
from core._11_merge_audio import merge_full_audio
from core._12_dub_to_vid import merge_video_audio

SUB_VIDEO = "output/output_sub.mp4"
DUB_VIDEO = "output/output_dub.mp4"


def print_step(step_name: str, emoji: str = "🔹"):
    """打印处理步骤"""
    print(f"\n{emoji} {step_name}")
    print("-" * 60)


def prepare_video():
    """准备视频文件"""
    print_step("准备视频文件", "🎬")

    # 清理旧的 output 目录（如果需要）
    output_dir = "output"
    if os.path.exists(output_dir):
        # 检查是否已有视频
        try:
            existing_video = find_video_files(output_dir)
            print(f"找到已存在的视频: {existing_video}")
            return existing_video
        except (ValueError, IndexError):
            # 没有找到视频，继续处理
            pass

    # 使用本地视频文件
    if VIDEO_PATH and os.path.exists(VIDEO_PATH):
        print(f"使用本地视频: {VIDEO_PATH}")
        os.makedirs(output_dir, exist_ok=True)

        # 复制视频到 output 目录
        filename = os.path.basename(VIDEO_PATH)
        dest_path = os.path.join(output_dir, filename)
        shutil.copy2(VIDEO_PATH, dest_path)

        # 检查是否是音频文件，如果是则转换为视频
        ext = os.path.splitext(filename)[1].lower()
        if ext in load_key("allowed_audio_formats"):
            dest_path = convert_audio_to_video(dest_path)

        return dest_path

    # 从 YouTube 下载
    if VIDEO_URL:
        print(f"从 YouTube 下载视频...")
        resolution = load_key("ytb_resolution")
        download_video_ytdlp(VIDEO_URL, resolution=resolution)
        return find_video_files(output_dir)

    raise FileNotFoundError(
        "未找到视频文件！请设置 VIDEO_PATH 或 VIDEO_URL\n"
        "1. VIDEO_PATH: 本地视频文件的完整路径\n"
        "2. VIDEO_URL: YouTube 视频 URL"
    )


def process_subtitle():
    """字幕处理流程"""
    print_step("开始字幕处理流程", "📝")

    steps = CUSTOM_STEPS if MODE == 'custom' else {
        'asr': True,
        'split_nlp': True,
        'split_meaning': True,
        'summarize': True,
        'translate': True,
        'split_sub': True,
        'align_sub': True,
        'merge_sub': True,
    }

    if steps.get('asr'):
        print_step("① WhisperX 词级转录", "🎤")
        transcribe()

    if steps.get('split_nlp'):
        print_step("② NLP 句子分割", "✂️")
        split_by_spacy()

    if steps.get('split_meaning'):
        print_step("③ AI 语义分割", "🧠")
        split_sentences_by_meaning()

    if steps.get('summarize'):
        print_step("④ 内容摘要 + 术语提取", "📋")
        get_summary()

        if load_key("pause_before_translate"):
            input("\n⚠️ PAUSE_BEFORE_TRANSLATE. 请编辑 output/log/terminology.json 后按 ENTER 继续...\n")

    if steps.get('translate'):
        print_step("⑤ 多步翻译 (直译 → 反思 → 意译)", "🌐")
        translate_all()

    if steps.get('split_sub'):
        print_step("⑥ 字幕长度优化 (最长 75 字符)", "📏")
        split_for_sub_main()

    if steps.get('align_sub'):
        print_step("⑦ 时间轴对齐", "⏰")
        align_timestamp_main()

    if steps.get('merge_sub'):
        print_step("⑧ 字幕烧录到视频", "🎞️")
        merge_subtitles_to_video()

    print_step("✅ 字幕处理完成！", "🎉")
    if os.path.exists(SUB_VIDEO):
        print(f"输出视频: {os.path.abspath(SUB_VIDEO)}")


def process_audio():
    """音频处理流程（配音）"""
    print_step("开始音频处理流程", "🎧")

    if not os.path.exists(SUB_VIDEO):
        print("⚠️ 警告: 未找到字幕视频，请先运行字幕处理流程")
        return

    steps = CUSTOM_STEPS if MODE == 'custom' else {
        'audio_task': True,
        'dub_chunks': True,
        'refer_audio': True,
        'gen_audio': True,
        'merge_audio': True,
        'dub_to_vid': True,
    }

    if steps.get('audio_task'):
        print_step("⑨ 音频任务生成", "📝")
        gen_audio_task_main()

    if steps.get('dub_chunks'):
        print_step("⑩ 配音分割", "🔪")
        gen_dub_chunks()

    if steps.get('refer_audio'):
        print_step("⑪ 参考音频提取", "🎵")
        extract_refer_audio_main()

    if steps.get('gen_audio'):
        print_step("⑫ TTS 音频生成", "🔊")
        gen_audio()

    if steps.get('merge_audio'):
        print_step("⑬ 音频合并", "🔗")
        merge_full_audio()

    if steps.get('dub_to_vid'):
        print_step("⑭ 最终配音合成", "🎬")
        merge_video_audio()

    print_step("✅ 音频处理完成！", "🎇")
    if os.path.exists(DUB_VIDEO):
        print(f"输出视频: {os.path.abspath(DUB_VIDEO)}")


def main():
    """主函数"""
    print("=" * 60)
    print("VideoVerse 独立调试脚本")
    print("=" * 60)
    print(f"处理模式: {MODE}")
    print()

    try:
        # 准备视频
        video_path = prepare_video()
        print(f"✅ 视频准备完成: {video_path}\n")

        # 根据模式执行相应处理
        if MODE in ['subtitle', 'full', 'custom']:
            process_subtitle()

        if MODE in ['audio', 'full', 'custom']:
            process_audio()

        print("\n" + "=" * 60)
        print("✅ 所有处理完成！")
        print("=" * 60)

        # 输出文件列表
        output_files = []
        if os.path.exists(SUB_VIDEO):
            output_files.append(f"字幕视频: {os.path.abspath(SUB_VIDEO)}")
        if os.path.exists(DUB_VIDEO):
            output_files.append(f"配音视频: {os.path.abspath(DUB_VIDEO)}")

        if output_files:
            print("\n📁 输出文件:")
            for f in output_files:
                print(f"  • {f}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

import os
import sys
import logging

# ===== 第一步：完全禁用 Streamlit 所有警告和日志（必须在任何导入之前） =====
# 禁用所有 streamlit 相关的日志输出
logging.getLogger("streamlit").setLevel(logging.CRITICAL)
logging.getLogger("streamlit.runtime").setLevel(logging.CRITICAL)
logging.getLogger("streamlit.runtime.scriptrunner").setLevel(logging.CRITICAL)
logging.getLogger("streamlit.runtime.scriptrunner_utils").setLevel(logging.CRITICAL)
logging.getLogger("streamlit.runtime.caching").setLevel(logging.CRITICAL)
logging.getLogger("streamlit.runtime.metrics").setLevel(logging.CRITICAL)
logging.getLogger("streamlit.components").setLevel(logging.CRITICAL)
logging.getLogger("streamlit.components.components_manager").setLevel(logging.CRITICAL)

# 设置根日志级别为 ERROR，避免所有 WARNING 级别的输出
logging.basicConfig(level=logging.ERROR, force=True)

# ===== 第二步：设置环境变量抑制警告 =====
os.environ['TORCHAUDIO_USE_BACKEND_DISPATCHER'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['STREAMLIT_LOG_LEVEL'] = 'error'

# ===== 第三步：抑制 warnings 模块 =====
import warnings
warnings.filterwarnings('ignore')

# 抑制所有类型的警告
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', message='.*ScriptRunContext.*')
warnings.filterwarnings('ignore', message='.*component manifest.*')
warnings.filterwarnings('ignore', message='.*TorchAudio.*')
warnings.filterwarnings('ignore', message='.*Torchaudio.*')
warnings.filterwarnings('ignore', message='.*enableCORS.*')
warnings.filterwarnings('ignore', message='.*enableXsrfProtection.*')

from core.st_utils.imports_and_utils import download_subtitle_zip_button, give_star_button, button_style
from core import (load_key, cleanup, delete_dubbing_files,
                  _1_ytdlp, _2_asr, _3_1_split_nlp, _3_2_split_meaning,
                  _4_1_summarize, _4_2_translate, _5_split_sub, _6_gen_sub,
                  _7_sub_into_vid, _8_1_audio_task, _8_2_dub_chunks,
                  _9_refer_audio, _10_gen_audio, _11_merge_audio, _12_dub_to_vid)

# SET PATH
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] += os.pathsep + current_dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="VideoLingo", page_icon="files/logo.svg")

SUB_VIDEO = "output/output_sub.mp4"
DUB_VIDEO = "output/output_dub.mp4"

def text_processing_section():
    st.header(t("b. Translate and Generate Subtitles"))
    with st.container(border=True):
        st.markdown(f"""
        <p style='font-size: 20px;'>
        {t("This stage includes the following steps:")}
        <p style='font-size: 20px;'>
            1. {t("WhisperX word-level transcription")}<br>
            2. {t("Sentence segmentation using NLP and LLM")}<br>
            3. {t("Summarization and multi-step translation")}<br>
            4. {t("Cutting and aligning long subtitles")}<br>
            5. {t("Generating timeline and subtitles")}<br>
            6. {t("Merging subtitles into the video")}
        """, unsafe_allow_html=True)

        if not os.path.exists(SUB_VIDEO):
            if st.button(t("Start Processing Subtitles"), key="text_processing_button"):
                process_text()
                st.rerun()
        else:
            if load_key("burn_subtitles"):
                st.video(SUB_VIDEO)
            download_subtitle_zip_button(text=t("Download All Srt Files"))
            
            if st.button(t("Archive to 'history'"), key="cleanup_in_text_processing"):
                cleanup()
                st.rerun()
            return True

def process_text():
    with st.spinner(t("Using Whisper for transcription...")):
        _2_asr.transcribe()
    with st.spinner(t("Splitting long sentences...")):  
        _3_1_split_nlp.split_by_spacy()
        _3_2_split_meaning.split_sentences_by_meaning()
    with st.spinner(t("Summarizing and translating...")):
        _4_1_summarize.get_summary()
        if load_key("pause_before_translate"):
            input(t("⚠️ PAUSE_BEFORE_TRANSLATE. Go to `output/log/terminology.json` to edit terminology. Then press ENTER to continue..."))
        _4_2_translate.translate_all()
    with st.spinner(t("Processing and aligning subtitles...")): 
        _5_split_sub.split_for_sub_main()
        _6_gen_sub.align_timestamp_main()
    with st.spinner(t("Merging subtitles to video...")):
        _7_sub_into_vid.merge_subtitles_to_video()
    
    st.success(t("Subtitle processing complete! 🎉"))
    st.balloons()

def audio_processing_section():
    st.header(t("c. Dubbing"))
    with st.container(border=True):
        st.markdown(f"""
        <p style='font-size: 20px;'>
        {t("This stage includes the following steps:")}
        <p style='font-size: 20px;'>
            1. {t("Generate audio tasks and chunks")}<br>
            2. {t("Extract reference audio")}<br>
            3. {t("Generate and merge audio files")}<br>
            4. {t("Merge final audio into video")}
        """, unsafe_allow_html=True)
        if not os.path.exists(DUB_VIDEO):
            if st.button(t("Start Audio Processing"), key="audio_processing_button"):
                process_audio()
                st.rerun()
        else:
            st.success(t("Audio processing is complete! You can check the audio files in the `output` folder."))
            if load_key("burn_subtitles"):
                st.video(DUB_VIDEO) 
            if st.button(t("Delete dubbing files"), key="delete_dubbing_files"):
                delete_dubbing_files()
                st.rerun()
            if st.button(t("Archive to 'history'"), key="cleanup_in_audio_processing"):
                cleanup()
                st.rerun()

def process_audio():
    with st.spinner(t("Generate audio tasks")): 
        _8_1_audio_task.gen_audio_task_main()
        _8_2_dub_chunks.gen_dub_chunks()
    with st.spinner(t("Extract refer audio")):
        _9_refer_audio.extract_refer_audio_main()
    with st.spinner(t("Generate all audio")):
        _10_gen_audio.gen_audio()
    with st.spinner(t("Merge full audio")):
        _11_merge_audio.merge_full_audio()
    with st.spinner(t("Merge dubbing to the video")):
        _12_dub_to_vid.merge_video_audio()
    
    st.success(t("Audio processing complete! 🎇"))
    st.balloons()

def main():
    logo_col, _ = st.columns([1,1])
    with logo_col:
        st.image("files/logo.png")
    st.markdown(button_style, unsafe_allow_html=True)
    welcome_text = t("Hello, welcome to VideoLingo. If you encounter any issues, feel free to get instant answers with our Free QA Agent <a href=\"https://share.fastgpt.in/chat/share?shareId=066w11n3r9aq6879r4z0v9rh\" target=\"_blank\">here</a>! You can also try out our SaaS website at <a href=\"https://videolingo.io\" target=\"_blank\">videolingo.io</a> for free!")
    st.markdown(f"<p style='font-size: 20px; color: #808080;'>{welcome_text}</p>", unsafe_allow_html=True)
    # add settings
    with st.sidebar:
        page_setting()
        st.markdown(give_star_button, unsafe_allow_html=True)
    download_video_section()
    text_processing_section()
    audio_processing_section()

if __name__ == "__main__":
    import subprocess
    import sys
    import os

    # 用环境变量防止重复启动
    if os.environ.get("__STREAMLIT_RUNNING__") != "1":
        os.environ["__STREAMLIT_RUNNING__"] = "1"
        # 重新启动当前进程，让环境变量生效
        streamlit_cmd = [sys.executable, "-m", "streamlit", "run", __file__] + sys.argv[1:]
        subprocess.run(streamlit_cmd)
    else:
        main()

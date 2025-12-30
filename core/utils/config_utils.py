import os
import threading
from pathlib import Path

from dotenv import load_dotenv
from ruamel.yaml import YAML

# 加载 .env 文件（优先级：.env.local > .env）
# 先加载 .env 作为基础，再用 .env.local 覆盖（如果存在）
load_dotenv(Path('.env'), override=False)
load_dotenv(Path('.env.local'), override=True)

CONFIG_PATH = 'config.yaml'
lock = threading.Lock()

yaml = YAML()
yaml.preserve_quotes = True

# 环境变量映射表：配置键 -> 环境变量名
ENV_KEY_MAPPING = {
    # API 配置
    'api.key': 'OPENAI_API_KEY',
    'api.base_url': 'OPENAI_API_BASE',
    # ASR 配置
    'whisper.whisperX_302_api_key': 'WHISPERX_302_API_KEY',
    'whisper.elevenlabs_api_key': 'ELEVENLABS_API_KEY',
    # TTS 配置
    'sf_fish_tts.api_key': 'SF_FISH_TTS_API_KEY',
    'openai_tts.api_key': 'OPENAI_TTS_API_KEY',
    'azure_tts.api_key': 'AZURE_TTS_API_KEY',
    'fish_tts.api_key': 'FISH_TTS_API_KEY',
    'sf_cosyvoice2.api_key': 'SF_COSYVOICE2_API_KEY',
    'f5tts.302_api': 'F5TTS_302_API_KEY',
}


# -----------------------
# load & update config
# -----------------------

def load_key(key, default=None):
    """加载配置值，优先从环境变量读取，其次从 config.yaml 读取"""
    # 1. 优先检查环境变量
    env_var = ENV_KEY_MAPPING.get(key)
    if env_var and env_var in os.environ:
        env_value = os.environ[env_var]
        # 如果环境变量有值且不是占位符，返回环境变量的值
        if env_value and not env_value.startswith('your_') and env_value != 'YOUR_API_KEY':
            return env_value

    # 2. 从 config.yaml 读取
    with lock:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
            data = yaml.load(file)

    keys = key.split('.')
    value = data
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            # 配置文件中不存在该键，返回默认值
            return default if default is not None else ''
    return value


def update_key(key, new_value):
    with lock:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
            data = yaml.load(file)

        keys = key.split('.')
        current = data
        for k in keys[:-1]:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return False

        if isinstance(current, dict) and keys[-1] in current:
            current[keys[-1]] = new_value
            with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
                yaml.dump(data, file)
            return True
        else:
            raise KeyError(f"Key '{keys[-1]}' not found in configuration")


# basic utils
def get_joiner(language):
    if language in load_key('language_split_with_space'):
        return " "
    elif language in load_key('language_split_without_space'):
        return ""
    else:
        raise ValueError(f"Unsupported language code: {language}")


if __name__ == "__main__":
    print(load_key('language_split_with_space'))

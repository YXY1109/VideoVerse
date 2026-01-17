

安装依赖包：
uv add ruff --optional dev
uv sync --extra dev

安装demucs，本地安装：
uv pip install D:\PycharmProjects\VideoVerse\files\demucs-main

代码质量检查：
uv run ruff check --fix .
uv run ruff format .
uv run mypy .
uv run bandit -r .
uv run pytest


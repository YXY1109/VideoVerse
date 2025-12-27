uv init -p 3.10
uv sync
pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu118
uv pip install git+https://github.com/adefossez/demucs.git
uv pip install numpy==1.26.4
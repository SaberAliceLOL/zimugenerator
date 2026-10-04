"""预下载模型到本地缓存（国内走 hf-mirror 镜像，加速首次运行）。

用法：venv\\Scripts\\python.exe prefetch_models.py
"""
import os

# 缓存放到项目目录（F 盘），避免占满 C 盘
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("HF_HOME", os.path.join(_PROJECT_DIR, ".hf_cache"))
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from huggingface_hub import snapshot_download  # noqa: E402

REPOS = [
    "mobiuslabsgmbh/faster-whisper-large-v3-turbo",  # 语音识别 large-v3-turbo
    "facebook/nllb-200-distilled-600M",              # 中英双向翻译
]

for repo in REPOS:
    print("正在下载 %s ..." % repo, flush=True)
    try:
        snapshot_download(repo)
        print("完成 %s" % repo, flush=True)
    except Exception as e:  # noqa: BLE001
        print("失败 %s: %s" % (repo, e), flush=True)

print("MODELS_PREFETCH_DONE")

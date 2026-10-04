"""一键获取翻译模型（OPUS-MT 转 CTranslate2 格式）。

运行前需先安装转换依赖（仅转换时需要，转换后可卸载）：
    pip install transformers torch

运行：
    python download_models.py

会生成 models/opus-mt-zh-en 和 models/opus-mt-en-zh 两个翻译模型。
"""
import json
import os
import shutil
import subprocess
import sys

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

MODELS = {
    "opus-mt-zh-en": "Helsinki-NLP/opus-mt-zh-en",
    "opus-mt-en-zh": "Helsinki-NLP/opus-mt-en-zh",
}


def _converter():
    exe = shutil.which("ct2-transformers-converter")
    if exe:
        return exe
    d = os.path.dirname(sys.executable)
    for name in ("ct2-transformers-converter.exe", "ct2-transformers-converter"):
        p = os.path.join(d, name)
        if os.path.isfile(p):
            return p
    return None


def main():
    converter = _converter()
    if not converter:
        print("错误：找不到 ct2-transformers-converter，请先 pip install ctranslate2")
        sys.exit(1)

    base = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(base, "models")
    os.makedirs(models_dir, exist_ok=True)

    from huggingface_hub import hf_hub_download

    for name, repo in MODELS.items():
        out = os.path.join(models_dir, name)
        if os.path.isfile(os.path.join(out, "model.bin")):
            print("[跳过] %s 已存在" % name)
            continue

        print("[转换] %s -> %s" % (repo, out))
        subprocess.run(
            [converter, "--model", repo, "--output_dir", out,
             "--force", "--quantization", "float16"],
            check=True,
        )

        # 补 sentencepiece 文件（ctranslate2 需要，转换器默认不复制）
        for f in ("source.spm", "target.spm"):
            hf_hub_download(repo, f, local_dir=out)

        # Marian 模型需源语言加 </s> 结束符，否则会重复生成
        cfg_path = os.path.join(out, "config.json")
        cfg = json.load(open(cfg_path, encoding="utf-8"))
        cfg["add_source_eos"] = True
        json.dump(cfg, open(cfg_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

        print("[完成] %s" % name)

    print("翻译模型获取完成，位于 %s" % models_dir)


if __name__ == "__main__":
    main()

"""基于 CTranslate2 版 OPUS-MT 的中英双向翻译模块（离线，无 torch 依赖）。

中→英用 Helsinki-NLP/opus-mt-zh-en，英→中用 Helsinki-NLP/opus-mt-en-zh，
转换为 CTranslate2 格式后由 ctranslate2 加载（与 faster-whisper 同生态），
相比 NLLB 蒸馏小模型：en→zh 质量明显更好，且彻底去掉 PyTorch（打包体积大减）。
"""
import os
import sys

import ctranslate2
import sentencepiece as spm


def _find_models_dir():
    """定位 models 目录（exe/项目同级的 models 文件夹，含 opus-mt 模型）。"""
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates = [exe_dir]
        d = exe_dir
        for _ in range(2):  # 向上找两级，覆盖 dist/ 嵌套
            d = os.path.dirname(d)
            candidates.append(d)
        for c in candidates:
            m = os.path.join(c, "models")
            if os.path.isdir(os.path.join(m, "opus-mt-zh-en")):
                return m
        return os.path.join(exe_dir, "models")
    # 开发模式：subtitle_app/ 的上级（项目根）下的 models
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")


_MODELS_DIR = _find_models_dir()


class Translator:
    """OPUS-MT 翻译器：中文↔英文双向。"""

    def __init__(self, device="cuda"):
        use_cuda = device == "cuda" and ctranslate2.get_cuda_device_count() > 0
        self.device = "cuda" if use_cuda else "cpu"
        compute_type = "float16" if use_cuda else "float32"

        zh2en_dir = os.path.join(_MODELS_DIR, "opus-mt-zh-en")
        en2zh_dir = os.path.join(_MODELS_DIR, "opus-mt-en-zh")

        self.zh2en = ctranslate2.Translator(zh2en_dir, device=self.device, compute_type=compute_type)
        self.en2zh = ctranslate2.Translator(en2zh_dir, device=self.device, compute_type=compute_type)

        # 两个方向的 sentencepiece 分词器（source=源语言，target=目标语言）
        self.zh_src = spm.SentencePieceProcessor(model_file=os.path.join(zh2en_dir, "source.spm"))
        self.zh_tgt = spm.SentencePieceProcessor(model_file=os.path.join(zh2en_dir, "target.spm"))
        self.en_src = spm.SentencePieceProcessor(model_file=os.path.join(en2zh_dir, "source.spm"))
        self.en_tgt = spm.SentencePieceProcessor(model_file=os.path.join(en2zh_dir, "target.spm"))

    def translate_batch(self, texts, to_english):
        """批量翻译。to_english=True 译成英文，否则译成中文。返回等长译文列表。"""
        if not texts:
            return []
        if to_english:
            translator, src_sp, tgt_sp = self.zh2en, self.zh_src, self.zh_tgt
        else:
            translator, src_sp, tgt_sp = self.en2zh, self.en_src, self.en_tgt

        tokens = [src_sp.encode(t, out_type=str) for t in texts]
        results = translator.translate_batch(tokens, beam_size=4)
        return [tgt_sp.decode(r.hypotheses[0]) for r in results]

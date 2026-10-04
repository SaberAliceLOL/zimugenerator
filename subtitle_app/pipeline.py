"""端到端流水线：识别 -> 翻译 -> 生成字幕 -> 烧录。

进度按阶段划分到 0~1 区间，由 on_progress 回调上抛给 GUI。
"""
import os
import tempfile

import av

from .transcriber import Transcriber
from .translator import Translator
from .subtitles import build_ass
from .burner import burn_subtitles


def _probe_video(path):
    """读取视频分辨率（PyAV 随 faster-whisper 一并安装）。"""
    container = av.open(path)
    try:
        stream = container.streams.video[0]
        return int(stream.width or 0), int(stream.height or 0)
    finally:
        container.close()


def run_pipeline(video_path, output_path, model_size, device, font_size,
                 use_gpu_encode=True, position="bottom", on_progress=None):
    """执行完整流程，返回输出文件路径。on_progress(fraction, message)。"""
    on_progress = on_progress or (lambda f, m: None)

    on_progress(0.00, "正在读取视频信息...")
    width, height = _probe_video(video_path)

    on_progress(0.01, "正在加载语音识别模型（首次运行会自动下载）...")
    compute = "float16" if device == "cuda" else "int8"
    transcriber = Transcriber(model_size=model_size, device=device, compute_type=compute)

    on_progress(0.02, "正在识别语音并生成时间轴...")

    def _trans_progress(f):
        on_progress(0.02 + f * 0.58, "识别中：%.0f%%" % (f * 100))

    language, segments, info = transcriber.transcribe(video_path, progress_cb=_trans_progress)
    duration = float(getattr(info, "duration", 0.0) or 0.0)

    on_progress(0.60, "检测到语言「%s」，正在加载翻译模型..." % language)
    translator = Translator(device=device)
    to_english = language == "zh"

    texts = [s.text for s in segments]
    translations = []
    batch = 8
    for i in range(0, len(texts), batch):
        chunk = texts[i:i + batch]
        translations.extend(translator.translate_batch(chunk, to_english))
        f = (i + len(chunk)) / len(texts) if texts else 1.0
        on_progress(0.60 + f * 0.28, "翻译中：%.0f%%" % (f * 100))

    on_progress(0.88, "正在生成双语字幕样式...")
    tmpdir = tempfile.mkdtemp(prefix="subtitle_")
    ass_path = os.path.join(tmpdir, "subtitle.ass")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(build_ass(segments, translations, width, height, font_size, position))

    on_progress(0.90, "正在烧录字幕到视频（%s）..." % ("GPU 硬件编码" if use_gpu_encode else "CPU 编码"))

    def _burn_progress(f):
        on_progress(0.90 + f * 0.10, "烧录中：%.0f%%" % (f * 100))

    burn_subtitles(video_path, ass_path, output_path,
                   duration=duration, use_gpu=use_gpu_encode, progress_cb=_burn_progress)

    on_progress(1.00, "完成！")
    return output_path

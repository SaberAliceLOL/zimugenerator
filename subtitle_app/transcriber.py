"""基于 faster-whisper 的语音识别模块。

提供词级时间戳、语音活动检测（VAD）和自动语言检测，
是整套工具「准确字幕」的核心来源。
"""
from faster_whisper import WhisperModel


class Transcriber:
    """封装 faster-whisper 模型，负责把音视频转成带时间轴的分段文本。"""

    def __init__(self, model_size="large-v3-turbo", device="cuda", compute_type="float16"):
        self.model_size = model_size
        # device="cuda" 时用 float16 加速；CPU 用 int8 量化省内存
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, media_path, progress_cb=None):
        """识别音视频文件。

        参数:
            media_path: 视频或音频文件路径（faster-whisper 内部用 PyAV 解码，可直接传视频）。
            progress_cb: 可选回调 progress_cb(fraction)，fraction ∈ [0, 1]。

        返回:
            (language, segments, info)：
                language  检测到的语言代码（如 "zh"、"en"）；
                segments  分段列表，每段含 .start / .end / .text / .words；
                info      识别元信息（含 .duration 音频时长）。
        """
        segments, info = self.model.transcribe(
            media_path,
            language=None,          # 自动检测语言
            task="transcribe",
            beam_size=5,            # 更大的 beam 提升准确率
            word_timestamps=True,   # 词级时间戳，让时间轴更精准
            vad_filter=True,        # 语音活动检测，过滤静音/背景段
            vad_parameters={"min_silence_duration_ms": 500},
        )

        duration = float(getattr(info, "duration", 0.0) or 0.0)
        results = []
        for seg in segments:
            results.append(seg)
            if progress_cb and duration:
                progress_cb(min(seg.end / duration, 1.0))

        return info.language, results, info

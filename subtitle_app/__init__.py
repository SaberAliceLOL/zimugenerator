"""视频字幕生成器 —— 核心包。

流水线：语音识别 (faster-whisper) -> 中英翻译 (NLLB) -> 生成 ASS 双语字幕 -> ffmpeg 烧录。
"""

__version__ = "0.1.0"

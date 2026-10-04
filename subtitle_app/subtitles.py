"""生成 ASS 双语字幕。

ASS 相比 SRT 能精确控制字体、字号、描边、位置，烧录效果更好。
每行字幕为「原文 + 译文」两行对照（用 ASS 换行符分隔）。
"""


def _fmt_time(t):
    """秒 -> ASS 时间格式 H:MM:SS.cc（厘秒）。"""
    t = max(0.0, t)
    total_cs = int(round(t * 100))
    h = total_cs // 360000
    m = (total_cs // 6000) % 60
    s = (total_cs // 100) % 60
    cs = total_cs % 100
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _clean(text):
    """清理字幕文本，去掉换行并转义 ASS 特殊字符。"""
    text = (text or "").replace("\n", " ").replace("\r", " ").strip()
    text = text.replace("\\", "").replace("{", "(").replace("}", ")")
    return text


def build_ass(segments, translations, width, height, font_size, position="bottom"):
    """把识别分段和译文拼装成 ASS 字幕文本。

    参数:
        segments:      识别分段列表（含 .start / .end / .text）。
        translations:  与 segments 一一对应的译文列表。
        width/height:  视频分辨率，用于设置 PlayRes 让字号相对缩放。
        font_size:     基准字号（按 1080p 计算）。
        position:      "bottom" 或 "top"。
    """
    width = width or 1920
    height = height or 1080
    scaled = max(18, round(font_size * height / 1080))
    margin_v = max(20, int(height * 0.05))
    alignment = 2 if position == "bottom" else 8  # 2=底部居中 8=顶部居中

    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: %d" % width,
        "PlayResY: %d" % height,
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Microsoft YaHei,%d,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,"
        "0,0,0,0,100,100,0,0,1,2,1,%d,10,10,%d,1" % (scaled, alignment, margin_v),
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    for seg, trans in zip(segments, translations):
        original = _clean(seg.text)
        translated = _clean(trans)
        if translated and translated.lower() != original.lower():
            text = original + "\\N" + translated
        else:
            text = original
        if not text:
            continue
        lines.append(
            "Dialogue: 0,%s,%s,Default,,0,0,0,,%s" % (_fmt_time(seg.start), _fmt_time(seg.end), text)
        )

    return "\n".join(lines)

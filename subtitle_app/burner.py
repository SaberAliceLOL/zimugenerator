"""用 ffmpeg 将 ASS 字幕硬烧录进视频。

有 NVIDIA GPU 时走 NVENC 硬件编码，否则回退 libx264。
"""
import glob
import os
import shutil
import subprocess


def find_ffmpeg():
    """查找 ffmpeg：exe 同级 -> PATH -> winget 安装目录 -> 项目本地 bin。"""
    import sys

    # 打包后：优先 exe 同级 / _MEIPASS（PyInstaller 解包目录）里的 ffmpeg.exe
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        meipass = getattr(sys, "_MEIPASS", exe_dir)
        for base in (exe_dir, meipass):
            for rel in ("ffmpeg.exe", os.path.join("bin", "ffmpeg.exe")):
                p = os.path.join(base, rel)
                if os.path.isfile(p):
                    return p

    exe = shutil.which("ffmpeg")
    if exe:
        return exe

    # winget 安装位置（新装的 PATH 可能要重启 shell 才生效，这里兜底）
    localappdata = os.environ.get("LOCALAPPDATA", "")
    packages = os.path.join(localappdata, "Microsoft", "WinGet", "Packages")
    if localappdata and os.path.isdir(packages):
        for p in glob.glob(os.path.join(packages, "**", "ffmpeg.exe"), recursive=True):
            return p

    # 项目本地 bin
    local_bin = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bin", "ffmpeg.exe"
    )
    if os.path.isfile(local_bin):
        return local_bin

    return None


def _build_cmd(ffmpeg, video_in, ass_name, video_out, use_gpu, acodec):
    """构造 ffmpeg 命令。acodec: 'copy' 或 'aac'。"""
    if use_gpu:
        vcodec = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "18"]
    else:
        vcodec = ["-c:v", "libx264", "-preset", "medium", "-crf", "18"]

    acodec_args = ["-c:a", acodec]
    if acodec == "aac":
        acodec_args += ["-b:a", "192k"]

    return [
        ffmpeg, "-y",
        "-i", video_in,
        "-vf", "subtitles=%s" % ass_name,
        *vcodec,
        *acodec_args,
        "-progress", "pipe:1",
        "-nostats",
        "-loglevel", "error",
        video_out,
    ]


def _run(cmd, ass_dir, duration, progress_cb):
    """执行 ffmpeg，解析进度；返回 (returncode, stderr)。"""
    proc = subprocess.Popen(
        cmd,
        cwd=ass_dir,  # 字幕用相对文件名，避免 Windows 路径转义问题
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    for line in proc.stdout:
        line = line.strip()
        if line.startswith("out_time_ms=") and progress_cb and duration:
            try:
                ms = int(line.split("=", 1)[1])
                progress_cb(min(ms / (duration * 1000), 1.0))
            except ValueError:
                pass
    err = proc.stderr.read()
    ret = proc.wait()
    return ret, err


def burn_subtitles(video_in, ass_path, video_out, duration=None, use_gpu=True, progress_cb=None):
    """把 ass_path 烧录到 video_in，输出 video_out。

    编码器按 NVENC(硬件) -> libx264(CPU) 依次尝试，NVENC 因驱动不兼容失败时自动回退。
    音轨优先复制，失败（如 webm/opus 不兼容 mp4）则回退为 AAC。
    """
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError(
            "未找到 ffmpeg。请先安装并加入 PATH：\n"
            "  winget install Gyan.FFmpeg\n"
            "或从 https://www.gyan.dev/ffmpeg/builds/ 下载后配置环境变量。"
        )

    ass_dir = os.path.dirname(os.path.abspath(ass_path))
    ass_name = os.path.basename(ass_path)

    encoders = ["nvenc", "x264"] if use_gpu else ["x264"]
    last_err = ""
    for enc in encoders:
        use_gpu_this = enc == "nvenc"
        for acodec in ("copy", "aac"):
            cmd = _build_cmd(ffmpeg, video_in, ass_name, video_out, use_gpu_this, acodec)
            ret, err = _run(cmd, ass_dir, duration, progress_cb)
            if ret == 0:
                return video_out
            last_err = err

    tail = "\n".join(last_err.strip().splitlines()[-20:]) if last_err else "（无输出）"
    raise RuntimeError("ffmpeg 烧录失败：\n%s" % tail)

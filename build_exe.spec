# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：生成 onedir 形式的「字幕生成器.exe」。

用法：venv\\Scripts\\pyinstaller.exe build_exe.spec
"""
import glob
import os

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

# 需要完整收集的包：含动态库(dll)、数据文件、动态导入的子模块
# 翻译改用 ctranslate2 版 OPUS-MT，已去掉 torch / transformers 等大依赖
COLLECT_ALL = [
    "faster_whisper",
    "ctranslate2",
    "onnxruntime",
    "av",
    "sentencepiece",
    "tokenizers",
    "huggingface_hub",
    "regex",
]
for pkg in COLLECT_ALL:
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# 打包 ffmpeg.exe 到 exe 同级（优先找 winget 安装目录，找不到则提示）
_ffmpeg = None
for _p in glob.glob(r"C:/Users/Alex/AppData/Local/Microsoft/WinGet/Packages/*/ffmpeg-*/bin/ffmpeg.exe"):
    _ffmpeg = _p
    break
if _ffmpeg and os.path.isfile(_ffmpeg):
    binaries.append((_ffmpeg, "."))
else:
    raise SystemExit("未找到 ffmpeg.exe，请先安装（winget install Gyan.FFmpeg）")

a = Analysis(
    ["run.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["torchvision", "torchaudio"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="字幕生成器",
    icon="F:/zimu/icon.ico",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # GUI 应用，不弹出黑色控制台窗口
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="字幕生成器",
)

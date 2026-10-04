# 视频字幕生成器（中英双语 · 烧录硬字幕）

一个本地运行的桌面工具：拖入视频，自动识别语音、翻译成中英双语字幕，并**直接烧录成带字幕的新视频**。

基于开源方案构建：

| 环节 | 库 | 说明 |
|---|---|---|
| 语音识别 | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Whisper 的 CTranslate2 加速版，词级时间戳 + VAD |
| 翻译 | [OPUS-MT](https://github.com/Helsinki-NLP/OPUS-MT) | 中英/英中双向，CTranslate2 加速，离线 |
| 字幕格式 | ASS | 可精确控制字体/字号/描边 |
| 烧录编码 | ffmpeg + NVENC | GPU 硬件编码，速度快 |

## 功能

- 桌面 GUI，支持**拖拽**或点击选择视频（mp4/mkv/mov/avi/webm 等）
- 自动检测语言：中文视频 → 中英对照；英文/其他 → 原文+中文
- 词级时间戳对齐，字幕时间轴更精准
- NVIDIA GPU 加速：识别（CUDA）+ 编码（NVENC）
- 可调模型大小、字号、位置（底部/顶部）
- 模型下载默认走国内镜像（hf-mirror.com），避免 HuggingFace 访问慢

## 环境要求

- Windows / macOS / Linux
- Python 3.10–3.12
- **ffmpeg**（必需，用于烧录）
- 推荐 NVIDIA GPU（无 GPU 也能跑，仅 CPU 较慢）

## 安装

### 1. 安装 ffmpeg

Windows（推荐 winget）：

```bash
winget install Gyan.FFmpeg
```

或从 https://www.gyan.dev/ffmpeg/builds/ 下载 `ffmpeg-release-full`，解压后把 `bin` 目录加入系统 PATH。

验证：

```bash
ffmpeg -version
```

> ⚠️ **GPU 硬件编码（NVENC）与 NVIDIA 驱动版本强相关**：最新版 ffmpeg（9.x）要求驱动 610+。若你的驱动较旧（如 566），NVENC 会报「Driver does not support the required nvenc API version」，程序会自动回退到 CPU 编码（仍可用，只是稍慢）。
> 想用 GPU 编码可二选一：升级 NVIDIA 驱动到 570+；或安装兼容旧驱动的 ffmpeg 版本，例如 `winget install Gyan.FFmpeg --version 6.1.1`（需先 `winget uninstall Gyan.FFmpeg`）。

### 2. 安装 Python 依赖

```bash
cd F:\zimu
python -m venv venv
venv\Scripts\activate        # Windows；macOS/Linux 用 source venv/bin/activate
pip install -r requirements.txt
```

> 依赖不含 PyTorch，体积大幅减小，首次安装较快。

### 3. 启动

```bash
python run.py
```

## 使用

1. 把视频拖进窗口（或点击选择）。
2. 按需调整：模型大小、计算设备、字号、位置、编码方式。
3. 点「开始生成字幕」。

首次运行会自动下载识别模型（约 1.6 GB）。翻译模型（OPUS-MT，约 600 MB）需放在程序同级的 `models` 目录。

输出文件与源视频同目录，命名为 `<原文件名>_字幕.mp4`。

## 模型选择建议（8GB 显存参考）

| 模型 | 速度 | 准确率 | 显存占用 |
|---|---|---|---|
| large-v3-turbo | 快 | 高（推荐） | ~1.6 GB |
| large-v3 | 慢 | 最高 | ~3 GB |
| medium | 更快 | 中高 | ~1.5 GB |
| small | 最快 | 中 | ~0.5 GB |

## 常见问题

**Q：提示「未找到 ffmpeg」？**
未安装或未加入 PATH，见「安装 ffmpeg」步骤。

**Q：模型下载很慢 / 卡住？**
默认已走国内镜像；也可手动设置环境变量 `HF_ENDPOINT=https://hf-mirror.com`。

**Q：选了 GPU 却报 CUDA 相关错误？**
确认已安装 NVIDIA 驱动；或在界面把「计算设备」切到 CPU。

**Q：字幕时间轴/文字不够准？**
- 换用 `large-v3` 模型（更准但更慢）。
- 源视频音质差、背景音乐响会影响识别，属正常现象。

## 项目结构

```
F:\zimu\
├── run.py                    # 启动入口
├── app.py                    # PySide6 桌面界面
├── requirements.txt
└── subtitle_app/
    ├── transcriber.py        # faster-whisper 语音识别
    ├── translator.py         # OPUS-MT 中英翻译
    ├── subtitles.py          # ASS 双语字幕生成
    ├── burner.py             # ffmpeg 烧录
    ├── pipeline.py           # 端到端流水线
    └── worker.py             # 后台线程
```

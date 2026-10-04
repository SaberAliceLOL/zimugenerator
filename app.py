"""视频字幕生成器 —— 桌面 GUI（PySide6）。

拖入视频 -> 选好模型/设备/样式 -> 一键生成烧录中英双语硬字幕的新视频。
"""
import os
import sys

# 关键：必须在导入 faster_whisper / transformers（它们依赖 huggingface_hub）之前设置 HF_HOME 和 HF_ENDPOINT。
# 否则 huggingface_hub 会在 import 时把缓存目录固化为 C 盘默认值（~/.cache/huggingface），
# 导致模型下载到系统盘、撑爆磁盘。
def _default_hf_home():
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates = [exe_dir]
        d = exe_dir
        for _ in range(2):  # 向上找两级，覆盖 dist/ 嵌套目录
            d = os.path.dirname(d)
            candidates.append(d)
        for c in candidates:
            cache = os.path.join(c, ".hf_cache")
            if os.path.isdir(cache):
                return cache
        return os.path.join(exe_dir, ".hf_cache")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), ".hf_cache")


os.environ.setdefault("HF_HOME", _default_hf_home())
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QCheckBox, QProgressBar, QTextEdit, QFileDialog,
    QGroupBox, QFormLayout, QMessageBox,
)

from subtitle_app.worker import Worker

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv",
              ".m4v", ".ts", ".wmv", ".mpg", ".mpeg"}

# 全局样式（浅色 · 现代扁平 · 蓝紫主色）
STYLE = """
QWidget {
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 13px;
    color: #1E293B;
}
QWidget#root { background: #EEF2F8; }

QLabel#title { font-size: 21px; font-weight: 700; color: #0F172A; }
QLabel#subtitle { font-size: 12px; color: #64748B; }
QLabel#status { font-size: 12px; color: #64748B; }

QLabel#drop {
    background: #FFFFFF;
    border: 2px dashed #B9C4D6;
    border-radius: 14px;
    color: #64748B;
    font-size: 14px;
    padding: 26px;
}
QLabel#drop[dragging="true"] {
    border-color: #3B82F6;
    background: #EFF6FF;
    color: #2563EB;
}

QGroupBox {
    background: #FFFFFF;
    border: 1px solid #E4E9F2;
    border-radius: 12px;
    margin-top: 14px;
    padding: 18px 16px 14px 16px;
    font-weight: 600;
    color: #0F172A;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
}

QComboBox, QSpinBox {
    background: #F7F9FC;
    border: 1px solid #DCE3EE;
    border-radius: 8px;
    padding: 5px 10px;
    min-height: 18px;
}
QComboBox:hover, QSpinBox:hover { border-color: #3B82F6; }
QComboBox:focus, QSpinBox:focus { border: 1px solid #3B82F6; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background: #FFFFFF;
    border: 1px solid #E4E9F2;
    border-radius: 8px;
    selection-background-color: #3B82F6;
    selection-color: #FFFFFF;
}

QCheckBox { spacing: 8px; color: #334155; }

QProgressBar {
    background: #E4E9F2;
    border: none;
    border-radius: 8px;
    height: 12px;
    text-align: center;
    font-size: 10px;
    color: #475569;
}
QProgressBar::chunk {
    border-radius: 8px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #6366F1);
}

QTextEdit#log {
    background: #F7F9FC;
    border: 1px solid #E4E9F2;
    border-radius: 10px;
    padding: 8px;
    color: #475569;
    font-size: 12px;
}

QPushButton#start {
    background: #3B82F6;
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 13px;
    font-size: 15px;
    font-weight: 600;
}
QPushButton#start:hover { background: #2563EB; }
QPushButton#start:pressed { background: #1D4ED8; }
QPushButton#start:disabled { background: #A5C4FC; }
"""


class DropLabel(QLabel):
    """可拖拽 / 点击选择视频的区域。"""
    fileDropped = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("drop")
        self.setText("将视频拖拽到此处\n或点击选择文件")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(128)
        self.setAcceptDrops(True)

    def _set_dragging(self, active):
        self.setProperty("dragging", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        self._pick()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self._set_dragging(True)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._set_dragging(False)

    def dropEvent(self, event):
        self._set_dragging(False)
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.splitext(path)[1].lower() in VIDEO_EXTS:
                self.fileDropped.emit(path)
                return

    def _pick(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频", "",
            "视频文件 (*.mp4 *.mkv *.mov *.avi *.webm *.flv *.m4v *.ts *.wmv *.mpg *.mpeg)"
        )
        if path:
            self.fileDropped.emit(path)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("root")
        self.setWindowTitle("视频字幕生成器")
        self.resize(620, 740)
        self.video_path = None
        self.worker = None
        self._model_sizes = ["large-v3-turbo", "large-v3", "medium", "small"]
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(14)

        title = QLabel("视频字幕生成器")
        title.setObjectName("title")
        root.addWidget(title)

        subtitle = QLabel("中英双语字幕 · 一键烧录进视频")
        subtitle.setObjectName("subtitle")
        root.addWidget(subtitle)

        self.drop = DropLabel()
        self.drop.fileDropped.connect(self._on_video)
        root.addWidget(self.drop)

        box = QGroupBox("设置")
        form = QFormLayout(box)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "large-v3-turbo（推荐：快且准）",
            "large-v3（最准，较慢）",
            "medium（更快，稍降准确率）",
            "small（最快，准确率一般）",
        ])
        form.addRow("识别模型", self.model_combo)

        self.device_combo = QComboBox()
        self.device_combo.addItem("GPU（NVIDIA CUDA）", "cuda")
        self.device_combo.addItem("CPU", "cpu")
        form.addRow("计算设备", self.device_combo)

        self.font_spin = QSpinBox()
        self.font_spin.setRange(24, 160)
        self.font_spin.setValue(56)
        self.font_spin.setSuffix(" px@1080p")
        form.addRow("字幕字号", self.font_spin)

        self.pos_combo = QComboBox()
        self.pos_combo.addItem("底部", "bottom")
        self.pos_combo.addItem("顶部", "top")
        form.addRow("字幕位置", self.pos_combo)

        self.gpu_enc_check = QCheckBox("使用 GPU 硬件编码（NVENC，更快）")
        self.gpu_enc_check.setChecked(True)
        form.addRow("视频编码", self.gpu_enc_check)

        root.addWidget(box)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        root.addWidget(self.progress)

        self.status = QLabel("就绪")
        self.status.setObjectName("status")
        root.addWidget(self.status)

        self.log = QTextEdit()
        self.log.setObjectName("log")
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(150)
        root.addWidget(self.log)

        self.btn = QPushButton("开始生成字幕")
        self.btn.setObjectName("start")
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.clicked.connect(self._start)
        root.addWidget(self.btn)

    def _on_video(self, path):
        self.video_path = path
        self.drop.setText("已选择：%s\n（可再次拖入更换）" % os.path.basename(path))
        self._log("已载入视频：%s" % path)

    def _log(self, msg):
        self.log.append(msg)

    def _output_path(self, src):
        base, _ = os.path.splitext(src)
        return base + "_字幕.mp4"

    def _start(self):
        if not self.video_path:
            QMessageBox.warning(self, "提示", "请先选择视频文件。")
            return

        params = dict(
            video_path=self.video_path,
            output_path=self._output_path(self.video_path),
            model_size=self._model_sizes[self.model_combo.currentIndex()],
            device=self.device_combo.currentData(),
            font_size=self.font_spin.value(),
            use_gpu_encode=self.gpu_enc_check.isChecked(),
            position=self.pos_combo.currentData(),
        )

        self.btn.setEnabled(False)
        self.progress.setValue(0)
        self.worker = Worker(params)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_progress(self, p, msg):
        self.progress.setValue(p)
        self.status.setText(msg)
        self._log(msg)

    def _on_finished(self, out):
        self.btn.setEnabled(True)
        self.progress.setValue(100)
        self.status.setText("完成")
        self._log("✅ 完成！输出文件：%s" % out)
        QMessageBox.information(self, "完成", "字幕已烧录完成：\n%s" % out)

    def _on_failed(self, msg):
        self.btn.setEnabled(True)
        self.status.setText("出错")
        self._log("❌ 出错：%s" % msg)
        QMessageBox.critical(self, "错误", msg)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

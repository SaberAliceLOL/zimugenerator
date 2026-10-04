"""后台线程：执行流水线并向 GUI 发进度信号。"""
from PySide6.QtCore import QThread, Signal

from .pipeline import run_pipeline


class Worker(QThread):
    progress = Signal(int, str)   # 0~100，说明文字
    finished = Signal(str)        # 输出文件路径
    failed = Signal(str)          # 错误信息

    def __init__(self, params, parent=None):
        super().__init__(parent)
        self.params = params

    def run(self):
        try:
            out = run_pipeline(
                video_path=self.params["video_path"],
                output_path=self.params["output_path"],
                model_size=self.params["model_size"],
                device=self.params["device"],
                font_size=self.params["font_size"],
                use_gpu_encode=self.params["use_gpu_encode"],
                position=self.params.get("position", "bottom"),
                on_progress=lambda f, msg: self.progress.emit(int(f * 100), msg),
            )
            self.finished.emit(out)
        except Exception as e:  # noqa: BLE001 —— 把异常转成信号上抛给界面
            self.failed.emit(str(e))

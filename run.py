"""启动入口：python run.py 或打包后的 exe。"""
import os
import sys
import traceback


def _write_error_log():
    """启动失败时写日志到 exe/脚本同级（GUI 无控制台，便于排查）。"""
    try:
        base = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
        with open(os.path.join(base, "启动错误.log"), "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
    except Exception:
        pass


if __name__ == "__main__":
    try:
        from app import main
        main()
    except Exception:
        _write_error_log()
        raise

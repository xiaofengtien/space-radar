"""
空间雷达 (SpaceRadar) - 启动入口
"""
import sys
import os

# macOS 原生 Dock 品牌保护：当作为普通 python 脚本被调用时，瞬时切入产品专属二进制名
# 确保 macOS WindowServer / LaunchServices 彻底将进程标识为 SpaceRadar，消除 python3.12 气泡提示
if sys.platform == "darwin" and not getattr(sys, "frozen", False) and os.path.basename(sys.executable) != "SpaceRadar":
    _bin = os.path.join(os.path.dirname(sys.executable), "SpaceRadar")
    try:
        # 必须是实体文件（非软链接），macOS 内核与 Dock 才会将进程名彻底认作 SpaceRadar
        if not os.path.exists(_bin) or os.path.islink(_bin):
            if os.path.islink(_bin):
                try:
                    os.unlink(_bin)
                except Exception:
                    pass
            import shutil
            real_py = os.path.realpath(sys.executable)
            shutil.copy2(real_py, _bin)
            os.chmod(_bin, 0o755)
        if os.path.exists(_bin) and os.access(_bin, os.X_OK):
            os.execv(_bin, [_bin] + sys.argv)
    except Exception:
        pass
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtCore import Qt

from brand import BRAND, get_asset_path
from core.macos_compat import setup_macos_app_identity
from ui.main_window import MainWindow

def main():
    # 启用 macOS 原生进程名与 Dock 品牌标识注入（彻底消除 python3.12 标识）
    setup_macos_app_identity(BRAND.WINDOW_TITLE, BRAND.NAME)

    # 启用高分屏支持与原生抗锯齿
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    app.setApplicationName(BRAND.NAME)
    app.setApplicationDisplayName(BRAND.WINDOW_TITLE)

    icon_path = get_asset_path("app_icon_128.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 全局样式干净重置：消除 macOS Aqua 原生按钮灰框与 QLabel 默认边框
    app.setStyleSheet("""
        QLabel {
            border: none;
            background: transparent;
        }
        QPushButton {
            outline: none;
        }
    """)

    # 全局字体排版系统：使用原生 .AppleSystemUIFont，避免不存在的字体别名查找开销
    font = QFont(".AppleSystemUIFont")
    font.setFamilies([".AppleSystemUIFont", "PingFang SC", "Helvetica Neue", "Arial"])
    font.setPixelSize(13)
    app.setFont(font)

    # 启动主界面
    window = MainWindow()
    window.show()

    # 窗口就绪后二次锁定 macOS 系统级 Dock 进程名
    setup_macos_app_identity(BRAND.WINDOW_TITLE, BRAND.NAME)

    exit_code = app.exec()
    if hasattr(window, "worker") and window.worker and window.worker.isRunning():
        try:
            window.worker.cancel()
            window.worker.terminate()
            window.worker.wait(200)
        except Exception:
            pass
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

"""
空间雷达 (SpaceRadar) - 启动入口
"""
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtCore import Qt

from brand import BRAND
from ui.main_window import MainWindow

def main():
    # 启用高分屏支持与原生抗锯齿
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    app.setApplicationName(BRAND.NAME)
    app.setApplicationDisplayName(BRAND.WINDOW_TITLE)

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

    # 全局字体排版系统：优先系统原生高精无衬线（macOS SF Pro / PingFang SC）
    font = QFont()
    font.setFamilies(["SF Pro Text", "-apple-system", "PingFang SC", "Geist", "Noto Sans SC", "Segoe UI", "sans-serif"])
    font.setPixelSize(13)
    app.setFont(font)

    # 启动主界面
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

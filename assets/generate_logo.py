"""
SpaceRadar 官方客户端矢量应用图标生成脚本
按照 Apple Human Interface Guidelines (macOS Big Sur / Sonoma App Icon) 规范生成
"""
import math
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QPen, QBrush,
    QLinearGradient, QRadialGradient, QConicalGradient, QPixmap
)
from PySide6.QtWidgets import QApplication

def generate_app_icon(size: int = 1024, output_path: str = "assets/icon.png"):
    app = QApplication.instance()
    if not app:
        app = QApplication([])

    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    # 1. 基础尺寸与标准 macOS 824x824 / 1024 视口网格
    padding = size * 0.10
    icon_rect = QRectF(padding, padding, size - 2 * padding, size - 2 * padding)
    radius = icon_rect.width() * 0.225  # Apple 标准超椭圆拟合圆角

    # 2. 柔和环境漫反射投影 (Squircle Ambient Shadow)
    shadow_path = QPainterPath()
    shadow_path.addRoundedRect(icon_rect.translated(0, size * 0.035), radius, radius)
    shadow_grad = QRadialGradient(size * 0.5, size * 0.55, size * 0.45)
    shadow_grad.setColorAt(0.0, QColor(0, 0, 0, 95))
    shadow_grad.setColorAt(0.7, QColor(0, 0, 0, 45))
    shadow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
    painter.fillPath(shadow_path, QBrush(shadow_grad))

    # 3. 主体卡片 (Deep Space Obsidian Squircle)
    squircle_path = QPainterPath()
    squircle_path.addRoundedRect(icon_rect, radius, radius)

    body_grad = QLinearGradient(icon_rect.left(), icon_rect.top(), icon_rect.left(), icon_rect.bottom())
    body_grad.setColorAt(0.0, QColor("#1A1E29"))
    body_grad.setColorAt(0.4, QColor("#12141C"))
    body_grad.setColorAt(1.0, QColor("#0B0D12"))

    painter.save()
    painter.setClipPath(squircle_path)
    painter.fillPath(squircle_path, QBrush(body_grad))

    # 4. 背景同心雷达网格 (Concentric Radar Rings)
    cx = icon_rect.center().x()
    cy = icon_rect.center().y()
    max_r = icon_rect.width() * 0.42

    # 底部微弱径向丁香紫辉光
    glow_grad = QRadialGradient(cx, cy, max_r * 1.1)
    glow_grad.setColorAt(0.0, QColor(124, 58, 237, 70))
    glow_grad.setColorAt(0.6, QColor(124, 58, 237, 20))
    glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
    painter.fillRect(icon_rect, QBrush(glow_grad))

    # 雷达扫描扇区 (Conical Sweep Beam)
    conical = QConicalGradient(cx, cy, 45)
    conical.setColorAt(0.0, QColor(167, 139, 250, 95))
    conical.setColorAt(0.12, QColor(124, 58, 237, 40))
    conical.setColorAt(0.28, QColor(124, 58, 237, 0))
    conical.setColorAt(1.0, QColor(124, 58, 237, 0))
    painter.setBrush(QBrush(conical))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(QPointF(cx, cy), max_r, max_r)

    # 3 重精密同心圆环
    ring_pen = QPen(QColor(167, 139, 250, 45), size * 0.0035)
    painter.setPen(ring_pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawEllipse(QPointF(cx, cy), max_r * 0.35, max_r * 0.35)
    painter.drawEllipse(QPointF(cx, cy), max_r * 0.68, max_r * 0.68)
    
    outer_pen = QPen(QColor(196, 181, 253, 90), size * 0.005)
    painter.setPen(outer_pen)
    painter.drawEllipse(QPointF(cx, cy), max_r, max_r)

    # 雷达十字瞄准准星刻度线
    cross_pen = QPen(QColor(167, 139, 250, 50), size * 0.0025, Qt.DashLine)
    painter.setPen(cross_pen)
    painter.drawLine(QPointF(cx - max_r, cy), QPointF(cx + max_r, cy))
    painter.drawLine(QPointF(cx, cy - max_r), QPointF(cx, cy + max_r))

    # 12 个时钟精准时间点刻度点 (Chronometer Pips - 象征秒级时间点归因)
    for i in range(12):
        angle = i * (math.pi / 6)
        r_inner = max_r * 0.94 if i % 3 != 0 else max_r * 0.90
        r_outer = max_r
        x1 = cx + r_inner * math.cos(angle)
        y1 = cy + r_inner * math.sin(angle)
        x2 = cx + r_outer * math.cos(angle)
        y2 = cy + r_outer * math.sin(angle)

        pip_color = QColor("#DDD6FE") if i % 3 == 0 else QColor(167, 139, 250, 160)
        pip_width = size * 0.005 if i % 3 == 0 else size * 0.003
        painter.setPen(QPen(pip_color, pip_width, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    # 5. 核心超级符号：动感时空雷达 "S" 雕塑
    s_path = QPainterPath()
    # 按照比例绘制流体现代科技感 "S" 徽标
    scale = size * 0.001
    
    # 上半环弧形
    s_path.moveTo(cx + 80 * scale, cy - 90 * scale)
    s_path.cubicTo(cx + 80 * scale, cy - 170 * scale, cx - 110 * scale, cy - 170 * scale, cx - 110 * scale, cy - 90 * scale)
    s_path.cubicTo(cx - 110 * scale, cy - 30 * scale, cx + 110 * scale, cy - 30 * scale, cx + 110 * scale, cy + 90 * scale)
    s_path.cubicTo(cx + 110 * scale, cy + 180 * scale, cx - 90 * scale, cy + 180 * scale, cx - 90 * scale, cy + 100 * scale)

    s_pen_glow = QPen(QColor(124, 58, 237, 120), size * 0.055, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(s_pen_glow)
    painter.drawPath(s_path)

    # 主体电光丁香紫渐变线条
    s_grad = QLinearGradient(cx - 100 * scale, cy - 160 * scale, cx + 100 * scale, cy + 170 * scale)
    s_grad.setColorAt(0.0, QColor("#C4B5FD"))  # 极光亮紫
    s_grad.setColorAt(0.5, QColor("#8B5CF6"))  # 经典紫
    s_grad.setColorAt(1.0, QColor("#6D28D9"))  # 深邃紫
    s_pen = QPen(QBrush(s_grad), size * 0.038, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(s_pen)
    painter.drawPath(s_path)

    # 6. 中心实时探测雷达光标小电珠 (Beacon Pulse Dot)
    pulse_grad = QRadialGradient(cx, cy, size * 0.04)
    pulse_grad.setColorAt(0.0, QColor("#FFFFFF"))
    pulse_grad.setColorAt(0.4, QColor("#C4B5FD"))
    pulse_grad.setColorAt(1.0, QColor(124, 58, 237, 0))
    painter.setBrush(QBrush(pulse_grad))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(QPointF(cx, cy), size * 0.035, size * 0.035)

    painter.restore()

    # 7. 外边框微倒角金属高光 (Inner Chamfer Rim)
    rim_pen = QPen(QColor(255, 255, 255, 38), size * 0.004)
    painter.setPen(rim_pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(icon_rect, radius, radius)

    # 顶部边缘天光高反光弧 (Top Highlight Bevel)
    top_rim_path = QPainterPath()
    top_rim_path.addRoundedRect(icon_rect.adjusted(1, 1, -1, -icon_rect.height() * 0.7), radius, radius)
    top_grad = QLinearGradient(icon_rect.left(), icon_rect.top(), icon_rect.left(), icon_rect.top() + size * 0.15)
    top_grad.setColorAt(0.0, QColor(255, 255, 255, 45))
    top_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
    painter.setPen(Qt.NoPen)
    painter.fillPath(top_rim_path, QBrush(top_grad))

    painter.end()

    # 保存不同尺寸
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    pix.save(output_path, "PNG")
    print(f"Generated {output_path} ({size}x{size})")

    # 同时导出标准 macOS Dock 512x512 和 128x128
    p512 = pix.scaled(512, 512, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    p512.save("assets/icon_512.png", "PNG")
    
    p128 = pix.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    p128.save("assets/icon_128.png", "PNG")

    p32 = pix.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    p32.save("assets/icon_32.png", "PNG")

if __name__ == "__main__":
    generate_app_icon(1024, "assets/icon_1024.png")

"""
自研桌面控件库 (Desktop UI Kit) - 彻底清除任何杂乱边框、方框嵌套与样式污染
1. DockTabItem: 专用无边框药丸标签项，1:1 复刻截图毛玻璃 Dock
2. PosterCard: 使用严格类型 ID 样式，杜绝 QLabel 继承 QFrame 边框产生方框
3. CapsuleButton: 强制 white-space: nowrap，彻底杜绝竖排折行
"""
from __future__ import annotations
from typing import Optional, Callable
from PySide6.QtCore import Qt, QRectF, QPointF, QSize, Signal, QPropertyAnimation, Property
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QBrush, QFontMetrics
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QGraphicsDropShadowEffect, QProgressBar, QSizePolicy
)

from ui.theme import THEME

def apply_soft_shadow(widget: QWidget, blur_radius: int = 24, y_offset: int = 6, alpha: int = 20):
    """为控件注入柔和深浅弥散阴影"""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur_radius)
    shadow.setOffset(0, y_offset)
    shadow.setColor(QColor(18, 22, 30, alpha))
    widget.setGraphicsEffect(shadow)

class ToggleSwitch(QWidget):
    """高精度 macOS / iOS 风格动画微型滑动开关"""
    toggled = Signal(bool)

    def __init__(self, checked: bool = True, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._thumb_position = 1.0 if checked else 0.0
        self.setFixedSize(34, 20)
        self.setCursor(Qt.PointingHandCursor)

        self._anim = QPropertyAnimation(self, b"thumb_position", self)
        self._anim.setDuration(160)

    def get_thumb_position(self) -> float:
        return self._thumb_position

    def set_thumb_position(self, pos: float):
        self._thumb_position = pos
        self.update()

    thumb_position = Property(float, get_thumb_position, set_thumb_position)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._checked = not self._checked
            self._anim.stop()
            self._anim.setStartValue(self._thumb_position)
            self._anim.setEndValue(1.0 if self._checked else 0.0)
            self._anim.start()
            self.toggled.emit(self._checked)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        track_color = QColor(THEME.ACCENT_PURPLE if self._checked else "#3A4252")
        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.NoPen)

        r = self.height() / 2
        painter.drawRoundedRect(0, 0, self.width(), self.height(), r, r)

        thumb_diameter = self.height() - 4
        x = 2 + (self.width() - thumb_diameter - 4) * self._thumb_position
        y = 2

        painter.setBrush(QBrush(Qt.white))
        painter.drawEllipse(QRectF(x, y, thumb_diameter, thumb_diameter))

class CapsuleButton(QPushButton):
    """全圆角胶囊按钮：严格锁死不换行，自适应宽度，防止文字挤压或边框污染"""
    def __init__(self, text: str = "", variant: str = "pill_gray", parent=None):
        super().__init__(text, parent)
        self.variant = variant
        self.setFixedHeight(34)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        
        font = QFont(".AppleSystemUIFont", 10)
        font.setWeight(QFont.DemiBold)
        self.setFont(font)
        fm = QFontMetrics(font)
        text_w = fm.horizontalAdvance(text)
        self.setMinimumWidth(text_w + 32)
        
        self._apply_style()

    def setText(self, text: str):
        super().setText(text)
        fm = QFontMetrics(self.font())
        text_w = fm.horizontalAdvance(text)
        self.setMinimumWidth(text_w + 32)

    def _apply_style(self):
        if self.variant == "white":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    color: #111318;
                    border: none;
                    outline: none;
                    border-radius: 17px;
                    padding: 0 16px;
                    font-weight: 700;
                    white-space: nowrap;
                }
                QPushButton:hover {
                    background-color: #F0F2F6;
                }
                QPushButton:pressed {
                    background-color: #E2E6ED;
                }
            """)
        elif self.variant == "dark":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #111318;
                    color: #FFFFFF;
                    border: none;
                    outline: none;
                    border-radius: 17px;
                    padding: 0 18px;
                    font-weight: 600;
                    white-space: nowrap;
                }
                QPushButton:hover {
                    background-color: #20242C;
                }
                QPushButton:pressed {
                    background-color: #080A0D;
                }
            """)
        elif self.variant == "hud_dark":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #1E2330;
                    color: #C2C9D6;
                    border: 1px solid #2B3345;
                    outline: none;
                    border-radius: 17px;
                    padding: 0 14px;
                    font-weight: 500;
                    white-space: nowrap;
                }
                QPushButton:hover {
                    background-color: #282F40;
                    color: #FFFFFF;
                }
            """)
        elif self.variant == "purple":
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME.ACCENT_PURPLE};
                    color: #FFFFFF;
                    border: none;
                    outline: none;
                    border-radius: 17px;
                    padding: 0 16px;
                    font-weight: 600;
                    white-space: nowrap;
                }}
                QPushButton:hover {{
                    background-color: {THEME.ACCENT_PURPLE_HOVER};
                }}
            """)
        else: # pill_gray
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME.BG_PILL_GRAY};
                    color: {THEME.TEXT_BODY};
                    border: 1px solid {THEME.BORDER_SUBTLE};
                    outline: none;
                    border-radius: 17px;
                    padding: 0 14px;
                    font-weight: 500;
                    white-space: nowrap;
                }}
                QPushButton:hover {{
                    background-color: {THEME.BG_PILL_HOVER};
                    color: {THEME.TEXT_MAIN};
                }}
            """)

class Card(QFrame):
    """白色基础圆角卡片，严格杜绝子控件继承边框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CustomCard")
        self.setStyleSheet(f"""
            QFrame#CustomCard {{
                background-color: {THEME.BG_CARD};
                border: 1px solid {THEME.BORDER_SUBTLE};
                border-radius: 16px;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        apply_soft_shadow(self, blur_radius=20, y_offset=4, alpha=15)

class HudCard(QFrame):
    """悬浮居中深黑动态控制岛 (HUD)"""
    action_triggered = Signal()
    dismiss_triggered = Signal()
    navigate_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HudCard")
        self.setFixedWidth(440)
        self.setStyleSheet(f"""
            QFrame#HudCard {{
                background-color: {THEME.HUD_BG};
                border: 1px solid {THEME.HUD_BORDER};
                border-radius: 20px;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        apply_soft_shadow(self, blur_radius=40, y_offset=14, alpha=80)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # 1. 顶部概要
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        self.thumb = QFrame()
        self.thumb.setObjectName("HudThumb")
        self.thumb.setFixedSize(48, 54)
        self.thumb.setStyleSheet("""
            QFrame#HudThumb {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E2330, stop:1 #2B3245);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        thumb_layout = QVBoxLayout(self.thumb)
        thumb_layout.setContentsMargins(2, 6, 2, 6)
        thumb_layout.setAlignment(Qt.AlignCenter)
        self.lbl_ico = QLabel("💬")
        self.lbl_ico.setStyleSheet("font-size: 16px;")
        self.lbl_tag = QLabel("WECHAT")
        self.lbl_tag.setStyleSheet("color: #C4B5FD; font-size: 8px; font-weight: bold;")
        thumb_layout.addWidget(self.lbl_ico, 0, Qt.AlignCenter)
        thumb_layout.addWidget(self.lbl_tag, 0, Qt.AlignCenter)
        top_row.addWidget(self.thumb)

        # 标题与说明
        info_col = QVBoxLayout()
        info_col.setSpacing(3)
        t_row = QHBoxLayout()
        t_row.setSpacing(6)
        self.lbl_title = QLabel("微信聊天与音视频缓存")
        self.lbl_title.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: bold;")
        self.lbl_badge = QLabel("+83.0 GB")
        self.lbl_badge.setStyleSheet("background: rgba(124, 58, 237, 0.35); color: #DDD6FE; font-size: 10px; font-weight: bold; border-radius: 4px; padding: 1px 6px;")
        t_row.addWidget(self.lbl_title)
        t_row.addWidget(self.lbl_badge)
        t_row.addStretch()

        self.lbl_desc = QLabel("群聊视频、小程序与网页缓存 · 正在静默占用大量空间")
        self.lbl_desc.setStyleSheet(f"color: {THEME.TEXT_HINT}; font-size: 11px;")

        info_col.addLayout(t_row)
        info_col.addWidget(self.lbl_desc)
        top_row.addLayout(info_col, 1)

        layout.addLayout(top_row)

        # 2. 进度条与状态
        p_row = QHBoxLayout()
        self.lbl_p_info = QLabel("检测到真实超大占用 · 属于可安全清理范畴")
        self.lbl_p_info.setStyleSheet(f"color: {THEME.TEXT_HINT}; font-size: 11px;")
        self.lbl_pct = QLabel("0%")
        self.lbl_pct.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: bold;")
        p_row.addWidget(self.lbl_p_info)
        p_row.addStretch()
        p_row.addWidget(self.lbl_pct)
        layout.addLayout(p_row)

        self.bar = QProgressBar()
        self.bar.setFixedHeight(6)
        self.bar.setTextVisible(False)
        self.bar.setValue(12)
        self.bar.setStyleSheet("""
            QProgressBar {
                background-color: #202534;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7C3AED, stop:1 #A78BFA);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.bar)

        # 3. 双胶囊操作按钮
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_act = CapsuleButton("▶ 一键释放空间 (-83.0 GB)", variant="white")
        self.btn_act.clicked.connect(self.action_triggered.emit)
        btn_row.addWidget(self.btn_act, 1)

        self.btn_dismiss = CapsuleButton("稍后处理", variant="hud_dark")
        self.btn_dismiss.clicked.connect(self.dismiss_triggered.emit)
        btn_row.addWidget(self.btn_dismiss)

        layout.addLayout(btn_row)

        # 4. 辅助特性入口 (一键直达核心页面)
        feat_row = QHBoxLayout()
        feat_row.setContentsMargins(0, 4, 0, 0)
        nav_targets = [
            ("✨ 智能诊断", 2),
            ("⏱ 定时巡检", 3),
            ("↗ 释放日志", 1),
            ("📋 监控清单", 5)
        ]
        for name, target_idx in nav_targets:
            btn = QPushButton(name)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #A6AFC2;
                    border: none;
                    outline: none;
                    font-size: 11px;
                    padding: 2px 4px;
                }
                QPushButton:hover {
                    color: #FFFFFF;
                }
            """)
            btn.clicked.connect(lambda checked=False, idx=target_idx: self.navigate_requested.emit(idx))
            feat_row.addWidget(btn)
        layout.addLayout(feat_row)

        # 5. 底部开关
        btm_row = QHBoxLayout()
        btm_row.setContentsMargins(0, 2, 0, 0)
        lbl_hint = QLabel("安全瘦身 · 100%保留文字聊天")
        lbl_hint.setStyleSheet(f"color: {THEME.TEXT_HINT}; font-size: 11px;")
        btm_row.addWidget(lbl_hint)
        btm_row.addStretch()

        sw = ToggleSwitch(checked=True)
        lbl_sw = QLabel("通知提醒")
        lbl_sw.setStyleSheet(f"color: {THEME.TEXT_HINT}; font-size: 10px;")
        btm_row.addWidget(sw)
        btm_row.addWidget(lbl_sw)
        layout.addLayout(btm_row)

    def update_data(self, title: str, subtitle: str, size_str: str, tag: str, icon: str):
        self.lbl_title.setText(title)
        self.lbl_desc.setText(subtitle)
        self.lbl_badge.setText(size_str)
        self.lbl_tag.setText(tag)
        self.lbl_ico.setText(icon)
        self.btn_act.setText(f"▶ 一键安全释放 ({size_str})")

class PosterCard(QFrame):
    """
    海报式圆角网格卡片 (截图下方剧目卡片同款)
    严格使用 #PosterCard 隔离样式，杜绝 QLabel 出现任何黑色/灰色方框！
    """
    clicked = Signal()

    def __init__(self, title: str, subtitle: str, size_str: str, safety_text: str, category: str, detail_desc: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("PosterCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame#PosterCard {{
                background-color: {THEME.BG_CARD};
                border: 1px solid {THEME.BORDER_SUBTLE};
                border-radius: 14px;
            }}
            QFrame#PosterCard:hover {{
                border: 1px solid rgba(124, 58, 237, 0.45);
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        apply_soft_shadow(self, blur_radius=16, y_offset=3, alpha=10)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 12)
        layout.setSpacing(8)

        # 上半部分海报缩略图
        self.thumb = QFrame()
        self.thumb.setObjectName("PosterThumb")
        self.thumb.setFixedHeight(120)
        
        bg_gradients = {
            "media": "stop:0 #1C1826, stop:1 #281D3B",
            "social": "stop:0 #14231E, stop:1 #1C332B",
            "ai": "stop:0 #241B2E, stop:1 #38244D",
            "dev": "stop:0 #16202E, stop:1 #22344D",
            "downloads": "stop:0 #1F222B, stop:1 #2A2F3D"
        }
        grad = bg_gradients.get(category, "stop:0 #1C2028, stop:1 #2B3240")
        self.thumb.setStyleSheet(f"""
            QFrame#PosterThumb {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, {grad});
                border-radius: 10px;
                border: none;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)

        t_layout = QVBoxLayout(self.thumb)
        t_layout.setContentsMargins(8, 8, 8, 8)

        # 右上角紫色对勾圆标
        top_h = QHBoxLayout()
        top_h.addStretch()
        check_circle = QLabel("✓")
        check_circle.setFixedSize(18, 18)
        check_circle.setAlignment(Qt.AlignCenter)
        check_circle.setStyleSheet(f"""
            background-color: {THEME.ACCENT_PURPLE};
            color: #FFFFFF;
            border-radius: 9px;
            font-size: 10px;
            font-weight: bold;
            border: none;
        """)
        top_h.addWidget(check_circle)
        t_layout.addLayout(top_h)
        t_layout.addStretch()

        # 左下角与右下角信息（纯净无边框）
        btm_h = QHBoxLayout()
        btm_h.setSpacing(4)
        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet("color: rgba(255, 255, 255, 0.85); font-size: 11px; font-weight: 500; border: none;")
        lbl_sub.setWordWrap(False)
        
        lbl_size = QLabel(size_str)
        lbl_size.setStyleSheet("background-color: rgba(0, 0, 0, 0.55); color: #FFFFFF; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; font-family: Menlo; border: none;")
        
        btm_h.addWidget(lbl_sub, 1)
        btm_h.addWidget(lbl_size, 0)
        t_layout.addLayout(btm_h)

        layout.addWidget(self.thumb)

        # 下半部分说明
        info_row = QHBoxLayout()
        lbl_m_title = QLabel(title)
        lbl_m_title.setStyleSheet(f"color: {THEME.TEXT_MAIN}; font-size: 13px; font-weight: bold; border: none;")
        
        lbl_saf = QLabel(safety_text)
        if "安全" in safety_text or "保留" in safety_text:
            lbl_saf.setStyleSheet("background-color: #ECFDF5; color: #059669; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; border: none;")
        else:
            lbl_saf.setStyleSheet("background-color: #FFFBEB; color: #D97706; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; border: none;")

        info_row.addWidget(lbl_m_title)
        info_row.addStretch()
        info_row.addWidget(lbl_saf)
        layout.addLayout(info_row)

        desc_text = detail_desc if detail_desc else "真实磁盘占用 · 点击在访达定位"
        lbl_desc = QLabel(desc_text)
        lbl_desc.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 11px; border: none;")
        lbl_desc.setWordWrap(False)
        layout.addWidget(lbl_desc)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

class DockTabItem(QFrame):
    """专用无边框药丸标签项：使用 QFrame 确保背景与圆角药丸高保真绘制，1:1 复刻设计稿"""
    clicked = Signal()

    def __init__(self, name: str, badge: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.setObjectName("DockTabItem")
        self.name = name
        self.badge = badge
        self.is_active = False
        self.is_hovered = False

        self.setFixedHeight(36)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(6)

        self.lbl = QLabel(name)
        font = QFont(".AppleSystemUIFont", 10)
        font.setWeight(QFont.DemiBold)
        self.lbl.setFont(font)
        layout.addWidget(self.lbl)

        if badge:
            self.b_lbl = QLabel(badge)
            self.b_lbl.setFixedSize(16, 16)
            self.b_lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.b_lbl)
        else:
            self.b_lbl = None

        self._update_appearance()

    def set_active(self, active: bool):
        self.is_active = active
        self._update_appearance()

    def set_badge(self, badge: Optional[str]):
        self.badge = badge
        if badge:
            if not self.b_lbl:
                self.b_lbl = QLabel(badge)
                self.b_lbl.setFixedSize(16, 16)
                self.b_lbl.setAlignment(Qt.AlignCenter)
                self.layout().addWidget(self.b_lbl)
            else:
                self.b_lbl.setText(badge)
                self.b_lbl.show()
        else:
            if self.b_lbl:
                self.b_lbl.hide()
        self._update_appearance()

    def enterEvent(self, event):
        self.is_hovered = True
        self._update_appearance()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self._update_appearance()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def _update_appearance(self):
        if self.is_active:
            bg_color = "#EDE9FE"  # 优雅丁香紫高光药丸
            text_color = THEME.ACCENT_PURPLE
            badge_bg = THEME.ACCENT_PURPLE
            badge_fg = "#FFFFFF"
            font_weight = "bold"
        elif self.is_hovered:
            bg_color = "#F1F3F7"
            text_color = THEME.TEXT_MAIN
            badge_bg = "#4B5563"
            badge_fg = "#FFFFFF"
            font_weight = "normal"
        else:
            bg_color = "transparent"
            text_color = THEME.TEXT_MUTED
            badge_bg = "#111318"
            badge_fg = "#FFFFFF"
            font_weight = "normal"

        self.setStyleSheet(f"""
            QFrame#DockTabItem {{
                background-color: {bg_color};
                border-radius: 18px;
                border: none;
            }}
            QLabel {{
                border: none;
                background: transparent;
                color: {text_color};
                font-weight: {font_weight};
                white-space: nowrap;
            }}
        """)
        if self.b_lbl:
            self.b_lbl.setStyleSheet(f"""
                background-color: {badge_bg};
                color: {badge_fg};
                font-size: 9px;
                font-weight: bold;
                border-radius: 8px;
                border: none;
            """)

class FloatingDock(QFrame):
    """
    截图底部悬浮毛玻璃胶囊 Dock 栏 (无任何默认方框，高保真胶囊)
    """
    tab_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FloatingDock")
        self.setFixedHeight(50)
        self.setFixedWidth(640)
        self.setStyleSheet("""
            QFrame#FloatingDock {
                background-color: rgba(255, 255, 255, 0.96);
                border: 1px solid rgba(220, 225, 235, 0.85);
                border-radius: 25px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        apply_soft_shadow(self, blur_radius=30, y_offset=8, alpha=35)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(6)

        self.tab_items: List[DockTabItem] = []
        items = [
            ("增长看板", "1", 0),
            ("时间流水", "6", 1),
            ("极速瘦身", None, 2),
            ("定时巡检", None, 3),
            ("清理规则", None, 4),
            ("设置", None, 5),
        ]

        for name, badge, idx in items:
            tab = DockTabItem(name, badge, self)
            tab.clicked.connect(lambda i=idx: self.select_tab(i))
            layout.addWidget(tab)
            self.tab_items.append(tab)

        self.select_tab(0)

    def select_tab(self, index: int, emit_signal: bool = True):
        for idx, tab in enumerate(self.tab_items):
            tab.set_active(idx == index)
        if emit_signal:
            self.tab_changed.emit(index)

    def set_badge(self, tab_idx: int, badge_text: Optional[str]):
        if 0 <= tab_idx < len(self.tab_items):
            self.tab_items[tab_idx].set_badge(badge_text)

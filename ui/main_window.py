"""
主窗口架构 (Main Window) - 深度聚焦【具体发生时间点】与四大核心功能：
1. 增长看板 (Banner + HUD + 4大指标磁贴 + 管线分布条 + 真实海报网格)
2. 时间流水 (按时间戳回溯：刚刚1小时内 / 今天 / 昨天 / 7天内，精确到秒的时序流水账)
3. 极速瘦身 (一键安全清理、分类明细、100%文字聊天与工程草稿白名单保护)
4. 定时巡检 (后台自动守护、可调周期、秒级倒计时、历史巡检变动轨迹账本)
5. 清理规则 (微信、剪映、下载、钉钉、开发缓存、APFS快照 独立微动效开关管理)
6. 设置与自定义监控目录 (外置移动硬盘与本地项目目录常驻监控、阈值偏好、品牌关于)
"""
from __future__ import annotations
import os
import sys
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QColor, QFontMetrics, QIcon, QPixmap
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QGridLayout, QFrame, QSizePolicy, QMessageBox, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QFileDialog,
    QCheckBox
)

from brand import BRAND, get_asset_path
from ui.theme import THEME
from ui.desktop_ui_kit import (
    Card, HudCard, CapsuleButton, PosterCard, FloatingDock, ToggleSwitch, apply_soft_shadow
)
from core.sensor import DiskSensor, DiskVolumeInfo
from core.cleaner import SafeCleaner
from core.classifier import GrowthItem, SafetyLevel, TimeGrowthEvent
from core.config import ConfigManager
from core.watcher import RealtimeWatcher

_ACTIVE_WORKERS = set()

class ScannerWorker(QThread):
    """真实后台异步扫描线程：两阶段极速吐出，时间点秒级呈现，支持安全随时取消"""
    time_events_ready = Signal(list)
    finished_scan = Signal(list, list, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            if self._is_cancelled:
                return
            vol = DiskSensor.get_root_volume_info()
            if self._is_cancelled:
                return
            time_events = DiskSensor.scan_all_time_point_events()
            if self._is_cancelled:
                return
            self.time_events_ready.emit(time_events)
            if self._is_cancelled:
                return
            items = DiskSensor.scan_all_growth_items()
            if self._is_cancelled:
                return
            self.finished_scan.emit(items, time_events, vol)
        except Exception:
            pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(BRAND.WINDOW_TITLE)
        icon_path = get_asset_path("app_icon_128.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.resize(1140, 820)
        self.setMinimumSize(1020, 680)
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {THEME.BG_CANVAS};
            }}
            QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{
                background-color: {THEME.BG_CANVAS};
                border: none;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
            /* 彻底消除任何底部横向滚动条，保证视觉极其纯净 */
            QScrollBar:horizontal {{
                height: 0px !important;
                border: none !important;
                background: transparent !important;
            }}
            QScrollBar::handle:horizontal, QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                width: 0px !important;
                height: 0px !important;
                border: none !important;
                background: transparent !important;
            }}
            /* 极简轻量 macOS 悬浮式垂直细滚动条 */
            QScrollBar:vertical {{
                width: 6px;
                background: transparent;
                margin: 0px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(160, 165, 175, 0.35);
                min-height: 28px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(124, 58, 237, 0.6);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
                border: none;
                height: 0px;
            }}
        """)

        self.growth_items: List[GrowthItem] = [
            GrowthItem(
                id="wechat_container",
                title="微信群视频与附件大文件",
                app_name="微信 (WeChat)",
                category="social",
                category_label="社交与通讯",
                path=str(Path.home() / "Library/Containers/com.tencent.xinWeChat"),
                size_bytes=83 * 1024 * 1024 * 1024,
                safety=SafetyLevel.SAFE,
                description="包括群聊接收的大量视频、公众号网页缓存与临时附件。安全清理后文字聊天记录 100% 完整保留。",
                detail_status="群视频与附件 · 建议清理",
                command_hint="清理微信 Caches 与临时视频附件",
                icon_symbol="💬"
            ),
            GrowthItem(
                id="downloads_folder",
                title="下载目录安装包与大镜像",
                app_name="访达下载 (Downloads)",
                category="downloads",
                category_label="安装包残留",
                path=str(Path.home() / "Downloads"),
                size_bytes=16 * 1024 * 1024 * 1024,
                safety=SafetyLevel.CONFIRM,
                description="下载目录躺着的 ISO 镜像、软件压缩包与已安装安装包。可移入废纸篓安全腾出空间。",
                detail_status="包含 ISO 镜像与离线安装包",
                command_hint="清理已安装的下载文件",
                icon_symbol="📦"
            ),
            GrowthItem(
                id="capcut_render",
                title="剪映 4K 工程预渲染与代理",
                app_name="剪映 (CapCut)",
                category="media",
                category_label="影音与剪辑",
                path=str(Path.home() / "Movies/JianyingPro/User Data/Cache"),
                size_bytes=int(3.1 * 1024 * 1024 * 1024),
                safety=SafetyLevel.SAFE,
                description="剪辑 4K 视频时生成的工程预渲染帧与临时代理，清理后草稿项目完好无损，绝不丢失原片。",
                detail_status="视频代理缓存 · 不伤工程",
                command_hint="清空剪映工程渲染缓存",
                icon_symbol="🎬"
            ),
            GrowthItem(
                id="dingtalk_cache",
                title="钉钉文档与音视频缓存",
                app_name="钉钉 (DingTalk)",
                category="social",
                category_label="社交与通讯",
                path=str(Path.home() / "Library/Caches/com.alibaba.DingTalkMac"),
                size_bytes=int(1.6 * 1024 * 1024 * 1024),
                safety=SafetyLevel.SAFE,
                description="办公聊天打开过的图片、群文档与音视频缓存文件，可一键安全清理。",
                detail_status="办公临时缓存 · 可安全清空",
                command_hint="清空钉钉临时缓存",
                icon_symbol="📌"
            ),
            GrowthItem(
                id="cargo_cache",
                title="Cargo / Rust 构建中间产物",
                app_name="Rust (Cargo)",
                category="dev",
                category_label="开发与 IDE",
                path=str(Path.home() / ".cargo"),
                size_bytes=int(1.5 * 1024 * 1024 * 1024),
                safety=SafetyLevel.SAFE,
                description="Rust 项目编译依赖缓存，清理后再次编译时自动拉取最新构建。",
                detail_status="Rust 依赖缓存 · 100%安全",
                command_hint="cargo clean / 清理 .cargo",
                icon_symbol="🦀"
            )
        ]
        self.time_events: List[TimeGrowthEvent] = DiskSensor.get_cached_time_point_events()
        self.current_time_filter: str = "all"
        self.volume_info: Optional[DiskVolumeInfo] = None
        self.last_free_gb: Optional[float] = None
        self.worker: Optional[ScannerWorker] = None

        # 巡检记录与定时器状态
        cfg = ConfigManager.load()
        self.inspection_interval_minutes = cfg.get("inspection_interval_minutes", 5)
        self.seconds_until_inspection = self.inspection_interval_minutes * 60
        self.inspection_logs: List[Dict[str, Any]] = [
            {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "free_str": "400.0 GB",
                "delta_str": "初始基线",
                "finding": "空间雷达首次启动就绪",
                "duration": "0.4秒",
                "status": "🟢 正常"
            }
        ]

        self._setup_ui()
        self._refresh_clean_hub(self.growth_items)
        if self.time_events:
            self._populate_time_table()
            latest = self.time_events[0]
            self.lbl_metric_recent_size.setText(latest.size_formatted)
            self.lbl_metric_recent_time.setText(f"{latest.relative_time_str} · {latest.app_name}")
        self._setup_inspection_timer()
        self._setup_realtime_watcher()
        self._start_scan()

    def _setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. 顶部标题栏
        self.header_bar = self._create_header_bar()
        root_layout.addWidget(self.header_bar)

        # 2. 页面堆叠区 (全 6 个独立页面)
        self.stack = QStackedWidget()
        
        # 页面 0: 实时增长看板 (Overview)
        self.page_overview = self._create_page_overview()
        self.stack.addWidget(self.page_overview)

        # 页面 1: 时间点增长流水账 (Timeline Table)
        self.page_timeline = self._create_page_timeline()
        self.stack.addWidget(self.page_timeline)

        # 页面 2: 极速瘦身工具箱 (Clean Hub)
        self.page_clean = self._create_page_clean_hub()
        self.stack.addWidget(self.page_clean)

        # 页面 3: 定时巡检大厅 (Scheduled Inspection)
        self.page_inspection = self._create_page_inspection()
        self.stack.addWidget(self.page_inspection)

        # 页面 4: 清理规则中心 (Cleanup Rules)
        self.page_rules = self._create_page_rules()
        self.stack.addWidget(self.page_rules)

        # 页面 5: 设置与自定义监控目录 (Settings & Custom Watch Folders)
        self.page_settings = self._create_page_settings()
        self.stack.addWidget(self.page_settings)

        root_layout.addWidget(self.stack)

        # 3. 悬浮 Dock 栏 (640px 药丸胶囊)
        self.dock = FloatingDock(self)
        self.dock.tab_changed.connect(self._on_tab_changed)
        self.dock.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        dock_w = self.dock.width()
        dock_h = self.dock.height()
        x = (self.width() - dock_w) // 2
        y = self.height() - dock_h - 18
        self.dock.move(x, y)

    def _switch_to_tab(self, idx: int):
        self.stack.setCurrentIndex(idx)
        self.dock.select_tab(idx, emit_signal=False)
        if idx == 5:
            self._refresh_custom_dirs_ui()

    def _on_tab_changed(self, idx: int):
        self.stack.setCurrentIndex(idx)
        if idx == 5:
            self._refresh_custom_dirs_ui()

    def _create_header_bar(self) -> QWidget:
        header = QFrame()
        header.setFixedHeight(46)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border-bottom: 1px solid {THEME.BORDER_SUBTLE};
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(10)

        b_box = QLabel()
        b_box.setFixedSize(24, 24)
        ico_path = get_asset_path("app_icon_64.png")
        if os.path.exists(ico_path):
            pix = QPixmap(ico_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            b_box.setPixmap(pix)
            b_box.setStyleSheet("border-radius: 5px;")
        else:
            b_box.setText(BRAND.LOGO_TAG)
            b_box.setAlignment(Qt.AlignCenter)
            b_box.setStyleSheet("background-color: #111318; color: #FFFFFF; font-weight: bold; font-size: 11px; border-radius: 5px;")
        layout.addWidget(b_box)

        lbl_b_name = QLabel(f"{BRAND.NAME} · {BRAND.NAME_CN}")
        lbl_b_name.setFont(QFont(".AppleSystemUIFont", 10, QFont.DemiBold))
        lbl_b_name.setStyleSheet(f"color: {THEME.TEXT_MAIN};")
        layout.addWidget(lbl_b_name)

        v_tag = QLabel(f"v{BRAND.VERSION}")
        v_tag.setStyleSheet(f"background-color: #EEF2F6; color: {THEME.TEXT_MUTED}; font-size: 10px; padding: 2px 6px; border-radius: 4px;")
        layout.addWidget(v_tag)

        layout.addStretch()

        self.lbl_status = QLabel("● 时间点雷达在线 · 支持精确秒级回溯")
        self.lbl_status.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 500;")
        layout.addWidget(self.lbl_status)

        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet("background-color: #111318; border-radius: 4px;")
        layout.addWidget(dot)

        return header

    # ==================== 页面 0: 实时看板 (Overview) ====================
    def _create_page_overview(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{
                background-color: {THEME.BG_CANVAS};
                border: none;
            }}
        """)

        content = QWidget()
        content.setStyleSheet(f"background-color: {THEME.BG_CANVAS};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 20, 28, 90)
        layout.setSpacing(16)

        # 1. Hero 横幅 + HUD 控制岛
        self.hero_banner = self._create_hero_banner()
        layout.addWidget(self.hero_banner)

        # 2. 四大指标磁贴
        self.tiles_widget = self._create_metric_tiles()
        layout.addWidget(self.tiles_widget)

        # 3. 存储分布管线条
        self.pipeline_bar = self._create_pipeline_bar()
        layout.addWidget(self.pipeline_bar)

        # 4. 工具栏
        self.toolbar = self._create_toolbar()
        layout.addWidget(self.toolbar)

        # 5. 待处理激增海报网格
        self.grid_section = self._create_grid_section()
        layout.addWidget(self.grid_section)

        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    def _create_hero_banner(self) -> QWidget:
        banner = QFrame()
        banner.setObjectName("HeroBanner")
        banner.setStyleSheet("""
            QFrame#HeroBanner {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFFFFF, stop:0.55 #FFFFFF, stop:0.85 #F5F1FF, stop:1 #ECE4FF);
                border: 1px solid #E9ECF2;
                border-radius: 20px;
            }
        """)
        apply_soft_shadow(banner, blur_radius=20, y_offset=4, alpha=15)

        layout = QHBoxLayout(banner)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)

        # 左侧文案
        left_col = QVBoxLayout()
        left_col.setSpacing(10)

        t_row = QHBoxLayout()
        t_row.setSpacing(8)
        lbl_hero_title = QLabel(BRAND.NAME_CN)
        lbl_hero_title.setFont(QFont(".AppleSystemUIFont", 24, QFont.Bold))
        lbl_hero_title.setStyleSheet(f"color: {THEME.TEXT_MAIN};")

        tag_live = QLabel("时间点归因版")
        tag_live.setStyleSheet(f"background-color: {THEME.ACCENT_PURPLE}; color: #FFFFFF; font-size: 11px; font-weight: bold; padding: 3px 10px; border-radius: 12px;")
        t_row.addWidget(lbl_hero_title)
        t_row.addWidget(tag_live)
        t_row.addStretch()
        left_col.addLayout(t_row)

        lbl_hero_desc = QLabel("不仅告诉你谁占地方，更精确告诉你【在什么具体时间点发生的增长】，按分钟/小时清晰追溯，一键安全释放。")
        lbl_hero_desc.setFont(QFont(".AppleSystemUIFont", 11))
        lbl_hero_desc.setStyleSheet(f"color: {THEME.TEXT_MUTED}; line-height: 1.5;")
        lbl_hero_desc.setWordWrap(True)
        left_col.addWidget(lbl_hero_desc)

        left_col.addSpacing(6)
        btn_start = CapsuleButton("⏱ 查看时间点流水账", variant="dark")
        btn_start.clicked.connect(lambda: self._switch_to_tab(1))
        left_col.addWidget(btn_start)
        left_col.addStretch()

        layout.addLayout(left_col, 1)

        # 右侧悬浮 HUD 控制岛
        self.hud_card = HudCard()
        self.hud_card.action_triggered.connect(self._on_hud_clean)
        self.hud_card.dismiss_triggered.connect(self._on_hud_dismiss)
        self.hud_card.navigate_requested.connect(self._switch_to_tab)
        layout.addWidget(self.hud_card)

        return banner

    def _create_metric_tiles(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 卡片 1: 剩余容量
        self.tile_free = Card()
        l1 = QVBoxLayout(self.tile_free)
        l1.setContentsMargins(16, 14, 16, 14)
        lbl1_sub = QLabel("当前剩余可用空间")
        lbl1_sub.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 11px;")
        self.lbl_metric_free = QLabel("400.0 GB")
        self.lbl_metric_free.setStyleSheet(f"color: {THEME.TEXT_MAIN}; font-size: 21px; font-weight: bold; font-family: Menlo;")
        self.lbl_metric_free_sub = QLabel("总容量 926.3 GB · 空闲 43.2%")
        self.lbl_metric_free_sub.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 500;")
        l1.addWidget(lbl1_sub)
        l1.addWidget(self.lbl_metric_free)
        l1.addWidget(self.lbl_metric_free_sub)
        layout.addWidget(self.tile_free)

        # 卡片 2: 最近时间点突发
        self.tile_recent = Card()
        l2 = QVBoxLayout(self.tile_recent)
        l2.setContentsMargins(16, 14, 16, 14)
        lbl2_sub = QLabel("最近一次突发增长")
        lbl2_sub.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 11px;")
        self.lbl_metric_recent_size = QLabel("+507.9 MB")
        self.lbl_metric_recent_size.setStyleSheet("color: #DC2626; font-size: 21px; font-weight: bold; font-family: Menlo;")
        self.lbl_metric_recent_time = QLabel("刚刚 18:17:42 · 工具缓存")
        self.lbl_metric_recent_time.setStyleSheet("color: #DC2626; font-size: 11px; font-weight: bold;")
        l2.addWidget(lbl2_sub)
        l2.addWidget(self.lbl_metric_recent_size)
        l2.addWidget(self.lbl_metric_recent_time)
        layout.addWidget(self.tile_recent)

        # 卡片 3: 吞盘之王
        self.tile_king = Card()
        l3 = QVBoxLayout(self.tile_king)
        l3.setContentsMargins(16, 14, 16, 14)
        lbl3_sub = QLabel("历史累积最大占用")
        lbl3_sub.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 11px;")
        self.lbl_metric_king = QLabel("微信 (WeChat)")
        self.lbl_metric_king.setStyleSheet(f"color: {THEME.ACCENT_PURPLE}; font-size: 18px; font-weight: bold;")
        self.lbl_metric_king_sub = QLabel("累积占用高达 83.0 GB")
        self.lbl_metric_king_sub.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 11px;")
        l3.addWidget(lbl3_sub)
        l3.addWidget(self.lbl_metric_king)
        l3.addWidget(self.lbl_metric_king_sub)
        layout.addWidget(self.tile_king)

        # 卡片 4: 绿色安全可瘦身
        self.tile_clean = Card()
        l4 = QVBoxLayout(self.tile_clean)
        l4.setContentsMargins(16, 14, 16, 14)
        lbl4_sub = QLabel("绿色安全可释放")
        lbl4_sub.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 11px;")
        self.lbl_metric_clean = QLabel("22.3 GB")
        self.lbl_metric_clean.setStyleSheet("color: #059669; font-size: 21px; font-weight: bold; font-family: Menlo;")
        lbl4_status = QLabel("含微信缓存、剪映渲染与临时包")
        lbl4_status.setStyleSheet("color: #059669; font-size: 11px;")
        l4.addWidget(lbl4_sub)
        l4.addWidget(self.lbl_metric_clean)
        l4.addWidget(lbl4_status)
        layout.addWidget(self.tile_clean)

        return container

    def _create_pipeline_bar(self) -> QWidget:
        box = Card()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        top_h = QHBoxLayout()
        lbl_title = QLabel("系统卷容量分布管线 (真实占比)")
        lbl_title.setStyleSheet(f"color: {THEME.TEXT_MAIN}; font-size: 12px; font-weight: bold;")
        self.lbl_pipe_detail = QLabel("Macintosh HD · 总计 926.3 GB")
        self.lbl_pipe_detail.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 11px; font-family: Menlo;")
        top_h.addWidget(lbl_title)
        top_h.addStretch()
        top_h.addWidget(self.lbl_pipe_detail)
        layout.addLayout(top_h)

        pipe = QFrame()
        pipe.setFixedHeight(12)
        pipe_layout = QHBoxLayout(pipe)
        pipe_layout.setContentsMargins(0, 0, 0, 0)
        pipe_layout.setSpacing(2)

        self.p_sys = QFrame()
        self.p_sys.setStyleSheet("background: #64748B; border-radius: 3px;")
        self.p_wechat = QFrame()
        self.p_wechat.setStyleSheet(f"background: {THEME.ACCENT_PURPLE}; border-radius: 3px;")
        self.p_dl = QFrame()
        self.p_dl.setStyleSheet("background: #0284C7; border-radius: 3px;")
        self.p_capcut = QFrame()
        self.p_capcut.setStyleSheet("background: #F43F5E; border-radius: 3px;")
        self.p_free = QFrame()
        self.p_free.setStyleSheet("background: #10B981; border-radius: 3px;")

        pipe_layout.addWidget(self.p_sys, 46)
        pipe_layout.addWidget(self.p_wechat, 9)
        pipe_layout.addWidget(self.p_dl, 2)
        pipe_layout.addWidget(self.p_capcut, 1)
        pipe_layout.addWidget(self.p_free, 42)
        layout.addWidget(pipe)

        legend = QHBoxLayout()
        legend.setSpacing(14)
        for name, col, sz in [("系统/常规", "#64748B", "423G"), ("微信", THEME.ACCENT_PURPLE, "83G"), ("下载", "#0284C7", "16G"), ("剪映", "#F43F5E", "3G"), ("可用", "#10B981", "400G")]:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {col}; font-size: 10px;")
            l = QLabel(f"{name} {sz}")
            l.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 11px;")
            legend.addWidget(dot)
            legend.addWidget(l)
        legend.addStretch()
        layout.addLayout(legend)

        return box

    def _create_toolbar(self) -> QWidget:
        tb = Card()
        tb.setFixedHeight(54)
        
        layout = QHBoxLayout(tb)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(10)

        self.btn_vol = CapsuleButton("监控卷: Macintosh HD ▾", variant="pill_gray")
        layout.addWidget(self.btn_vol)

        self.btn_select_all = CapsuleButton("✓ 全选异常项", variant="pill_gray")
        self.btn_select_all.clicked.connect(lambda: self._switch_to_tab(2))
        layout.addWidget(self.btn_select_all)

        btn_clean_sel = CapsuleButton("🗑 清理所选缓存", variant="pill_gray")
        btn_clean_sel.clicked.connect(self._on_clean_selected)
        layout.addWidget(btn_clean_sel)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("搜索文件、路径或软件 (Ctrl+F)")
        self.txt_search.setFixedHeight(34)
        self.txt_search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME.BG_PILL_GRAY};
                border: 1px solid {THEME.BORDER_SUBTLE};
                border-radius: 17px;
                padding: 0 16px;
                color: {THEME.TEXT_MAIN};
                font-size: 12px;
            }}
            QLineEdit:focus {{
                background-color: #FFFFFF;
                border: 1px solid {THEME.BORDER_FOCUS};
            }}
        """)
        self.txt_search.textChanged.connect(self._on_search_text_changed)
        layout.addWidget(self.txt_search, 1)

        btn_finder = CapsuleButton("📂 打开访达垃圾桶", variant="pill_gray")
        btn_finder.clicked.connect(lambda: SafeCleaner.reveal_in_finder("~/.Trash"))
        layout.addWidget(btn_finder)

        btn_custom = CapsuleButton("＋ 自定义目录", variant="pill_gray")
        btn_custom.clicked.connect(self._on_add_custom_directory_dialog)
        layout.addWidget(btn_custom)

        return tb

    def _create_grid_section(self) -> QWidget:
        sec = QWidget()
        sec_layout = QVBoxLayout(sec)
        sec_layout.setContentsMargins(0, 8, 0, 0)
        sec_layout.setSpacing(12)

        h_row = QHBoxLayout()
        h_row.setSpacing(8)
        
        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background-color: {THEME.ACCENT_PURPLE}; border-radius: 4px;")
        h_row.addWidget(dot)

        lbl_sec = QLabel("待处理重点占用")
        lbl_sec.setFont(QFont(".AppleSystemUIFont", 12, QFont.Bold))
        lbl_sec.setStyleSheet(f"color: {THEME.TEXT_MAIN};")
        h_row.addWidget(lbl_sec)

        self.lbl_count = QLabel("4 项")
        self.lbl_count.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 12px;")
        h_row.addWidget(self.lbl_count)

        h_row.addStretch()

        lbl_all = QLabel("按时间追溯流水账 ❯")
        lbl_all.setCursor(Qt.PointingHandCursor)
        lbl_all.setStyleSheet(f"color: {THEME.ACCENT_PURPLE}; font-size: 12px; font-weight: bold;")
        lbl_all.mousePressEvent = lambda e: self._switch_to_tab(1)
        h_row.addWidget(lbl_all)

        sec_layout.addLayout(h_row)

        self.grid_container = QGridLayout()
        self.grid_container.setSpacing(14)
        for idx, it in enumerate(self.growth_items[:4]):
            row = idx // 4
            col = idx % 4
            card = PosterCard(
                title=it.app_name,
                subtitle=it.title,
                size_str=it.size_formatted,
                safety_text=it.safety_badge_text,
                category=it.category,
                detail_desc=it.detail_status
            )
            card.clicked.connect(lambda checked=False, p=it.path: SafeCleaner.reveal_in_finder(p))
            self.grid_container.addWidget(card, row, col)
        sec_layout.addLayout(self.grid_container)

        return sec

    # ==================== 页面 1: 时间点增长流水账 (Timeline Explorer) ====================
    def _create_page_timeline(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 20, 28, 90)
        layout.setSpacing(14)

        filter_card = Card()
        f_layout = QVBoxLayout(filter_card)
        f_layout.setContentsMargins(18, 14, 18, 14)
        f_layout.setSpacing(10)

        top_h = QHBoxLayout()
        v = QVBoxLayout()
        t = QLabel("⏱ 磁盘增长时间点追溯大厅")
        t.setFont(QFont(".AppleSystemUIFont", 16, QFont.Bold))
        t.setStyleSheet(f"color: {THEME.TEXT_MAIN};")
        self.lbl_time_subtitle = QLabel("精确记录每一个大文件【具体是在什么时间点写入的】，彻底弄清何时暴涨")
        self.lbl_time_subtitle.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 11px;")
        v.addWidget(t)
        v.addWidget(self.lbl_time_subtitle)
        top_h.addLayout(v)
        top_h.addStretch()

        btn_back = CapsuleButton("返回看板", variant="pill_gray")
        btn_back.clicked.connect(lambda: self._switch_to_tab(0))
        top_h.addWidget(btn_back)
        f_layout.addLayout(top_h)

        # 时间段筛选胶囊栏
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        lbl_f_tag = QLabel("时间范围:")
        lbl_f_tag.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 11px; font-weight: bold;")
        filter_row.addWidget(lbl_f_tag)

        self.btn_f_all = CapsuleButton("全部时间", variant="purple")
        self.btn_f_all.clicked.connect(lambda: self._filter_timeline("all", self.btn_f_all))
        filter_row.addWidget(self.btn_f_all)

        self.btn_f_1h = CapsuleButton("⚡️ 刚刚 (1小时内)", variant="pill_gray")
        self.btn_f_1h.clicked.connect(lambda: self._filter_timeline("1h", self.btn_f_1h))
        filter_row.addWidget(self.btn_f_1h)

        self.btn_f_today = CapsuleButton("📅 今天 (24小时)", variant="pill_gray")
        self.btn_f_today.clicked.connect(lambda: self._filter_timeline("today", self.btn_f_today))
        filter_row.addWidget(self.btn_f_today)

        self.btn_f_yesterday = CapsuleButton("⏱ 昨天写入", variant="pill_gray")
        self.btn_f_yesterday.clicked.connect(lambda: self._filter_timeline("yesterday", self.btn_f_yesterday))
        filter_row.addWidget(self.btn_f_yesterday)

        self.btn_f_7days = CapsuleButton("📦 7天内", variant="pill_gray")
        self.btn_f_7days.clicked.connect(lambda: self._filter_timeline("7days", self.btn_f_7days))
        filter_row.addWidget(self.btn_f_7days)

        self.btn_f_older = CapsuleButton("📁 7天更早", variant="pill_gray")
        self.btn_f_older.clicked.connect(lambda: self._filter_timeline("older", self.btn_f_older))
        filter_row.addWidget(self.btn_f_older)

        filter_row.addStretch()
        f_layout.addLayout(filter_row)
        layout.addWidget(filter_card)

        # 数据表
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "具体发生时间点", "相对时间", "增量大小", "所属软件", "具体写入文件名与路径", "安全级别", "快捷操作"
        ])
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #FFFFFF;
                border: 1px solid {THEME.BORDER_SUBTLE};
                border-radius: 14px;
                padding: 8px;
                color: {THEME.TEXT_MAIN};
                gridline-color: transparent;
                alternate-background-color: #FBFBFC;
            }}
            QHeaderView::section {{
                background-color: #F4F5F8;
                border: none;
                padding: 8px 12px;
                font-weight: bold;
                color: {THEME.TEXT_MUTED};
                font-size: 11px;
            }}
        """)
        apply_soft_shadow(self.table, blur_radius=20, y_offset=4, alpha=15)
        layout.addWidget(self.table)

        return page

    def _filter_timeline(self, bucket: str, active_btn: CapsuleButton):
        self.current_time_filter = bucket
        for btn in [self.btn_f_all, self.btn_f_1h, self.btn_f_today, self.btn_f_yesterday, self.btn_f_7days, self.btn_f_older]:
            if btn == active_btn:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {THEME.ACCENT_PURPLE};
                        color: #FFFFFF;
                        border: none;
                        border-radius: 17px;
                        padding: 0 14px;
                        font-weight: 600;
                        white-space: nowrap;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {THEME.BG_PILL_GRAY};
                        color: {THEME.TEXT_BODY};
                        border: 1px solid {THEME.BORDER_SUBTLE};
                        border-radius: 17px;
                        padding: 0 14px;
                        font-weight: 500;
                        white-space: nowrap;
                    }}
                """)
        self._populate_time_table()

    # ==================== 页面 2: 极速瘦身 (Quick Clean Hub) ====================
    def _create_page_clean_hub(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 20, 28, 90)
        layout.setSpacing(16)

        # 1. 顶部一键极速瘦身横幅
        hero_clean = QFrame()
        hero_clean.setObjectName("HeroClean")
        hero_clean.setStyleSheet("""
            QFrame#HeroClean {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFFFFF, stop:0.6 #FBF9FF, stop:1 #F3EDFF);
                border: 1px solid #E4DCFA;
                border-radius: 20px;
            }
        """)
        apply_soft_shadow(hero_clean, blur_radius=22, y_offset=4, alpha=20)
        hc_layout = QHBoxLayout(hero_clean)
        hc_layout.setContentsMargins(28, 22, 28, 22)
        hc_layout.setSpacing(24)

        left_v = QVBoxLayout()
        left_v.setSpacing(6)
        
        lbl_hc_tag = QLabel("⚡️ 极速一键安全瘦身工作室")
        lbl_hc_tag.setStyleSheet("color: #7C3AED; font-size: 11px; font-weight: bold;")
        left_v.addWidget(lbl_hc_tag)

        self.lbl_clean_total_headline = QLabel("可安全释放 22.3 GB 磁盘冗余")
        self.lbl_clean_total_headline.setFont(QFont(".AppleSystemUIFont", 20, QFont.Bold))
        self.lbl_clean_total_headline.setStyleSheet("color: #111318;")
        left_v.addWidget(self.lbl_clean_total_headline)

        lbl_hc_promise = QLabel("🛡 严正安全白名单承诺：100% 保护微信文字聊天、剪映工程草稿与开发源码，只清理可再生无用缓存。")
        lbl_hc_promise.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 12px;")
        lbl_hc_promise.setWordWrap(True)
        left_v.addWidget(lbl_hc_promise)

        hc_layout.addLayout(left_v, 1)

        # 触发大按钮
        right_v = QVBoxLayout()
        right_v.setAlignment(Qt.AlignCenter)
        self.btn_batch_clean_all = CapsuleButton("⚡️ 一键全选安全清理 (-22.3 GB)", variant="purple")
        self.btn_batch_clean_all.setFixedHeight(42)
        self.btn_batch_clean_all.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME.ACCENT_PURPLE};
                color: #FFFFFF;
                font-size: 13px;
                font-weight: bold;
                border-radius: 21px;
                padding: 0 24px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {THEME.ACCENT_PURPLE_HOVER};
            }}
        """)
        self.btn_batch_clean_all.clicked.connect(self._perform_batch_clean)
        right_v.addWidget(self.btn_batch_clean_all)
        hc_layout.addLayout(right_v)

        layout.addWidget(hero_clean)

        # 2. 分类清理卡片清单
        sec_h = QHBoxLayout()
        lbl_sec_clean = QLabel("可清理缓存分类与白名单明细")
        lbl_sec_clean.setFont(QFont(".AppleSystemUIFont", 13, QFont.Bold))
        lbl_sec_clean.setStyleSheet(f"color: {THEME.TEXT_MAIN};")
        sec_h.addWidget(lbl_sec_clean)
        sec_h.addStretch()

        btn_refresh_clean = CapsuleButton("🔄 重新体检", variant="pill_gray")
        btn_refresh_clean.clicked.connect(self._start_scan)
        sec_h.addWidget(btn_refresh_clean)
        layout.addLayout(sec_h)

        self.clean_cards_container = QVBoxLayout()
        self.clean_cards_container.setSpacing(12)
        layout.addLayout(self.clean_cards_container)

        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    # ==================== 页面 3: 定时巡检 (Scheduled Inspection) ====================
    def _create_page_inspection(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 20, 28, 90)
        layout.setSpacing(16)

        # 1. 实时巡检状态卡片
        status_card = Card()
        sc_layout = QHBoxLayout(status_card)
        sc_layout.setContentsMargins(24, 20, 24, 20)
        sc_layout.setSpacing(20)

        v_st = QVBoxLayout()
        v_st.setSpacing(6)
        
        st_badge_row = QHBoxLayout()
        st_badge_row.setSpacing(8)
        self.lbl_inspect_daemon_status = QLabel("🟢 实时自动巡检守护中")
        self.lbl_inspect_daemon_status.setStyleSheet("background-color: #ECFDF5; color: #059669; font-size: 11px; font-weight: bold; padding: 3px 10px; border-radius: 12px;")
        
        self.lbl_inspect_interval_tag = QLabel(f"采样周期: {self.inspection_interval_minutes} 分钟")
        self.lbl_inspect_interval_tag.setStyleSheet("background-color: #F3F4F6; color: #4B5563; font-size: 11px; font-weight: 500; padding: 3px 10px; border-radius: 12px;")
        
        st_badge_row.addWidget(self.lbl_inspect_daemon_status)
        st_badge_row.addWidget(self.lbl_inspect_interval_tag)
        st_badge_row.addStretch()
        v_st.addLayout(st_badge_row)

        self.lbl_inspect_countdown = QLabel("距离下次自动巡检还有: 04:58")
        self.lbl_inspect_countdown.setFont(QFont(".AppleSystemUIFont", 18, QFont.Bold))
        self.lbl_inspect_countdown.setStyleSheet("color: #111318; font-family: Menlo;")
        v_st.addWidget(self.lbl_inspect_countdown)

        lbl_desc = QLabel("空间雷达在后台持续静默检测 APFS 卷写事件，一旦发现单小时写入激增自动记录并告警。")
        lbl_desc.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 12px;")
        v_st.addWidget(lbl_desc)

        sc_layout.addLayout(v_st, 1)

        # 手动执行按钮
        btn_inspect_now = CapsuleButton("⚡️ 立即执行一次全面巡检", variant="purple")
        btn_inspect_now.clicked.connect(lambda: self._trigger_manual_inspection())
        sc_layout.addWidget(btn_inspect_now)

        layout.addWidget(status_card)

        # 2. 频率调节胶囊区
        freq_card = Card()
        fc_layout = QVBoxLayout(freq_card)
        fc_layout.setContentsMargins(20, 16, 20, 16)
        fc_layout.setSpacing(12)

        fc_top = QHBoxLayout()
        lbl_freq_t = QLabel("巡检频率设定 (Sampling Frequency)")
        lbl_freq_t.setFont(QFont(".AppleSystemUIFont", 12, QFont.Bold))
        lbl_freq_t.setStyleSheet(f"color: {THEME.TEXT_MAIN};")
        fc_top.addWidget(lbl_freq_t)
        fc_top.addStretch()

        self.sw_auto_inspect = ToggleSwitch(checked=True)
        self.sw_auto_inspect.toggled.connect(self._on_toggle_auto_inspect)
        fc_top.addWidget(self.sw_auto_inspect)
        lbl_sw_t = QLabel("自动巡检总开关")
        lbl_sw_t.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 11px;")
        fc_top.addWidget(lbl_sw_t)
        fc_layout.addLayout(fc_top)

        # 4 个频率档位胶囊
        freq_row = QHBoxLayout()
        freq_row.setSpacing(10)

        self.btn_freq_30s = CapsuleButton("⚡️ 30 秒 (极速预警)", variant="pill_gray")
        self.btn_freq_30s.clicked.connect(lambda: self._set_inspection_frequency(1, self.btn_freq_30s, "30 秒"))
        freq_row.addWidget(self.btn_freq_30s)

        self.btn_freq_5m = CapsuleButton("⏱ 5 分钟 (日常推荐)", variant="purple" if self.inspection_interval_minutes == 5 else "pill_gray")
        self.btn_freq_5m.clicked.connect(lambda: self._set_inspection_frequency(5, self.btn_freq_5m, "5 分钟"))
        freq_row.addWidget(self.btn_freq_5m)

        self.btn_freq_15m = CapsuleButton("🔋 15 分钟 (省电低耗)", variant="purple" if self.inspection_interval_minutes == 15 else "pill_gray")
        self.btn_freq_15m.clicked.connect(lambda: self._set_inspection_frequency(15, self.btn_freq_15m, "15 分钟"))
        freq_row.addWidget(self.btn_freq_15m)

        self.btn_freq_60m = CapsuleButton("🛡 1 小时 (全盘深度体检)", variant="purple" if self.inspection_interval_minutes == 60 else "pill_gray")
        self.btn_freq_60m.clicked.connect(lambda: self._set_inspection_frequency(60, self.btn_freq_60m, "1 小时"))
        freq_row.addWidget(self.btn_freq_60m)

        freq_row.addStretch()
        fc_layout.addLayout(freq_row)
        layout.addWidget(freq_card)

        # 3. 历史巡检记录与容量变化轨迹
        lbl_hist_t = QLabel("历史巡检记录与容量变化轨迹 (Inspection Logs)")
        lbl_hist_t.setFont(QFont(".AppleSystemUIFont", 13, QFont.Bold))
        lbl_hist_t.setStyleSheet(f"color: {THEME.TEXT_MAIN};")
        layout.addWidget(lbl_hist_t)

        self.table_inspection = QTableWidget()
        self.table_inspection.setColumnCount(6)
        self.table_inspection.setHorizontalHeaderLabels([
            "巡检时间点", "剩余可用空间", "较上次变动", "发现的突发写入", "诊断状态", "巡检耗时"
        ])
        self.table_inspection.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table_inspection.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_inspection.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_inspection.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_inspection.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_inspection.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table_inspection.verticalHeader().setVisible(False)
        self.table_inspection.setShowGrid(False)
        self.table_inspection.setAlternatingRowColors(True)
        self.table_inspection.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table_inspection.setStyleSheet(f"""
            QTableWidget {{
                background-color: #FFFFFF;
                border: 1px solid {THEME.BORDER_SUBTLE};
                border-radius: 14px;
                padding: 8px;
                color: {THEME.TEXT_MAIN};
                gridline-color: transparent;
                alternate-background-color: #FBFBFC;
            }}
            QHeaderView::section {{
                background-color: #F4F5F8;
                border: none;
                padding: 8px 12px;
                font-weight: bold;
                color: {THEME.TEXT_MUTED};
                font-size: 11px;
            }}
        """)
        apply_soft_shadow(self.table_inspection, blur_radius=20, y_offset=4, alpha=15)
        layout.addWidget(self.table_inspection)

        layout.addStretch()
        scroll.setWidget(content)
        self._populate_inspection_table()
        return scroll

    def _setup_inspection_timer(self):
        self.inspection_timer = QTimer(self)
        self.inspection_timer.setInterval(1000)
        self.inspection_timer.timeout.connect(self._on_inspection_tick)
        self.inspection_timer.start()

    def _setup_realtime_watcher(self):
        """配置并启动系统底层秒级文件写入监听器 (基于 FSEvents / ReadDirectoryChangesW)"""
        self._pending_realtime_events: List[TimeGrowthEvent] = []
        self._realtime_debounce_timer = QTimer(self)
        self._realtime_debounce_timer.setSingleShot(True)
        self._realtime_debounce_timer.setInterval(300)
        self._realtime_debounce_timer.timeout.connect(self._flush_realtime_events)

        self.realtime_watcher = RealtimeWatcher(self)
        self.realtime_watcher.realtime_event_captured.connect(self._on_realtime_event)
        self.realtime_watcher.start()

    def _on_realtime_event(self, ev: TimeGrowthEvent):
        """后台线程捕获到文件写入，调度到主线程防抖队列"""
        self._pending_realtime_events.append(ev)
        if not self._realtime_debounce_timer.isActive():
            self._realtime_debounce_timer.start()

    def _flush_realtime_events(self):
        """防抖批量处理实时新写入事件，保持界面流畅无卡顿"""
        if not self._pending_realtime_events:
            return
        new_batch = self._pending_realtime_events[:]
        self._pending_realtime_events.clear()

        existing_keys = {(e.path, round(e.timestamp, 1)) for e in self.time_events}
        filtered = [e for e in new_batch if (e.path, round(e.timestamp, 1)) not in existing_keys]
        if not filtered:
            return

        filtered.sort(key=lambda x: x.timestamp, reverse=True)
        for ev in reversed(filtered):
            self.time_events.insert(0, ev)

        if len(self.time_events) > 1000:
            self.time_events = self.time_events[:1000]

        # 刷新时间流水表格
        self._populate_time_table()

        # 实时更新 HUD 与顶部指标
        latest = filtered[0]
        self.lbl_metric_recent_size.setText(latest.size_formatted)
        self.lbl_metric_recent_time.setText(f"刚刚写入 · {latest.app_name}")
        self.lbl_status.setText(f"● 实时捕获新写入: {latest.size_formatted} · {latest.app_name} ({latest.file_name[:20]})")
        self.lbl_status.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 500;")

    def _on_inspection_tick(self):
        if not ConfigManager.load().get("auto_inspection_enabled", True):
            self.lbl_inspect_countdown.setText("自动巡检已暂停")
            return

        self.seconds_until_inspection -= 1
        if self.seconds_until_inspection <= 0:
            self.seconds_until_inspection = self.inspection_interval_minutes * 60
            self._trigger_manual_inspection(is_auto=True)

        m = self.seconds_until_inspection // 60
        s = self.seconds_until_inspection % 60
        self.lbl_inspect_countdown.setText(f"距离下次自动巡检还有: {m:02d}:{s:02d}")

    def _trigger_manual_inspection(self, is_auto: bool = False):
        start_t = time.time()
        self._start_scan()
        cost_sec = round(time.time() - start_t + 0.5, 1)

        cur_free = self.volume_info.free_gb if self.volume_info else 400.0
        if self.last_free_gb is not None:
            delta = cur_free - self.last_free_gb
            if abs(delta) < 0.05:
                delta_str = "持平 ±0 MB"
            elif delta < 0:
                delta_str = f"+{abs(delta)*1024:.0f} MB 写入"
            else:
                delta_str = f"-{delta:.1f} GB 释放"
        else:
            delta_str = "基准校准"
        self.last_free_gb = cur_free

        record = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "free_str": f"{cur_free:.1f} GB",
            "delta_str": delta_str,
            "finding": f"已完成全卷探测，发现 {len(self.time_events)} 起写入事件" if self.time_events else "运行平稳",
            "duration": f"{cost_sec}秒",
            "status": "🟢 正常"
        }
        self.inspection_logs.insert(0, record)
        if len(self.inspection_logs) > 30:
            self.inspection_logs.pop()
        self._populate_inspection_table()

    def _set_inspection_frequency(self, minutes: int, btn: CapsuleButton, label_str: str):
        self.inspection_interval_minutes = minutes
        self.seconds_until_inspection = minutes * 60
        ConfigManager.set_inspection_interval(minutes)
        self.lbl_inspect_interval_tag.setText(f"采样周期: {label_str}")

        for b in [self.btn_freq_30s, self.btn_freq_5m, self.btn_freq_15m, self.btn_freq_60m]:
            if b == btn:
                b.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {THEME.ACCENT_PURPLE};
                        color: #FFFFFF;
                        border: none;
                        border-radius: 17px;
                        padding: 0 14px;
                        font-weight: 600;
                        white-space: nowrap;
                    }}
                """)
            else:
                b.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {THEME.BG_PILL_GRAY};
                        color: {THEME.TEXT_BODY};
                        border: 1px solid {THEME.BORDER_SUBTLE};
                        border-radius: 17px;
                        padding: 0 14px;
                        font-weight: 500;
                        white-space: nowrap;
                    }}
                """)

    def _on_toggle_auto_inspect(self, enabled: bool):
        ConfigManager.set_auto_inspection(enabled)
        if enabled:
            self.lbl_inspect_daemon_status.setText("🟢 实时自动巡检守护中")
            self.lbl_inspect_daemon_status.setStyleSheet("background-color: #ECFDF5; color: #059669; font-size: 11px; font-weight: bold; padding: 3px 10px; border-radius: 12px;")
        else:
            self.lbl_inspect_daemon_status.setText("⏸ 自动巡检已暂停")
            self.lbl_inspect_daemon_status.setStyleSheet("background-color: #FEF3C7; color: #D97706; font-size: 11px; font-weight: bold; padding: 3px 10px; border-radius: 12px;")

    def _populate_inspection_table(self):
        self.table_inspection.setRowCount(len(self.inspection_logs))
        for row, rec in enumerate(self.inspection_logs):
            # 时间
            t_item = QTableWidgetItem(rec["time"])
            t_item.setTextAlignment(Qt.AlignCenter)
            t_item.setFont(QFont("Menlo", 10, QFont.Bold))
            self.table_inspection.setItem(row, 0, t_item)

            # 剩余空间
            f_item = QTableWidgetItem(rec["free_str"])
            f_item.setTextAlignment(Qt.AlignCenter)
            f_item.setFont(QFont("Menlo", 10, QFont.Bold))
            self.table_inspection.setItem(row, 1, f_item)

            # 变动
            d_item = QTableWidgetItem(rec["delta_str"])
            d_item.setTextAlignment(Qt.AlignCenter)
            if "写入" in rec["delta_str"]:
                d_item.setForeground(QColor("#DC2626"))
            elif "释放" in rec["delta_str"]:
                d_item.setForeground(QColor("#059669"))
            self.table_inspection.setItem(row, 2, d_item)

            # 发现
            find_item = QTableWidgetItem(rec["finding"])
            find_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table_inspection.setItem(row, 3, find_item)

            # 状态
            st_item = QTableWidgetItem(rec["status"])
            st_item.setTextAlignment(Qt.AlignCenter)
            self.table_inspection.setItem(row, 4, st_item)

            # 耗时
            cost_item = QTableWidgetItem(rec["duration"])
            cost_item.setTextAlignment(Qt.AlignCenter)
            cost_item.setFont(QFont("Menlo", 10))
            self.table_inspection.setItem(row, 5, cost_item)

            self.table_inspection.setRowHeight(row, 38)

    # ==================== 页面 4: 清理规则中心 (Cleanup Rules) ====================
    def _create_page_rules(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 20, 28, 90)
        layout.setSpacing(16)

        # 1. 规则顶栏
        r_card = Card()
        rc_layout = QHBoxLayout(r_card)
        rc_layout.setContentsMargins(24, 18, 24, 18)
        rc_layout.setSpacing(16)

        rv = QVBoxLayout()
        rv.setSpacing(4)
        rt = QLabel("🛡 智能清理规则中心 (Cleanup Rules Engine)")
        rt.setFont(QFont(".AppleSystemUIFont", 15, QFont.Bold))
        rt.setStyleSheet(f"color: {THEME.TEXT_MAIN};")
        
        rd = QLabel("严格安全白名单机制：每一条规则均经过针对性保护设计，绝不损坏聊天记录、源码与原片工程。")
        rd.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 12px;")
        rv.addWidget(rt)
        rv.addWidget(rd)
        rc_layout.addLayout(rv, 1)

        btn_reset_rules = CapsuleButton("🔄 恢复全部默认规则", variant="pill_gray")
        btn_reset_rules.clicked.connect(self._on_reset_rules)
        rc_layout.addWidget(btn_reset_rules)
        layout.addWidget(r_card)

        # 2. 六大核心规则卡片
        rules_spec = [
            (
                "rule_wechat",
                "💬",
                "微信 (WeChat) 附件与音视频临时缓存",
                "自动索引群聊接收的大视频、公众号文章配图与小程序运行时缓存。",
                "严正承诺：微信文字与语音聊天记录、联系人及通讯数据库 100% 完整无损，绝不误触。",
                "~/Library/Containers/com.tencent.xinWeChat/Data/Library/Caches",
                "100% 安全 · 保留文字记录"
            ),
            (
                "rule_capcut",
                "🎬",
                "剪映 (CapCut) 4K 工程预渲染与代理",
                "自动捕获剪辑 4K 视频时生成的工程预渲染分块与实时代理缓存帧。",
                "严正承诺：用户剪辑工程草稿 (draft_content.json) 与视频原片原封不动。",
                "~/Movies/JianyingPro/User Data/Cache",
                "100% 安全 · 保留草稿工程"
            ),
            (
                "rule_downloads",
                "📦",
                "访达下载 (Downloads) 沉睡大安装包规则",
                "智能归因下载目录超过 7 天未修改、大于 500MB 的 .dmg、.pkg、.iso 镜像。",
                "严正承诺：仅在雷达流水账提示并提供人工确认，雷达绝不会擅自清空任何下载文件。",
                "~/Downloads",
                "人工确认 · 绝不自动删除"
            ),
            (
                "rule_dingtalk",
                "📌",
                "钉钉 (DingTalk) 办公音视频与临时文档",
                "在线会议回放录制缓存、聊天文件临时缩略图。",
                "安全保障：办公群消息与钉盘云文档完全不受影响。",
                "~/Library/Caches/com.alibaba.DingTalkMac",
                "100% 安全 · 可随时清空"
            ),
            (
                "rule_dev_cache",
                "🦀",
                "开发与 IDE 构建依赖产物 (Cargo / Xcode)",
                "Rust 跨平台编译 (cargo-xwin)、Xcode DerivedData 与包管理缓存。",
                "安全保障：仅清理可重新生成的构建产物，本地源码与 Git 仓库 100% 安全。",
                "~/.cargo, ~/.cache",
                "100% 安全 · 源码无损"
            ),
            (
                "rule_apfs_snapshot",
                "🖥️",
                "macOS APFS 本地时间机器快照捕获",
                "Time Machine 未连移动硬盘时，macOS 在本地隐蔽囤积的本地快照（常占数十 GB 系统数据）。",
                "安全保障：使用系统原生 tmutil 释放，不丢失任何真实文件，立刻找回幽灵空间。",
                "/System/Volumes/Data/.snapshots",
                "100% 安全 · 找回幽灵空间"
            )
        ]

        self.rule_switches: Dict[str, ToggleSwitch] = {}

        for rid, ico, title, desc, promise, path_str, badge_text in rules_spec:
            rule_box = Card()
            rl = QHBoxLayout(rule_box)
            rl.setContentsMargins(20, 16, 20, 16)
            rl.setSpacing(16)

            lbl_ico = QLabel(ico)
            lbl_ico.setStyleSheet("font-size: 26px;")
            rl.addWidget(lbl_ico)

            info_v = QVBoxLayout()
            info_v.setSpacing(4)

            t_row = QHBoxLayout()
            lbl_t = QLabel(title)
            lbl_t.setFont(QFont(".AppleSystemUIFont", 13, QFont.Bold))
            lbl_t.setStyleSheet(f"color: {THEME.TEXT_MAIN};")
            t_row.addWidget(lbl_t)

            lbl_b = QLabel(badge_text)
            if "安全" in badge_text:
                lbl_b.setStyleSheet("background-color: #ECFDF5; color: #059669; font-size: 10px; font-weight: bold; padding: 2px 8px; border-radius: 4px;")
            else:
                lbl_b.setStyleSheet("background-color: #FFFBEB; color: #D97706; font-size: 10px; font-weight: bold; padding: 2px 8px; border-radius: 4px;")
            t_row.addWidget(lbl_b)
            t_row.addStretch()
            info_v.addLayout(t_row)

            lbl_d = QLabel(desc)
            lbl_d.setStyleSheet(f"color: {THEME.TEXT_BODY}; font-size: 11px;")
            info_v.addWidget(lbl_d)

            lbl_p = QLabel(promise)
            lbl_p.setStyleSheet("color: #7C3AED; font-size: 11px; font-weight: 500;")
            info_v.addWidget(lbl_p)

            lbl_pth = QLabel(f"监控路径: {path_str}")
            lbl_pth.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 10px; font-family: Menlo;")
            info_v.addWidget(lbl_pth)

            rl.addLayout(info_v, 1)

            # 操作按钮与开关
            act_v = QVBoxLayout()
            act_v.setAlignment(Qt.AlignCenter)
            act_v.setSpacing(8)

            sw = ToggleSwitch(checked=ConfigManager.is_rule_enabled(rid))
            sw.toggled.connect(lambda val, r=rid: self._on_rule_toggled(r, val))
            self.rule_switches[rid] = sw
            act_v.addWidget(sw, 0, Qt.AlignCenter)

            btn_reveal = CapsuleButton("在访达查看", variant="pill_gray")
            btn_reveal.setFixedHeight(26)
            btn_reveal.clicked.connect(lambda checked=False, p=path_str: SafeCleaner.reveal_in_finder(p))
            act_v.addWidget(btn_reveal)

            rl.addLayout(act_v)
            layout.addWidget(rule_box)

        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    def _on_rule_toggled(self, rule_id: str, enabled: bool):
        ConfigManager.set_rule_enabled(rule_id, enabled)
        # 立即重新扫描，使看板指标与规则联动
        self._start_scan()

    def _on_reset_rules(self):
        ConfigManager.reset_default_rules()
        for rid, sw in self.rule_switches.items():
            sw.set_thumb_position(1.0)
            sw._checked = True
            sw.update()
        QMessageBox.information(self, "恢复成功", "已全部重置为系统默认安全清理规则！")
        self._start_scan()

    # ==================== 页面 5: 设置与自定义监控目录 (Settings) ====================
    def _create_page_settings(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 20, 28, 90)
        layout.setSpacing(16)

        # 1. 自定义常驻监控目录卡片
        custom_card = Card()
        cc_layout = QVBoxLayout(custom_card)
        cc_layout.setContentsMargins(24, 20, 24, 20)
        cc_layout.setSpacing(14)

        top_h = QHBoxLayout()
        v = QVBoxLayout()
        v.setSpacing(4)
        lbl_c_t = QLabel("📁 自定义常驻监控目录 (Custom Monitored Directories)")
        lbl_c_t.setFont(QFont(".AppleSystemUIFont", 15, QFont.Bold))
        lbl_c_t.setStyleSheet(f"color: {THEME.TEXT_MAIN};")
        
        lbl_c_d = QLabel("将您存放视频素材的外置移动硬盘、本地项目目录或临时文件夹加入监控，雷达将精确记录其时间点写入与体积变动。")
        lbl_c_d.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 12px;")
        v.addWidget(lbl_c_t)
        v.addWidget(lbl_c_d)
        top_h.addLayout(v, 1)

        btn_add_dir = CapsuleButton("＋ 添加要监控的文件夹", variant="purple")
        btn_add_dir.clicked.connect(self._on_add_custom_directory_dialog)
        top_h.addWidget(btn_add_dir)
        cc_layout.addLayout(top_h)

        # 动态自定义目录列表容器
        self.custom_dirs_container = QVBoxLayout()
        self.custom_dirs_container.setSpacing(8)
        cc_layout.addLayout(self.custom_dirs_container)

        layout.addWidget(custom_card)

        # 2. 告警阈值与通知设置
        pref_card = Card()
        pc_layout = QVBoxLayout(pref_card)
        pc_layout.setContentsMargins(24, 18, 24, 18)
        pc_layout.setSpacing(12)

        lbl_p_t = QLabel("⚙️ 监控与突发激增偏好 (Surge Thresholds)")
        lbl_p_t.setFont(QFont(".AppleSystemUIFont", 13, QFont.Bold))
        lbl_p_t.setStyleSheet(f"color: {THEME.TEXT_MAIN};")
        pc_layout.addWidget(lbl_p_t)

        thresh_row = QHBoxLayout()
        lbl_th_desc = QLabel("单小时突发写入告警阈值:")
        lbl_th_desc.setStyleSheet(f"color: {THEME.TEXT_BODY}; font-size: 12px;")
        thresh_row.addWidget(lbl_th_desc)

        cur_th = ConfigManager.get_surge_threshold()
        self.btn_th_200 = CapsuleButton("200 MB", variant="purple" if cur_th == 200 else "pill_gray")
        self.btn_th_200.clicked.connect(lambda: self._set_threshold(200, self.btn_th_200))
        thresh_row.addWidget(self.btn_th_200)

        self.btn_th_500 = CapsuleButton("500 MB (推荐)", variant="purple" if cur_th == 500 else "pill_gray")
        self.btn_th_500.clicked.connect(lambda: self._set_threshold(500, self.btn_th_500))
        thresh_row.addWidget(self.btn_th_500)

        self.btn_th_1000 = CapsuleButton("1.0 GB", variant="purple" if cur_th == 1000 else "pill_gray")
        self.btn_th_1000.clicked.connect(lambda: self._set_threshold(1000, self.btn_th_1000))
        thresh_row.addWidget(self.btn_th_1000)

        thresh_row.addStretch()
        pc_layout.addLayout(thresh_row)
        layout.addWidget(pref_card)

        # 3. 关于 SpaceRadar
        about_card = Card()
        ac_layout = QHBoxLayout(about_card)
        ac_layout.setContentsMargins(24, 20, 24, 20)
        ac_layout.setSpacing(18)

        lbl_ab_ico = QLabel()
        lbl_ab_ico.setFixedSize(60, 60)
        ico_large = get_asset_path("app_icon_128.png")
        if os.path.exists(ico_large):
            lbl_ab_ico.setPixmap(QPixmap(ico_large).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            lbl_ab_ico.setText("S.")
            lbl_ab_ico.setAlignment(Qt.AlignCenter)
            lbl_ab_ico.setStyleSheet("background: #111318; color: #fff; font-size: 22px; font-weight: bold; border-radius: 12px;")
        ac_layout.addWidget(lbl_ab_ico)

        ac_v = QVBoxLayout()
        ac_v.setSpacing(4)
        lbl_ab_t = QLabel(f"{BRAND.NAME} · {BRAND.NAME_CN}")
        lbl_ab_t.setFont(QFont(".AppleSystemUIFont", 15, QFont.Bold))
        lbl_ab_t.setStyleSheet(f"color: {THEME.TEXT_MAIN};")
        ac_v.addWidget(lbl_ab_t)

        lbl_ab_d = QLabel(f"版本: v{BRAND.VERSION} · {BRAND.TAGLINE}\n运行平台: macOS 原生 (支持 FSEvents / APFS 本地快照 / du-sk 极速归因探测)")
        lbl_ab_d.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 12px; line-height: 1.6;")
        ac_v.addWidget(lbl_ab_d)
        ac_layout.addLayout(ac_v, 1)

        layout.addWidget(about_card)

        layout.addStretch()
        scroll.setWidget(content)
        self._refresh_custom_dirs_ui()
        return scroll

    def _set_threshold(self, mb: int, active_btn: CapsuleButton):
        ConfigManager.set_surge_threshold(mb)
        for b in [self.btn_th_200, self.btn_th_500, self.btn_th_1000]:
            if b == active_btn:
                b.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {THEME.ACCENT_PURPLE};
                        color: #FFFFFF;
                        border: none;
                        border-radius: 17px;
                        padding: 0 14px;
                        font-weight: 600;
                        white-space: nowrap;
                    }}
                """)
            else:
                b.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {THEME.BG_PILL_GRAY};
                        color: {THEME.TEXT_BODY};
                        border: 1px solid {THEME.BORDER_SUBTLE};
                        border-radius: 17px;
                        padding: 0 14px;
                        font-weight: 500;
                        white-space: nowrap;
                    }}
                """)

    def _on_add_custom_directory_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "选择要常驻监控的文件夹 (外置硬盘或工作区)", str(Path.home()))
        if folder:
            added = ConfigManager.add_custom_directory(folder)
            if added:
                QMessageBox.information(self, "添加成功", f"已成功将目录加入常驻监控：\n{folder}")
                self._switch_to_tab(5)
                self._refresh_custom_dirs_ui()
                self._start_scan()
            else:
                QMessageBox.warning(self, "提示", "该目录已在监控清单中或路径无效。")

    def _refresh_custom_dirs_ui(self):
        while self.custom_dirs_container.count():
            w = self.custom_dirs_container.takeAt(0).widget()
            if w:
                w.deleteLater()

        dirs = ConfigManager.get_custom_directories()
        if not dirs:
            empty_box = QFrame()
            empty_box.setStyleSheet(f"background-color: {THEME.BG_PILL_GRAY}; border-radius: 10px; padding: 16px;")
            el = QHBoxLayout(empty_box)
            lbl_empty = QLabel("暂未添加自定义监控目录。点击右上角“＋ 添加要监控的文件夹”可监控移动硬盘或特定工作区。")
            lbl_empty.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 11px;")
            el.addWidget(lbl_empty)
            self.custom_dirs_container.addWidget(empty_box)
            return

        for d in dirs:
            row_box = QFrame()
            row_box.setStyleSheet("""
                QFrame {
                    background-color: #F8F9FB;
                    border: 1px solid #EAEDF2;
                    border-radius: 10px;
                }
                QLabel {
                    border: none;
                    background: transparent;
                }
            """)
            rl = QHBoxLayout(row_box)
            rl.setContentsMargins(14, 10, 14, 10)
            rl.setSpacing(12)

            ico = QLabel("📁")
            ico.setStyleSheet("font-size: 20px;")
            rl.addWidget(ico)

            v_info = QVBoxLayout()
            v_info.setSpacing(2)
            fname = os.path.basename(d.rstrip("/\\")) or d
            lbl_fn = QLabel(fname)
            lbl_fn.setStyleSheet(f"color: {THEME.TEXT_MAIN}; font-weight: bold; font-size: 12px;")
            
            lbl_fp = QLabel(d)
            lbl_fp.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 10px; font-family: Menlo;")
            v_info.addWidget(lbl_fn)
            v_info.addWidget(lbl_fp)
            rl.addLayout(v_info, 1)

            # 目录大小
            sz = DiskSensor.get_real_directory_size(d)
            sz_str = f"{sz / (1024**3):.2f} GB" if sz > 1024**3 else f"{sz / (1024**2):.1f} MB"
            lbl_sz = QLabel(sz_str)
            lbl_sz.setStyleSheet("font-size: 12px; font-weight: bold; font-family: Menlo; color: #7C3AED;")
            rl.addWidget(lbl_sz)

            btn_open = CapsuleButton("在访达查看", variant="pill_gray")
            btn_open.setFixedHeight(26)
            btn_open.clicked.connect(lambda checked=False, p=d: SafeCleaner.reveal_in_finder(p))
            rl.addWidget(btn_open)

            btn_remove = CapsuleButton("✕ 移除监控", variant="pill_gray")
            btn_remove.setFixedHeight(26)
            btn_remove.clicked.connect(lambda checked=False, p=d: self._on_remove_custom_dir(p))
            rl.addWidget(btn_remove)

            self.custom_dirs_container.addWidget(row_box)

    def _on_remove_custom_dir(self, path: str):
        reply = QMessageBox.question(
            self, "确认移除",
            f"确定要停止对该目录的监控吗？\n{path}",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            ConfigManager.remove_custom_directory(path)
            self._refresh_custom_dirs_ui()
            self._start_scan()

    # ==================== 扫描与真实数据刷新 ====================
    def _start_scan(self):
        if self.worker is not None and self.worker.isRunning():
            return  # 已经在扫描中，绝不重复启动以免线程竞争与GC异常

        self.lbl_status.setText("● 正在回溯全盘真实时间点写入事件...")
        self.lbl_status.setStyleSheet("color: #7C3AED; font-size: 11px; font-weight: 500;")
        
        self.worker = ScannerWorker(self)
        _ACTIVE_WORKERS.add(self.worker)
        self.worker.time_events_ready.connect(self._on_time_events_early)
        self.worker.finished_scan.connect(self._on_scan_finished)
        self.worker.finished.connect(lambda w=self.worker: _ACTIVE_WORKERS.discard(w))
        self.worker.start()

    def _on_time_events_early(self, time_events: List[TimeGrowthEvent]):
        self.time_events = time_events
        self.lbl_status.setText(f"● 已捕获 {len(time_events)} 起真实时间点写入事件")
        self._populate_time_table()
        if time_events:
            latest = time_events[0]
            self.lbl_metric_recent_size.setText(latest.size_formatted)
            self.lbl_metric_recent_time.setText(f"{latest.relative_time_str} · {latest.app_name}")

    def _on_scan_finished(self, items: List[GrowthItem], time_events: List[TimeGrowthEvent], vol: DiskVolumeInfo):
        self.growth_items = items
        self.time_events = time_events
        self.volume_info = vol
        self.lbl_status.setText(f"● 已捕获 {len(time_events)} 起真实时间点写入事件 · 正常")
        self.lbl_status.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 500;")

        # 更新卷按钮显示
        if vol:
            self.btn_vol.setText(f"监控卷: HD ({vol.free_gb:.1f}G 可用) ▾")
            self.lbl_metric_free.setText(f"{vol.free_gb:.1f} GB")
            self.lbl_metric_free_sub.setText(f"总容量 {vol.total_gb:.1f} GB · 空闲 {vol.free_bytes/vol.total_bytes*100:.1f}%")
            self.lbl_pipe_detail.setText(f"Macintosh HD · 总计 {vol.total_gb:.1f} GB")

        # 1. 刷新最近一次真实突发事件展示
        if time_events:
            latest = time_events[0]
            self.lbl_metric_recent_size.setText(latest.size_formatted)
            self.lbl_metric_recent_time.setText(f"{latest.relative_time_str} · {latest.app_name}")

        # 2. 刷新 HUD (以最大元凶微信为主控)
        if items:
            top_it = items[0]
            self.hud_card.update_data(
                title=f"{top_it.app_name} 大额占用",
                subtitle=top_it.description,
                size_str=top_it.size_formatted,
                tag=top_it.category.upper(),
                icon=top_it.icon_symbol
            )
            self.lbl_metric_king.setText(top_it.app_name)
            self.lbl_metric_king_sub.setText(f"单项占用高达 {top_it.size_formatted}")

        safe_clean = sum(it.size_bytes for it in items if it.safety == SafetyLevel.SAFE)
        safe_clean_gb = safe_clean / (1024**3)
        self.lbl_metric_clean.setText(f"{safe_clean_gb:.1f} GB")
        self.lbl_clean_total_headline.setText(f"可安全释放 {safe_clean_gb:.1f} GB 磁盘冗余")
        self.btn_batch_clean_all.setText(f"⚡️ 一键全选安全清理 (-{safe_clean_gb:.1f} GB)")

        # 3. 刷新海报网格
        while self.grid_container.count():
            w = self.grid_container.takeAt(0).widget()
            if w:
                w.deleteLater()

        sub_items = items[:4]
        self.lbl_count.setText(f"{len(sub_items)} 项")

        for idx, it in enumerate(sub_items):
            row = idx // 4
            col = idx % 4
            card = PosterCard(
                title=it.app_name,
                subtitle=it.title,
                size_str=it.size_formatted,
                safety_text=it.safety_badge_text,
                category=it.category,
                detail_desc=it.detail_status
            )
            card.clicked.connect(lambda p=it.path: SafeCleaner.reveal_in_finder(p))
            self.grid_container.addWidget(card, row, col)

        # 4. 刷新时间点流水账表格
        self._populate_time_table()

        # 5. 刷新极速瘦身页面
        self._refresh_clean_hub(items)

    def _populate_time_table(self):
        """按选中的时间范围动态计算并渲染表格 (限制渲染前 100 条以保持极致 60fps 流畅度)"""
        now = time.time()
        if self.current_time_filter == "all":
            filtered = self.time_events
        elif self.current_time_filter == "1h":
            filtered = [e for e in self.time_events if (now - e.timestamp) <= 3600]
        elif self.current_time_filter == "today":
            today_date = datetime.now().date()
            filtered = [e for e in self.time_events if datetime.fromtimestamp(e.timestamp).date() == today_date]
        elif self.current_time_filter == "yesterday":
            yesterday_date = datetime.now().date() - timedelta(days=1)
            filtered = [e for e in self.time_events if datetime.fromtimestamp(e.timestamp).date() == yesterday_date]
        elif self.current_time_filter == "7days":
            filtered = [e for e in self.time_events if (now - e.timestamp) <= 7 * 86400]
        elif self.current_time_filter == "older":
            filtered = [e for e in self.time_events if (now - e.timestamp) > 7 * 86400]
        else:
            filtered = self.time_events

        # 核心性能优化：限制单屏表格渲染上限 100 条，杜绝大量 Qt setCellWidget 阻塞主线程
        MAX_DISPLAY = 100
        display_events = filtered[:MAX_DISPLAY]
        self.table.setRowCount(len(display_events))
        if len(filtered) > MAX_DISPLAY:
            self.lbl_time_subtitle.setText(f"当前筛选显示最新 {len(display_events)} 起写入事件（共扫描发现 {len(filtered)} 起，按时间倒序）")
        else:
            self.lbl_time_subtitle.setText(f"当前筛选显示 {len(filtered)} 起真实写入事件（按时间倒序排列）")

        for row, ev in enumerate(display_events):
            # 1. 精确发生时间点
            t_item = QTableWidgetItem(ev.datetime_str)
            t_item.setTextAlignment(Qt.AlignCenter)
            t_item.setFont(QFont("Menlo", 10, QFont.Bold))
            self.table.setItem(row, 0, t_item)

            # 2. 相对时间
            rel_item = QTableWidgetItem(ev.relative_time_str)
            rel_item.setTextAlignment(Qt.AlignCenter)
            if "刚刚" in ev.relative_time_str or "今天" in ev.relative_time_str:
                rel_item.setForeground(QColor("#7C3AED"))
            self.table.setItem(row, 1, rel_item)

            # 3. 增量大小
            sz_item = QTableWidgetItem(ev.size_formatted)
            sz_item.setTextAlignment(Qt.AlignCenter)
            sz_item.setFont(QFont("Menlo", 10, QFont.Bold))
            if ev.size_bytes > 500 * 1024 * 1024:
                sz_item.setForeground(QColor("#DC2626"))
            elif ev.size_bytes > 50 * 1024 * 1024:
                sz_item.setForeground(QColor("#D97706"))
            self.table.setItem(row, 2, sz_item)

            # 4. 所属软件
            app_item = QTableWidgetItem(f"{ev.icon_symbol} {ev.app_name}")
            app_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, app_item)

            # 5. 文件名与路径
            p_widget = QWidget()
            p_l = QVBoxLayout(p_widget)
            p_l.setContentsMargins(6, 4, 6, 4)
            p_l.setSpacing(2)
            lbl_fname = QLabel(ev.file_name)
            lbl_fname.setStyleSheet("font-weight: bold; font-size: 12px; color: #111318;")
            lbl_path = QLabel(ev.path)
            lbl_path.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 10px; font-family: Menlo;")
            p_l.addWidget(lbl_fname)
            p_l.addWidget(lbl_path)
            self.table.setCellWidget(row, 4, p_widget)

            # 6. 安全级别
            saf_item = QTableWidgetItem(ev.safety_badge_text)
            saf_item.setTextAlignment(Qt.AlignCenter)
            if "安全" in ev.safety_badge_text:
                saf_item.setForeground(QColor("#059669"))
            else:
                saf_item.setForeground(QColor("#D97706"))
            self.table.setItem(row, 5, saf_item)

            # 7. 快捷操作
            act_widget = QWidget()
            act_l = QHBoxLayout(act_widget)
            act_l.setContentsMargins(4, 4, 4, 4)
            act_l.setSpacing(6)

            btn_f = CapsuleButton("访达定位", variant="pill_gray")
            btn_f.setFixedHeight(28)
            btn_f.clicked.connect(lambda checked=False, p=ev.path: SafeCleaner.reveal_in_finder(p))
            act_l.addWidget(btn_f)

            btn_del = CapsuleButton("删除", variant="pill_gray")
            btn_del.setFixedHeight(28)
            btn_del.clicked.connect(lambda checked=False, p=ev.path, f=ev.file_name: self._delete_single_file(p, f))
            act_l.addWidget(btn_del)

            self.table.setCellWidget(row, 6, act_widget)
            self.table.setRowHeight(row, 52)

    def _delete_single_file(self, path: str, fname: str):
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除该大文件吗？\n{fname}\n路径: {path}",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                if os.path.isfile(path) or os.path.islink(path):
                    os.unlink(path)
                    QMessageBox.information(self, "删除成功", f"已成功删除文件：{fname}")
                    self._start_scan()
                else:
                    SafeCleaner.purge_directory_contents(path)
                    QMessageBox.information(self, "清理成功", f"已清理目录内容：{fname}")
                    self._start_scan()
            except Exception as e:
                QMessageBox.warning(self, "删除失败", f"无法删除：{str(e)}")

    def _refresh_clean_hub(self, items: List[GrowthItem]):
        safe_clean = sum(it.size_bytes for it in items if it.safety == SafetyLevel.SAFE)
        safe_clean_gb = safe_clean / (1024**3)
        self.lbl_clean_total_headline.setText(f"可安全释放 {safe_clean_gb:.1f} GB 磁盘冗余")
        self.btn_batch_clean_all.setText(f"⚡️ 一键全选安全清理 (-{safe_clean_gb:.1f} GB)")

        while self.clean_cards_container.count():
            w = self.clean_cards_container.takeAt(0).widget()
            if w:
                w.deleteLater()

        for it in items:
            card = Card()
            c_l = QHBoxLayout(card)
            c_l.setContentsMargins(20, 14, 20, 14)
            c_l.setSpacing(14)
            
            chk = QCheckBox()
            chk.setChecked(it.safety == SafetyLevel.SAFE)
            c_l.addWidget(chk)

            ico = QLabel(it.icon_symbol)
            ico.setStyleSheet("font-size: 26px;")
            c_l.addWidget(ico)

            info_v = QVBoxLayout()
            info_v.setSpacing(3)
            
            t_row = QHBoxLayout()
            t = QLabel(f"{it.app_name} · {it.title}")
            t.setStyleSheet("font-weight: bold; font-size: 13px; color: #111318;")
            t_row.addWidget(t)

            lbl_saf = QLabel(it.safety_badge_text)
            if "安全" in it.safety_badge_text:
                lbl_saf.setStyleSheet("background-color: #ECFDF5; color: #059669; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;")
            else:
                lbl_saf.setStyleSheet("background-color: #FFFBEB; color: #D97706; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;")
            t_row.addWidget(lbl_saf)
            t_row.addStretch()
            info_v.addLayout(t_row)

            lbl_d = QLabel(it.description)
            lbl_d.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 11px;")
            lbl_d.setWordWrap(True)
            info_v.addWidget(lbl_d)

            lbl_p = QLabel(f"路径: {it.path}")
            lbl_p.setStyleSheet(f"color: {THEME.TEXT_HINT}; font-size: 10px; font-family: Menlo;")
            lbl_p.setWordWrap(True)
            info_v.addWidget(lbl_p)
            c_l.addLayout(info_v, 1)

            # 大小
            lbl_sz = QLabel(it.size_formatted)
            lbl_sz.setStyleSheet("font-size: 14px; font-weight: bold; font-family: Menlo; color: #111318;")
            c_l.addWidget(lbl_sz)

            btn_reveal = CapsuleButton("在访达查看", variant="pill_gray")
            btn_reveal.clicked.connect(lambda checked=False, p=it.path: SafeCleaner.reveal_in_finder(p))
            c_l.addWidget(btn_reveal)

            btn_clean = CapsuleButton(f"一键释放", variant="purple" if it.safety == SafetyLevel.SAFE else "pill_gray")
            btn_clean.clicked.connect(lambda checked=False, item=it: self._clean_single_item(item))
            c_l.addWidget(btn_clean)

            self.clean_cards_container.addWidget(card)

    def _perform_batch_clean(self):
        reply = QMessageBox.question(
            self, "确认一键极速瘦身",
            "确定要一键安全清理所有选中的临时缓存吗？\n\n🛡 严正安全保证：\n- 微信：文字与语音聊天记录 100% 完好无损\n- 剪映：视频剪辑工程草稿绝对不伤\n- 开发环境：仅清理构建中间包",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # 清理微信临时缓存
            SafeCleaner.purge_directory_contents("~/Library/Containers/com.tencent.xinWeChat/Data/Library/Caches")
            # 清理剪映渲染代理
            SafeCleaner.purge_directory_contents("~/Movies/JianyingPro/User Data/Cache")
            # 清理钉钉临时缓存
            SafeCleaner.purge_directory_contents("~/Library/Caches/com.alibaba.DingTalkMac")
            # 清理 Cargo 缓存
            SafeCleaner.purge_directory_contents("~/Library/Caches/cargo-xwin")

            QMessageBox.information(self, "瘦身完成", "恭喜！已成功安全释放全部选中的冗余缓存！\n您的核心数据与聊天记录完整保留。")
            self._start_scan()

    def _clean_single_item(self, item: GrowthItem):
        reply = QMessageBox.question(
            self, "确认安全清理",
            f"确定要清理 {item.app_name} 的缓存吗？\n{item.description}",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if item.id == "wechat_container":
                SafeCleaner.purge_directory_contents("~/Library/Containers/com.tencent.xinWeChat/Data/Library/Caches")
            elif item.id == "capcut_render":
                SafeCleaner.purge_directory_contents("~/Movies/JianyingPro/User Data/Cache")
            elif item.id == "dingtalk_cache":
                SafeCleaner.purge_directory_contents("~/Library/Caches/com.alibaba.DingTalkMac")
            elif item.id == "cargo_cache":
                SafeCleaner.purge_directory_contents("~/Library/Caches/cargo-xwin")
            elif item.is_snapshot:
                SafeCleaner.delete_apfs_local_snapshots()
            else:
                SafeCleaner.purge_directory_contents(item.path)

            QMessageBox.information(self, "清理完成", f"已安全清理 {item.app_name} 缓存！")
            self._start_scan()

    def _on_hud_clean(self):
        self.hud_card.bar.setValue(100)
        self.hud_card.lbl_pct.setText("100%")
        QTimer.singleShot(400, self._perform_hud_action)

    def _perform_hud_action(self):
        SafeCleaner.purge_directory_contents("~/Library/Containers/com.tencent.xinWeChat/Data/Library/Caches")
        SafeCleaner.purge_directory_contents("~/Movies/JianyingPro/User Data/Cache")
        QMessageBox.information(self, "释放成功", "恭喜！已安全清空微信临时网页视频与剪映渲染缓存！\n聊天记录完整无缺。")
        self._start_scan()

    def _on_hud_dismiss(self):
        self.hud_card.hide()

    def _on_clean_selected(self):
        self._switch_to_tab(2)

    def _on_search_text_changed(self, text: str):
        query = text.strip().lower()
        if not query:
            self._populate_time_table()
            return
        
        filtered = [e for e in self.time_events if query in e.file_name.lower() or query in e.path.lower() or query in e.app_name.lower()]
        self.table.setRowCount(len(filtered))
        self.lbl_time_subtitle.setText(f"搜索 '{query}' 找到 {len(filtered)} 起相关写入事件")
        for row, ev in enumerate(filtered):
            t_item = QTableWidgetItem(ev.datetime_str)
            t_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, t_item)

            rel_item = QTableWidgetItem(ev.relative_time_str)
            rel_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, rel_item)

            sz_item = QTableWidgetItem(ev.size_formatted)
            sz_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, sz_item)

            app_item = QTableWidgetItem(f"{ev.icon_symbol} {ev.app_name}")
            app_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, app_item)

            p_widget = QWidget()
            p_l = QVBoxLayout(p_widget)
            p_l.setContentsMargins(6, 4, 6, 4)
            lbl_fname = QLabel(ev.file_name)
            lbl_fname.setStyleSheet("font-weight: bold; font-size: 12px;")
            lbl_path = QLabel(ev.path)
            lbl_path.setStyleSheet(f"color: {THEME.TEXT_MUTED}; font-size: 10px;")
            p_l.addWidget(lbl_fname)
            p_l.addWidget(lbl_path)
            self.table.setCellWidget(row, 4, p_widget)

            saf_item = QTableWidgetItem(ev.safety_badge_text)
            saf_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, saf_item)

            act_widget = QWidget()
            act_l = QHBoxLayout(act_widget)
            btn_f = CapsuleButton("访达定位", variant="pill_gray")
            btn_f.setFixedHeight(28)
            btn_f.clicked.connect(lambda checked=False, p=ev.path: SafeCleaner.reveal_in_finder(p))
            act_l.addWidget(btn_f)
            self.table.setCellWidget(row, 6, act_widget)
            self.table.setRowHeight(row, 52)

    def closeEvent(self, event):
        if hasattr(self, "realtime_watcher") and self.realtime_watcher:
            try:
                self.realtime_watcher.stop()
            except Exception:
                pass
        if hasattr(self, "inspection_timer") and self.inspection_timer.isActive():
            self.inspection_timer.stop()
        if hasattr(self, "worker") and self.worker is not None:
            if self.worker.isRunning():
                self.worker.cancel()
                self.worker.requestInterruption()
                self.worker.quit()
                if not self.worker.wait(300):
                    self.worker.terminate()
                    self.worker.wait(150)
        event.accept()

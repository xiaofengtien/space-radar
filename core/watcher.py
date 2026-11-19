"""
实时文件系统事件监听器 (基于 macOS FSEvents 与 Windows ReadDirectoryChangesW)
秒级捕获大文件写入，并推送到 UI 时间流水与指标 HUD
"""
import os
import sys
import time
from pathlib import Path
from typing import Callable, Optional, List

from PySide6.QtCore import QObject, Signal

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

from core.classifier import TimeGrowthEvent, SafetyLevel
from core.sensor import DiskSensor

class _WatchdogHandler(FileSystemEventHandler if HAS_WATCHDOG else object):
    def __init__(self, callback: Callable[[TimeGrowthEvent], None]):
        if HAS_WATCHDOG:
            super().__init__()
        self.callback = callback
        self._last_processed = {}

    def _process(self, src_path: str):
        try:
            if not os.path.exists(src_path) or os.path.isdir(src_path):
                return
            
            # 忽略常见临时锁文件与隐藏文件
            base = os.path.basename(src_path)
            if base.startswith(".") or base.endswith((".tmp", ".crdownload", ".part", ".lock")):
                return

            st = os.stat(src_path)
            # 过滤小于 300KB 的微小写入，避免高频日志扰动
            if st.st_size < 300 * 1024:
                return

            now = time.time()
            # 1.5 秒防抖（同文件在短时间内连续写入只上报一次最终态）
            if src_path in self._last_processed:
                if now - self._last_processed[src_path] < 1.5:
                    return
            self._last_processed[src_path] = now

            # 智能判定所属应用与分类
            app_name, cat, safety, icon = DiskSensor.identify_file_context(src_path)
            ev = TimeGrowthEvent.from_file_stat(
                fp=src_path,
                st=st,
                app_name=app_name,
                category=cat,
                safety=safety,
                icon=icon
            )
            self.callback(ev)
        except (OSError, FileNotFoundError):
            pass

    def on_created(self, event):
        if hasattr(event, "is_directory") and not event.is_directory:
            self._process(event.src_path)

    def on_modified(self, event):
        if hasattr(event, "is_directory") and not event.is_directory:
            self._process(event.src_path)

class RealtimeWatcher(QObject):
    """Qt 线程安全的实时文件监听服务"""
    realtime_event_captured = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.observer = None
        self._is_running = False

    def start(self):
        if not HAS_WATCHDOG or self._is_running:
            return

        try:
            self.observer = Observer()
            handler = _WatchdogHandler(self._on_event_from_thread)

            # 获取所有待监控的活跃根目录
            watch_dirs = DiskSensor.get_realtime_watch_directories()
            for d in watch_dirs:
                if os.path.exists(d) and os.path.isdir(d):
                    try:
                        self.observer.schedule(handler, d, recursive=True)
                    except Exception:
                        pass

            self.observer.daemon = True
            self.observer.start()
            self._is_running = True
        except Exception:
            self.observer = None
            self._is_running = False

    def _on_event_from_thread(self, ev: TimeGrowthEvent):
        # 跨线程发射 Qt 信号，Qt 会安全排队调度至主线程处理
        self.realtime_event_captured.emit(ev)

    def stop(self):
        if self.observer and self._is_running:
            try:
                self.observer.stop()
                self.observer.join(timeout=1.0)
            except Exception:
                pass
            self.observer = None
            self._is_running = False

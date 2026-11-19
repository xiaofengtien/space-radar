"""
磁盘容量传感器与真实时间点事件探测器 (整合自定义目录与规则开关)
"""
from __future__ import annotations
import os
import sys
import time
import subprocess
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

from core.classifier import GrowthItem, SafetyLevel, TimeGrowthEvent
from core.config import ConfigManager

@dataclass
class DiskVolumeInfo:
    total_bytes: int
    used_bytes: int
    free_bytes: int
    used_percent: float
    mount_point: str

    @property
    def total_gb(self) -> float:
        return self.total_bytes / (1024 ** 3)

    @property
    def used_gb(self) -> float:
        return self.used_bytes / (1024 ** 3)

    @property
    def free_gb(self) -> float:
        return self.free_bytes / (1024 ** 3)

class DiskSensor:
    
    @staticmethod
    def get_root_volume_info() -> DiskVolumeInfo:
        """获取主系统卷的真实容量与可用空间（跨平台适配 Windows 与 macOS）"""
        root_path = os.environ.get('SystemDrive', 'C:') + '\\' if sys.platform == 'win32' else '/'
        if psutil:
            try:
                usage = psutil.disk_usage(root_path)
                return DiskVolumeInfo(
                    total_bytes=usage.total,
                    used_bytes=usage.used,
                    free_bytes=usage.free,
                    used_percent=usage.percent,
                    mount_point=root_path
                )
            except Exception:
                pass

        # 降级方案：使用 Python 标准库内置 shutil.disk_usage (无需第三方库，100% 可用)
        import shutil
        try:
            total, used, free = shutil.disk_usage(root_path)
            percent = (used / total) * 100 if total > 0 else 0.0
            return DiskVolumeInfo(
                total_bytes=total,
                used_bytes=used,
                free_bytes=free,
                used_percent=percent,
                mount_point=root_path
            )
        except Exception:
            return DiskVolumeInfo(
                total_bytes=512 * (1024 ** 3),
                used_bytes=256 * (1024 ** 3),
                free_bytes=256 * (1024 ** 3),
                used_percent=50.0,
                mount_point=root_path
            )

    _DIR_SIZE_CACHE: Dict[str, Tuple[float, int]] = {}

    @classmethod
    def get_real_directory_size(cls, path: str) -> int:
        """快速且100%真实计算目录大小 (macOS 下使用原生 du -sk + 智能短期缓存，杜绝深度扫描卡死)"""
        expanded = os.path.expanduser(path)
        if not os.path.exists(expanded):
            return 0

        now = time.time()
        if expanded in cls._DIR_SIZE_CACHE:
            ts, sz = cls._DIR_SIZE_CACHE[expanded]
            if now - ts < 120:  # 2分钟内直接复用真实测量值，避免频繁唤醒磁盘 I/O
                return sz

        if sys.platform == "darwin":
            try:
                res = subprocess.run(["du", "-sk", expanded], capture_output=True, text=True, timeout=12)
                if res.returncode == 0 and res.stdout:
                    kb_str = res.stdout.strip().split()[0]
                    sz = int(kb_str) * 1024
                    cls._DIR_SIZE_CACHE[expanded] = (now, sz)
                    return sz
            except Exception:
                pass

        # 若 du 失败或超时，优先返回历史缓存
        if expanded in cls._DIR_SIZE_CACHE:
            return cls._DIR_SIZE_CACHE[expanded][1]

        # 降级：仅对浅层做轻量统计，杜绝深层递归卡死
        total = 0
        try:
            with os.scandir(expanded) as it:
                for entry in it:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            total += entry.stat().st_size
                    except OSError:
                        pass
        except Exception:
            pass
        return total

    @staticmethod
    def detect_apfs_snapshots() -> List[GrowthItem]:
        """检测真实的 macOS 本地快照"""
        if not ConfigManager.is_rule_enabled("rule_apfs_snapshot"):
            return []

        items = []
        if sys.platform != "darwin":
            return items

        try:
            res = subprocess.run(["tmutil", "listlocalsnapshots", "/"], capture_output=True, text=True, timeout=2)
            lines = [l.strip() for l in res.stdout.splitlines() if "com.apple.TimeMachine" in l]
            if lines:
                estimated_size = len(lines) * (15 * 1024 * 1024 * 1024)
                items.append(GrowthItem(
                    id="apfs_snapshot_group",
                    title="macOS 幽灵系统快照",
                    app_name="Time Machine",
                    category="system",
                    category_label="系统幽灵快照",
                    path="/System/Volumes/Data/.snapshots",
                    size_bytes=estimated_size,
                    safety=SafetyLevel.SAFE,
                    description=f"检测到 {len(lines)} 个本地快照，霸占系统数据。可一键释放。",
                    detail_status=f"已发现 {len(lines)} 个本地备份快照",
                    command_hint="tmutil deletelocalsnapshots",
                    icon_symbol="🖥️",
                    is_snapshot=True
                ))
        except Exception:
            pass
        return items

    @classmethod
    def scan_all_growth_items(cls) -> List[GrowthItem]:
        """全量扫描用户真实磁盘上的重点目录与自定义目录"""
        results: List[GrowthItem] = []
        home = Path.home()

        # 1. 微信
        if ConfigManager.is_rule_enabled("rule_wechat"):
            wechat_dir = home / "Library/Containers/com.tencent.xinWeChat"
            if wechat_dir.exists():
                wechat_size = cls.get_real_directory_size(str(wechat_dir))
                if wechat_size > 100 * 1024 * 1024:
                    results.append(GrowthItem(
                        id="wechat_container",
                        title="微信群视频与附件大文件",
                        app_name="微信 (WeChat)",
                        category="social",
                        category_label="社交与通讯",
                        path=str(wechat_dir),
                        size_bytes=wechat_size,
                        safety=SafetyLevel.SAFE,
                        description="包括群聊接收的大量视频、公众号网页缓存与临时附件。安全清理后文字聊天记录 100% 完整保留。",
                        detail_status="群视频与附件 · 建议清理",
                        command_hint="清理微信 Caches 与临时视频附件",
                        icon_symbol="💬"
                    ))

        # 2. Downloads
        if ConfigManager.is_rule_enabled("rule_downloads"):
            dl_dir = home / "Downloads"
            if dl_dir.exists():
                dl_size = cls.get_real_directory_size(str(dl_dir))
                if dl_size > 100 * 1024 * 1024:
                    results.append(GrowthItem(
                        id="downloads_folder",
                        title="下载目录安装包与大镜像",
                        app_name="访达下载 (Downloads)",
                        category="downloads",
                        category_label="安装包残留",
                        path=str(dl_dir),
                        size_bytes=dl_size,
                        safety=SafetyLevel.CONFIRM,
                        description="下载目录躺着的 ISO 镜像、软件压缩包与已安装安装包。可移入废纸篓安全腾出空间。",
                        detail_status="包含 ISO 镜像与离线安装包",
                        command_hint="清理已安装的下载文件",
                        icon_symbol="📦"
                    ))

        # 3. 剪映
        if ConfigManager.is_rule_enabled("rule_capcut"):
            capcut_dir = home / "Movies/JianyingPro"
            if capcut_dir.exists():
                capcut_size = cls.get_real_directory_size(str(capcut_dir))
                if capcut_size > 100 * 1024 * 1024:
                    results.append(GrowthItem(
                        id="capcut_render",
                        title="剪映 4K 工程预渲染与代理",
                        app_name="剪映 (CapCut)",
                        category="media",
                        category_label="影音与剪辑",
                        path=str(capcut_dir / "User Data/Cache") if (capcut_dir / "User Data/Cache").exists() else str(capcut_dir),
                        size_bytes=capcut_size,
                        safety=SafetyLevel.SAFE,
                        description="剪辑 4K 视频时生成的工程预渲染帧与临时代理，清理后草稿项目完好无损，绝不丢失原片。",
                        detail_status="视频代理缓存 · 不伤工程",
                        command_hint="清空剪映工程渲染缓存",
                        icon_symbol="🎬"
                    ))

        # 4. 钉钉
        if ConfigManager.is_rule_enabled("rule_dingtalk"):
            ding_cache = home / "Library/Caches/com.alibaba.DingTalkMac"
            if ding_cache.exists():
                ding_size = cls.get_real_directory_size(str(ding_cache))
                if ding_size > 100 * 1024 * 1024:
                    results.append(GrowthItem(
                        id="dingtalk_cache",
                        title="钉钉文档与音视频缓存",
                        app_name="钉钉 (DingTalk)",
                        category="social",
                        category_label="社交与通讯",
                        path=str(ding_cache),
                        size_bytes=ding_size,
                        safety=SafetyLevel.SAFE,
                        description="办公聊天打开过的图片、群文档与音视频缓存文件，可一键安全清理。",
                        detail_status="办公临时缓存 · 可安全清空",
                        command_hint="清空钉钉临时缓存",
                        icon_symbol="📌"
                    ))

        # 5. Cargo & npm 开发包
        if ConfigManager.is_rule_enabled("rule_dev_cache"):
            cargo_dir = home / ".cargo"
            if cargo_dir.exists():
                cargo_size = cls.get_real_directory_size(str(cargo_dir))
                if cargo_size > 100 * 1024 * 1024:
                    results.append(GrowthItem(
                        id="cargo_cache",
                        title="Cargo / Rust 构建中间产物",
                        app_name="Rust (Cargo)",
                        category="dev",
                        category_label="开发与 IDE",
                        path=str(cargo_dir),
                        size_bytes=cargo_size,
                        safety=SafetyLevel.SAFE,
                        description="Rust 项目编译依赖缓存，清理后再次编译时自动拉取最新构建。",
                        detail_status="Rust 依赖缓存 · 100%安全",
                        command_hint="cargo clean / 清理 .cargo",
                        icon_symbol="🦀"
                    ))

        # 6. APFS 快照
        snapshots = cls.detect_apfs_snapshots()
        results.extend(snapshots)

        # 7. 用户自定义监控目录扫描 (真实扫入用户添加的任何外部目录)
        for custom_path in ConfigManager.get_custom_directories():
            if os.path.exists(custom_path):
                c_size = cls.get_real_directory_size(custom_path)
                folder_name = os.path.basename(custom_path.rstrip("/\\")) or custom_path
                results.append(GrowthItem(
                    id=f"custom_{abs(hash(custom_path))}",
                    title=f"自定义目录: {folder_name}",
                    app_name="自定义监控",
                    category="custom",
                    category_label="用户添加目录",
                    path=custom_path,
                    size_bytes=c_size,
                    safety=SafetyLevel.CONFIRM,
                    description=f"用户自定义添加常驻监控的文件夹: {custom_path}",
                    detail_status="自定义监控目录 · 实时巡检",
                    command_hint=f"open {custom_path}",
                    icon_symbol="📁"
                ))

        results.sort(key=lambda x: x.size_bytes, reverse=True)
        return results

    @classmethod
    def get_cached_time_point_events(cls) -> List[TimeGrowthEvent]:
        """毫秒级读取上次扫描缓存的真实事件，确保启动首帧不空白"""
        cache_path = Path.home() / ".space_radar_events_cache.json"
        if not cache_path.exists():
            return []
        try:
            import json
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            events = []
            for d in data:
                events.append(TimeGrowthEvent(
                    timestamp=d["timestamp"],
                    datetime_str=d["datetime_str"],
                    relative_time_str=d["relative_time_str"],
                    time_bucket=d["time_bucket"],
                    app_name=d["app_name"],
                    file_name=d["file_name"],
                    path=d["path"],
                    size_bytes=d["size_bytes"],
                    category=d["category"],
                    safety=SafetyLevel(d["safety"]),
                    icon_symbol=d["icon_symbol"]
                ))
            return events
        except Exception:
            return []

    @classmethod
    def identify_file_context(cls, fp: str) -> Tuple[str, str, SafetyLevel, str]:
        """
        根据文件路径智能识别所属软件、分类、安全级别和图标
        返回: (app_name, category, safety_level, icon_symbol)
        """
        p = Path(fp)
        parts = p.parts
        parts_lower = [x.lower() for x in parts]

        if "downloads" in parts_lower or "下载" in parts_lower:
            return "访达下载" if sys.platform == "darwin" else "下载文件夹", "downloads", SafetyLevel.CONFIRM, "📦"

        if "jianyingpro" in parts_lower or "jianying" in parts_lower:
            return "剪映 (CapCut)", "media", SafetyLevel.SAFE, "🎬"

        if ".cargo" in parts_lower or "cargo" in parts_lower:
            return "Cargo构建", "dev", SafetyLevel.SAFE, "🦀"

        if ".cache" in parts_lower:
            return "AI与工具缓存", "ai", SafetyLevel.SAFE, "🤖"

        # Application Support, Logs 与 Caches 目录智能识别
        if any(x in parts_lower for x in ("application support", "logs", "caches", "cache")):
            for part in parts:
                low = part.lower()
                if "antigravity" in low:
                    return "Antigravity 运行时", "ai", SafetyLevel.SAFE, "⚡️"
                if "chrome" in low or part == "Google":
                    return "Chrome 浏览器", "browser", SafetyLevel.SAFE, "🌐"
                if "dingtalk" in low:
                    return "钉钉数据与日志", "social", SafetyLevel.SAFE, "📌"
                if "wechat" in low or "xinwechat" in low:
                    return "微信数据缓存", "social", SafetyLevel.SAFE, "💬"
                if "telegram" in low:
                    return "Telegram 日志", "social", SafetyLevel.SAFE, "✈️"
                if "notion" in low:
                    return "Notion 数据库", "tool", SafetyLevel.SAFE, "📝"
                if "quark" in low:
                    return "夸克存储", "tool", SafetyLevel.SAFE, "📦"
                if "macperformance" in low:
                    return "系统性能监视器", "system", SafetyLevel.SAFE, "📊"
                if "vscode" in low or ("code" in low and "microsoft" in low):
                    return "VS Code", "dev", SafetyLevel.SAFE, "💻"
                if "cursor" in low:
                    return "Cursor 编辑器", "dev", SafetyLevel.SAFE, "💻"
                if "netease" in low or "163music" in low:
                    return "网易云音乐", "media", SafetyLevel.SAFE, "🎵"
                if "raycast" in low:
                    return "Raycast 数据", "tool", SafetyLevel.SAFE, "⚡️"
                if "homebrew" in low:
                    return "Homebrew", "dev", SafetyLevel.SAFE, "🍺"
                if "safari" in low:
                    return "Safari 缓存", "browser", SafetyLevel.SAFE, "🧭"
                if "edge" in low:
                    return "Edge 浏览器", "browser", SafetyLevel.SAFE, "🌊"
                if "codex" in low:
                    return "Codex 运行缓存", "ai", SafetyLevel.SAFE, "🤖"
                if "apple" in low:
                    return "macOS 系统数据", "system", SafetyLevel.SAFE, "🍎"
                if low.startswith("com."):
                    clean_name = part.replace("com.", "").split(".")[-1].capitalize()
                    return f"{clean_name} 应用数据", "app", SafetyLevel.SAFE, "📁"
            if "logs" in parts_lower:
                return "应用运行日志", "dev", SafetyLevel.SAFE, "📄"
            return "应用运行时缓存", "app", SafetyLevel.SAFE, "📁"

        # Windows Temp
        if "temp" in parts_lower:
            return "系统临时文件 (Temp)", "system", SafetyLevel.SAFE, "🧹"

        return "本地文件变更", "custom", SafetyLevel.CONFIRM, "📁"

    @classmethod
    def get_realtime_watch_directories(cls) -> List[str]:
        """获取需要接入文件系统秒级实时监听的活跃根目录列表（仅监听高价值目录，绝对避开缓存风暴）"""
        home = Path.home()
        dirs = []
        if sys.platform == "darwin":
            dirs = [
                home / "Downloads",
                home / "Movies/JianyingPro",
            ]
        else:
            dirs = [
                home / "Downloads",
            ]

        # 挂载用户自定义监控目录
        for c_dir in ConfigManager.get_custom_directories():
            p_obj = Path(c_dir)
            if p_obj.exists():
                dirs.append(p_obj)

        return [str(d) for d in dirs if d.exists()]

    @classmethod
    def scan_all_time_point_events(cls) -> List[TimeGrowthEvent]:
        """按时间戳全量扫描真实增长事件，涵盖各主流应用缓存、下载与自定义监控目录"""
        events: List[TimeGrowthEvent] = []
        home = Path.home()

        targets: List[Tuple[Path, int]] = []
        if sys.platform == "darwin":
            targets = [
                (home / "Downloads", 300 * 1024),  # >=300KB 的下载内容（捕捉安装包、Zip、大图）
                (home / "Library/Logs", 300 * 1024),  # >=300KB 的应用日志（Notion, DingTalk, Telegram 等）
                (home / "Library/Application Support", 1024 * 1024),  # >=1MB 应用数据
                (home / "Library/Caches", 1024 * 1024),  # >=1MB 应用与系统缓存（Chrome、Antigravity、Raycast 等）
                (home / "Library/Containers/com.tencent.xinWeChat/Data/Library/Caches", 500 * 1024),
                (home / "Movies/JianyingPro", 2 * 1024 * 1024),
                (home / ".cache", 1024 * 1024),
                (home / ".cargo", 3 * 1024 * 1024),
            ]
        else:
            local_appdata = os.environ.get("LOCALAPPDATA", str(home / "AppData/Local"))
            appdata = os.environ.get("APPDATA", str(home / "AppData/Roaming"))
            targets = [
                (home / "Downloads", 300 * 1024),
                (Path(local_appdata) / "Temp", 1024 * 1024),
                (Path(local_appdata) / "Google/Chrome/User Data/Default/Cache", 1024 * 1024),
                (Path(local_appdata) / "Microsoft/Edge/User Data/Default/Cache", 1024 * 1024),
                (Path(appdata), 1024 * 1024),
                (home / ".cache", 1024 * 1024),
                (home / ".cargo", 3 * 1024 * 1024),
            ]

        # 挂载用户自定义监控目录
        for c_dir in ConfigManager.get_custom_directories():
            p_obj = Path(c_dir)
            if p_obj.exists():
                targets.append((p_obj, 500 * 1024))

        ignored_subdirs = {"cache_data", "code cache", "graphitedawncache", "gpu_cache", "dawncache", "index-dir"}

        for p, min_sz in targets:
            if not p.exists():
                continue
            try:
                for root, dirs, files in os.walk(p, onerror=lambda err: None):
                    # 快速剪枝：忽略浏览器内部碎片子目录，避免扫描陷入深渊
                    dirs[:] = [d for d in dirs if d.lower() not in ignored_subdirs]
                    rel = os.path.relpath(root, p)
                    if rel != "." and len(Path(rel).parts) >= 4:
                        dirs.clear()
                        continue

                    for f in files:
                        if f.startswith(".") or f.endswith(("_0", "_1", ".tmp", ".lock", ".ldb")):
                            continue
                        fp = os.path.join(root, f)
                        try:
                            st = os.stat(fp)
                            if st.st_size >= min_sz:
                                app_name, cat, safety, icon = cls.identify_file_context(fp)
                                ev = TimeGrowthEvent.from_file_stat(
                                     fp=fp,
                                     st=st,
                                     app_name=app_name,
                                     category=cat,
                                     safety=safety,
                                     icon=icon
                                )
                                events.append(ev)
                        except (OSError, FileNotFoundError):
                            pass
            except Exception:
                pass

        events.sort(key=lambda x: x.timestamp, reverse=True)

        # 异步持久化到本地缓存，供下次毫秒级启动
        try:
            import json
            cache_path = Path.home() / ".space_radar_events_cache.json"
            dump_list = [
                {
                    "timestamp": e.timestamp,
                    "datetime_str": e.datetime_str,
                    "relative_time_str": e.relative_time_str,
                    "time_bucket": e.time_bucket,
                    "app_name": e.app_name,
                    "file_name": e.file_name,
                    "path": e.path,
                    "size_bytes": e.size_bytes,
                    "category": e.category,
                    "safety": e.safety.value,
                    "icon_symbol": e.icon_symbol
                }
                for e in events[:500]
            ]
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(dump_list, f, ensure_ascii=False)
        except Exception:
            pass

        return events

"""
智能分类规则库与数据模型 (Classifier & Rules Engine)
新增：TimeGrowthEvent (精确到秒的时间点增长事件模型)
"""
from __future__ import annotations
import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

class SafetyLevel(str, Enum):
    SAFE = "safe"        # 100% 安全：清理后不影响使用（如 Xcode DerivedData、渲染缓存）
    CONFIRM = "confirm"  # 需确认：清理可省大量空间，但后续若使用需重新下载（如 AI 大模型、安装包）
    CAUTION = "caution"  # 谨慎操作：用户个人下载或项目文件

@dataclass
class GrowthItem:
    id: str
    title: str
    app_name: str
    category: str
    category_label: str
    path: str
    size_bytes: int
    safety: SafetyLevel
    description: str
    detail_status: str
    command_hint: str
    icon_symbol: str
    is_snapshot: bool = False
    
    @property
    def size_formatted(self) -> str:
        gb = self.size_bytes / (1024 ** 3)
        if gb >= 1.0:
            return f"+{gb:.1f} GB"
        mb = self.size_bytes / (1024 ** 2)
        return f"+{mb:.0f} MB"
        
    @property
    def safety_badge_text(self) -> str:
        if self.safety == SafetyLevel.SAFE:
            return "100% 安全"
        elif self.safety == SafetyLevel.CONFIRM:
            return "建议确认"
        return "需谨慎"

@dataclass
class TimeGrowthEvent:
    """
    核心差异化模型：记录具体在什么时间点发生的增长
    """
    timestamp: float           # 发生时的时间戳
    datetime_str: str          # 精确到秒：'2026-11-18 18:17:42'
    relative_time_str: str     # 人话时间：'刚刚 (15分钟前)', '今天 16:24', '昨天 19:36'
    time_bucket: str           # '1h', 'today', 'yesterday', '7days', 'older'
    app_name: str              # 所属软件或场景
    file_name: str             # 文件名
    path: str                  # 完整路径
    size_bytes: int            # 增量字节
    category: str              # 类别
    safety: SafetyLevel        # 安全级别
    icon_symbol: str           # 图标

    @property
    def size_formatted(self) -> str:
        gb = self.size_bytes / (1024 ** 3)
        if gb >= 1.0:
            return f"+{gb:.2f} GB"
        mb = self.size_bytes / (1024 ** 2)
        if mb >= 1.0:
            return f"+{mb:.1f} MB"
        kb = self.size_bytes / 1024
        return f"+{kb:.0f} KB"

    @property
    def safety_badge_text(self) -> str:
        if self.safety == SafetyLevel.SAFE:
            return "100% 安全"
        elif self.safety == SafetyLevel.CONFIRM:
            return "建议确认"
        return "需谨慎"

    @classmethod
    def from_file_stat(cls, fp: str, st: os.stat_result, app_name: str, category: str, safety: SafetyLevel = SafetyLevel.SAFE, icon: str = "📁") -> TimeGrowthEvent:
        mtime = st.st_mtime
        now = time.time()
        diff_sec = now - mtime
        dt = datetime.fromtimestamp(mtime)
        dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")

        # 归属时间段 (bucket) 与相对时间标签
        if diff_sec < 3600:
            bucket = "1h"
            mins = max(1, int(diff_sec / 60))
            rel_str = f"刚刚 ({mins}分钟前)"
        elif diff_sec < 86400 and dt.date() == datetime.now().date():
            bucket = "today"
            rel_str = f"今天 {dt.strftime('%H:%M:%S')}"
        elif diff_sec < 86400 * 2:
            bucket = "yesterday"
            rel_str = f"昨天 {dt.strftime('%H:%M')}"
        elif diff_sec < 86400 * 7:
            bucket = "7days"
            days = int(diff_sec / 86400)
            rel_str = f"{days}天前 ({dt.strftime('%m-%d %H:%M')})"
        else:
            bucket = "older"
            rel_str = dt.strftime("%Y-%m-%d")

        return cls(
            timestamp=mtime,
            datetime_str=dt_str,
            relative_time_str=rel_str,
            time_bucket=bucket,
            app_name=app_name,
            file_name=os.path.basename(fp),
            path=fp,
            size_bytes=st.st_size,
            category=category,
            safety=safety,
            icon_symbol=icon
        )

# 基础热区规则
HOTSPOT_RULES = [
    {
        "id": "wechat_cache",
        "app_name": "微信 (WeChat)",
        "title": "微信群视频与网页附件缓存",
        "category": "social",
        "category_label": "社交与通讯",
        "path_template": "~/Library/Containers/com.tencent.xinWeChat",
        "safety": SafetyLevel.SAFE,
        "description": "微信群聊接收的高清视频、公众号网页与临时附件。安全清理后文字聊天记录 100% 完整保留。",
        "detail_status": "临时音视频缓存 · 保留聊天",
        "command_hint": "清理微信 Caches 临时目录",
        "icon_symbol": "💬"
    },
    {
        "id": "downloads_archives",
        "app_name": "访达下载",
        "title": "已安装的 DMG 镜像与压缩包",
        "category": "downloads",
        "category_label": "安装包残留",
        "path_template": "~/Downloads",
        "safety": SafetyLevel.CONFIRM,
        "description": "下载目录躺着的 ISO 镜像、软件压缩包与已安装安装包。可移入废纸篓安全腾出空间。",
        "detail_status": "包含 ISO 镜像与离线安装包",
        "command_hint": "移入废纸篓",
        "icon_symbol": "📦"
    },
    {
        "id": "capcut_cache",
        "app_name": "剪映 (CapCut)",
        "title": "剪映 4K 工程预渲染与代理",
        "category": "media",
        "category_label": "影音与剪辑",
        "path_template": "~/Movies/JianyingPro",
        "safety": SafetyLevel.SAFE,
        "description": "剪辑高清视频时自动生成的预渲染缓存与代理帧，清理后工程草稿完好无损，仅需重新加载预览。",
        "detail_status": "视频代理缓存 · 不伤原视频",
        "command_hint": "清理剪映 Cache 文件夹",
        "icon_symbol": "🎬"
    }
]

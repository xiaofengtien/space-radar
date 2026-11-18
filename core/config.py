"""
用户配置与规则持久化管理器 (Config & State Persistence)
保存自定义监控目录、定时巡检周期、告警阈值与清理规则状态。
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import List, Dict, Any

CONFIG_FILE = Path.home() / ".space_radar_config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "custom_directories": [],
    "inspection_interval_minutes": 5,
    "surge_threshold_mb": 500,
    "auto_inspection_enabled": True,
    "system_notification_enabled": True,
    "rules": {
        "rule_wechat": True,       # 微信音视频与网页缓存自动拦截
        "rule_capcut": True,       # 剪映 4K 预渲染代理自动拦截
        "rule_downloads": True,    # 下载目录沉睡安装包自动索引
        "rule_dingtalk": True,     # 钉钉临时办公音视频缓存清理
        "rule_dev_cache": True,    # Cargo 与 npm 开发包缓存监测
        "rule_apfs_snapshot": True # APFS 本地幽灵快照自动捕获
    }
}

class ConfigManager:
    _cached_config: Dict[str, Any] = None

    @classmethod
    def load(cls) -> Dict[str, Any]:
        if cls._cached_config is not None:
            return cls._cached_config

        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 补齐可能缺失的默认项
                    for k, v in DEFAULT_CONFIG.items():
                        if k not in data:
                            data[k] = v
                    cls._cached_config = data
                    return data
            except Exception:
                pass

        cls._cached_config = dict(DEFAULT_CONFIG)
        cls.save()
        return cls._cached_config

    @classmethod
    def save(cls):
        if cls._cached_config is None:
            return
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cls._cached_config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @classmethod
    def get_custom_directories(cls) -> List[str]:
        cfg = cls.load()
        return cfg.get("custom_directories", [])

    @classmethod
    def add_custom_directory(cls, path: str) -> bool:
        cfg = cls.load()
        dirs = cfg.setdefault("custom_directories", [])
        if path not in dirs and os.path.exists(path):
            dirs.append(path)
            cls.save()
            return True
        return False

    @classmethod
    def remove_custom_directory(cls, path: str) -> bool:
        cfg = cls.load()
        dirs = cfg.get("custom_directories", [])
        if path in dirs:
            dirs.remove(path)
            cls.save()
            return True
        return False

    @classmethod
    def set_rule_enabled(cls, rule_id: str, enabled: bool):
        cfg = cls.load()
        rules = cfg.setdefault("rules", {})
        rules[rule_id] = enabled
        cls.save()

    @classmethod
    def is_rule_enabled(cls, rule_id: str) -> bool:
        cfg = cls.load()
        return cfg.get("rules", {}).get(rule_id, True)

    @classmethod
    def set_inspection_interval(cls, minutes: int):
        cfg = cls.load()
        cfg["inspection_interval_minutes"] = minutes
        cls.save()

    @classmethod
    def set_auto_inspection(cls, enabled: bool):
        cfg = cls.load()
        cfg["auto_inspection_enabled"] = enabled
        cls.save()

    @classmethod
    def reset_default_rules(cls):
        cfg = cls.load()
        cfg["rules"] = dict(DEFAULT_CONFIG["rules"])
        cls.save()

    @classmethod
    def set_surge_threshold(cls, mb: int):
        cfg = cls.load()
        cfg["surge_threshold_mb"] = mb
        cls.save()

    @classmethod
    def get_surge_threshold(cls) -> int:
        cfg = cls.load()
        return cfg.get("surge_threshold_mb", 500)

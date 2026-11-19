"""
品牌配置中心 - 可随时在此修改产品名称与标语
"""
import os
import sys
from dataclasses import dataclass

@dataclass(frozen=True)
class BrandConfig:
    # 英文名称
    NAME: str = "SpaceRadar"
    # 中文名称
    NAME_CN: str = "空间雷达"
    # 品牌 LOGO 缩写 (如 "S." 或 "⚡️")
    LOGO_TAG: str = "S."
    # 副标题与标语
    TAGLINE: str = "Mac 磁盘增长时间点归因与一键瘦身"
    VERSION: str = "1.0.0"
    # 窗口标题展示
    WINDOW_TITLE: str = "SpaceRadar · 空间雷达"

BRAND = BrandConfig()

def get_asset_path(filename: str = "") -> str:
    """
    获取资源文件的绝对路径（兼顾源码运行、PyInstaller 单目录、Windows 与 macOS .app Bundle）
    """
    candidates = []
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            candidates.append(os.path.join(sys._MEIPASS, 'assets'))
            candidates.append(os.path.join(sys._MEIPASS, '_internal', 'assets'))
        app_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(app_dir, 'assets'))
        candidates.append(os.path.join(app_dir, '_internal', 'assets'))
        res_dir = os.path.join(os.path.dirname(app_dir), 'Resources')
        candidates.append(res_dir)
        candidates.append(os.path.join(res_dir, 'assets'))

    cur_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(cur_dir, 'assets'))
    candidates.append(os.path.join(os.path.dirname(cur_dir), 'assets'))

    for c in candidates:
        target = os.path.join(c, filename) if filename else c
        if os.path.exists(target):
            return target

    return os.path.join(cur_dir, 'assets', filename) if filename else os.path.join(cur_dir, 'assets')


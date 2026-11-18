"""
品牌配置中心 - 可随时在此修改产品名称与标语
"""
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

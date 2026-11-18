"""
调色板与视觉设计系统 (Theme & Color Tokens)
1:1 复刻截图：浅色瓷感画板 + 丁香紫轻柔微渐变 + 悬浮深黑 HUD 控制岛 + 紫色高光
"""
from dataclasses import dataclass
from PySide6.QtGui import QColor

@dataclass(frozen=True)
class Theme:
    # 核心背景
    BG_CANVAS = "#F6F7FA"         # 画板底色（浅灰瓷白）
    BG_CARD = "#FFFFFF"           # 卡片底色（纯白）
    BG_PILL_GRAY = "#F4F5F8"      # 胶囊灰底
    BG_PILL_HOVER = "#ECF0F6"     # 胶囊悬浮灰底
    
    # 悬浮深黑控制岛 (HUD)
    HUD_BG = "#111318"            # 深邃黑渊底色
    HUD_CARD_SUB = "#1E2330"      # 控制岛内二级卡片
    HUD_BORDER = "#232733"        # 控制岛外微边框
    
    # 边框与分割
    BORDER_SUBTLE = "#EAEDF2"     # 浅色 1px 描边
    BORDER_FOCUS = "#7C3AED"      # 激活边框
    
    # 关键强调色（丁香紫 / 电光紫）
    ACCENT_PURPLE = "#7C3AED"     # 核心紫
    ACCENT_PURPLE_LIGHT = "#F5F3FF" # 浅紫淡色背景
    ACCENT_PURPLE_HOVER = "#6D28D9"
    ACCENT_EMERALD = "#10B981"    # 绿色安全标
    ACCENT_AMBER = "#F59E0B"      # 琥珀黄警告标
    
    # 文字层级
    TEXT_MAIN = "#111318"         # 主标题纯黑
    TEXT_BODY = "#333842"         # 正文深灰
    TEXT_MUTED = "#656D76"        # 次级说明灰
    TEXT_HINT = "#8C95A6"         # 弱化标签灰

THEME = Theme()

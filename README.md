# 空间雷达 · SpaceRadar 🚀
> Mac 磁盘增长智能雷达与小白一键瘦身桌面应用

融合现代高质感桌面 UI 架构：**极简浅色瓷感画板 + 丁香紫轻渐变横幅 + 悬浮居中深黑动态控制岛 (HUD) + 底部悬浮毛玻璃胶囊 Dock 栏**。

---

## 🌟 核心特性

1. **悬浮居中深黑动态控制岛 (HUD Card)**：
   - 自动将当前最严峻的“吞盘元凶”（如 APFS 本地快照、剪映渲染、AI 大模型）提取为顶层控制卡片；
   - 提供白底黑字高亮胶囊 `[ ▶ 一键释放空间 ]`，秒级回收空间。
2. **小白通俗人话与三色安全指示**：
   - 不给用户看晦涩的深层终端路径，用通俗语言解释“发生了什么”；
   - 标明安全级别（🟢 100% 安全、🟡 建议确认），彻底消除误删恐惧。
3. **海报网格与胶囊工具栏**：
   - 原版复刻带对勾徽章的海报式网格卡片；
   - 支持全选、监控卷切换、在访达中一键高亮定位。
4. **品牌与产品名称自由定制**：
   - 产品名称与标语统一定义在 `brand.py` 中，随时可自定义。

---

## 🏃 快速启动

在终端中执行：

```bash
cd ~/Desktop/project/space-radar
.venv/bin/python main.py
```

或者使用 `uv`：

```bash
cd ~/Desktop/project/space-radar
uv run main.py
```

---

## 📁 项目工程目录

```text
space-radar/
├── brand.py              # 品牌定义配置 (可随时修改产品名称)
├── core/
│   ├── classifier.py     # 智能分类规则库与安全分级
│   ├── cleaner.py        # 底层安全清理执行器 (tmutil, 访达定位, 缓存清空)
│   └── sensor.py         # 磁盘容量与热区探测器
├── ui/
│   ├── theme.py          # 浅色瓷白 + 丁香紫 + 深黑 HUD 调色板
│   ├── desktop_ui_kit.py # 自研控件库 (Card, HudCard, CapsuleButton, PosterCard, FloatingDock)
│   └── main_window.py    # 主窗口布局与后台扫描联动
└── main.py               # 应用启动入口
```

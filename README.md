# SpaceRadar · 空间雷达 🚀
> **精确到秒级的磁盘增长归因与智能安全瘦身桌面客户端**  
> *Mac & Windows 双平台支持 · 极简浅色瓷感画板 + 悬浮深黑 HUD 动态岛 + 底部毛玻璃胶囊 Dock*

[![Build & Release Windows NSIS Installer](https://github.com/xiaofengtien/space-radar/actions/workflows/build-windows.yml/badge.svg)](https://github.com/xiaofengtien/space-radar/actions/workflows/build-windows.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-brightgreen.svg)]()

---

## 💡 为什么需要 SpaceRadar？

市面上传统的磁盘清理工具多存在两个通病：
1. **只能看静态存量，无法感知“增长发生的时间点”**：用户经常困惑“昨晚还有 100G，怎么今天突然满了？到底是哪个软件在什么时候偷吞的？”
2. **专业门槛高、容易误删重要数据**：充斥晦涩的文件路径，小白用户面对深层缓存不敢删、怕坏事。

**SpaceRadar · 空间雷达** 围绕“**秒级时间归因 + 绝对安全白名单**”打造：
* ⚡️ **时间流水账**：精确记录每次磁盘突增发生的**年月日、时分秒**与对应软件。
* 🛡️ **安全白名单**：微信聊天记录、剪映工程原件、代码开发源文件 100% 绝对保护，仅处理可再生的高危冗余。
* 🎯 **动态控制岛 (HUD)**：智能锁定当前最严峻的空间激增源（APFS 本地快照、超大渲染、下载镜像），一键胶囊释放。

---

## 📦 跨平台打包与发布 (Packaging)

### 🪟 Windows (NSIS 现代化安装包)
已集成 GitHub Actions 自动化 CI/CD 流水线：
* **自动编译**：每次推送 Release Tag（如 `v1.0.0`），云端自动通过 `PyInstaller` 提取依赖，并通过 `makensis` 编译生成标准 Windows 安装引导程序。
* **产物下载**：进入 GitHub 仓库右侧 **Releases** 即可下载 `SpaceRadar-Setup-v1.0.0-win64.exe`。
* **本地构建**：若本地有 NSIS 环境，可直接执行：
  ```bash
  packaging/windows/build_nsis.sh
  ```

### 🍎 macOS 原生启动
```bash
git clone https://github.com/xiaofengtien/space-radar.git
cd space-radar
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
./run.sh
```

---

## 📁 工程架构

```text
space-radar/
├── .github/workflows/         # GitHub Actions 自动化 CI/CD
│   └── build-windows.yml     # Windows NSIS 安装包自动编译发布
├── assets/                   # 高清矢量多分辨率图标 (PNG / ICNS / ICO)
├── brand.py                  # 品牌与产品名称集中配置
├── core/
│   ├── classifier.py         # 智能分类规则库与安全分级
│   ├── cleaner.py            # 底层安全清理执行器 (tmutil / APFS / 缓存安全释放)
│   ├── macos_compat.py       # macOS 系统级进程身份与 Dock 品牌守护
│   └── sensor.py             # 磁盘容量探测与秒级增长热区监听
├── packaging/windows/
│   ├── build_nsis.sh         # NSIS 交叉编译脚本
│   ├── installer.nsi         # NSIS Modern UI 2 现代流线安装向导
│   └── spaceradar.spec       # PyInstaller Windows 打包规范
├── ui/
│   ├── desktop_ui_kit.py     # 桌面级自研组件 (Card, HudCard, CapsuleButton, FloatingDock)
│   ├── main_window.py        # 主窗口布局与六大看板联动
│   └── theme.py              # 极简浅色瓷感 + 丁香紫 + 深黑钛金调色板
├── main.py                   # 客户端入口
└── run.sh                    # 一键极速启动入口
```

---

## 📄 开源许可证

本项目基于 [MIT 许可证](LICENSE) 开源。

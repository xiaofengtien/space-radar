#!/bin/bash
# ============================================================================
# SpaceRadar Windows NSIS 编译打包辅助脚本
# ============================================================================
set -e

DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$DIR"

echo "=== 1. 检查构建依赖 ==="
if ! command -v makensis &> /dev/null; then
    echo "❌ 错误: 未检测到 makensis。请在 Mac 上执行: brew install makensis"
    exit 1
fi
echo "✅ makensis 已就绪: $(makensis -VERSION)"

if [ ! -d "dist/SpaceRadar" ]; then
    echo "⚠️ 提示: 未检测到 dist/SpaceRadar 二进制应用目录。"
    echo "👉 方式 A (推荐): 在 GitHub Actions CI 或 Windows 虚拟机中执行: pyinstaller packaging/windows/spaceradar.spec"
    echo "👉 方式 B: 若仅验证 NSIS 安装向导外观，可创建模拟目录测试。"
    read -p "是否创建临时模拟目录验证 NSIS 编译? (y/N) " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        mkdir -p dist/SpaceRadar
        touch dist/SpaceRadar/SpaceRadar.exe
    else
        exit 0
    fi
fi

echo "=== 2. 编译 NSIS 安装程序 ==="
makensis packaging/windows/installer.nsi

echo "=== 3. 构建成功 ==="
ls -lh dist/SpaceRadar-Setup-*.exe 2>/dev/null || true

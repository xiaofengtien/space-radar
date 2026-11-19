#!/usr/bin/env bash
set -e

# SpaceRadar macOS 一键打包 DMG 脚本
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${PROJECT_DIR}"

echo "=========================================="
echo "🚀 开始打包 SpaceRadar macOS 独立应用与 DMG"
echo "=========================================="

# 确定 Python / PyInstaller 解释器
if [ -f ".venv/bin/pyinstaller" ]; then
    PYINSTALLER=".venv/bin/pyinstaller"
elif command -v pyinstaller &> /dev/null; then
    PYINSTALLER="pyinstaller"
else
    echo "❌ 未检测到 pyinstaller，正在通过 uv 安装..."
    /Users/Aaron/.local/bin/uv pip install pyinstaller
    PYINSTALLER=".venv/bin/pyinstaller"
fi

echo "📦 1. 运行 PyInstaller 构建 SpaceRadar.app..."
"${PYINSTALLER}" packaging/macos/spaceradar.spec --clean --noconfirm

if [ ! -d "dist/SpaceRadar.app" ]; then
    echo "❌ 构建失败：未生成 dist/SpaceRadar.app"
    exit 1
fi

echo "✅ SpaceRadar.app 构建成功！"

# 获取架构标识 (arm64 或 x86_64)
ARCH=$(uname -m)
DMG_NAME="SpaceRadar-v1.0.0-macOS-${ARCH}.dmg"
DMG_PATH="dist/${DMG_NAME}"

echo "💿 2. 生成现代化拖拽安装 DMG 镜像 (${DMG_NAME})..."
rm -rf dist/dmg
mkdir -p dist/dmg
cp -R dist/SpaceRadar.app dist/dmg/
ln -s /Applications dist/dmg/Applications

rm -f "${DMG_PATH}"
hdiutil create -volname "SpaceRadar" -srcfolder dist/dmg -ov -format UDZO "${DMG_PATH}"
rm -rf dist/dmg

echo "=========================================="
echo "🎉 打包完成！"
echo "产物路径: ${PROJECT_DIR}/${DMG_PATH}"
echo "产物大小: $(du -sh "${DMG_PATH}" | cut -f1)"
echo "=========================================="

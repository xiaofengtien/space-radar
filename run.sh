#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# 确保 SpaceRadar 专属独立实体二进制存在 (非 symlink，macOS 内核与 Dock 才能真正识别)
if [ ! -f "$DIR/.venv/bin/SpaceRadar" ] || [ -L "$DIR/.venv/bin/SpaceRadar" ]; then
    rm -f "$DIR/.venv/bin/SpaceRadar"
    REAL_PY="$(readlink -f "$DIR/.venv/bin/python" 2>/dev/null || python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$DIR/.venv/bin/python")"
    cp "$REAL_PY" "$DIR/.venv/bin/SpaceRadar"
    chmod +x "$DIR/.venv/bin/SpaceRadar"
fi

exec "$DIR/.venv/bin/SpaceRadar" "$DIR/main.py" "$@"

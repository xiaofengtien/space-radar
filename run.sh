#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# 确保 SpaceRadar 专属可执行二进制链接存在
if [ ! -f "$DIR/.venv/bin/SpaceRadar" ]; then
    ln -sf python "$DIR/.venv/bin/SpaceRadar"
fi

exec "$DIR/.venv/bin/SpaceRadar" "$DIR/main.py" "$@"

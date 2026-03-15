#!/bin/bash
# 象棋AI启动脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "错误: 需要Python3"
    exit 1
fi

# 运行bot
python3 bot.py "$@"

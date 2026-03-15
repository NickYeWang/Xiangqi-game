#!/bin/bash
# 飞书消息处理入口

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 获取输入消息（从环境变量或参数）
MESSAGE="${1:-}"

if [ -z "$MESSAGE" ]; then
    # 尝试从stdin读取
    MESSAGE=$(cat)
fi

if [ -z "$MESSAGE" ]; then
    echo "No message provided"
    exit 1
fi

# 调用Python处理
python3 bot.py "@PROCESS@" <<< "$MESSAGE"

#!/bin/bash
# 象棋AI安装脚本

set -e

echo "🎯 象棋AI安装脚本"
echo "=================="

# 工作目录
WORK_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$WORK_DIR"

# 检测架构
ARCH=$(uname -m)
OS=$(uname -s)
echo "检测到系统: $OS $ARCH"

# 尝试多种方式安装引擎
echo ""
echo "📥 正在获取象棋引擎..."

# 方式1: 尝试brew安装fairy-stockfish
if command -v brew &> /dev/null; then
    echo "尝试通过Homebrew安装 fairy-stockfish..."
    brew install fairy-stockfish 2>/dev/null || echo "brew安装失败，尝试其他方式"
fi

# 方式2: 下载Pikafish预编译版本
if [ ! -f "./pikafish" ]; then
    echo "尝试下载Pikafish..."
    
    # macOS ARM64
    if [[ "$OS" == "Darwin" && "$ARCH" == "arm64" ]]; then
        URL="https://github.com/official-pikafish/Pikafish/releases/download/Pikafish-2026-01-02/Pikafish.2026-01-02.7z"
        echo "下载地址: $URL"
        
        if command -v curl &> /dev/null; then
            curl -L -o pikafish.7z "$URL" --max-time 300 || echo "下载中断，请手动下载"
        fi
        
        if [ -f "pikafish.7z" ]; then
            if command -v 7z &> /dev/null; then
                7z x pikafish.7z
                # 查找并复制引擎
                find . -name "pikafish*" -type f -executable -exec cp {} ./pikafish \; 2>/dev/null || true
            else
                echo "⚠️ 需要安装 p7zip 来解压: brew install p7zip"
            fi
        fi
    fi
fi

# 方式3: 从源码编译（备用）
if [ ! -f "./pikafish" ] && [ ! -f "./Pikafish/src/pikafish" ]; then
    echo "尝试从源码编译Pikafish..."
    if command -v git &> /dev/null && command -v make &> /dev/null; then
        git clone --depth 1 https://github.com/official-pikafish/Pikafish.git 2>/dev/null || true
        if [ -d "Pikafish/src" ]; then
            cd Pikafish/src
            make build ARCH=apple-silicon 2>/dev/null || make build ARCH=x86-64 2>/dev/null || echo "编译失败"
            cd ../..
            if [ -f "Pikafish/src/pikafish" ]; then
                cp Pikafish/src/pikafish ./pikafish
            fi
        fi
    fi
fi

# 检查安装结果
echo ""
echo "✅ 安装检查:"

ENGINE_FOUND=""

if [ -f "./pikafish" ] && [ -x "./pikafish" ]; then
    echo "✓ 找到本地引擎: ./pikafish"
    ENGINE_FOUND="./pikafish"
elif [ -f "./Pikafish/src/pikafish" ]; then
    echo "✓ 找到编译引擎: ./Pikafish/src/pikafish"
    ENGINE_FOUND="./Pikafish/src/pikafish"
elif command -v fairy-stockfish &> /dev/null; then
    echo "✓ 找到系统引擎: $(which fairy-stockfish)"
    ENGINE_FOUND="fairy-stockfish"
elif command -v pikafish &> /dev/null; then
    echo "✓ 找到系统引擎: $(which pikafish)"
    ENGINE_FOUND="pikafish"
else
    echo "⚠️ 未找到引擎，请手动安装:"
    echo "   方式1: brew install fairy-stockfish"
    echo "   方式2: 从 https://github.com/official-pikafish/Pikafish/releases 下载"
    exit 1
fi

# 测试引擎
echo ""
echo "🧪 测试引擎..."

if [ -n "$ENGINE_FOUND" ]; then
    # 简单UCI测试
    echo "uci" | "$ENGINE_FOUND" 2>/dev/null | head -5 || echo "引擎测试完成"
fi

# 创建启动脚本
cat > start_bot.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
python3 xiangqi_bot.py
EOF
chmod +x start_bot.sh

echo ""
echo "🎉 安装完成!"
echo ""
echo "使用方法:"
echo "  1. 测试: python3 xiangqi_bot.py"
echo "  2. 在飞书中输入: 象棋 对战"
echo ""
echo "文件位置: $WORK_DIR"
ls -la

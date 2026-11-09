#!/bin/bash
# AI副业自动化系统 - 一键启动脚本
# 在 UCloud Linux 服务器上运行

set -e

echo "=============================================="
echo "  🚀 AI副业自动化系统 启动"
echo "=============================================="

cd "$(dirname "$0")"

# 1. 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 python3，请先安装"
    echo "   Ubuntu: sudo apt install python3 python3-pip"
    echo "   CentOS: sudo yum install python3 python3-pip"
    exit 1
fi

# 2. 安装依赖
echo "📦 安装依赖..."
pip3 install -r requirements.txt -q 2>/dev/null || pip install -r requirements.txt -q

# 3. 创建必要目录
mkdir -p data logs

# 4. 停止旧进程
if pgrep -f "python3 main.py" > /dev/null; then
    echo "⏹️  停止旧进程..."
    pkill -f "python3 main.py"
    sleep 1
fi

if pgrep -f "python3 web.py" > /dev/null; then
    echo "⏹️  停止旧Web面板..."
    pkill -f "python3 web.py"
    sleep 1
fi

# 5. 启动主程序（后台运行）
echo "🔄 启动自动化主程序..."
nohup python3 main.py > logs/main.log 2>&1 &
MAIN_PID=$!
echo "   主程序 PID: $MAIN_PID"

# 6. 启动 Web 面板（后台运行）
echo "🌐 启动Web管理面板..."
nohup python3 web.py > logs/web.log 2>&1 &
WEB_PID=$!
echo "   Web面板 PID: $WEB_PID"

# 7. 保存 PID
echo "$MAIN_PID" > logs/main.pid
echo "$WEB_PID" > logs/web.pid

sleep 2

# 8. 检查是否启动成功
if kill -0 $MAIN_PID 2>/dev/null; then
    echo "✅ 主程序启动成功"
else
    echo "❌ 主程序启动失败，查看 logs/main.log"
    tail -20 logs/main.log
fi

if kill -0 $WEB_PID 2>/dev/null; then
    echo "✅ Web面板启动成功"
else
    echo "❌ Web面板启动失败，查看 logs/web.log"
    tail -20 logs/web.log
fi

# 9. 显示访问地址
IP=$(hostname -I | awk '{print $1}')
echo ""
echo "=============================================="
echo "  ✅ 启动完成！"
echo ""
echo "  📊 Web管理面板：http://$IP:8080"
echo "  📱 手机打开就能用"
echo ""
echo "  📋 查看状态：tail -f logs/main.log"
echo "  📋 查看Web日志：tail -f logs/web.log"
echo ""
echo "  🛑 停止命令：bash stop.sh"
echo "=============================================="

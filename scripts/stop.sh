#!/bin/bash
# 停止所有服务

cd "$(dirname "$0")/.."

echo "🛑 停止 AI副业自动化系统..."

if [ -f logs/main.pid ]; then
    MAIN_PID=$(cat logs/main.pid)
    if kill -0 $MAIN_PID 2>/dev/null; then
        kill $MAIN_PID && echo "✅ 主程序已停止 (PID: $MAIN_PID)"
    fi
fi

if [ -f logs/web.pid ]; then
    WEB_PID=$(cat logs/web.pid)
    if kill -0 $WEB_PID 2>/dev/null; then
        kill $WEB_PID && echo "✅ Web面板已停止 (PID: $WEB_PID)"
    fi
fi

# 兜底：确保没有残留
pkill -f "python3 main.py" 2>/dev/null && echo "🧹 清理残留主进程" || true
pkill -f "python3 web.py" 2>/dev/null && echo "🧹 清理残留Web进程" || true

echo "✅ 全部停止"

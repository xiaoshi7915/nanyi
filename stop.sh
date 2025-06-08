#!/bin/bash
# 南意秋棠 - 停止服务脚本

echo "🛑 停止南意秋棠服务..."

# 停止后端服务
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        kill $BACKEND_PID
        echo "✅ 后端服务已停止 (PID: $BACKEND_PID)"
    else
        echo "⚠️ 后端服务进程不存在"
    fi
    rm -f logs/backend.pid
else
    echo "⚠️ 未找到后端服务PID文件"
fi

# 停止前端服务
if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null; then
        kill $FRONTEND_PID
        echo "✅ 前端服务已停止 (PID: $FRONTEND_PID)"
    else
        echo "⚠️ 前端服务进程不存在"
    fi
    rm -f logs/frontend.pid
else
    echo "⚠️ 未找到前端服务PID文件"
fi

# 强制杀死可能残留的进程
pkill -f "python.*app.py"
pkill -f "python.*server.py"

echo "🏁 所有服务已停止" 
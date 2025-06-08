#!/bin/bash
# 南意秋棠服务停止脚本

echo "🛑 停止南意秋棠服务..."

# 停止后端服务（包括所有版本）
echo "停止后端服务..."
pkill -f "backend/app.py" 2>/dev/null || true
pkill -f "backend/standalone_app.py" 2>/dev/null || true

# 停止前端服务
echo "停止前端服务..."
pkill -f "frontend/app.py" 2>/dev/null || true

# 等待进程完全停止
sleep 2

echo "✅ 所有服务已停止" 
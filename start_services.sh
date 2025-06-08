#!/bin/bash
# 南意秋棠服务启动脚本 v3.0 - 真实数据库版本

echo "🚀 启动南意秋棠服务（真实数据库版本）..."

# 创建日志目录
mkdir -p logs

# 停止现有进程
echo "📋 停止现有进程..."
pkill -f "backend/app.py" 2>/dev/null || true
pkill -f "backend/standalone_app.py" 2>/dev/null || true
pkill -f "frontend/app.py" 2>/dev/null || true
sleep 1

# 设置环境变量
export FLASK_ENV=development
export PORT=5001
export HOST=0.0.0.0

# 启动后端服务（真实数据库版本）
echo "🔧 启动后端服务 - 真实数据库 (端口5001)..."
cd /opt/hanfu/products
nohup python3 backend/app.py > logs/backend.log 2>&1 &
backend_pid=$!
echo "后端服务PID: $backend_pid"

# 等待后端启动
sleep 5

# 启动前端服务
echo "🎨 启动前端服务 (端口8500)..."
nohup python3 frontend/app.py > logs/frontend.log 2>&1 &
frontend_pid=$!
echo "前端服务PID: $frontend_pid"

# 等待服务启动
sleep 3

# 检查服务状态
echo "🔍 检查服务状态..."

# 检查后端
echo "后端健康检查:"
curl -s "http://localhost:5001/health" | jq '.' 2>/dev/null || curl -s "http://localhost:5001/health" || echo "后端服务未响应"

echo ""

# 检查前端
echo "前端健康检查:"
curl -s "http://localhost:8500/health" | jq '.' 2>/dev/null || echo "前端服务未响应"

echo ""
echo "📱 访问地址:"
echo "前端: http://121.36.205.70:8500"
echo "后端API: http://121.36.205.70:5001/api"
echo ""
echo "💡 服务管理:"
echo "查看后端日志: tail -f logs/backend.log"
echo "查看前端日志: tail -f logs/frontend.log"
echo "停止服务: ./stop_services.sh"
echo ""
echo "🗄️ 数据库连接: 使用真实数据库"
echo "✅ 服务启动完成!" 
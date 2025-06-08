#!/bin/bash
# 南意秋棠 - 一键启动脚本

echo "🚀 启动南意秋棠服务..."

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    echo "❌ 错误: .env文件不存在"
    echo "请复制.env.example为.env并配置相关参数"
    exit 1
fi

# 检查Python依赖
echo "📦 检查Python依赖..."
pip install -r requirements.txt

# 启动后端服务（后台运行）
echo "🔧 启动后端API服务..."
cd backend
nohup python app.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "后端服务PID: $BACKEND_PID"
cd ..

# 等待后端启动
sleep 3

# 启动前端服务（后台运行）
echo "🎨 启动前端服务..."
cd frontend
nohup python server.py > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端服务PID: $FRONTEND_PID"
cd ..

# 保存PID到文件
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo "✅ 服务启动完成!"
echo "📱 前端访问: http://localhost:8500"
echo "🔗 后端API: http://localhost:5001"
echo "📋 查看日志: tail -f logs/backend.log 或 tail -f logs/frontend.log"
echo "�� 停止服务: ./stop.sh" 
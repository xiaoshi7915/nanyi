#!/bin/bash

echo "重启汉服展示系统..."

# 停止现有进程
echo "停止现有服务..."
pkill -f "app.py" 2>/dev/null
pkill -f "server.py" 2>/dev/null
sleep 2

# 启动后端
echo "启动后端服务..."
cd /opt/hanfu/products/backend
nohup python app.py > ../logs/backend.log 2>&1 &
echo $! > ../backend.pid

# 启动前端
echo "启动前端服务..."
cd /opt/hanfu/products/frontend
nohup python server.py > ../logs/frontend.log 2>&1 &
echo $! > ../frontend.pid

cd /opt/hanfu/products

echo "✅ 服务重启完成"
echo "前端: http://localhost:8500"
echo "后端: http://localhost:5001"
echo "域名: http://products.nanyiqiutang.cn" 
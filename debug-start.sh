#!/bin/bash

# 调试启动脚本 - 基于用户成功的启动过程

echo "🔍 调试启动后端服务..."

# 设置环境
export PYTHONPATH=/opt/hanfu/products:$PYTHONPATH
source products_env/bin/activate

echo "✅ 环境设置完成"
echo "Python: $(which python)"
echo "PYTHONPATH: $PYTHONPATH"

# 进入后端目录
cd backend

echo "🚀 启动后端服务 (前台模式，便于调试)..."
python app.py 
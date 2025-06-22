#!/bin/bash

# 汉服产品展示系统 - 简单服务管理脚本

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 虚拟环境路径
VENV_PATH="${SCRIPT_DIR}/products_env"

# 检查虚拟环境是否存在
check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        echo "❌ 虚拟环境不存在: $VENV_PATH"
        echo "请先运行: ./setup-env.sh"
        exit 1
    fi
}

case "$1" in
    start)
        echo "启动服务..."
        check_venv
        
        # 创建日志目录
        mkdir -p "${SCRIPT_DIR}/logs"
        
        # 激活虚拟环境
        echo "🔧 激活虚拟环境..."
        source "${VENV_PATH}/bin/activate"
        echo "✅ 虚拟环境已激活: $(which python)"
        
        # 启动后端服务
        echo "🔧 启动后端服务..."
        cd "${SCRIPT_DIR}/backend"
        nohup python app.py > ../logs/backend.log 2>&1 &
        BACKEND_PID=$!
        echo $BACKEND_PID > ../backend.pid
        echo "后端服务已启动 (PID: $BACKEND_PID)"
        cd "${SCRIPT_DIR}"
        
        # 等待后端启动
        sleep 3
        
        # 启动前端服务
        echo "🌐 启动前端服务..."
        cd "${SCRIPT_DIR}/frontend"
        nohup python server.py > ../logs/frontend.log 2>&1 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > ../frontend.pid
        echo "前端服务已启动 (PID: $FRONTEND_PID)"
        cd "${SCRIPT_DIR}"
        
        # 等待服务启动
        sleep 3
        
        echo "✅ 服务启动完成"
        echo "前端: http://localhost:8500"
        echo "后端: http://localhost:5001"
        
        # 检查服务状态
        $0 status
        ;;
    stop)
        echo "停止服务..."
        
        # 停止后端
        if [ -f "${SCRIPT_DIR}/backend.pid" ]; then
            BACKEND_PID=$(cat "${SCRIPT_DIR}/backend.pid")
            echo "🔧 停止后端服务 (PID: $BACKEND_PID)..."
            if kill -0 $BACKEND_PID 2>/dev/null; then
                kill $BACKEND_PID 2>/dev/null
                echo "✅ 后端服务已停止"
            else
                echo "⚠️ 后端服务进程不存在"
            fi
            rm "${SCRIPT_DIR}/backend.pid"
        else
            echo "⚠️ 未找到后端PID文件"
        fi
        
        # 停止前端
        if [ -f "${SCRIPT_DIR}/frontend.pid" ]; then
            FRONTEND_PID=$(cat "${SCRIPT_DIR}/frontend.pid")
            echo "🌐 停止前端服务 (PID: $FRONTEND_PID)..."
            if kill -0 $FRONTEND_PID 2>/dev/null; then
                kill $FRONTEND_PID 2>/dev/null
                echo "✅ 前端服务已停止"
            else
                echo "⚠️ 前端服务进程不存在"
            fi
            rm "${SCRIPT_DIR}/frontend.pid"
        else
            echo "⚠️ 未找到前端PID文件"
        fi
        
        # 强制杀死可能残留的进程
        echo "🧹 清理残留进程..."
        pkill -f "python.*app.py" 2>/dev/null && echo "清理后端残留进程" || true
        pkill -f "python.*server.py" 2>/dev/null && echo "清理前端残留进程" || true
        
        echo "✅ 服务停止完成"
        ;;
    restart)
        echo "重启服务..."
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        echo "服务状态:"
        
        # 检查后端服务状态（通过进程名查找，更可靠）
        RUNNING_BACKEND_PID=$(pgrep -f "python.*app.py" | head -1)
        if [ -n "$RUNNING_BACKEND_PID" ]; then
            echo "✅ 后端服务运行中 (PID: $RUNNING_BACKEND_PID)"
            # 更新PID文件
            echo $RUNNING_BACKEND_PID > "${SCRIPT_DIR}/backend.pid"
        else
            echo "❌ 后端服务未运行"
            rm -f "${SCRIPT_DIR}/backend.pid"
        fi
        
        # 检查前端服务状态（通过进程名查找，更可靠）
        RUNNING_FRONTEND_PID=$(pgrep -f "python.*server.py" | head -1)
        if [ -n "$RUNNING_FRONTEND_PID" ]; then
            echo "✅ 前端服务运行中 (PID: $RUNNING_FRONTEND_PID)"
            # 更新PID文件
            echo $RUNNING_FRONTEND_PID > "${SCRIPT_DIR}/frontend.pid"
        else
            echo "❌ 前端服务未运行"
            rm -f "${SCRIPT_DIR}/frontend.pid"
        fi
        ;;
    deploy-nginx)
        echo "部署nginx配置..."
        cd "${SCRIPT_DIR}"
        chmod +x deploy-nginx.sh
        ./deploy-nginx.sh
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|deploy-nginx}"
        echo ""
        echo "命令说明:"
        echo "  start        - 启动前后端服务"
        echo "  stop         - 停止前后端服务"
        echo "  restart      - 重启前后端服务"
        echo "  status       - 查看服务状态"
        echo "  deploy-nginx - 部署nginx配置（只需运行一次）"
        exit 1
        ;;
esac 
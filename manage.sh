#!/bin/bash

# 汉服产品展示系统 - 简单服务管理脚本

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$1" in
    start)
        echo "启动服务..."
        # 启动后端
        cd "${SCRIPT_DIR}/backend" && nohup python app.py > ../logs/backend.log 2>&1 & echo $! > ../backend.pid
        cd "${SCRIPT_DIR}"
        # 启动前端
        cd "${SCRIPT_DIR}/frontend" && nohup python server.py > ../logs/frontend.log 2>&1 & echo $! > ../frontend.pid
        cd "${SCRIPT_DIR}"
        echo "✅ 服务启动完成"
        echo "前端: http://localhost:8500"
        echo "后端: http://localhost:5001"
        ;;
    stop)
        echo "停止服务..."
        # 停止后端
        if [ -f "${SCRIPT_DIR}/backend.pid" ]; then
            kill $(cat "${SCRIPT_DIR}/backend.pid") 2>/dev/null
            rm "${SCRIPT_DIR}/backend.pid"
        fi
        # 停止前端
        if [ -f "${SCRIPT_DIR}/frontend.pid" ]; then
            kill $(cat "${SCRIPT_DIR}/frontend.pid") 2>/dev/null
            rm "${SCRIPT_DIR}/frontend.pid"
        fi
        echo "✅ 服务已停止"
        ;;
    restart)
        echo "重启服务..."
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        echo "服务状态:"
        if [ -f "${SCRIPT_DIR}/backend.pid" ] && kill -0 $(cat "${SCRIPT_DIR}/backend.pid") 2>/dev/null; then
            echo "✅ 后端服务运行中 (PID: $(cat "${SCRIPT_DIR}/backend.pid"))"
        else
            echo "❌ 后端服务未运行"
        fi
        
        if [ -f "${SCRIPT_DIR}/frontend.pid" ] && kill -0 $(cat "${SCRIPT_DIR}/frontend.pid") 2>/dev/null; then
            echo "✅ 前端服务运行中 (PID: $(cat "${SCRIPT_DIR}/frontend.pid"))"
        else
            echo "❌ 前端服务未运行"
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
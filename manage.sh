#!/bin/bash

# 汉服产品展示系统 - 增强版服务管理脚本
# 基于用户成功的启动实践优化

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 虚拟环境路径
VENV_PATH="${SCRIPT_DIR}/products_env"

# 日志目录
LOG_DIR="${SCRIPT_DIR}/logs"

# 检查虚拟环境是否存在
check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        echo "❌ 虚拟环境不存在: $VENV_PATH"
        echo "请先运行: ./setup-env.sh"
        exit 1
    fi
}

# 激活虚拟环境并设置环境变量
activate_env() {
    echo "🔧 激活虚拟环境..."
    source "${VENV_PATH}/bin/activate"
    
    # 设置Python路径 - 关键！
    export PYTHONPATH="${SCRIPT_DIR}:$PYTHONPATH"
    
    echo "✅ 虚拟环境已激活: $(which python)"
    echo "✅ Python路径已设置: $PYTHONPATH"
}

# 启动后端服务的函数
start_backend() {
    echo "🔧 启动后端服务..."
    
    # 切换到backend目录
    cd "${SCRIPT_DIR}/backend"
    
    # 设置环境变量并使用虚拟环境中的python启动
    export PYTHONPATH="${SCRIPT_DIR}:"
    "${VENV_PATH}/bin/python" app.py > "${LOG_DIR}/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "${SCRIPT_DIR}/backend.pid"
    
    # 返回项目根目录
    cd "${SCRIPT_DIR}"
    
    echo "后端服务已启动 (PID: $BACKEND_PID)"
    echo "📋 后端日志: tail -f ${LOG_DIR}/backend.log"
    
    return $BACKEND_PID
}

# 启动前端服务的函数
start_frontend() {
    echo "🌐 启动前端服务..."
    
    # 切换到frontend目录
    cd "${SCRIPT_DIR}/frontend"
    
    export PYTHONPATH="${SCRIPT_DIR}:"
    
    # 使用虚拟环境中的python启动，确保有详细日志
    "${VENV_PATH}/bin/python" server.py > "${LOG_DIR}/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "${SCRIPT_DIR}/frontend.pid"
    
    # 返回项目根目录
    cd "${SCRIPT_DIR}"
    
    echo "前端服务已启动 (PID: $FRONTEND_PID)"
    echo "📋 前端日志: tail -f ${LOG_DIR}/frontend.log"
    
    return $FRONTEND_PID
}

case "$1" in
    start)
        echo "启动服务..."
        check_venv
        
        # 创建日志目录
        mkdir -p "${LOG_DIR}"
        
        # 激活虚拟环境并设置环境变量
        activate_env
        
        # 清空之前的日志（可选）
        echo "🧹 清理旧日志..."
        > "${LOG_DIR}/backend.log"
        > "${LOG_DIR}/frontend.log"
        
        # 启动后端服务
        start_backend
        
        # 等待后端启动
        echo "⏳ 等待后端服务启动..."
        sleep 5
        # 激活虚拟环境并设置环境变量
        activate_env
        
        # 启动前端服务
        start_frontend
        
        # 等待前端启动
        echo "⏳ 等待前端服务启动..."
        sleep 3
        
        echo ""
        echo "✅ 服务启动完成！"
        echo "🌐 前端访问: http://localhost:8500"
        echo "🔗 后端API: http://localhost:5001"
        echo "🌍 域名访问: http://products.nanyiqiutang.cn"
        echo ""
        echo "📋 实时日志监控:"
        echo "   后端日志: tail -f ${LOG_DIR}/backend.log"
        echo "   前端日志: tail -f ${LOG_DIR}/frontend.log"
        echo ""
        
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
        
        # 显示端口监听状态
        echo ""
        echo "端口监听状态:"
        netstat -tulpn 2>/dev/null | grep -E "(5001|8500)" | while read line; do
            echo "  $line"
        done
        ;;
    logs)
        # 新增日志查看功能
        case "$2" in
            backend|be)
                echo "📋 后端日志 (实时):"
                tail -f "${LOG_DIR}/backend.log"
                ;;
            frontend|fe)
                echo "📋 前端日志 (实时):"
                tail -f "${LOG_DIR}/frontend.log"
                ;;
            all|*)
                echo "📋 查看所有日志 (最新50行):"
                echo "=== 后端日志 ==="
                tail -25 "${LOG_DIR}/backend.log" 2>/dev/null || echo "后端日志文件不存在"
                echo ""
                echo "=== 前端日志 ==="
                tail -25 "${LOG_DIR}/frontend.log" 2>/dev/null || echo "前端日志文件不存在"
                ;;
        esac
        ;;
    test)
        # 新增测试功能
        echo "🧪 测试服务连接..."
        
        echo "测试后端API..."
        if curl -s http://localhost:5001/api/health >/dev/null 2>&1; then
            echo "✅ 后端API正常"
        else
            echo "❌ 后端API无响应"
        fi
        
        echo "测试前端服务..."
        if curl -s http://localhost:8500 >/dev/null 2>&1; then
            echo "✅ 前端服务正常"
        else
            echo "❌ 前端服务无响应"
        fi
        ;;
    deploy-nginx)
        echo "部署nginx配置..."
        cd "${SCRIPT_DIR}"
        chmod +x deploy-nginx.sh
        ./deploy-nginx.sh
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs|test|deploy-nginx}"
        echo ""
        echo "命令说明:"
        echo "  start            - 启动前后端服务"
        echo "  stop             - 停止前后端服务"
        echo "  restart          - 重启前后端服务"
        echo "  status           - 查看服务状态"
        echo "  logs [be|fe|all] - 查看日志 (backend/frontend/all)"
        echo "  test             - 测试服务连接"
        echo "  deploy-nginx     - 部署nginx配置（只需运行一次）"
        echo ""
        echo "日志监控示例:"
        echo "  $0 logs backend  - 实时查看后端日志"
        echo "  $0 logs frontend - 实时查看前端日志"
        echo "  $0 logs all      - 查看所有日志摘要"
        exit 1
        ;;
esac 
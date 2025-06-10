#!/bin/bash
# 南意秋棠 - 服务停止脚本（增强版）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_DIR=$(pwd)
BACKEND_PID_FILE="$PROJECT_DIR/backend.pid"
FRONTEND_PID_FILE="$PROJECT_DIR/frontend.pid"

# 打印彩色消息
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 停止指定PID的进程
stop_process() {
    local pid=$1
    local service_name=$2
    local timeout=10
    
    if [ -z "$pid" ] || [ "$pid" = "0" ]; then
        print_warning "$service_name PID无效"
        return 1
    fi
    
    # 检查进程是否存在
    if ! kill -0 "$pid" 2>/dev/null; then
        print_warning "$service_name 进程不存在 (PID: $pid)"
        return 1
    fi
    
    print_status "停止 $service_name 进程 (PID: $pid)..."
    
    # 优雅停止
    kill -TERM "$pid" 2>/dev/null || true
    
    # 等待进程退出
    local count=0
    while [ $count -lt $timeout ]; do
        if ! kill -0 "$pid" 2>/dev/null; then
            print_success "$service_name 已停止"
            return 0
        fi
        sleep 1
        ((count++))
    done
    
    # 强制停止
    print_warning "$service_name 未响应，强制停止..."
    kill -KILL "$pid" 2>/dev/null || true
    sleep 1
    
    if ! kill -0 "$pid" 2>/dev/null; then
        print_success "$service_name 已强制停止"
        return 0
    else
        print_error "$service_name 停止失败"
        return 1
    fi
}

# 清理相关进程
cleanup_processes() {
    print_status "清理相关进程..."
    
    # 清理可能的僵尸进程
    local python_pids=$(pgrep -f "python.*app.py" 2>/dev/null || true)
    if [ -n "$python_pids" ]; then
        print_status "清理后端相关进程: $python_pids"
        echo "$python_pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        echo "$python_pids" | xargs kill -KILL 2>/dev/null || true
    fi
    
    local server_pids=$(pgrep -f "python.*server.py" 2>/dev/null || true)
    if [ -n "$server_pids" ]; then
        print_status "清理前端相关进程: $server_pids"
        echo "$server_pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        echo "$server_pids" | xargs kill -KILL 2>/dev/null || true
    fi
    
    # 清理http.server进程
    local http_pids=$(pgrep -f "http.server.*8500" 2>/dev/null || true)
    if [ -n "$http_pids" ]; then
        print_status "清理HTTP服务进程: $http_pids"
        echo "$http_pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        echo "$http_pids" | xargs kill -KILL 2>/dev/null || true
    fi
}

# 清理端口占用
cleanup_ports() {
    print_status "检查端口占用..."
    
    local ports=(5001 8500)
    for port in "${ports[@]}"; do
        local pid=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | head -1)
        if [ -n "$pid" ] && [ "$pid" != "-" ]; then
            print_status "端口 $port 被进程 $pid 占用，正在清理..."
            kill -TERM "$pid" 2>/dev/null || true
            sleep 2
            kill -KILL "$pid" 2>/dev/null || true
        fi
    done
}

# 清理PID文件
cleanup_pid_files() {
    print_status "清理PID文件..."
    
    [ -f "$BACKEND_PID_FILE" ] && rm -f "$BACKEND_PID_FILE"
    [ -f "$FRONTEND_PID_FILE" ] && rm -f "$FRONTEND_PID_FILE"
    
    print_success "PID文件已清理"
}

# 显示停止状态
show_stop_status() {
    echo ""
    echo "========================================"
    echo "        南意秋棠服务停止状态"
    echo "========================================"
    
    # 检查后端进程
    echo -e "\n📡 后端API服务:"
    local backend_running=false
    if pgrep -f "python.*app.py" > /dev/null 2>&1; then
        print_warning "仍在运行"
        backend_running=true
    else
        print_success "已停止"
    fi
    
    # 检查前端进程
    echo -e "\n🎨 前端Web服务:"
    local frontend_running=false
    if pgrep -f "python.*server.py\|http.server.*8500" > /dev/null 2>&1; then
        print_warning "仍在运行"
        frontend_running=true
    else
        print_success "已停止"
    fi
    
    # 检查端口占用
    echo -e "\n🔌 端口状态:"
    local ports_occupied=false
    for port in 5001 8500; do
        if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
            print_warning "端口 $port 仍被占用"
            ports_occupied=true
        else
            print_success "端口 $port 已释放"
        fi
    done
    
    echo "========================================"
    
    # 返回状态
    if [ "$backend_running" = true ] || [ "$frontend_running" = true ] || [ "$ports_occupied" = true ]; then
        return 1
    else
        return 0
    fi
}

# 主函数
main() {
    echo "🛑 停止南意秋棠服务..."
    echo ""
    
    local stop_success=true
    
    # 停止后端服务
    if [ -f "$BACKEND_PID_FILE" ]; then
        local backend_pid=$(cat "$BACKEND_PID_FILE" 2>/dev/null)
        if ! stop_process "$backend_pid" "后端API服务"; then
            stop_success=false
        fi
    else
        print_warning "后端PID文件不存在"
    fi
    
    # 停止前端服务
    if [ -f "$FRONTEND_PID_FILE" ]; then
        local frontend_pid=$(cat "$FRONTEND_PID_FILE" 2>/dev/null)
        if ! stop_process "$frontend_pid" "前端Web服务"; then
            stop_success=false
        fi
    else
        print_warning "前端PID文件不存在"
    fi
    
    # 清理相关进程
    cleanup_processes
    
    # 清理端口占用
    cleanup_ports
    
    # 清理PID文件
    cleanup_pid_files
    
    # 等待一下再检查状态
    sleep 2
    
    # 显示停止状态
    if show_stop_status; then
        echo ""
        print_success "🎉 南意秋棠服务已完全停止！"
        exit 0
    else
        echo ""
        print_warning "⚠️ 部分服务或端口可能仍在使用中"
        echo ""
        echo "💡 可以尝试:"
        echo "   - 重新运行此脚本"
        echo "   - 手动检查进程: ps aux | grep python"
        echo "   - 检查端口占用: netstat -tlnp | grep -E ':(5001|8500)'"
        exit 1
    fi
}

# 执行主函数
main "$@" 
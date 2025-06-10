#!/bin/bash
# 南意秋棠 - 服务启动脚本（增强版）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
BACKEND_PORT=5001
FRONTEND_PORT=8500
PROJECT_DIR=$(pwd)
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOGS_DIR="$PROJECT_DIR/logs"

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

# 检查端口是否被占用
check_port() {
    local port=$1
    local service_name=$2
    
    if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        print_warning "$service_name 端口 $port 已被占用"
        local pid=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1)
        if [[ -n "$pid" && "$pid" != "-" ]]; then
            print_warning "进程 PID: $pid"
            read -p "是否终止占用进程？(y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                kill -9 "$pid" 2>/dev/null || true
                print_success "进程已终止"
                sleep 2
            else
                print_error "无法启动 $service_name，端口被占用"
                return 1
            fi
        fi
    fi
    return 0
}

# 检查Python依赖
check_dependencies() {
    print_status "检查Python依赖..."
    
    # 检查Python版本
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        return 1
    fi
    
    # 检查pip依赖
    if ! python3 -c "import flask" &> /dev/null; then
        print_warning "Flask依赖缺失，正在安装..."
        pip3 install -r requirements.txt
    fi
    
    # 检查其他关键依赖
    local deps=("flask_cors" "pymysql" "requests" "PIL")
    for dep in "${deps[@]}"; do
        if ! python3 -c "import $dep" &> /dev/null; then
            print_warning "$dep 依赖缺失，正在安装..."
            pip3 install -r requirements.txt
            break
        fi
    done
    
    print_success "依赖检查完成"
}

# 创建日志目录和轮转配置
setup_logging() {
    print_status "配置日志系统..."
    
    # 创建日志目录
    mkdir -p "$LOGS_DIR"
    
    # 创建日志轮转配置
    cat > "$LOGS_DIR/logrotate.conf" << EOF
$LOGS_DIR/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    postrotate
        # 重启服务以刷新日志句柄
        systemctl restart nanyi-backend nanyi-frontend 2>/dev/null || true
    endscript
}
EOF
    
    # 设置定时日志轮转
    if [ -f /etc/crontab ]; then
        if ! grep -q "nanyi-logrotate" /etc/crontab; then
            echo "0 0 * * * root logrotate -f $LOGS_DIR/logrotate.conf" >> /etc/crontab
            print_success "日志轮转已配置"
        fi
    fi
    
    print_success "日志系统配置完成"
}

# 健康检查
health_check() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    print_status "检查 $service 服务健康状态..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
            print_success "$service 服务健康检查通过"
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "$service 服务健康检查失败"
            return 1
        fi
        
        print_status "等待 $service 服务启动... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
}

# 启动后端服务
start_backend() {
    print_status "启动后端API服务..."
    
    # 检查端口
    if ! check_port $BACKEND_PORT "后端API"; then
        return 1
    fi
    
    # 切换到后端目录
    cd "$BACKEND_DIR"
    
    # 启动后端服务
    nohup python3 app.py > "$LOGS_DIR/backend.log" 2>&1 &
    local backend_pid=$!
    echo $backend_pid > "$PROJECT_DIR/backend.pid"
    
    # 等待服务启动
    sleep 5
    
    # 检查进程是否还在运行
    if ! kill -0 $backend_pid 2>/dev/null; then
        print_error "后端服务启动失败"
        cat "$LOGS_DIR/backend.log" | tail -20
        return 1
    fi
    
    # 健康检查
    if ! health_check "后端API" $BACKEND_PORT; then
        return 1
    fi
    
    print_success "后端API服务启动成功 (PID: $backend_pid)"
    return 0
}

# 启动前端服务
start_frontend() {
    print_status "启动前端Web服务..."
    
    # 检查端口
    if ! check_port $FRONTEND_PORT "前端Web"; then
        return 1
    fi
    
    # 切换到前端目录
    cd "$FRONTEND_DIR"
    
    # 启动前端服务
    nohup python3 server.py > "$LOGS_DIR/frontend.log" 2>&1 &
    local frontend_pid=$!
    echo $frontend_pid > "$PROJECT_DIR/frontend.pid"
    
    # 等待服务启动
    sleep 3
    
    # 检查进程是否还在运行
    if ! kill -0 $frontend_pid 2>/dev/null; then
        print_error "前端服务启动失败"
        cat "$LOGS_DIR/frontend.log" | tail -20
        return 1
    fi
    
    # 检查端口是否监听
    local attempt=1
    while [ $attempt -le 10 ]; do
        if netstat -tlnp 2>/dev/null | grep -q ":$FRONTEND_PORT "; then
            print_success "前端Web服务启动成功 (PID: $frontend_pid)"
            return 0
        fi
        sleep 1
        ((attempt++))
    done
    
    print_error "前端服务启动超时"
    return 1
}

# 显示服务状态
show_status() {
    echo ""
    echo "========================================"
    echo "          南意秋棠服务状态"
    echo "========================================"
    
    # 后端服务状态
    echo -e "\n📡 后端API服务:"
    if [ -f "$PROJECT_DIR/backend.pid" ]; then
        local backend_pid=$(cat "$PROJECT_DIR/backend.pid")
        if kill -0 $backend_pid 2>/dev/null; then
            print_success "运行中 (PID: $backend_pid)"
            echo "   端口: $BACKEND_PORT"
            echo "   访问: http://localhost:$BACKEND_PORT"
            echo "   健康: http://localhost:$BACKEND_PORT/health"
        else
            print_error "已停止"
        fi
    else
        print_error "未启动"
    fi
    
    # 前端服务状态
    echo -e "\n🎨 前端Web服务:"
    if [ -f "$PROJECT_DIR/frontend.pid" ]; then
        local frontend_pid=$(cat "$PROJECT_DIR/frontend.pid")
        if kill -0 $frontend_pid 2>/dev/null; then
            print_success "运行中 (PID: $frontend_pid)"
            echo "   端口: $FRONTEND_PORT"
            echo "   访问: http://localhost:$FRONTEND_PORT"
            echo "   域名: http://chenxiaoshivivid.com.cn:$FRONTEND_PORT"
        else
            print_error "已停止"
        fi
    else
        print_error "未启动"
    fi
    
    echo ""
    echo "📝 日志文件:"
    echo "   后端: $LOGS_DIR/backend.log"
    echo "   前端: $LOGS_DIR/frontend.log"
    echo "   访问: $LOGS_DIR/access.log"
    echo "   错误: $LOGS_DIR/error.log"
    echo ""
    echo "📊 实时日志:"
    echo "   tail -f $LOGS_DIR/backend.log"
    echo "   tail -f $LOGS_DIR/frontend.log"
    echo "   tail -f $LOGS_DIR/access.log"
    echo "========================================"
}

# 主函数
main() {
    echo "🚀 启动南意秋棠服务..."
    echo ""
    
    # 检查依赖
    if ! check_dependencies; then
        print_error "依赖检查失败"
        exit 1
    fi
    
    # 设置日志
    setup_logging
    
    # 启动后端服务
    if ! start_backend; then
        print_error "后端服务启动失败"
        exit 1
    fi
    
    # 启动前端服务
    if ! start_frontend; then
        print_error "前端服务启动失败"
        exit 1
    fi
    
    # 显示状态
    show_status
    
    echo ""
    print_success "🎉 南意秋棠服务启动完成！"
    echo ""
    echo "💡 提示:"
    echo "   - 使用 './stop_services.sh' 停止服务"
    echo "   - 使用 'sudo ./service-manager.sh install' 安装系统服务"
    echo "   - 查看日志: tail -f logs/*.log"
}

# 执行主函数
main "$@" 
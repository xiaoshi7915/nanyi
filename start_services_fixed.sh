#!/bin/bash
# 南意秋棠 - 服务启动脚本（修复版）

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

# 环境变量设置
export DOMAIN=chenxiaoshivivid.com.cn
export BACKEND_URL=http://chenxiaoshivivid.com.cn:5001
export FRONTEND_PORT=8500
export BACKEND_PORT=5001
export HOST=0.0.0.0
export CORS_ORIGINS="http://localhost:8500,http://121.36.205.70:8500,http://chenxiaoshivivid.com.cn:8500"

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
        if [ ! -z "$pid" ] && [ "$pid" != "-" ]; then
            print_status "尝试停止占用端口的进程 PID: $pid"
            kill -TERM "$pid" 2>/dev/null || true
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                print_warning "进程未正常停止，强制杀死"
                kill -KILL "$pid" 2>/dev/null || true
            fi
        fi
    fi
}

# 检查依赖
check_dependencies() {
    print_status "检查Python依赖..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    
    # 检查必要的Python包
    python3 -c "import flask, flask_cors, flask_sqlalchemy" 2>/dev/null || {
        print_error "缺少必要的Python包，请运行: pip3 install -r requirements.txt"
        exit 1
    }
    
    print_success "依赖检查完成"
}

# 创建日志目录
setup_logs() {
    print_status "配置日志系统..."
    mkdir -p "$LOGS_DIR"
    
    # 配置日志轮转
    if ! grep -q "南意秋棠日志轮转" /etc/crontab 2>/dev/null; then
        echo "0 0 * * * root find $LOGS_DIR -name '*.log' -mtime +30 -delete # 南意秋棠日志轮转" >> /etc/crontab
        print_success "日志轮转已配置"
    fi
    
    print_success "日志系统配置完成"
}

# 启动后端服务
start_backend() {
    print_status "启动后端API服务..."
    
    check_port $BACKEND_PORT "后端API"
    
    cd "$BACKEND_DIR"
    
    # 测试配置
    if ! python3 -c "from app import create_app; create_app('development')" &>/dev/null; then
        print_error "后端服务配置测试失败"
        return 1
    fi
    
    # 启动服务
    nohup python3 app.py > "$LOGS_DIR/backend.log" 2>&1 &
    local backend_pid=$!
    echo $backend_pid > "$PROJECT_DIR/backend.pid"
    
    # 等待服务启动
    sleep 3
    
    # 健康检查
    if curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
        print_success "后端API服务启动成功 (PID: $backend_pid)"
        return 0
    else
        print_error "后端服务启动失败"
        return 1
    fi
}

# 启动前端服务
start_frontend() {
    print_status "启动前端Web服务..."
    
    check_port $FRONTEND_PORT "前端Web"
    
    cd "$FRONTEND_DIR"
    
    # 启动服务
    nohup python3 server.py > "$LOGS_DIR/frontend.log" 2>&1 &
    local frontend_pid=$!
    echo $frontend_pid > "$PROJECT_DIR/frontend.pid"
    
    # 等待服务启动
    sleep 2
    
    # 健康检查
    if curl -s http://localhost:$FRONTEND_PORT/health > /dev/null 2>&1; then
        print_success "前端Web服务启动成功 (PID: $frontend_pid)"
        return 0
    else
        print_error "前端服务启动失败"
        return 1
    fi
}

# 主函数
main() {
    echo -e "\n🚀 启动南意秋棠服务...\n"
    
    # 检查依赖
    check_dependencies
    
    # 配置日志
    setup_logs
    
    # 启动后端
    if start_backend; then
        print_success "后端服务启动完成"
    else
        print_error "后端服务启动失败"
        exit 1
    fi
    
    # 启动前端
    if start_frontend; then
        print_success "前端服务启动完成"
    else
        print_error "前端服务启动失败"
        exit 1
    fi
    
    # 显示服务状态
    echo -e "\n========================================="
    echo -e "          南意秋棠服务状态"
    echo -e "========================================="
    echo -e ""
    echo -e "📡 后端API服务:"
    echo -e "   本地访问: ${GREEN}http://localhost:$BACKEND_PORT${NC}"
    echo -e "   IP访问:   ${GREEN}http://121.36.205.70:$BACKEND_PORT${NC}"
    echo -e "   域名访问: ${GREEN}http://$DOMAIN:$BACKEND_PORT${NC}"
    echo -e ""
    echo -e "🎨 前端Web服务:"
    echo -e "   本地访问: ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "   IP访问:   ${GREEN}http://121.36.205.70:$FRONTEND_PORT${NC}"
    echo -e "   域名访问: ${GREEN}http://$DOMAIN:$FRONTEND_PORT${NC}"
    echo -e ""
    echo -e "📊 监控接口:"
    echo -e "   缓存统计: ${GREEN}http://$DOMAIN:$BACKEND_PORT/api/cache/stats${NC}"
    echo -e "   访问日志: ${GREEN}http://$DOMAIN:$BACKEND_PORT/api/logs/access/stats${NC}"
    echo -e ""
    echo -e "📁 日志文件:"
    echo -e "   后端日志: ${LOGS_DIR}/backend.log"
    echo -e "   前端日志: ${LOGS_DIR}/frontend.log"
    echo -e "   访问日志: ${LOGS_DIR}/access.log"
    echo -e "=========================================\n"
    
    print_success "🎉 南意秋棠服务启动完成！"
    print_status "使用 ./stop_services.sh 停止服务"
}

# 执行主函数
main "$@" 
#!/bin/bash
# 南意秋棠 - 系统服务管理脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务名称
BACKEND_SERVICE="nanyi-backend.service"
FRONTEND_SERVICE="nanyi-frontend.service"
PROJECT_DIR="/opt/hanfu/products"

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

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "请使用root权限运行此脚本"
        echo "使用: sudo $0 $1"
        exit 1
    fi
}

# 安装服务
install_services() {
    print_status "开始安装南意秋棠系统服务..."
    
    # 复制服务文件到systemd目录
    print_status "复制服务文件..."
    cp "${PROJECT_DIR}/nanyi-backend.service" /etc/systemd/system/
    cp "${PROJECT_DIR}/nanyi-frontend.service" /etc/systemd/system/
    
    # 重新加载systemd配置
    print_status "重新加载systemd配置..."
    systemctl daemon-reload
    
    # 启用服务开机自启
    print_status "启用服务开机自启..."
    systemctl enable $BACKEND_SERVICE
    systemctl enable $FRONTEND_SERVICE
    
    print_success "系统服务安装完成！"
    print_status "使用以下命令管理服务："
    echo "  启动: sudo $0 start"
    echo "  停止: sudo $0 stop"
    echo "  重启: sudo $0 restart"
    echo "  状态: sudo $0 status"
    echo "  卸载: sudo $0 uninstall"
}

# 卸载服务
uninstall_services() {
    print_status "开始卸载南意秋棠系统服务..."
    
    # 停止并禁用服务
    systemctl stop $BACKEND_SERVICE $FRONTEND_SERVICE 2>/dev/null || true
    systemctl disable $BACKEND_SERVICE $FRONTEND_SERVICE 2>/dev/null || true
    
    # 删除服务文件
    rm -f /etc/systemd/system/$BACKEND_SERVICE
    rm -f /etc/systemd/system/$FRONTEND_SERVICE
    
    # 重新加载systemd配置
    systemctl daemon-reload
    
    print_success "系统服务卸载完成！"
}

# 启动服务
start_services() {
    print_status "启动南意秋棠服务..."
    systemctl start $BACKEND_SERVICE
    systemctl start $FRONTEND_SERVICE
    print_success "服务启动完成！"
    
    # 等待服务启动并检查状态
    sleep 3
    show_status
}

# 停止服务
stop_services() {
    print_status "停止南意秋棠服务..."
    systemctl stop $FRONTEND_SERVICE
    systemctl stop $BACKEND_SERVICE
    print_success "服务停止完成！"
}

# 重启服务
restart_services() {
    print_status "重启南意秋棠服务..."
    systemctl restart $BACKEND_SERVICE
    systemctl restart $FRONTEND_SERVICE
    print_success "服务重启完成！"
    
    # 等待服务启动并检查状态
    sleep 3
    show_status
}

# 显示服务状态
show_status() {
    echo ""
    echo "========================================"
    echo "          南意秋棠服务状态"
    echo "========================================"
    
    # 后端服务状态
    echo -e "\n📡 后端API服务 ($BACKEND_SERVICE):"
    if systemctl is-active --quiet $BACKEND_SERVICE; then
        print_success "运行中"
        echo "   端口: 5001"
        echo "   访问: http://localhost:5001"
    else
        print_error "已停止"
    fi
    
    # 前端服务状态
    echo -e "\n🎨 前端Web服务 ($FRONTEND_SERVICE):"
    if systemctl is-active --quiet $FRONTEND_SERVICE; then
        print_success "运行中"
        echo "   端口: 8500"
        echo "   访问: http://localhost:8500"
    else
        print_error "已停止"
    fi
    
    # 开机自启状态
    echo -e "\n🔄 开机自启状态:"
    if systemctl is-enabled --quiet $BACKEND_SERVICE; then
        print_success "后端服务已启用"
    else
        print_warning "后端服务未启用"
    fi
    
    if systemctl is-enabled --quiet $FRONTEND_SERVICE; then
        print_success "前端服务已启用"
    else
        print_warning "前端服务未启用"
    fi
    
    echo ""
    echo "📝 查看日志:"
    echo "   后端: journalctl -u $BACKEND_SERVICE -f"
    echo "   前端: journalctl -u $FRONTEND_SERVICE -f"
    echo "========================================"
}

# 显示帮助信息
show_help() {
    echo "南意秋棠 - 系统服务管理脚本"
    echo ""
    echo "用法: $0 <命令>"
    echo ""
    echo "命令:"
    echo "  install    安装系统服务并启用开机自启"
    echo "  uninstall  卸载系统服务"
    echo "  start      启动服务"
    echo "  stop       停止服务"
    echo "  restart    重启服务"
    echo "  status     查看服务状态"
    echo "  help       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  sudo $0 install    # 安装并启用服务"
    echo "  sudo $0 start      # 启动服务"
    echo "  sudo $0 status     # 查看状态"
}

# 主函数
main() {
    case "${1:-help}" in
        install)
            check_root
            install_services
            ;;
        uninstall)
            check_root
            uninstall_services
            ;;
        start)
            check_root
            start_services
            ;;
        stop)
            check_root
            stop_services
            ;;
        restart)
            check_root
            restart_services
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@" 
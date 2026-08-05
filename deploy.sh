#!/bin/bash
# 南意秋棠汉服展示网站部署脚本
# 版本: 2.0
# 作者: 南意秋棠团队
# 日期: 2025-06-23

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_NAME="南意秋棠汉服展示网站"
PROJECT_DIR="/opt/hanfu/products"
VENV_NAME="products_env"
BACKEND_PORT=5432
FRONTEND_PORT=8500

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查Python版本
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装，请先安装 Python 3.8+"
        exit 1
    fi
    
    local python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    log_info "Python版本: $python_version"
    
    # 检查pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 未安装，请先安装 pip"
        exit 1
    fi
    
    # 检查MySQL客户端（可选）
    if command -v mysql &> /dev/null; then
        log_info "MySQL客户端已安装"
    else
        log_warning "MySQL客户端未安装，数据库连接可能需要额外配置"
    fi
    
    log_success "系统要求检查完成"
}

# 创建虚拟环境
create_virtual_env() {
    log_info "设置Python虚拟环境..."
    
    cd $PROJECT_DIR
    
    if [ -d "$VENV_NAME" ]; then
        log_info "虚拟环境已存在，跳过创建"
    else
        log_info "创建虚拟环境: $VENV_NAME"
        python3 -m venv $VENV_NAME
        log_success "虚拟环境创建完成"
    fi
    
    # 激活虚拟环境
    source $VENV_NAME/bin/activate
    
    # 升级pip
    log_info "升级pip到最新版本..."
    pip install --upgrade pip
    
    log_success "虚拟环境设置完成"
}

# 安装Python依赖
install_dependencies() {
    log_info "安装Python依赖包..."
    
    cd $PROJECT_DIR
    source $VENV_NAME/bin/activate
    
    # 安装核心依赖
    if [ -f "requirements.txt" ]; then
        log_info "从 requirements.txt 安装依赖..."
        pip install -r requirements.txt
    elif [ -f "requirements-current.txt" ]; then
        log_info "从 requirements-current.txt 安装依赖..."
        pip install -r requirements-current.txt
    else
        log_error "未找到依赖文件 requirements.txt 或 requirements-current.txt"
        exit 1
    fi
    
    log_success "Python依赖安装完成"
}

# 配置环境变量
setup_environment() {
    log_info "配置环境变量..."
    
    cd $PROJECT_DIR
    
    # 创建.env文件（如果不存在）
    if [ ! -f ".env" ]; then
        log_info "创建环境配置文件..."
        cat > .env << EOF
# 南意秋棠环境配置
FLASK_ENV=development
DEBUG=True
BACKEND_PORT=$BACKEND_PORT
FRONTEND_PORT=$FRONTEND_PORT
HOST=0.0.0.0

# 数据库配置
DB_HOST=47.118.250.53
DB_PORT=3306
DB_NAME=nanyiqiutang
DB_USER=nanyiqiutang
DB_PASSWORD=your_password_here

# 安全配置
SECRET_KEY=your_secret_key_here
EOF
        log_warning "请编辑 .env 文件，填入正确的数据库密码和安全密钥"
    else
        log_info "环境配置文件已存在"
    fi
    
    log_success "环境配置完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    cd $PROJECT_DIR
    source $VENV_NAME/bin/activate
    
    # 测试数据库连接
    log_info "测试数据库连接..."
    cd backend
    python -c "
import sys
sys.path.append('..')
from app import create_app
from models import db

app = create_app()
with app.app_context():
    try:
        db.engine.connect()
        print('✅ 数据库连接成功')
        db.create_all()
        print('✅ 数据表创建成功')
    except Exception as e:
        print(f'❌ 数据库初始化失败: {e}')
        sys.exit(1)
"
    cd ..
    
    log_success "数据库初始化完成"
}

# 配置Nginx（可选）
setup_nginx() {
    log_info "配置Nginx反向代理..."
    
    if command -v nginx &> /dev/null; then
        log_info "Nginx已安装"
        
        # 检查配置文件
        if [ -f "nginx/products-sites.conf" ]; then
            log_info "Nginx配置文件已存在"
            
            # 可选：复制配置到nginx sites-available
            if [ -d "/etc/nginx/sites-available" ]; then
                log_info "可以运行以下命令配置Nginx:"
                echo "sudo cp nginx/products-sites.conf /etc/nginx/sites-available/"
                echo "sudo ln -sf /etc/nginx/sites-available/products-sites.conf /etc/nginx/sites-enabled/"
                echo "sudo nginx -t && sudo systemctl reload nginx"
            fi
        else
            log_warning "Nginx配置文件不存在，跳过配置"
        fi
    else
        log_warning "Nginx未安装，跳过配置"
    fi
    
    log_success "Nginx配置检查完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    cd $PROJECT_DIR
    
    # 生产以 systemd 为准；本地可用 start_services.sh
    if systemctl list-unit-files nanyi-backend.service &>/dev/null; then
        systemctl restart nanyi-backend nanyi-frontend
        log_success "已通过 systemd 重启 nanyi-backend / nanyi-frontend"
    elif [ -f "start_services.sh" ]; then
        chmod +x start_services.sh
        ./start_services.sh
        log_success "服务启动完成（start_services.sh）"
    else
        log_error "未找到 systemd 单元或 start_services.sh，请手动: systemctl restart nanyi-backend nanyi-frontend"
        exit 1
    fi
}

# 验证部署
verify_deployment() {
    log_info "验证部署..."
    
    # 等待服务启动
    sleep 3
    
    # 检查后端服务
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:$BACKEND_PORT/health | grep -q "200"; then
        log_success "后端服务正常运行 (端口: $BACKEND_PORT)"
    else
        log_error "后端服务启动失败"
        exit 1
    fi
    
    # 检查前端服务
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:$FRONTEND_PORT | grep -q "200"; then
        log_success "前端服务正常运行 (端口: $FRONTEND_PORT)"
    else
        log_error "前端服务启动失败"
        exit 1
    fi
    
    log_success "部署验证完成"
}

# 显示部署信息
show_deployment_info() {
    log_success "🎉 $PROJECT_NAME 部署完成！"
    echo ""
    echo "访问地址:"
    echo "  前端页面: http://localhost:$FRONTEND_PORT"
    echo "  后端API:  http://localhost:$BACKEND_PORT"
    echo "  健康检查: http://localhost:$BACKEND_PORT/health"
    echo ""
    echo "服务管理（systemd，无 manage.sh）:"
    echo "  重启: systemctl restart nanyi-backend nanyi-frontend"
    echo "  状态: systemctl status nanyi-backend nanyi-frontend"
    echo "  部署: ./deploy.sh"
    echo ""
    echo "日志查看:"
    echo "  sudo journalctl -u nanyi-backend.service -f"
    echo "  sudo journalctl -u nanyi-frontend.service -f"
    echo "  tail -f logs/backend.log logs/frontend.log"
    echo ""
    echo "发版三步:"
    echo "  1. bump APP_RELEASE_VERSION（scripts/bump-release-version.sh 或改 frontend/js/app-version.js）"
    echo "  2. systemctl restart nanyi-backend nanyi-frontend && nginx -s reload"
    echo "  3. 可选清缓存: curl -X POST -H \"X-Admin-Token: \$ADMIN_API_TOKEN\" http://127.0.0.1:5432/api/cache/clear"
    echo ""
    log_info "部署完成！请检查上述访问地址确认服务正常运行。"
}

# 主函数
main() {
    echo "========================================"
    echo "  $PROJECT_NAME"
    echo "  自动部署脚本 v2.0"
    echo "========================================"
    echo ""
    
    check_requirements
    create_virtual_env
    install_dependencies
    setup_environment
    init_database
    setup_nginx
    start_services
    verify_deployment
    show_deployment_info
}

# 脚本参数处理
case "${1:-deploy}" in
    deploy)
        main
        ;;
    install)
        check_requirements
        create_virtual_env
        install_dependencies
        setup_environment
        ;;
    start)
        start_services
        ;;
    verify)
        verify_deployment
        ;;
    help|--help|-h)
        echo "用法: $0 [命令]"
        echo ""
        echo "命令:"
        echo "  deploy    完整部署 (默认)"
        echo "  install   仅安装依赖和配置"
        echo "  start     仅启动服务"
        echo "  verify    验证部署状态"
        echo "  help      显示帮助信息"
        ;;
    *)
        log_error "未知命令: $1"
        echo "使用 '$0 help' 查看可用命令"
        exit 1
        ;;
esac 
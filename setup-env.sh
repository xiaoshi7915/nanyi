#!/bin/bash
# 南意秋棠虚拟环境快速设置脚本
# 版本: 1.1
# 用途: 快速创建或恢复 Python 虚拟环境（pip 损坏时自动重建）

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# 配置（优先使用 Python 3.12，与后端服务一致）
VENV_NAME="products_env"
PYTHON_VERSION="3.12"
FORCE_RECREATE=0

# 解析参数：./setup-env.sh --force 强制重建虚拟环境
for arg in "$@"; do
    case "$arg" in
        --force|-f)
            FORCE_RECREATE=1
            ;;
        --help|-h)
            echo "用法: $0 [--force]"
            echo "  --force  删除现有虚拟环境并重新创建"
            exit 0
            ;;
    esac
done

# 检查虚拟环境 / pip 是否可用
venv_is_healthy() {
    [ -x "$VENV_NAME/bin/python" ] && [ -x "$VENV_NAME/bin/pip" ] || return 1
    "$VENV_NAME/bin/python" -m pip --version &>/dev/null || return 1
    "$VENV_NAME/bin/pip" list &>/dev/null || return 1
    return 0
}

# 创建全新虚拟环境
create_venv() {
    echo "🔨 创建虚拟环境: $VENV_NAME"
    $PYTHON_CMD -m venv "$VENV_NAME"
}

# 删除并重建虚拟环境
recreate_venv() {
    echo -e "${YELLOW}⚠️  虚拟环境异常，正在重建: $VENV_NAME${NC}"
    rm -rf "$VENV_NAME"
    create_venv
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  南意秋棠虚拟环境设置脚本${NC}"
echo -e "${BLUE}========================================${NC}"

# 检查 Python 版本（优先 3.12）
echo -e "${BLUE}[1/5]${NC} 检查 Python 环境..."
PYTHON_CMD=""
command -v python3.12 &> /dev/null && PYTHON_CMD="python3.12" || true
[ -z "$PYTHON_CMD" ] && command -v python3 &> /dev/null && PYTHON_CMD="python3" || true
if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}❌ Python3 未安装（建议安装 Python 3.12）${NC}"
    exit 1
fi

python_version=$($PYTHON_CMD -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
echo "✅ Python 版本: $python_version (使用: $PYTHON_CMD)"

# 创建或校验虚拟环境
echo -e "${BLUE}[2/5]${NC} 设置虚拟环境..."
if [ "$FORCE_RECREATE" -eq 1 ]; then
    echo "🔄 已指定 --force，强制重建虚拟环境"
    recreate_venv
elif [ -d "$VENV_NAME" ]; then
    if venv_is_healthy; then
        echo "📁 虚拟环境正常: $VENV_NAME"
    else
        recreate_venv
    fi
else
    create_venv
fi

# 激活虚拟环境
echo -e "${BLUE}[3/5]${NC} 激活虚拟环境..."
# shellcheck disable=SC1091
source "$VENV_NAME/bin/activate"
echo "✅ 虚拟环境已激活"

# 升级 pip / setuptools / wheel
echo -e "${BLUE}[4/5]${NC} 升级 pip 工具链..."
if ! python -m pip install --upgrade pip setuptools wheel; then
    echo -e "${YELLOW}⚠️  pip 升级失败，尝试重建虚拟环境后重试...${NC}"
    deactivate 2>/dev/null || true
    recreate_venv
    # shellcheck disable=SC1091
    source "$VENV_NAME/bin/activate"
    python -m pip install --upgrade pip setuptools wheel
fi

# 安装项目依赖
echo -e "${BLUE}[5/5]${NC} 安装 Python 包..."
if [ -f "requirements.txt" ]; then
    echo "📦 从 requirements.txt 安装依赖..."
    pip install -r requirements.txt
elif [ -f "requirements-current.txt" ]; then
    echo "📦 从 requirements-current.txt 安装依赖..."
    pip install -r requirements-current.txt
else
    echo "⚠️  未找到依赖文件，手动安装核心包..."
    pip install flask flask-cors flask-sqlalchemy pymysql python-dotenv pillow requests gunicorn
fi

echo ""
echo -e "${GREEN}🎉 虚拟环境设置完成！${NC}"
echo ""
echo "使用方法："
echo "  激活环境: source $VENV_NAME/bin/activate"
echo "  退出环境: deactivate"
echo "  强制重建: ./setup-env.sh --force"
echo ""
echo "已安装的包："
pip list --format=columns
echo ""
echo -e "${YELLOW}注意：请确保 .env 文件中的数据库配置正确${NC}"
echo -e "${YELLOW}生产环境更新依赖后建议执行:${NC}"
echo "  systemctl restart nanyi-backend.service nanyi-frontend.service"

#!/bin/bash
# 南意秋棠虚拟环境快速设置脚本
# 版本: 1.0
# 用途: 快速创建或恢复Python虚拟环境

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置（优先使用 Python 3.12，与后端服务一致）
VENV_NAME="products_env"
PYTHON_VERSION="3.12"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  南意秋棠虚拟环境设置脚本${NC}"
echo -e "${BLUE}========================================${NC}"

# 检查Python版本（优先 3.12）
echo -e "${BLUE}[1/4]${NC} 检查Python环境..."
PYTHON_CMD=""
command -v python3.12 &> /dev/null && PYTHON_CMD="python3.12" || true
[ -z "$PYTHON_CMD" ] && command -v python3 &> /dev/null && PYTHON_CMD="python3" || true
if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python3 未安装（建议安装 Python 3.12）"
    exit 1
fi

python_version=$($PYTHON_CMD -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
echo "✅ Python版本: $python_version (使用: $PYTHON_CMD)"

# 创建虚拟环境
echo -e "${BLUE}[2/4]${NC} 设置虚拟环境..."
if [ -d "$VENV_NAME" ]; then
    echo "📁 虚拟环境已存在: $VENV_NAME"
else
    echo "🔨 创建虚拟环境: $VENV_NAME"
    $PYTHON_CMD -m venv $VENV_NAME
fi

# 激活虚拟环境
echo -e "${BLUE}[3/4]${NC} 激活虚拟环境..."
source $VENV_NAME/bin/activate
echo "✅ 虚拟环境已激活"

# 升级pip并安装依赖
echo -e "${BLUE}[4/4]${NC} 安装Python包..."
pip install --upgrade pip

# 选择依赖文件
if [ -f "requirements.txt" ]; then
    echo "📦 从 requirements.txt 安装依赖..."
    pip install -r requirements.txt
elif [ -f "requirements-current.txt" ]; then
    echo "📦 从 requirements-current.txt 安装依赖..."
    pip install -r requirements-current.txt
else
    echo "⚠️  未找到依赖文件，手动安装核心包..."
    pip install flask flask-cors flask-sqlalchemy pymysql python-dotenv pillow requests
fi

echo ""
echo -e "${GREEN}🎉 虚拟环境设置完成！${NC}"
echo ""
echo "使用方法："
echo "  激活环境: source $VENV_NAME/bin/activate"
echo "  退出环境: deactivate"
echo ""
echo "已安装的包："
pip list --format=columns
echo ""
echo -e "${YELLOW}注意：请确保 .env 文件中的数据库配置正确${NC}" 
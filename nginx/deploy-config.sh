#!/bin/bash

# Nginx配置部署脚本
# 用于部署产品站点配置

set -e

echo "🚀 开始部署Nginx配置..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}项目目录: $PROJECT_DIR${NC}"

# 1. 检查nginx是否安装
if ! command -v nginx &> /dev/null; then
    echo -e "${RED}❌ Nginx未安装，请先安装nginx${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Nginx已检测到${NC}"

# 2. 测试配置文件语法
echo "🔍 测试配置文件语法..."
if nginx -t -c "$SCRIPT_DIR/products-sites.conf" 2>/dev/null; then
    echo -e "${GREEN}✅ 配置文件语法正确${NC}"
else
    echo -e "${YELLOW}⚠️ 单独测试失败，将在主配置中测试${NC}"
fi

# 3. 备份现有配置
BACKUP_DIR="/etc/nginx/backup/$(date +%Y%m%d_%H%M%S)"
echo "📦 创建配置备份: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

if [ -f "/etc/nginx/conf.d/products-sites.conf" ]; then
    cp "/etc/nginx/conf.d/products-sites.conf" "$BACKUP_DIR/products-sites.conf.old"
    echo -e "${GREEN}✅ 已备份现有配置${NC}"
fi

# 4. 复制新配置
echo "📄 部署新配置..."
cp "$SCRIPT_DIR/products-sites.conf" "/etc/nginx/conf.d/products-sites.conf"
echo -e "${GREEN}✅ 配置文件已复制到 /etc/nginx/conf.d/${NC}"

# 5. 测试完整nginx配置
echo "🧪 测试完整nginx配置..."
if nginx -t; then
    echo -e "${GREEN}✅ Nginx配置测试通过${NC}"
else
    echo -e "${RED}❌ Nginx配置测试失败，恢复备份...${NC}"
    if [ -f "$BACKUP_DIR/products-sites.conf.old" ]; then
        cp "$BACKUP_DIR/products-sites.conf.old" "/etc/nginx/conf.d/products-sites.conf"
        echo -e "${YELLOW}⚠️ 已恢复原配置${NC}"
    else
        rm -f "/etc/nginx/conf.d/products-sites.conf"
        echo -e "${YELLOW}⚠️ 已删除错误配置${NC}"
    fi
    exit 1
fi

# 6. 重新加载nginx配置
echo "🔄 重新加载Nginx配置..."
if systemctl reload nginx; then
    echo -e "${GREEN}✅ Nginx配置重新加载成功${NC}"
else
    echo -e "${RED}❌ Nginx重新加载失败${NC}"
    exit 1
fi

# 7. 检查nginx状态
echo "📊 检查nginx服务状态..."
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx服务运行正常${NC}"
else
    echo -e "${RED}❌ Nginx服务状态异常${NC}"
    systemctl status nginx
    exit 1
fi

# 8. 验证端口监听
echo "🔌 检查端口监听状态..."
if netstat -tlnp | grep -q ":80.*nginx"; then
    echo -e "${GREEN}✅ Nginx正在监听80端口${NC}"
else
    echo -e "${YELLOW}⚠️ 80端口监听状态异常${NC}"
fi

# 9. 测试upstream连接
echo "🌐 测试upstream服务连接..."

# 测试前端服务
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8500 | grep -q "200"; then
    echo -e "${GREEN}✅ 前端服务(8500)连接正常${NC}"
else
    echo -e "${YELLOW}⚠️ 前端服务(8500)连接异常，请检查服务状态${NC}"
fi

# 测试后端服务
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5432 | grep -q "200"; then
    echo -e "${GREEN}✅ 后端服务(5432)连接正常${NC}"
else
    echo -e "${YELLOW}⚠️ 后端服务(5432)连接异常，请检查服务状态${NC}"
fi

# 10. 显示配置摘要
echo ""
echo "🎉 配置部署完成！"
echo ""
echo "📋 配置摘要:"
echo "  - products.nanyiqiutang.cn -> 127.0.0.1:8500"
echo "  - products.chenxiaoshivivid.com.cn -> 127.0.0.1:8500" 
echo "  - API路由: /api/* -> 127.0.0.1:5432"
echo "  - 裸域名重定向: nanyiqiutang.cn -> products.nanyiqiutang.cn"
echo "  - 裸域名重定向: chenxiaoshivivid.com.cn -> products.chenxiaoshivivid.com.cn"
echo ""
echo "🌐 测试地址:"
echo "  - http://products.nanyiqiutang.cn"
echo "  - http://products.chenxiaoshivivd.com.cn"
echo ""
echo "📊 查看日志:"
echo "  - access: tail -f /var/log/nginx/products.*.access.log"
echo "  - error:  tail -f /var/log/nginx/products.*.error.log"
echo ""
echo "🔧 管理命令:"
echo "  - 重新加载: systemctl reload nginx"
echo "  - 重启服务: systemctl restart nginx"
echo "  - 测试配置: nginx -t"
echo ""
echo -e "${GREEN}✨ 现在可以通过域名访问您的网站了！${NC}" 
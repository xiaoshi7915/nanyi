#!/bin/bash
# 南意秋棠 - 服务安装脚本

echo "🚀 安装南意秋棠系统服务..."

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用root权限运行此脚本"
    echo "使用: sudo $0"
    exit 1
fi

# 项目目录
PROJECT_DIR="/opt/hanfu/products"

# 复制服务文件到systemd目录
echo "📋 复制服务文件..."
cp "${PROJECT_DIR}/nanyi-backend.service" /etc/systemd/system/
cp "${PROJECT_DIR}/nanyi-frontend.service" /etc/systemd/system/

# 重新加载systemd配置
echo "🔄 重新加载systemd配置..."
systemctl daemon-reload

# 启用服务开机自启
echo "⚡ 启用服务开机自启..."
systemctl enable nanyi-backend.service
systemctl enable nanyi-frontend.service

# 启动服务
echo "🚀 启动服务..."
systemctl start nanyi-backend.service
systemctl start nanyi-frontend.service

echo "✅ 系统服务安装完成！"
echo ""
echo "📊 服务状态:"
systemctl status nanyi-backend.service --no-pager -l
echo ""
systemctl status nanyi-frontend.service --no-pager -l
echo ""
echo "🔧 管理命令:"
echo "  启动: sudo systemctl start nanyi-backend nanyi-frontend"
echo "  停止: sudo systemctl stop nanyi-backend nanyi-frontend"
echo "  重启: sudo systemctl restart nanyi-backend nanyi-frontend"
echo "  状态: systemctl status nanyi-backend nanyi-frontend"
echo "  日志: journalctl -u nanyi-backend -f"
echo "       journalctl -u nanyi-frontend -f" 
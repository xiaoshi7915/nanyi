#!/bin/bash

# Nginx安装和配置脚本
# 适用于CentOS/RHEL系统

echo "🚀 开始安装和配置Nginx..."

# 1. 安装nginx
echo "📦 安装Nginx..."
yum install -y epel-release
yum install -y nginx

# 2. 检查安装结果
if ! command -v nginx &> /dev/null; then
    echo "❌ Nginx安装失败"
    exit 1
fi

echo "✅ Nginx安装成功"
nginx -v

# 3. 创建配置目录
mkdir -p /etc/nginx/conf.d

# 4. 备份原配置
if [ -f "/etc/nginx/nginx.conf" ]; then
    cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ 原配置已备份"
fi

# 5. 启动并设置开机自启
systemctl enable nginx
systemctl start nginx

# 6. 检查服务状态
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx服务启动成功"
else
    echo "❌ Nginx服务启动失败"
    systemctl status nginx
    exit 1
fi

# 7. 检查端口占用
echo "📋 检查端口状态:"
netstat -tlnp | grep :80 || echo "⚠️ 端口80未监听，需要检查配置"

echo "🎉 Nginx安装完成！"
echo "📝 下一步请运行配置脚本：./nginx/configure-domains.sh" 
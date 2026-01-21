#!/bin/bash

# 安装nginx
apt-get update
apt-get install -y nginx

# 创建必要的目录
mkdir -p /var/log/nginx

# 复制nginx配置文件
cp products-sites-new.conf /etc/nginx/conf.d/

# 测试nginx配置
nginx -t

# 如果配置测试成功，重启nginx
if [ $? -eq 0 ]; then
    systemctl restart nginx
    systemctl enable nginx
    echo "Nginx配置成功并已启动"
else
    echo "Nginx配置测试失败，请检查配置文件"
    exit 1
fi

# 检查nginx状态
systemctl status nginx 
#!/bin/bash

# 简单的nginx部署脚本
echo "部署nginx配置..."

# 1. 安装nginx（如果未安装）
if ! command -v nginx &> /dev/null; then
    echo "安装nginx..."
    yum install -y nginx
fi

# 2. 创建配置目录
mkdir -p /etc/nginx/conf.d

# 3. 复制配置文件
echo "复制配置文件..."
cp nginx/products-sites.conf /etc/nginx/conf.d/

# 4. 测试nginx配置
echo "测试nginx配置..."
nginx -t

if [ $? -eq 0 ]; then
    # 5. 启动并重载nginx
    echo "启动nginx..."
    systemctl enable nginx
    systemctl start nginx
    systemctl reload nginx
    
    # 6. 开放80端口
    echo "配置防火墙..."
    firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || echo "防火墙配置跳过"
    firewall-cmd --reload 2>/dev/null || echo "防火墙重载跳过"
    
    echo "✅ nginx配置部署成功！"
    echo ""
    echo "现在可以访问："
    echo "- http://products.nanyiqiutang.cn"
    echo "- http://products.chenxiaoshivivid.com.cn"
    echo "- http://121.36.205.70:8500 (直接访问)"
else
    echo "❌ nginx配置测试失败！"
    exit 1
fi 
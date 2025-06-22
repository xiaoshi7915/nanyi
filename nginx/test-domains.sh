#!/bin/bash

# 域名访问测试脚本

echo "🧪 开始测试域名访问..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试域名列表
DOMAINS=(
    "products.nanyiqiutang.cn"
    "products.chenxiaoshivivid.com.cn"
    "nanyiqiutang.cn"
    "chenxiaoshivivid.com.cn"
)

# 测试函数
test_domain() {
    local domain=$1
    local protocol=${2:-http}
    
    echo -e "${BLUE}🔍 测试 $protocol://$domain${NC}"
    
    # DNS解析测试
    if nslookup $domain > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ DNS解析正常${NC}"
    else
        echo -e "  ${RED}❌ DNS解析失败${NC}"
        return 1
    fi
    
    # HTTP连接测试
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 $protocol://$domain 2>/dev/null)
    
    case $response in
        200)
            echo -e "  ${GREEN}✅ HTTP响应正常 (200)${NC}"
            ;;
        301|302)
            redirect_url=$(curl -s -I --connect-timeout 10 $protocol://$domain | grep -i location | cut -d' ' -f2 | tr -d '\r')
            echo -e "  ${YELLOW}🔄 重定向 ($response) -> $redirect_url${NC}"
            ;;
        000)
            echo -e "  ${RED}❌ 连接超时或无法连接${NC}"
            ;;
        *)
            echo -e "  ${YELLOW}⚠️ HTTP响应异常 ($response)${NC}"
            ;;
    esac
    
    # 简单内容测试
    if [ "$response" = "200" ]; then
        if curl -s --connect-timeout 5 $protocol://$domain | grep -q "南意秋棠" 2>/dev/null; then
            echo -e "  ${GREEN}✅ 页面内容正常${NC}"
        else
            echo -e "  ${YELLOW}⚠️ 页面内容异常${NC}"
        fi
    fi
    
    echo ""
}

# 本地服务测试
echo -e "${YELLOW}📋 本地服务状态检查${NC}"
echo "前端服务(8500): $(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8500 2>/dev/null || echo "无法连接")"
echo "后端服务(5001): $(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5001 2>/dev/null || echo "无法连接")"
echo ""

# 测试所有域名
for domain in "${DOMAINS[@]}"; do
    test_domain $domain
done

# API测试
echo -e "${YELLOW}🔧 API接口测试${NC}"
for domain in "products.nanyiqiutang.cn" "products.chenxiaoshivivid.com.cn"; do
    echo -e "${BLUE}测试 $domain API${NC}"
    
    # 测试API健康检查
    api_response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://$domain/api/images 2>/dev/null)
    if [ "$api_response" = "200" ]; then
        echo -e "  ${GREEN}✅ API接口正常${NC}"
    else
        echo -e "  ${RED}❌ API接口异常 ($api_response)${NC}"
    fi
    
    # 测试CORS
    cors_response=$(curl -s -H "Origin: http://example.com" -I --connect-timeout 5 http://$domain/api/images 2>/dev/null | grep -i "access-control-allow-origin")
    if [ -n "$cors_response" ]; then
        echo -e "  ${GREEN}✅ CORS配置正常${NC}"
    else
        echo -e "  ${YELLOW}⚠️ CORS配置可能异常${NC}"
    fi
    
    echo ""
done

# Nginx状态检查
echo -e "${YELLOW}🖥️ Nginx服务状态${NC}"
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx服务运行正常${NC}"
    
    # 检查配置文件
    if nginx -t 2>/dev/null; then
        echo -e "${GREEN}✅ Nginx配置语法正确${NC}"
    else
        echo -e "${RED}❌ Nginx配置语法错误${NC}"
    fi
    
    # 检查监听端口
    if netstat -tlnp | grep -q ":80.*nginx"; then
        echo -e "${GREEN}✅ Nginx正在监听80端口${NC}"
    else
        echo -e "${YELLOW}⚠️ 80端口监听异常${NC}"
    fi
else
    echo -e "${RED}❌ Nginx服务未运行${NC}"
fi

echo ""
echo -e "${GREEN}🎉 测试完成！${NC}"
echo ""
echo "💡 提示:"
echo "  - 如果DNS解析失败，请检查域名配置"
echo "  - 如果连接超时，请检查防火墙设置"
echo "  - 如果HTTP响应异常，请检查nginx配置"
echo "  - 查看详细日志: tail -f /var/log/nginx/products.*.log" 
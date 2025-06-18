#!/bin/bash
# OSS访问测试脚本
# 用于诊断OSS权限和连接问题

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== OSS访问测试 ===${NC}"
echo ""

# 测试OSS基本连接
echo -e "${YELLOW}1. 测试OSS基本连接...${NC}"
OSS_BASE_URL="https://nanyiqiutang.oss-cn-hangzhou.aliyuncs.com"
curl -I "$OSS_BASE_URL" 2>/dev/null | head -3
echo ""

# 测试图片访问
echo -e "${YELLOW}2. 测试图片访问...${NC}"
TEST_IMAGE_URL="$OSS_BASE_URL/images/buliaotu/江南春/江南春-布料图-06.jpg"
echo "测试URL: $TEST_IMAGE_URL"
RESPONSE=$(curl -I "$TEST_IMAGE_URL" 2>/dev/null | head -1)
echo "响应: $RESPONSE"

if echo "$RESPONSE" | grep -q "200 OK"; then
    echo -e "${GREEN}✅ 图片访问成功${NC}"
elif echo "$RESPONSE" | grep -q "403 Forbidden"; then
    echo -e "${RED}❌ 图片访问被禁止 (403 Forbidden)${NC}"
    echo -e "${YELLOW}💡 可能的解决方案:${NC}"
    echo "1. 检查OSS存储桶的读权限设置"
    echo "2. 确认存储桶是否设置为公共读"
    echo "3. 检查防盗链设置"
    echo "4. 验证图片路径是否正确"
elif echo "$RESPONSE" | grep -q "404 Not Found"; then
    echo -e "${RED}❌ 图片不存在 (404 Not Found)${NC}"
else
    echo -e "${RED}❌ 未知错误${NC}"
fi
echo ""

# 测试缩略图访问
echo -e "${YELLOW}3. 测试缩略图处理...${NC}"
THUMBNAIL_URL="$TEST_IMAGE_URL?x-oss-process=image/resize,w_300,h_300,m_lfit/quality,q_80/format,webp"
echo "缩略图URL: $THUMBNAIL_URL"
THUMB_RESPONSE=$(curl -I "$THUMBNAIL_URL" 2>/dev/null | head -1)
echo "响应: $THUMB_RESPONSE"

if echo "$THUMB_RESPONSE" | grep -q "200 OK"; then
    echo -e "${GREEN}✅ 缩略图处理成功${NC}"
else
    echo -e "${RED}❌ 缩略图处理失败${NC}"
fi
echo ""

# 测试本地API
echo -e "${YELLOW}4. 测试本地API图片数据...${NC}"
API_RESPONSE=$(curl -s "http://121.36.205.70:5001/api/images?per_page=1" 2>/dev/null)
if echo "$API_RESPONSE" | grep -q "medium_url"; then
    echo -e "${GREEN}✅ API返回OSS图片URL${NC}"
    echo "示例URL:"
    echo "$API_RESPONSE" | grep -o '"medium_url":"[^"]*"' | head -1 | cut -d'"' -f4
elif echo "$API_RESPONSE" | grep -q "static/images"; then
    echo -e "${YELLOW}⚠️ API返回本地图片路径${NC}"
    echo "示例路径:"
    echo "$API_RESPONSE" | grep -o '"/static/images/[^"]*"' | head -1 | cut -d'"' -f2
else
    echo -e "${RED}❌ API响应异常${NC}"
fi
echo ""

# 显示建议
echo -e "${BLUE}=== 建议操作 ===${NC}"
echo "如果OSS访问被禁止，请检查以下设置："
echo ""
echo "1. 阿里云OSS控制台 > 存储桶 > nanyiqiutang > 权限管理"
echo "2. 确保存储桶ACL设置为 '公共读'"
echo "3. 检查防盗链设置，确保没有限制访问来源"
echo "4. 验证图片文件是否正确上传到OSS"
echo ""
echo "临时解决方案："
echo "  ./switch-image-source.sh local  # 切换到本地图片源"
echo "  ./switch-image-source.sh oss    # 切换到OSS图片源"
echo "" 
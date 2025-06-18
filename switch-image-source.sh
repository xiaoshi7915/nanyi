#!/bin/bash
# 图片源切换脚本
# 支持在OSS和本地图片源之间切换

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示当前状态
show_current_status() {
    echo -e "${BLUE}=== 南意秋棠图片源状态 ===${NC}"
    
    # 检查环境变量
    if [ -z "$IMAGE_SOURCE" ]; then
        echo -e "${YELLOW}当前图片源: 未设置 (默认: oss)${NC}"
    else
        echo -e "${GREEN}当前图片源: $IMAGE_SOURCE${NC}"
    fi
    
    # 检查服务状态
    if pgrep -f "backend/app.py" > /dev/null; then
        echo -e "${GREEN}后端服务: 运行中${NC}"
    else
        echo -e "${RED}后端服务: 未运行${NC}"
    fi
    
    if pgrep -f "frontend/server.py" > /dev/null; then
        echo -e "${GREEN}前端服务: 运行中${NC}"
    else
        echo -e "${RED}前端服务: 未运行${NC}"
    fi
    echo ""
}

# 切换到OSS图片源
switch_to_oss() {
    echo -e "${BLUE}正在切换到OSS图片源...${NC}"
    
    # 设置环境变量
    export IMAGE_SOURCE=oss
    
    # 更新.env文件
    if [ -f .env ]; then
        # 删除现有的IMAGE_SOURCE行
        sed -i '/^IMAGE_SOURCE=/d' .env
    fi
    echo "IMAGE_SOURCE=oss" >> .env
    
    echo -e "${GREEN}✅ 已切换到OSS图片源${NC}"
    echo -e "${YELLOW}📝 提示: 需要重启后端服务以生效${NC}"
}

# 切换到本地图片源
switch_to_local() {
    echo -e "${BLUE}正在切换到本地图片源...${NC}"
    
    # 设置环境变量
    export IMAGE_SOURCE=local
    
    # 更新.env文件
    if [ -f .env ]; then
        # 删除现有的IMAGE_SOURCE行
        sed -i '/^IMAGE_SOURCE=/d' .env
    fi
    echo "IMAGE_SOURCE=local" >> .env
    
    echo -e "${GREEN}✅ 已切换到本地图片源${NC}"
    echo -e "${YELLOW}📝 提示: 需要重启后端服务以生效${NC}"
}

# 重启服务
restart_services() {
    echo -e "${BLUE}正在重启服务...${NC}"
    
    # 停止服务
    ./stop_services.sh
    sleep 2
    
    # 启动服务
    ./start_services_fixed.sh
    
    echo -e "${GREEN}✅ 服务重启完成${NC}"
}

# 显示帮助信息
show_help() {
    echo -e "${BLUE}=== 图片源切换脚本使用说明 ===${NC}"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  oss      切换到OSS图片源 (阿里云对象存储)"
    echo "  local    切换到本地图片源 (服务器文件)"
    echo "  status   显示当前状态"
    echo "  restart  重启服务"
    echo "  help     显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 oss       # 切换到OSS图片源"
    echo "  $0 local     # 切换到本地图片源"
    echo "  $0 status    # 查看当前状态"
    echo "  $0 restart   # 重启服务"
    echo ""
    echo -e "${YELLOW}注意: 切换图片源后需要重启后端服务才能生效${NC}"
}

# 主逻辑
case "$1" in
    "oss")
        show_current_status
        switch_to_oss
        echo ""
        echo -e "${YELLOW}是否立即重启服务? (y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            restart_services
        fi
        ;;
    "local")
        show_current_status
        switch_to_local
        echo ""
        echo -e "${YELLOW}是否立即重启服务? (y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            restart_services
        fi
        ;;
    "status")
        show_current_status
        ;;
    "restart")
        restart_services
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    "")
        show_current_status
        echo ""
        echo -e "${YELLOW}请选择操作:${NC}"
        echo "1. 切换到OSS图片源"
        echo "2. 切换到本地图片源"
        echo "3. 查看状态"
        echo "4. 重启服务"
        echo "5. 退出"
        echo ""
        echo -n "请输入选择 (1-5): "
        read -r choice
        
        case $choice in
            1)
                switch_to_oss
                echo ""
                echo -e "${YELLOW}是否立即重启服务? (y/n)${NC}"
                read -r response
                if [[ "$response" =~ ^[Yy]$ ]]; then
                    restart_services
                fi
                ;;
            2)
                switch_to_local
                echo ""
                echo -e "${YELLOW}是否立即重启服务? (y/n)${NC}"
                read -r response
                if [[ "$response" =~ ^[Yy]$ ]]; then
                    restart_services
                fi
                ;;
            3)
                show_current_status
                ;;
            4)
                restart_services
                ;;
            5)
                echo -e "${GREEN}退出${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}无效选择${NC}"
                exit 1
                ;;
        esac
        ;;
    *)
        echo -e "${RED}错误: 未知选项 '$1'${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac 
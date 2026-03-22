#!/bin/bash

# Awesome Claude Skills 安装脚本
# 此脚本将克隆 awesome-claude-skills 仓库并安装所有技能到 Claude Code

set -e

echo "🚀 开始安装 Awesome Claude Skills..."

# 定义目录
SKILLS_DIR="$HOME/.config/claude-code/skills"
REPO_DIR="$SKILLS_DIR/awesome-claude-skills"
REPO_URL="https://github.com/ComposioHQ/awesome-claude-skills.git"

# 创建技能目录
echo "📁 创建技能目录..."
mkdir -p "$SKILLS_DIR"

# 检查是否已存在仓库
if [ -d "$REPO_DIR" ]; then
    echo "⚠️  仓库已存在，更新中..."
    cd "$REPO_DIR"
    git pull
else
    echo "📥 克隆仓库..."
    cd "$SKILLS_DIR"
    git clone "$REPO_URL" || {
        echo "❌ 克隆失败，请检查网络连接"
        echo "💡 提示：你可以稍后手动运行："
        echo "   cd $SKILLS_DIR"
        echo "   git clone $REPO_URL"
        exit 1
    }
fi

# 安装所有技能
echo "📦 安装技能..."
cd "$REPO_DIR"

INSTALLED=0
SKIPPED=0

for skill_dir in */; do
    # 移除尾部斜杠
    skill_name="${skill_dir%/}"
    
    # 跳过 .git 和其他隐藏目录
    if [[ "$skill_name" == .* ]]; then
        continue
    fi
    
    # 检查是否有 SKILL.md 文件
    if [ -f "$skill_dir/SKILL.md" ]; then
        target_dir="$SKILLS_DIR/$skill_name"
        
        # 如果已存在，询问是否覆盖
        if [ -d "$target_dir" ]; then
            echo "⚠️  技能 '$skill_name' 已存在，跳过..."
            SKIPPED=$((SKIPPED + 1))
        else
            echo "  ✓ 安装技能: $skill_name"
            cp -r "$skill_dir" "$target_dir"
            INSTALLED=$((INSTALLED + 1))
        fi
    fi
done

echo ""
echo "✅ 安装完成！"
echo "   - 已安装: $INSTALLED 个技能"
echo "   - 已跳过: $SKIPPED 个技能（已存在）"
echo ""
echo "📝 下一步："
echo "   1. 重启 Claude Code"
echo "   2. 技能将自动加载"
echo "   3. 查看 .cursor/awesome-claude-skills-list.md 了解所有可用技能"
echo ""
echo "💡 提示：你可以选择性地安装特定技能："
echo "   cp -r $REPO_DIR/[skill-name] $SKILLS_DIR/"

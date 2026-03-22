# Awesome Claude Skills 快速开始

## 🎯 概述

Awesome Claude Skills 是一个包含 **69 个实用技能**的精选集合，涵盖文档处理、开发工具、数据分析、商业营销、创意媒体、生产力工具等多个领域。

**GitHub 仓库**: https://github.com/ComposioHQ/awesome-claude-skills

## 📚 文档索引

本项目已为您准备了完整的文档：

1. **安装指南** - `.cursor/awesome-claude-skills-setup.md`
   - 详细的安装步骤
   - 每个技能的说明和使用示例
   - 故障排除

2. **完整技能列表** - `.cursor/awesome-claude-skills-list.md`
   - 所有 69 个技能的详细列表
   - 技能分类和统计
   - 快速查找指南

3. **安装脚本** - `.cursor/install-awesome-skills.sh`
   - 一键安装所有技能
   - 自动处理依赖和冲突

## 🚀 快速安装

### 方法一：使用安装脚本（推荐）

```bash
# 运行安装脚本
bash .cursor/install-awesome-skills.sh
```

### 方法二：手动安装

```bash
# 1. 创建技能目录
mkdir -p ~/.config/claude-code/skills/

# 2. 克隆仓库
cd ~/.config/claude-code/skills/
git clone https://github.com/ComposioHQ/awesome-claude-skills.git

# 3. 安装所有技能
cd awesome-claude-skills
for skill in */; do
  if [ -f "$skill/SKILL.md" ]; then
    cp -r "$skill" ~/.config/claude-code/skills/
  fi
done
```

### 方法三：选择性安装

只安装你需要的技能：

```bash
# 例如：只安装文档处理技能
mkdir -p ~/.config/claude-code/skills/
cd ~/.config/claude-code/skills/
git clone https://github.com/ComposioHQ/awesome-claude-skills.git
cp -r awesome-claude-skills/docx ~/.config/claude-code/skills/
cp -r awesome-claude-skills/pdf ~/.config/claude-code/skills/
cp -r awesome-claude-skills/xlsx ~/.config/claude-code/skills/
```

## ✅ 验证安装

```bash
# 检查已安装的技能
ls ~/.config/claude-code/skills/

# 查看技能元数据
head ~/.config/claude-code/skills/docx/SKILL.md
```

## 🎯 热门技能推荐

### 📄 文档处理
- **docx** - Word 文档处理
- **pdf** - PDF 文档处理
- **xlsx** - Excel 电子表格处理

### 💻 开发工具
- **artifacts-builder** - 前端构建工具
- **Webapp Testing** - Web 应用测试
- **test-driven-development** - 测试驱动开发
- **MCP Builder** - MCP 服务器构建器

### 📊 数据分析
- **CSV Data Summarizer** - CSV 数据汇总器
- **postgres** - PostgreSQL 数据库查询

### ✍️ 内容创作
- **Content Research Writer** - 内容研究写作
- **Twitter Algorithm Optimizer** - Twitter 算法优化器

### 🔗 自动化
- **connect-apps** - 连接 1000+ 应用

## 💡 使用示例

### 示例 1：处理 Word 文档

```
使用 docx 技能：创建一个包含目录、标题和段落的 Word 文档
```

### 示例 2：测试 Web 应用

```
使用 Webapp Testing 技能：测试我的本地应用在 localhost:3000 上的所有主要功能
```

### 示例 3：分析数据

```
使用 CSV Data Summarizer 技能：分析这个销售数据 CSV 文件并生成报告
```

### 示例 4：连接应用

```
使用 connect-apps 技能：发送一封电子邮件到 john@example.com
```

## 📖 完整技能列表

查看 `.cursor/awesome-claude-skills-list.md` 获取所有 69 个技能的完整列表。

## 🔗 相关资源

- **GitHub 仓库**: https://github.com/ComposioHQ/awesome-claude-skills
- **官方文档**: https://docs.anthropic.com/claude/docs/skills
- **技能市场**: https://claude.ai/skills
- **社区讨论**: https://community.anthropic.com/

## 🐛 需要帮助？

1. 查看 **安装指南** (`.cursor/awesome-claude-skills-setup.md`)
2. 查看 **技能列表** (`.cursor/awesome-claude-skills-list.md`)
3. 检查 GitHub 仓库的 Issues 和 Discussions

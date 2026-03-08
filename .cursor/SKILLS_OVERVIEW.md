# 技能总览：全局 vs 项目级

**最后更新**: 2026-01-25

---

## 📊 快速统计

| 类型 | 数量 | 位置 | 状态 |
|------|------|------|------|
| **全局技能** | 44 个 | `~/.config/claude-code/skills/` | ✅ |
| **项目级技能** | 1 个 | `/opt/hanfu/products/.claude/skills/` | ⚠️ 有重复 |
| **MCP 服务器技能** | 140 个 | MCP 服务器（全局配置） | ✅ |
| **Anthropic 官方技能** | 16 个 | 文档配置（全局） | ✅ |
| **Awesome Skills 仓库** | 69 个 | 仓库形式（全局） | ✅ |

**总计**: 约 **280+ 个可用技能**

---

## 🌐 全局技能 (44 个)

**位置**: `~/.config/claude-code/skills/`

### 按类别分类

#### 🚀 Superpowers 框架 (14 个)
- brainstorming, dispatching-parallel-agents, executing-plans
- finishing-a-development-branch, receiving-code-review
- requesting-code-review, subagent-driven-development
- systematic-debugging, test-driven-development
- using-git-worktrees, using-superpowers
- verification-before-completion, writing-plans, writing-skills

#### 🎨 UI/UX 设计 (1 个)
- ui-ux-pro-max ⚠️ **注意**: 在项目级也有重复

#### 📄 文档与内容处理 (5 个)
- artifacts-builder, brand-guidelines, canvas-design
- content-research-writer, image-enhancer

#### 💻 开发与代码工具 (4 个)
- changelog-generator, langsmith-fetch, mcp-builder, webapp-testing

#### 🔗 连接与集成 (2 个)
- connect, connect-apps

#### 📊 商业与营销 (4 个)
- competitive-ads-extractor, domain-name-brainstormer
- lead-research-assistant, internal-comms

#### 📁 生产力工具 (4 个)
- file-organizer, invoice-organizer
- tailored-resume-generator, raffle-winner-picker

#### ✍️ 沟通与写作 (2 个)
- meeting-insights-analyzer, twitter-algorithm-optimizer

#### 🎨 创意与媒体 (3 个)
- slack-gif-creator, theme-factory, video-downloader

#### 🛠️ 技能管理 (4 个)
- skill-creator, skill-share, template-skill, developer-growth-analysis

#### 📦 仓库 (1 个)
- awesome-claude-skills (包含 69 个子技能)

---

## 📁 项目级技能 (1 个)

**位置**: `/opt/hanfu/products/.claude/skills/`

### 当前技能

1. **ui-ux-pro-max** - UI/UX 设计智能助手
   - ⚠️ **重复**: 全局版本已存在
   - **建议**: 删除项目级版本，使用全局版本

---

## 🔬 MCP 服务器技能 (140 个) - 全局

**配置**: MCP 服务器（全局配置）
**服务器**: `claude-scientific-skills`
**URL**: `https://mcp.k-dense.ai/claude-scientific-skills/mcp`

### 主要类别

- 🧬 生物信息学与基因组学 (23 个)
- 🧪 化学信息学与药物发现 (14 个)
- 🔬 蛋白质组学与质谱 (2 个)
- 🏥 临床研究与精准医学 (12+ 个)
- 📚 科学文献与数据库 (10+ 个)
- 🔬 其他科学领域

**查看完整列表**: `.cursor/claude-scientific-skills-list.md`

---

## 📄 Anthropic 官方技能 (16 个) - 全局

**配置**: 通过文档配置（全局）

- 文档处理技能 (4 个): xlsx, docx, pptx, pdf
- 示例技能 (12 个)

**查看完整列表**: `.cursor/anthropics-skills-list.md`

---

## ⚠️ 发现的问题

### 重复技能

**ui-ux-pro-max** 同时存在于：
- 全局: `~/.config/claude-code/skills/ui-ux-pro-max/`
- 项目级: `/opt/hanfu/products/.claude/skills/ui-ux-pro-max/`

**建议操作**:
```bash
# 删除项目级版本，使用全局版本
rm -rf /opt/hanfu/products/.claude/skills/ui-ux-pro-max
```

**原因**: 
- 全局版本在所有项目中都可用
- 避免版本冲突
- 节省磁盘空间

---

## 💡 使用建议

### 何时使用全局技能

✅ **适合全局的技能**:
- 通用工具和框架（Superpowers、UI/UX Pro Max）
- 文档处理工具（docx、pdf、xlsx）
- 开发工具（测试、调试、代码审查）
- 生产力工具（文件组织、发票管理）

### 何时使用项目级技能

✅ **适合项目级的技能**:
- 项目特定的设计系统
- 项目特定的工作流
- 实验性技能
- 项目特定的配置

### 何时使用 MCP 服务器技能

✅ **适合 MCP 的技能**:
- 大型技能集合（如 140 个科学技能）
- 需要外部服务的技能
- 需要频繁更新的技能

---

## 🔍 查看技能命令

```bash
# 查看全局技能
ls ~/.config/claude-code/skills/

# 查看项目级技能
ls /opt/hanfu/products/.claude/skills/

# 统计全局技能数量
ls -1 ~/.config/claude-code/skills/ | wc -l

# 统计项目级技能数量
ls -1 /opt/hanfu/products/.claude/skills/ | wc -l

# 查找重复技能
comm -12 \
  <(ls -1 ~/.config/claude-code/skills/ | sort) \
  <(ls -1 /opt/hanfu/products/.claude/skills/ | sort)
```

---

## 📚 相关文档

- **详细分类**: `.cursor/SKILLS_CLASSIFICATION.md`
- **技能清单**: `.cursor/MY_SKILLS_SUMMARY.md`
- **Superpowers 指南**: `.cursor/superpowers-setup.md`
- **UI/UX Pro Max 指南**: `.cursor/ui-ux-pro-max-setup.md`
- **Awesome Skills 指南**: `.cursor/awesome-claude-skills-setup.md`
- **科学技能指南**: `.cursor/claude-scientific-skills-setup.md`
- **MCP 配置**: `.cursor/MCP_CONFIGURATION.md`

---

## 🎯 总结

### 全局技能 (44 个)
- ✅ 在所有项目中可用
- ✅ 包含 Superpowers 框架（14 个技能）
- ✅ 包含 UI/UX、文档处理、开发工具等

### 项目级技能 (1 个)
- ⚠️ 发现重复：ui-ux-pro-max
- 💡 建议删除项目级版本

### MCP 服务器技能 (140 个)
- ✅ 科学技能集合
- ✅ 通过 MCP 协议访问
- ✅ 不占用本地空间

### 其他技能
- ✅ Anthropic 官方技能 (16 个)
- ✅ Awesome Skills 仓库 (69 个)

**总计**: 约 **280+ 个可用技能**

---

**提示**: 建议清理重复的技能，保持技能管理的整洁性。

# 技能分类：全局 vs 项目级

**最后更新**: 2026-01-25

---

## 📊 技能统计总览

| 类型 | 数量 | 位置 |
|------|------|------|
| **全局技能** | 44 个 | `~/.config/claude-code/skills/` |
| **项目级技能** | 1 个 | `/opt/hanfu/products/.claude/skills/` |
| **MCP 服务器技能** | 140 个 | 通过 MCP 服务器配置（全局） |
| **Anthropic 官方技能** | 16 个 | 通过文档配置（全局） |
| **Awesome Skills 仓库** | 69 个 | 仓库形式（全局） |

**总计**: 约 **280+ 个可用技能**

---

## 🌐 全局技能 (44 个)

**位置**: `~/.config/claude-code/skills/`

这些技能在所有项目中都可用。

### 🚀 Superpowers 框架 (14 个技能)

1. **brainstorming** - 头脑风暴（设计完善）
2. **dispatching-parallel-agents** - 分派并行代理
3. **executing-plans** - 执行计划
4. **finishing-a-development-branch** - 完成开发分支
5. **receiving-code-review** - 接收代码审查
6. **requesting-code-review** - 请求代码审查
7. **subagent-driven-development** - 子代理驱动开发
8. **systematic-debugging** - 系统化调试
9. **test-driven-development** - 测试驱动开发
10. **using-git-worktrees** - 使用 Git Worktrees
11. **using-superpowers** - 使用 Superpowers
12. **verification-before-completion** - 完成前验证
13. **writing-plans** - 编写计划
14. **writing-skills** - 编写技能

### 🎨 UI/UX 设计

15. **ui-ux-pro-max** - UI/UX 设计智能助手（67 种风格、96 种调色板）

### 📄 文档与内容处理

16. **artifacts-builder** - 前端构建工具（React、Tailwind CSS、shadcn/ui）
17. **brand-guidelines** - 品牌指南应用
18. **canvas-design** - 画布设计工具
19. **content-research-writer** - 内容研究写作助手
20. **image-enhancer** - 图像增强器

### 💻 开发与代码工具

21. **changelog-generator** - 变更日志生成器
22. **langsmith-fetch** - LangSmith 调试工具
23. **mcp-builder** - MCP 服务器构建器
24. **webapp-testing** - Web 应用测试（Playwright）

### 🔗 连接与集成

25. **connect** - 连接应用（基础版）
26. **connect-apps** - 连接 1000+ 应用（Gmail、Slack、GitHub 等）

### 📊 商业与营销

27. **competitive-ads-extractor** - 竞争广告提取器
28. **domain-name-brainstormer** - 域名头脑风暴
29. **lead-research-assistant** - 潜在客户研究助手
30. **internal-comms** - 内部通信工具

### 📁 生产力工具

31. **file-organizer** - 文件组织器
32. **invoice-organizer** - 发票组织器
33. **tailored-resume-generator** - 定制简历生成器
34. **raffle-winner-picker** - 抽奖获胜者选择器

### ✍️ 沟通与写作

35. **meeting-insights-analyzer** - 会议洞察分析器
36. **twitter-algorithm-optimizer** - Twitter 算法优化器

### 🎨 创意与媒体

37. **slack-gif-creator** - Slack GIF 创建器
38. **theme-factory** - 主题工厂
39. **video-downloader** - 视频下载器

### 🛠️ 技能管理

40. **skill-creator** - 技能创建器
41. **skill-share** - 技能分享工具
42. **template-skill** - 技能模板
43. **developer-growth-analysis** - 开发者成长分析

### 📦 仓库

44. **awesome-claude-skills** - Awesome Claude Skills 完整仓库（包含 69 个子技能）

---

## 📁 项目级技能 (1 个)

**位置**: `/opt/hanfu/products/.claude/skills/`

这些技能仅在当前项目中可用。

### 🎨 UI/UX 设计

1. **ui-ux-pro-max** - UI/UX 设计智能助手
   - **说明**: 这个技能同时存在于全局和项目级
   - **项目级版本**: 可能是通过 `uipro init --ai claude` 在项目目录中安装的
   - **建议**: 可以删除项目级版本，使用全局版本即可

---

## 🔬 MCP 服务器技能 (140 个) - 全局配置

**配置方式**: 通过 MCP 服务器配置（全局）

**服务器**: `claude-scientific-skills`
**URL**: `https://mcp.k-dense.ai/claude-scientific-skills/mcp`

### 技能分类

#### 🧬 生物信息学与基因组学 (23 个)
- adaptyv, anndata, arboreto, biopython, bioservices, cellxgene-census, deeptools
- ena-database, ensembl-database, ete-toolkit, flowio, gene-database, geo-database
- geniml, gget, gtars, gwas-database, pysam, pydeseq2, scanpy, scikit-bio
- scvi-tools, zarr-python

#### 🧪 化学信息学与药物发现 (14 个)
- chembl-database, datamol, deepchem, diffdock, drugbank-database, hmdb-database
- medchem, molfeat, pubchem-database, pytdc, rdkit, rowan, torchdrug, zinc-database

#### 🔬 蛋白质组学与质谱 (2 个)
- matchms, pyOpenMS

#### 🏥 临床研究与精准医学 (12+ 个)
- ClinicalTrials.gov, ClinVar, ClinPGx, COSMIC, FDA Databases
- PyHealth, NeuroKit2, Clinical Decision Support 等

#### 📚 科学文献与数据库 (10+ 个)
- PubMed Database, arXiv Database, UniProt Database, PDB Database 等

#### 🔬 其他科学领域
- 物理学、材料科学、环境科学等领域的技能

**查看完整列表**: `.cursor/claude-scientific-skills-list.md`

---

## 📄 Anthropic 官方技能 (16 个) - 全局配置

**配置方式**: 通过文档配置（全局）

### 文档处理技能 (4 个)
1. **xlsx** - Excel 电子表格处理
2. **docx** - Word 文档处理
3. **pptx** - PowerPoint 演示文稿处理
4. **pdf** - PDF 文档处理

### 示例技能 (12 个)
- 各种示例和模板技能

**查看完整列表**: `.cursor/anthropics-skills-list.md`

---

## 📦 Awesome Claude Skills 仓库 (69 个技能) - 全局

**位置**: `~/.config/claude-code/skills/awesome-claude-skills/`

这是一个完整的技能仓库，包含 69 个子技能，涵盖：
- 文档处理
- 开发工具
- 数据分析
- 商业营销
- 沟通写作
- 创意媒体
- 生产力工具
- 协作管理
- 安全系统

**查看完整列表**: `.cursor/awesome-claude-skills-list.md`

---

## 🔍 如何区分全局和项目级技能

### 全局技能
- **位置**: `~/.config/claude-code/skills/`
- **特点**: 在所有项目中都可用
- **用途**: 通用工具和框架

### 项目级技能
- **位置**: `<项目根目录>/.claude/skills/`
- **特点**: 仅在当前项目中可用
- **用途**: 项目特定的技能和配置

### MCP 服务器技能
- **配置**: 通过 MCP 服务器配置（全局或项目级）
- **特点**: 通过 MCP 协议访问，不占用本地技能目录
- **用途**: 大型技能集合（如科学技能）

---

## 💡 使用建议

### 1. 全局技能
- 适合：通用工具、框架、可重用技能
- 优点：一次安装，所有项目可用
- 示例：Superpowers、UI/UX Pro Max、文档处理工具

### 2. 项目级技能
- 适合：项目特定的技能、实验性技能
- 优点：不影响其他项目，项目特定配置
- 示例：项目特定的设计系统、项目特定的工作流

### 3. MCP 服务器技能
- 适合：大型技能集合、需要外部服务的技能
- 优点：不占用本地空间，易于更新
- 示例：科学技能集合（140 个技能）

---

## 🔄 管理建议

### 清理重复技能

**发现**: `ui-ux-pro-max` 同时存在于全局和项目级

**建议操作**:
```bash
# 删除项目级版本，使用全局版本
rm -rf /opt/hanfu/products/.claude/skills/ui-ux-pro-max
```

### 查看技能位置

```bash
# 查看全局技能
ls ~/.config/claude-code/skills/

# 查看项目级技能
ls /opt/hanfu/products/.claude/skills/

# 查看 MCP 服务器配置
cat ~/.config/Code/User/globalStorage/tencent-cloud.coding-copilot/settings/Craft_mcp_settings.json
```

---

## 📚 相关文档

- **技能清单**: `.cursor/MY_SKILLS_SUMMARY.md`
- **Superpowers 指南**: `.cursor/superpowers-setup.md`
- **UI/UX Pro Max 指南**: `.cursor/ui-ux-pro-max-setup.md`
- **Awesome Skills 指南**: `.cursor/awesome-claude-skills-setup.md`
- **科学技能指南**: `.cursor/claude-scientific-skills-setup.md`
- **MCP 配置**: `.cursor/MCP_CONFIGURATION.md`

---

**提示**: 全局技能适合通用工具，项目级技能适合项目特定需求。MCP 服务器技能适合大型技能集合。

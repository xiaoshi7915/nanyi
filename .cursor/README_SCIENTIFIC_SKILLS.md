# Claude Scientific Skills 快速开始指南

## 🎯 概述

Claude Scientific Skills 是一个包含 **140 个科学技能**的集合，涵盖生物学、化学、医学、物理学等多个科学领域。这些技能可以让 Claude AI 执行复杂的多步骤科学工作流程。

## 📚 文档索引

本项目已为您准备了完整的文档：

1. **安装指南** - `.cursor/claude-scientific-skills-setup.md`
   - 详细的安装步骤
   - 前置要求
   - 故障排除

2. **MCP 配置指南** - `.cursor/MCP_CONFIGURATION.md`
   - MCP 服务器配置方法
   - 配置文件位置
   - 验证和测试

3. **完整技能列表** - `.cursor/claude-scientific-skills-list.md`
   - 所有 140 个技能的详细列表
   - 技能分类
   - 使用建议

## 🚀 快速开始

### 第一步：安装 MCP 服务器

**方法一：一键安装（最简单）**
```
访问：https://cursor.com/en-US/install-mcp?name=claude-scientific-skills&config=eyJ1cmwiOiJodHRwczovL21jcC5rLWRlbnNlLmFpL2NsYXVkZS1zY2llbnRpZmljLXNraWxscy9tY3AifQ%3D%3D
```

**方法二：手动配置**
1. 打开 Cursor 设置（`Ctrl+,` 或 `Cmd+,`）
2. 搜索 "MCP" 或 "Model Context Protocol"
3. 添加以下配置：
```json
{
  "mcpServers": {
    "claude-scientific-skills": {
      "url": "https://mcp.k-dense.ai/claude-scientific-skills/mcp"
    }
  }
}
```

### 第二步：验证安装

1. 重启 Cursor IDE
2. 检查 MCP 服务器连接状态
3. 尝试使用一个简单的技能

### 第三步：开始使用

直接在对话中描述你的科学任务，Claude 会自动选择合适的技能来执行。

## 💡 使用示例

### 示例 1：查询科学文献

```
使用可用的技能：搜索 PubMed 数据库，查找关于"CRISPR gene editing"的最新研究论文，
并总结主要发现。
```

**使用的技能：** PubMed Database

### 示例 2：分析 DNA 序列

```
使用可用的技能：使用 BioPython 读取 FASTA 格式的 DNA 序列文件，
计算 GC 含量，查找开放阅读框（ORF），并生成序列统计报告。
```

**使用的技能：** BioPython

### 示例 3：药物发现工作流

```
使用可用的技能：查询 ChEMBL 数据库获取 EGFR 抑制剂（IC50 < 50nM），
使用 RDKit 分析构效关系，生成改进的类似物，并进行虚拟筛选。
```

**使用的技能：** ChEMBL Database, RDKit, Datamol

### 示例 4：单细胞 RNA-seq 分析

```
使用可用的技能：使用 Scanpy 加载 10X Genomics 数据集，进行质量控制，
识别细胞类型，进行差异表达分析，并可视化结果。
```

**使用的技能：** Scanpy, AnnData

### 示例 5：蛋白质结构分析

```
使用可用的技能：从 AlphaFold 数据库获取蛋白质结构，使用 BioPython 分析
结构特征，识别结合位点，并生成结构可视化。
```

**使用的技能：** AlphaFold Database, BioPython

## 📖 技能分类速查

### 🧬 生物信息学
- **序列分析**: BioPython, pysam
- **单细胞分析**: Scanpy, AnnData, scvi-tools
- **基因组工具**: gget, Ensembl, NCBI Gene

### 🧪 药物发现
- **分子操作**: RDKit, Datamol, Molfeat
- **虚拟筛选**: DiffDock, ZINC Database
- **数据库**: ChEMBL, PubChem, DrugBank

### 🏥 临床研究
- **临床试验**: ClinicalTrials.gov
- **变异分析**: ClinVar, COSMIC
- **医疗 AI**: PyHealth, NeuroKit2

### 📊 数据分析
- **可视化**: Matplotlib, Seaborn, Plotly
- **统计分析**: statsmodels, scikit-learn
- **网络分析**: NetworkX

### 📚 科学交流
- **文献**: PubMed, OpenAlex, bioRxiv
- **写作**: Scientific Writing, Peer Review
- **可视化**: Scientific Visualization

## 🔍 如何查找技能

1. **按领域查找**
   - 查看 `.cursor/claude-scientific-skills-list.md` 中的分类

2. **按功能查找**
   - 在 GitHub 仓库中搜索：https://github.com/K-Dense-AI/claude-scientific-skills

3. **查看技能文档**
   - 每个技能都有详细的 `SKILL.md` 文档
   - 包含使用示例、最佳实践和参考材料

## ⚙️ 前置要求

- **Python**: 3.9+ (推荐 3.12+)
- **uv**: Python 包管理器
- **Cursor IDE**: 最新版本

### 安装 uv

```bash
# macOS 和 Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或通过 pip
pip install uv
```

## 🐛 常见问题

### Q: 技能未加载怎么办？
A: 
1. 检查 MCP 服务器配置是否正确
2. 重启 Cursor IDE
3. 查看 MCP 服务器连接状态

### Q: 如何查看所有可用技能？
A: 查看 `.cursor/claude-scientific-skills-list.md` 文件

### Q: 技能执行失败怎么办？
A: 
1. 检查 Python 环境
2. 确保已安装所需依赖
3. 查看错误消息
4. 参考技能的 `SKILL.md` 文档

### Q: 如何组合使用多个技能？
A: 在对话中描述完整的工作流程，Claude 会自动选择合适的技能组合

## 📚 更多资源

- **GitHub 仓库**: https://github.com/K-Dense-AI/claude-scientific-skills
- **官方文档**: https://github.com/K-Dense-AI/claude-scientific-skills/tree/main/docs
- **示例工作流**: https://github.com/K-Dense-AI/claude-scientific-skills/blob/main/docs/examples.md
- **完整技能描述**: https://github.com/K-Dense-AI/claude-scientific-skills/blob/main/docs/scientific-skills.md

## 🎓 学习路径

### 初学者
1. 从简单的数据库查询开始（如 PubMed, OpenAlex）
2. 尝试基本的序列分析（BioPython）
3. 学习数据可视化（Matplotlib, Seaborn）

### 中级用户
1. 组合多个技能完成复杂工作流
2. 使用单细胞分析工具（Scanpy）
3. 进行药物发现研究（RDKit, ChEMBL）

### 高级用户
1. 构建端到端的研究管道
2. 集成多个数据库和工具
3. 自动化复杂的工作流程

## 💬 获取帮助

- **查看文档**: 参考项目中的文档文件
- **GitHub Issues**: https://github.com/K-Dense-AI/claude-scientific-skills/issues
- **社区支持**: 加入 K-Dense 社区

## 📝 许可证

本项目采用 MIT 许可证。每个技能可能有自己的许可证，请查看各自的 `SKILL.md` 文件。

---

**祝您使用愉快！** 🚀

如有任何问题，请参考相关文档或联系支持团队。

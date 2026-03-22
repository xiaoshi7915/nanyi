# Claude Scientific Skills 安装和使用指南

## 📦 简介

Claude Scientific Skills 是一个包含 **140 个科学技能**的集合，涵盖生物学、化学、医学、物理学等多个科学领域。这些技能可以让 Claude AI 执行复杂的多步骤科学工作流程。

## 🚀 安装方法

### 方法一：通过 Cursor IDE 一键安装（推荐）

1. 访问一键安装链接：
   ```
   https://cursor.com/en-US/install-mcp?name=claude-scientific-skills&config=eyJ1cmwiOiJodHRwczovL21jcC5rLWRlbnNlLmFpL2NsYXVkZS1zY2llbnRpZmljLXNraWxscy9tY3AifQ%3D%3D
   ```

2. 或者在 Cursor 设置中添加 MCP 服务器：
   - 打开 Cursor 设置
   - 找到 MCP Servers 配置
   - 添加以下配置：
   ```json
   {
     "mcpServers": {
       "claude-scientific-skills": {
         "url": "https://mcp.k-dense.ai/claude-scientific-skills/mcp"
       }
     }
   }
   ```

### 方法二：手动配置 MCP 服务器

在项目根目录的 `.cursor` 文件夹中创建 `mcp.json` 文件（如果不存在）：

```json
{
  "mcpServers": {
    "claude-scientific-skills": {
      "url": "https://mcp.k-dense.ai/claude-scientific-skills/mcp"
    }
  }
}
```

## 📚 技能分类

### 🧬 生物信息学与基因组学 (16+ 技能)
- **序列分析**: BioPython, pysam, scikit-bio, BioServices
- **单细胞分析**: Scanpy, AnnData, scvi-tools, Arboreto, Cellxgene Census
- **基因组工具**: gget, geniml, gtars, deepTools, FlowIO, Zarr
- **系统发育**: ETE Toolkit

### 🧪 化学信息学与药物发现 (11+ 技能)
- **分子操作**: RDKit, Datamol, Molfeat
- **深度学习**: DeepChem, TorchDrug
- **对接与筛选**: DiffDock
- **云量子化学**: Rowan (pKa, docking, cofolding)
- **药物相似性**: MedChem
- **基准测试**: PyTDC

### 🔬 蛋白质组学与质谱 (2 技能)
- **光谱处理**: matchms, pyOpenMS

### 🏥 临床研究与精准医学 (12+ 技能)
- **临床数据库**: ClinicalTrials.gov, ClinVar, ClinPGx, COSMIC, FDA Databases
- **医疗 AI**: PyHealth, NeuroKit2, Clinical Decision Support
- **临床文档**: Clinical Reports, Treatment Plans
- **变异分析**: Ensembl, NCBI Gene

### 🖼️ 医学影像与数字病理学 (3 技能)
- **DICOM 处理**: pydicom
- **全切片成像**: histolab, PathML

### 🧠 神经科学与电生理学 (1 技能)
- **神经记录**: Neuropixels-Analysis

### 🤖 机器学习与 AI (15+ 技能)
- **深度学习**: PyTorch Lightning, Transformers, Stable Baselines3, PufferLib
- **经典 ML**: scikit-learn, scikit-survival, SHAP
- **时间序列**: aeon
- **贝叶斯方法**: PyMC
- **优化**: PyMOO
- **图 ML**: Torch Geometric
- **降维**: UMAP-learn
- **统计建模**: statsmodels

### 🔮 材料科学、化学与物理学 (7 技能)
- **材料**: Pymatgen
- **代谢建模**: COBRApy
- **天文学**: Astropy
- **量子计算**: Cirq, PennyLane, Qiskit, QuTiP

### ⚙️ 工程与仿真 (4 技能)
- **数值计算**: MATLAB/Octave
- **计算流体动力学**: FluidSim
- **离散事件仿真**: SimPy
- **数据处理**: Dask, Polars, Vaex

### 📊 数据分析与可视化 (14+ 技能)
- **可视化**: Matplotlib, Seaborn, Plotly, Scientific Visualization
- **地理空间分析**: GeoPandas
- **网络分析**: NetworkX
- **符号数学**: SymPy
- **PDF 生成**: ReportLab
- **数据访问**: Data Commons
- **探索性数据分析**: EDA workflows
- **统计分析**: Statistical Analysis workflows

### 🧪 实验室自动化 (3 技能)
- **液体处理**: PyLabRobot
- **协议管理**: Protocols.io
- **LIMS 集成**: Benchling, LabArchives

### 🔬 多组学与系统生物学 (5+ 技能)
- **通路分析**: KEGG, Reactome, STRING
- **多组学**: Denario, HypoGeniC
- **数据管理**: LaminDB

### 🧬 蛋白质工程与设计 (2 技能)
- **蛋白质语言模型**: ESM
- **云实验室平台**: Adaptyv

### 📚 科学交流 (20+ 技能)
- **文献**: OpenAlex, PubMed, bioRxiv, Literature Review
- **网络搜索**: Perplexity Search
- **写作**: Scientific Writing, Peer Review
- **文档处理**: XLSX, MarkItDown, Document Skills
- **发布**: Paper-2-Web, Venue Templates
- **演示**: Scientific Slides, LaTeX Posters, PPTX Posters
- **图表**: Scientific Schematics
- **引用**: Citation Management
- **插图**: Generate Image

### 🔬 科学数据库 (28+ 技能)
- **蛋白质**: UniProt, PDB, AlphaFold DB
- **化学**: PubChem, ChEMBL, DrugBank, ZINC, HMDB
- **基因组**: Ensembl, NCBI Gene, GEO, ENA, GWAS Catalog
- **文献**: bioRxiv
- **临床**: ClinVar, COSMIC, ClinicalTrials.gov, ClinPGx, FDA Databases
- **通路**: KEGG, Reactome, STRING
- **靶点**: Open Targets
- **代谢组学**: Metabolomics Workbench
- **酶**: BRENDA
- **专利**: USPTO

### 🔧 基础设施与平台 (6+ 技能)
- **云计算**: Modal
- **基因组平台**: DNAnexus, LatchBio
- **显微镜**: OMERO
- **自动化**: Opentrons
- **工具发现**: ToolUniverse, Get Available Resources

### 🎓 研究方法与规划 (8+ 技能)
- **构思**: Scientific Brainstorming, Hypothesis Generation
- **批判分析**: Scientific Critical Thinking, Scholar Evaluation
- **资金**: Research Grants
- **发现**: Research Lookup
- **市场分析**: Market Research Reports

### ⚖️ 监管与标准 (1 技能)
- **医疗器械标准**: ISO 13485 Certification

## 💡 使用示例

### 示例 1: 药物发现流程
```
使用可用的技能：查询 ChEMBL 获取 EGFR 抑制剂（IC50 < 50nM），
使用 RDKit 分析构效关系，使用 datamol 生成改进的类似物，
使用 DiffDock 对 AlphaFold EGFR 结构进行虚拟筛选，
搜索 PubMed 了解耐药机制，检查 COSMIC 的突变，
并创建可视化和综合报告。
```

### 示例 2: 单细胞 RNA-seq 分析
```
使用可用的技能：使用 Scanpy 加载 10X 数据集，进行 QC 和双联体去除，
与 Cellxgene Census 数据集成，使用 NCBI Gene 标记识别细胞类型，
使用 PyDESeq2 进行差异表达，使用 Arboreto 推断基因调控网络，
通过 Reactome/KEGG 富集通路，使用 Open Targets 识别治疗靶点。
```

### 示例 3: 多组学生物标志物发现
```
使用可用的技能：使用 PyDESeq2 分析 RNA-seq，使用 pyOpenMS 处理质谱，
从 HMDB/Metabolomics Workbench 整合代谢物，通过 UniProt/KEGG 映射蛋白质到通路，
通过 STRING 查找相互作用，使用 statsmodels 关联组学层，
使用 scikit-learn 构建预测模型，搜索 ClinicalTrials.gov 查找相关试验。
```

## 📖 更多信息

- **GitHub 仓库**: https://github.com/K-Dense-AI/claude-scientific-skills
- **官方文档**: 每个技能都有详细的 `SKILL.md` 文档
- **示例工作流**: 查看 `docs/examples.md`
- **完整技能列表**: 查看 `docs/scientific-skills.md`

## ⚙️ 前置要求

- **Python**: 3.9+ (推荐 3.12+)
- **uv**: Python 包管理器（用于安装技能依赖）
- **客户端**: Cursor IDE 或任何 MCP 兼容客户端

### 安装 uv

**macOS 和 Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**或者通过 pip:**
```bash
pip install uv
```

## 🔧 故障排除

### 问题：技能未加载
- 解决方案：确保已安装最新版本的 Cursor IDE
- 验证插件是否已安装
- 尝试重新安装

### 问题：缺少 Python 依赖
- 解决方案：检查特定技能的 `SKILL.md` 文件中的必需包
- 安装依赖：`uv pip install package-name`

### 问题：API 速率限制
- 解决方案：许多数据库都有速率限制，请查看特定数据库文档
- 考虑实施缓存或批量请求

## 📝 许可证

本项目采用 MIT 许可证。但是，每个技能都有自己的许可证，请在各自的 `SKILL.md` 文件中查看。

## 🙏 致谢

Claude Scientific Skills 基于 50+ 优秀的开源项目构建，包括 Biopython, Scanpy, RDKit, scikit-learn, PyTorch Lightning 等。

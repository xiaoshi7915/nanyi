# Awesome Claude Skills 安装和使用指南

## 📋 概述

Awesome Claude Skills 是一个精选的实用 Claude Skills 集合，包含 40+ 个技能，涵盖文档处理、开发工具、数据分析、商业营销、创意媒体、生产力工具等多个领域。这些技能可以让 Claude 在 Claude.ai、Claude Code 和 Claude API 中执行专业任务。

**GitHub 仓库**: https://github.com/ComposioHQ/awesome-claude-skills

## 🚀 安装方法

### 方法一：在 Claude Code 中安装（推荐）

#### 步骤 1：创建技能目录

```bash
mkdir -p ~/.config/claude-code/skills/
```

#### 步骤 2：克隆仓库

```bash
cd ~/.config/claude-code/skills/
git clone https://github.com/ComposioHQ/awesome-claude-skills.git
```

#### 步骤 3：安装单个技能

每个技能都是独立的文件夹。你可以选择安装需要的技能：

```bash
# 例如：安装文档处理技能
cp -r awesome-claude-skills/docx ~/.config/claude-code/skills/
cp -r awesome-claude-skills/pdf ~/.config/claude-code/skills/
cp -r awesome-claude-skills/xlsx ~/.config/claude-code/skills/
```

或者安装所有技能：

```bash
cd awesome-claude-skills
for skill in */; do
  if [ -f "$skill/SKILL.md" ]; then
    cp -r "$skill" ~/.config/claude-code/skills/
  fi
done
```

#### 步骤 4：验证安装

```bash
# 检查技能是否正确安装
head ~/.config/claude-code/skills/docx/SKILL.md
```

#### 步骤 5：重启 Claude Code

```bash
# 重启 Claude Code 以加载新技能
exit
claude
```

### 方法二：在 Claude.ai 中使用

1. 点击聊天界面中的技能图标（🧩）
2. 从市场添加技能或上传自定义技能
3. Claude 会根据任务自动激活相关技能

### 方法三：通过 Claude API 使用

```python
import anthropic

client = anthropic.Anthropic(api_key="your-api-key")

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    skills=["skill-id-here"],
    messages=[{"role": "user", "content": "Your prompt"}]
)
```

## 📚 技能分类和使用

### 📄 文档处理技能

#### 1. **docx** - Word 文档处理
- **功能**：创建、编辑、分析 Word 文档，支持跟踪更改、评论、格式化
- **使用场景**：
  - 创建专业文档
  - 编辑现有文档并保留格式
  - 分析文档内容
- **使用示例**：
  ```
  使用 docx 技能：创建一个包含目录、标题和段落的 Word 文档
  ```

#### 2. **pdf** - PDF 文档处理
- **功能**：提取文本、表格、元数据，合并和注释 PDF
- **使用场景**：
  - 从 PDF 提取信息
  - 合并多个 PDF 文件
  - 添加注释和标记
- **使用示例**：
  ```
  使用 pdf 技能：从这个 PDF 文件中提取所有表格数据
  ```

#### 3. **pptx** - PowerPoint 演示文稿处理
- **功能**：读取、生成和调整幻灯片、布局、模板
- **使用场景**：
  - 创建演示文稿
  - 修改现有幻灯片
  - 应用模板和主题
- **使用示例**：
  ```
  使用 pptx 技能：创建一个关于项目进展的 10 页演示文稿
  ```

#### 4. **xlsx** - Excel 电子表格处理
- **功能**：电子表格操作：公式、图表、数据转换
- **使用场景**：
  - 创建带公式的电子表格
  - 数据分析和可视化
  - 数据转换和清理
- **使用示例**：
  ```
  使用 xlsx 技能：创建一个包含销售数据的 Excel 表格，添加公式计算总销售额
  ```

#### 5. **Markdown to EPUB Converter** - Markdown 转 EPUB
- **功能**：将 Markdown 文档和聊天摘要转换为专业的 EPUB 电子书文件
- **使用场景**：
  - 将文档转换为电子书格式
  - 创建可发布的电子书
- **使用示例**：
  ```
  使用 Markdown to EPUB Converter 技能：将这个 Markdown 文件转换为 EPUB 电子书
  ```

### 💻 开发与代码工具

#### 6. **artifacts-builder** - 前端构建工具
- **功能**：使用现代前端技术（React、Tailwind CSS、shadcn/ui）创建复杂的多组件 HTML 工件
- **使用场景**：
  - 创建交互式网页应用
  - 构建前端原型
- **使用示例**：
  ```
  使用 artifacts-builder 技能：创建一个带有搜索功能的待办事项应用
  ```

#### 7. **Changelog Generator** - 变更日志生成器
- **功能**：通过分析 Git 提交历史，自动创建面向用户的变更日志
- **使用场景**：
  - 生成发布说明
  - 将技术提交转换为用户友好的发布说明
- **使用示例**：
  ```
  使用 Changelog Generator 技能：基于最近的 Git 提交生成版本 2.0 的变更日志
  ```

#### 8. **MCP Builder** - MCP 服务器构建器
- **功能**：指导创建高质量的 MCP（Model Context Protocol）服务器
- **使用场景**：
  - 集成外部 API 和服务
  - 创建自定义 MCP 服务器
- **使用示例**：
  ```
  使用 MCP Builder 技能：创建一个连接 GitHub API 的 MCP 服务器
  ```

#### 9. **Playwright Browser Automation** - 浏览器自动化
- **功能**：用于测试和验证 Web 应用程序的模型调用 Playwright 自动化
- **使用场景**：
  - 自动化 Web 测试
  - 验证前端功能
- **使用示例**：
  ```
  使用 Playwright Browser Automation 技能：测试登录流程是否正常工作
  ```

#### 10. **Webapp Testing** - Web 应用测试
- **功能**：使用 Playwright 测试本地 Web 应用程序，验证前端功能、调试 UI 行为并捕获截图
- **使用场景**：
  - 测试本地开发的应用
  - 调试 UI 问题
- **使用示例**：
  ```
  使用 Webapp Testing 技能：测试我的本地应用在 localhost:3000 上的所有主要功能
  ```

#### 11. **test-driven-development** - 测试驱动开发
- **功能**：在实现任何功能或修复错误之前使用，先编写测试
- **使用场景**：
  - 实施新功能前编写测试
  - 确保代码质量
- **使用示例**：
  ```
  使用 test-driven-development 技能：为新的用户注册功能编写测试
  ```

#### 12. **software-architecture** - 软件架构
- **功能**：实现设计模式，包括清洁架构、SOLID 原则和全面的软件设计最佳实践
- **使用场景**：
  - 设计系统架构
  - 重构代码
- **使用示例**：
  ```
  使用 software-architecture 技能：为我的电商应用设计一个清洁架构
  ```

### 📊 数据分析技能

#### 13. **CSV Data Summarizer** - CSV 数据汇总器
- **功能**：自动分析 CSV 文件并生成带有可视化的全面洞察，无需用户提示
- **使用场景**：
  - 快速分析数据文件
  - 生成数据报告
- **使用示例**：
  ```
  使用 CSV Data Summarizer 技能：分析这个销售数据 CSV 文件并生成报告
  ```

#### 14. **deep-research** - 深度研究
- **功能**：使用 Gemini Deep Research Agent 执行自主多步骤研究
- **使用场景**：
  - 市场分析
  - 竞争格局分析
  - 文献综述
- **使用示例**：
  ```
  使用 deep-research 技能：研究人工智能在医疗保健中的应用趋势
  ```

#### 15. **postgres** - PostgreSQL 数据库
- **功能**：对 PostgreSQL 数据库执行安全的只读 SQL 查询，支持多连接和深度防御安全
- **使用场景**：
  - 查询数据库
  - 数据分析
- **使用示例**：
  ```
  使用 postgres 技能：查询用户表中最近 30 天的注册用户数量
  ```

### 💼 商业与营销技能

#### 16. **Brand Guidelines** - 品牌指南
- **功能**：将 Anthropic 官方品牌颜色和排版应用于工件，实现一致的视觉识别和专业设计标准
- **使用场景**：
  - 创建品牌一致的文档
  - 应用设计标准
- **使用示例**：
  ```
  使用 Brand Guidelines 技能：将这个文档应用 Anthropic 品牌风格
  ```

#### 17. **Competitive Ads Extractor** - 竞争广告提取器
- **功能**：从广告库中提取和分析竞争对手的广告，了解引起共鸣的消息和创意方法
- **使用场景**：
  - 竞争分析
  - 广告策略研究
- **使用示例**：
  ```
  使用 Competitive Ads Extractor 技能：分析竞争对手在 Facebook 上的广告策略
  ```

#### 18. **Domain Name Brainstormer** - 域名头脑风暴
- **功能**：生成创意域名想法并检查多个 TLD 的可用性，包括 .com、.io、.dev 和 .ai 扩展名
- **使用场景**：
  - 为新项目寻找域名
  - 检查域名可用性
- **使用示例**：
  ```
  使用 Domain Name Brainstormer 技能：为我的 AI 创业公司生成 10 个域名建议
  ```

#### 19. **Lead Research Assistant** - 潜在客户研究助手
- **功能**：通过分析您的产品、搜索目标公司并提供可操作的拓展策略来识别和评估高质量潜在客户
- **使用场景**：
  - 寻找潜在客户
  - 客户拓展
- **使用示例**：
  ```
  使用 Lead Research Assistant 技能：为我的 SaaS 产品找到 20 个潜在客户
  ```

### ✍️ 沟通与写作技能

#### 20. **Content Research Writer** - 内容研究写作
- **功能**：通过进行研究、添加引用、改进钩子和提供逐节反馈来协助撰写高质量内容
- **使用场景**：
  - 撰写博客文章
  - 创建内容营销材料
- **使用示例**：
  ```
  使用 Content Research Writer 技能：撰写一篇关于"AI 在医疗中的应用"的博客文章
  ```

#### 21. **Meeting Insights Analyzer** - 会议洞察分析器
- **功能**：分析会议记录以发现行为模式，包括冲突回避、发言比例、填充词和领导风格
- **使用场景**：
  - 会议分析
  - 团队沟通改进
- **使用示例**：
  ```
  使用 Meeting Insights Analyzer 技能：分析这次团队会议的记录并生成洞察报告
  ```

#### 22. **Twitter Algorithm Optimizer** - Twitter 算法优化器
- **功能**：使用 Twitter 开源算法洞察分析和优化推文以获得最大覆盖范围
- **使用场景**：
  - 优化社交媒体内容
  - 提高推文参与度
- **使用示例**：
  ```
  使用 Twitter Algorithm Optimizer 技能：优化这条推文以提高参与度
  ```

### 🎨 创意与媒体技能

#### 23. **Canvas Design** - 画布设计
- **功能**：使用设计哲学和美学原则在 PNG 和 PDF 文档中创建美丽的视觉艺术
- **使用场景**：
  - 创建海报
  - 设计视觉资产
- **使用示例**：
  ```
  使用 Canvas Design 技能：创建一个产品发布会的海报设计
  ```

#### 24. **Image Enhancer** - 图像增强器
- **功能**：通过提高分辨率、锐度和清晰度来改善图像和截图质量
- **使用场景**：
  - 增强截图质量
  - 准备演示材料
- **使用示例**：
  ```
  使用 Image Enhancer 技能：增强这个截图的清晰度
  ```

#### 25. **Slack GIF Creator** - Slack GIF 创建器
- **功能**：创建针对 Slack 优化的动画 GIF，具有大小约束验证器和可组合动画原语
- **使用场景**：
  - 创建团队沟通 GIF
  - 制作动画表情
- **使用示例**：
  ```
  使用 Slack GIF Creator 技能：创建一个庆祝项目完成的 GIF
  ```

#### 26. **Theme Factory** - 主题工厂
- **功能**：将专业字体和颜色主题应用于工件，包括幻灯片、文档、报告和 HTML 登录页面，提供 10 个预设主题
- **使用场景**：
  - 应用设计主题
  - 统一视觉风格
- **使用示例**：
  ```
  使用 Theme Factory 技能：将这个演示文稿应用现代科技主题
  ```

#### 27. **Video Downloader** - 视频下载器
- **功能**：从 YouTube 和其他平台下载视频，支持离线观看、编辑或归档，支持各种格式和质量选项
- **使用场景**：
  - 下载视频内容
  - 创建视频库
- **使用示例**：
  ```
  使用 Video Downloader 技能：下载这个 YouTube 视频的 1080p 版本
  ```

### 📁 生产力与组织技能

#### 28. **File Organizer** - 文件组织器
- **功能**：通过理解上下文、查找重复项和建议更好的组织结构来智能组织文件和文件夹
- **使用场景**：
  - 整理项目文件
  - 清理文件系统
- **使用示例**：
  ```
  使用 File Organizer 技能：整理我的下载文件夹
  ```

#### 29. **Invoice Organizer** - 发票组织器
- **功能**：通过读取文件、提取信息和一致重命名来自动组织发票和收据以进行税务准备
- **使用场景**：
  - 整理财务文档
  - 税务准备
- **使用示例**：
  ```
  使用 Invoice Organizer 技能：整理这个文件夹中的所有发票
  ```

#### 30. **Tailored Resume Generator** - 定制简历生成器
- **功能**：分析工作描述并生成定制简历，突出相关经验、技能和成就，以最大化面试机会
- **使用场景**：
  - 创建求职简历
  - 定制申请材料
- **使用示例**：
  ```
  使用 Tailored Resume Generator 技能：基于这个职位描述生成一份定制简历
  ```

### 🔗 连接应用技能

#### 31. **connect-apps** / **connect** - 连接应用
- **功能**：将 Claude 连接到任何应用。发送电子邮件、创建问题、发布消息、更新数据库 - 在 Gmail、Slack、GitHub、Notion 和 1000+ 服务中执行真实操作
- **使用场景**：
  - 自动化工作流
  - 集成多个服务
- **安装步骤**：
  1. 安装插件：`claude --plugin-dir ./connect-apps-plugin`
  2. 运行设置：`/connect-apps:setup`
  3. 粘贴 API 密钥（在 platform.composio.dev 获取免费密钥）
  4. 重启 Claude Code
- **使用示例**：
  ```
  使用 connect-apps 技能：发送一封电子邮件到 john@example.com
  ```

## 📖 完整技能列表

### 文档处理
- docx, pdf, pptx, xlsx, Markdown to EPUB Converter

### 开发与代码工具
- artifacts-builder, aws-skills, Changelog Generator, Claude Code Terminal Title, D3.js Visualization, FFUF Web Fuzzing, finishing-a-development-branch, iOS Simulator, jules, LangSmith Fetch, MCP Builder, move-code-quality-skill, Playwright Browser Automation, prompt-engineering, pypict-claude-skill, reddit-fetch, Skill Creator, Skill Seekers, software-architecture, subagent-driven-development, test-driven-development, using-git-worktrees, connect, Webapp Testing

### 数据分析
- CSV Data Summarizer, deep-research, postgres, root-cause-tracing

### 商业与营销
- Brand Guidelines, Competitive Ads Extractor, Domain Name Brainstormer, Internal Comms, Lead Research Assistant

### 沟通与写作
- article-extractor, brainstorming, Content Research Writer, family-history-research, Meeting Insights Analyzer, NotebookLM Integration, Twitter Algorithm Optimizer

### 创意与媒体
- Canvas Design, imagen, Image Enhancer, Slack GIF Creator, Theme Factory, Video Downloader, youtube-transcript

### 生产力与组织
- File Organizer, Invoice Organizer, kaizen, n8n-skills, Raffle Winner Picker, Tailored Resume Generator, ship-learn-next, tapestry

### 协作与项目管理
- git-pushing, google-workspace-skills, outline, review-implementing, test-fixing

### 安全与系统
- computer-forensics, file-deletion, metadata-extraction, threat-hunting-with-sigma-rules

## ✅ 验证安装

安装完成后，可以通过以下方式验证：

1. **检查技能目录**
   ```bash
   ls ~/.config/claude-code/skills/
   ```

2. **查看技能元数据**
   ```bash
   head ~/.config/claude-code/skills/[skill-name]/SKILL.md
   ```

3. **重启 Claude Code**
   ```bash
   exit
   claude
   ```

4. **测试技能**
   在 Claude Code 中直接描述任务，Claude 会自动激活相关技能。

## 💡 使用建议

1. **从简单开始**：先尝试使用一些简单的文档处理技能
2. **查看示例**：每个技能文件夹中都有详细的 `SKILL.md` 文档和示例
3. **组合使用**：多个技能可以组合使用完成复杂任务
4. **阅读文档**：参考 GitHub 仓库中的详细文档

## 🔗 相关资源

- **GitHub 仓库**: https://github.com/ComposioHQ/awesome-claude-skills
- **官方文档**: https://docs.anthropic.com/claude/docs/skills
- **技能市场**: https://claude.ai/skills
- **社区讨论**: https://community.anthropic.com/

## 🐛 故障排除

### 问题 1：技能未加载

**解决方案：**
- 确保技能文件夹包含 `SKILL.md` 文件
- 检查 `SKILL.md` 文件格式是否正确（需要 YAML frontmatter）
- 重启 Claude Code

### 问题 2：技能执行失败

**解决方案：**
- 检查前置要求（某些技能需要安装特定工具或库）
- 查看技能的 `SKILL.md` 文档了解依赖项
- 检查错误消息以获取更多信息

### 问题 3：找不到技能

**解决方案：**
- 确认技能已正确复制到 `~/.config/claude-code/skills/` 目录
- 检查技能文件夹名称是否正确
- 验证 `SKILL.md` 文件是否存在且格式正确

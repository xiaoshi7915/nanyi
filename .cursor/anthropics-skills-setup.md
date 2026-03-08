# Anthropic Skills 安装和使用指南

## 📋 概述

Anthropic Skills 是 Anthropic 官方提供的技能集合，包含文档处理、创意设计、技术开发、企业通信等多个领域的技能。这些技能可以让 Claude 更好地完成专业任务。

## 🚀 安装方法

### 方法一：通过 Claude Code 安装（推荐）

#### 步骤 1：注册插件市场

在 Claude Code 中运行以下命令：

```
/plugin marketplace add anthropics/skills
```

#### 步骤 2：安装技能插件

**选项 A：安装文档处理技能**
```
/plugin install document-skills@anthropic-agent-skills
```

**选项 B：安装示例技能集合**
```
/plugin install example-skills@anthropic-agent-skills
```

**选项 C：交互式安装**
1. 在 Claude Code 中运行 `/plugin`
2. 选择 `Browse and install plugins`
3. 选择 `anthropic-agent-skills`
4. 选择 `document-skills` 或 `example-skills`
5. 点击 `Install now`

### 方法二：在 Claude.ai 中使用

这些示例技能在 Claude.ai 的付费计划中已经可用。

要使用这些技能或上传自定义技能，请按照 [Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude) 的说明操作。

### 方法三：通过 Claude API 使用

可以通过 Claude API 使用 Anthropic 的预构建技能，也可以上传自定义技能。详情请参考 [Skills API Quickstart](https://docs.claude.com/en/api/skills-guide#creating-a-skill)。

## 📚 可用技能列表

### 📄 文档处理技能 (document-skills)

#### 1. **xlsx** - Excel 电子表格处理
- **功能**：创建、编辑和分析电子表格
- **支持格式**：.xlsx, .xlsm, .csv, .tsv
- **主要能力**：
  - 创建带公式和格式的新电子表格
  - 读取和分析数据
  - 修改现有电子表格并保留公式
  - 数据分析和可视化
  - 重新计算公式

**使用示例**：
```
使用 xlsx 技能：创建一个包含销售数据的 Excel 表格，添加公式计算总销售额和平均值。
```

#### 2. **docx** - Word 文档处理
- **功能**：创建、编辑和分析 Word 文档
- **主要能力**：
  - 创建新文档
  - 修改或编辑内容
  - 处理跟踪更改（Track Changes）
  - 添加评论
  - 保留格式
  - 文本提取

**使用示例**：
```
使用 docx 技能：创建一个新的 Word 文档，包含标题、段落和列表格式。
```

#### 3. **pptx** - PowerPoint 演示文稿处理
- **功能**：创建、编辑和分析演示文稿
- **主要能力**：
  - 创建新演示文稿
  - 修改或编辑内容
  - 处理布局
  - 添加评论或演讲者备注

**使用示例**：
```
使用 pptx 技能：创建一个包含 5 张幻灯片的演示文稿，介绍项目进展。
```

#### 4. **pdf** - PDF 文档处理
- **功能**：PDF 操作工具包
- **主要能力**：
  - 提取文本和表格
  - 创建新 PDF
  - 合并/拆分文档
  - 处理表单
  - 填写 PDF 表单

**使用示例**：
```
使用 pdf 技能：从 PDF 文件中提取所有文本内容，并创建一个摘要文档。
```

### 🎨 示例技能集合 (example-skills)

#### 5. **algorithmic-art** - 算法艺术创作
- **功能**：使用 p5.js 创建算法艺术
- **主要能力**：
  - 生成艺术代码
  - 生成艺术
  - 算法艺术
  - 流场
  - 粒子系统

**使用示例**：
```
使用 algorithmic-art 技能：创建一个基于粒子系统的生成艺术作品。
```

#### 6. **brand-guidelines** - 品牌指南
- **功能**：应用 Anthropic 官方品牌颜色和排版
- **主要能力**：
  - 应用品牌颜色
  - 应用样式指南
  - 视觉格式设置
  - 公司设计标准

**使用示例**：
```
使用 brand-guidelines 技能：创建一个符合 Anthropic 品牌指南的文档。
```

#### 7. **canvas-design** - 画布设计
- **功能**：创建精美的视觉艺术作品
- **输出格式**：.png 和 .pdf
- **主要能力**：
  - 创建海报
  - 创建艺术作品
  - 创建设计
  - 静态视觉作品

**使用示例**：
```
使用 canvas-design 技能：设计一个科技主题的海报。
```

#### 8. **doc-coauthoring** - 文档协作
- **功能**：引导用户完成结构化文档协作工作流
- **主要能力**：
  - 编写文档
  - 创建提案
  - 技术规范
  - 决策文档

**使用示例**：
```
使用 doc-coauthoring 技能：帮助我创建一个技术规范文档。
```

#### 9. **frontend-design** - 前端设计
- **功能**：创建独特、生产级的前端界面
- **主要能力**：
  - 构建 Web 组件
  - 创建页面
  - 创建仪表板
  - React 组件
  - HTML/CSS 布局
  - 美化 Web UI

**使用示例**：
```
使用 frontend-design 技能：创建一个现代化的登录页面，使用 React 和 Tailwind CSS。
```

#### 10. **internal-comms** - 内部通信
- **功能**：帮助编写各种内部通信
- **主要能力**：
  - 状态报告
  - 领导更新
  - 公司通讯
  - FAQ
  - 事件报告
  - 项目更新

**使用示例**：
```
使用 internal-comms 技能：创建一个项目状态报告，包含进度、风险和下一步计划。
```

#### 11. **mcp-builder** - MCP 服务器构建器
- **功能**：创建高质量的 MCP（Model Context Protocol）服务器
- **主要能力**：
  - 构建 MCP 服务器
  - 集成外部 API
  - Python (FastMCP)
  - Node/TypeScript (MCP SDK)

**使用示例**：
```
使用 mcp-builder 技能：创建一个 MCP 服务器来集成 GitHub API。
```

#### 12. **skill-creator** - 技能创建器
- **功能**：创建有效技能的指南
- **主要能力**：
  - 创建新技能
  - 更新现有技能
  - 扩展 Claude 的能力
  - 专业知识和工作流

**使用示例**：
```
使用 skill-creator 技能：帮助我创建一个自定义技能来处理项目特定的任务。
```

#### 13. **slack-gif-creator** - Slack GIF 创建器
- **功能**：创建针对 Slack 优化的动画 GIF
- **主要能力**：
  - 创建动画 GIF
  - Slack 优化
  - 约束和验证工具
  - 动画概念

**使用示例**：
```
使用 slack-gif-creator 技能：创建一个展示加载动画的 GIF，用于 Slack。
```

#### 14. **theme-factory** - 主题工厂
- **功能**：为工件应用主题样式
- **主要能力**：
  - 应用预设主题（10 个）
  - 生成新主题
  - 样式化幻灯片、文档、报告
  - HTML 登录页面

**使用示例**：
```
使用 theme-factory 技能：为我的演示文稿应用一个专业的蓝色主题。
```

#### 15. **webapp-testing** - Web 应用测试
- **功能**：使用 Playwright 与本地 Web 应用交互和测试
- **主要能力**：
  - 验证前端功能
  - 调试 UI 行为
  - 捕获浏览器截图
  - 查看浏览器日志

**使用示例**：
```
使用 webapp-testing 技能：测试我的 Web 应用的登录功能，并捕获截图。
```

#### 16. **web-artifacts-builder** - Web 工件构建器
- **功能**：使用现代前端技术创建复杂的多组件 HTML 工件
- **主要能力**：
  - React
  - Tailwind CSS
  - shadcn/ui
  - 状态管理
  - 路由

**使用示例**：
```
使用 web-artifacts-builder 技能：创建一个包含多个页面的 React 应用工件。
```

## 💡 使用技巧

### 1. 直接提及技能名称

安装插件后，可以直接在对话中提及技能名称：

```
使用 pdf 技能：从 document.pdf 中提取表单字段。
```

```
使用 docx 技能：创建一个包含标题、段落和列表的新 Word 文档。
```

```
使用 frontend-design 技能：创建一个现代化的登录页面。
```

### 2. 组合使用多个技能

可以组合使用多个技能完成复杂任务：

```
使用 docx 和 pdf 技能：从 PDF 中提取内容，然后创建一个格式化的 Word 文档。
```

### 3. 查看技能文档

每个技能都有详细的 `SKILL.md` 文档，包含：
- 功能概述
- 使用示例
- 最佳实践
- API 参考

## 🔍 技能分类总结

### 文档处理类
- **xlsx** - Excel 电子表格
- **docx** - Word 文档
- **pptx** - PowerPoint 演示文稿
- **pdf** - PDF 文档

### 创意设计类
- **algorithmic-art** - 算法艺术
- **canvas-design** - 画布设计
- **frontend-design** - 前端设计
- **theme-factory** - 主题工厂

### 开发工具类
- **mcp-builder** - MCP 服务器构建
- **skill-creator** - 技能创建
- **webapp-testing** - Web 应用测试
- **web-artifacts-builder** - Web 工件构建

### 企业通信类
- **internal-comms** - 内部通信
- **doc-coauthoring** - 文档协作
- **brand-guidelines** - 品牌指南

### 其他工具类
- **slack-gif-creator** - Slack GIF 创建

## 📖 更多资源

- **GitHub 仓库**: https://github.com/anthropics/skills
- **Agent Skills 规范**: https://agentskills.io
- **Claude 支持文档**:
  - [What are skills?](https://support.claude.com/en/articles/12512176-what-are-skills)
  - [Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
  - [How to create custom skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)
- **Anthropic 工程博客**: [Equipping agents for the real world with Agent Skills](https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

## ⚠️ 重要提示

1. **演示和教育目的**：这些技能主要用于演示和教育目的。虽然某些功能可能在 Claude 中可用，但实际实现和行为可能与技能中显示的不同。

2. **测试技能**：在关键任务中依赖技能之前，请在自己的环境中彻底测试技能。

3. **许可证**：许多技能是开源的（Apache 2.0），但文档创建和编辑技能（docx, pdf, pptx, xlsx）是源代码可用的，不是开源的。

## 🎯 快速开始示例

### 示例 1：处理 Excel 文件
```
使用 xlsx 技能：读取 sales.xlsx 文件，计算每个产品的总销售额，并创建一个新的汇总表格。
```

### 示例 2：创建 Word 文档
```
使用 docx 技能：创建一个包含项目提案的 Word 文档，包括执行摘要、项目目标和时间表。
```

### 示例 3：设计前端界面
```
使用 frontend-design 技能：创建一个响应式的产品展示页面，包含产品卡片、导航栏和页脚。
```

### 示例 4：测试 Web 应用
```
使用 webapp-testing 技能：测试我的 Web 应用的用户注册流程，验证所有表单验证是否正常工作。
```

---

**祝您使用愉快！** 🚀

如有任何问题，请参考相关文档或查看 GitHub Issues。

# Awesome Claude Skills 完整技能列表

本文档列出了 Awesome Claude Skills 仓库中所有可用的技能及其简要描述。

**GitHub 仓库**: https://github.com/ComposioHQ/awesome-claude-skills

## 📋 技能目录

### 📄 文档处理 (5 个技能)

1. **docx** - Word 文档处理
   - 创建、编辑、分析 Word 文档，支持跟踪更改、评论、格式化

2. **pdf** - PDF 文档处理
   - 提取文本、表格、元数据，合并和注释 PDF

3. **pptx** - PowerPoint 演示文稿处理
   - 读取、生成和调整幻灯片、布局、模板

4. **xlsx** - Excel 电子表格处理
   - 电子表格操作：公式、图表、数据转换

5. **Markdown to EPUB Converter** - Markdown 转 EPUB
   - 将 Markdown 文档和聊天摘要转换为专业的 EPUB 电子书文件
   - 作者：@smerchek

### 💻 开发与代码工具 (23 个技能)

6. **artifacts-builder** - 前端构建工具
   - 使用现代前端技术（React、Tailwind CSS、shadcn/ui）创建复杂的多组件 HTML 工件

7. **aws-skills** - AWS 开发技能
   - AWS 开发与 CDK 最佳实践、成本优化 MCP 服务器、无服务器/事件驱动架构模式

8. **Changelog Generator** - 变更日志生成器
   - 通过分析 Git 提交历史，自动创建面向用户的变更日志

9. **Claude Code Terminal Title** - Claude Code 终端标题
   - 为每个 Claude Code 终端窗口提供动态标题，描述正在完成的工作

10. **D3.js Visualization** - D3.js 可视化
    - 教授 Claude 生成 D3 图表和交互式数据可视化
    - 作者：@chrisvoncsefalvay

11. **FFUF Web Fuzzing** - FFUF Web 模糊测试
    - 集成 ffuf web 模糊测试工具，让 Claude 可以运行模糊测试任务并分析漏洞结果
    - 作者：@jthack

12. **finishing-a-development-branch** - 完成开发分支
    - 通过呈现清晰的选项和处理所选工作流来指导开发工作的完成

13. **iOS Simulator** - iOS 模拟器
    - 使 Claude 能够与 iOS 模拟器交互，用于测试和调试 iOS 应用程序
    - 作者：@conorluddy

14. **jules** - Jules AI 代理
    - 将编码任务委托给 Google Jules AI 代理，用于异步错误修复、文档、测试和 GitHub 仓库上的功能实现
    - 作者：@sanjay3290

15. **LangSmith Fetch** - LangSmith 获取
    - 通过自动获取和分析 LangSmith Studio 的执行跟踪来调试 LangChain 和 LangGraph 代理
    - 作者：@OthmanAdi

16. **MCP Builder** - MCP 服务器构建器
    - 指导创建高质量的 MCP（Model Context Protocol）服务器，用于使用 Python 或 TypeScript 将外部 API 和服务与 LLM 集成

17. **move-code-quality-skill** - Move 代码质量
    - 根据官方 Move Book 代码质量检查清单分析 Move 语言包，确保 Move 2024 Edition 合规性和最佳实践

18. **Playwright Browser Automation** - Playwright 浏览器自动化
    - 用于测试和验证 Web 应用程序的模型调用 Playwright 自动化
    - 作者：@lackeyjb

19. **prompt-engineering** - 提示工程
    - 教授著名的提示工程技术和模式，包括 Anthropic 最佳实践和代理说服原则

20. **pypict-claude-skill** - PICT 测试用例设计
    - 使用 PICT（成对独立组合测试）为需求或代码设计全面的测试用例，生成具有成对覆盖率的优化测试套件

21. **reddit-fetch** - Reddit 内容获取
    - 当 WebFetch 被阻止或返回 403 错误时，通过 Gemini CLI 获取 Reddit 内容

22. **Skill Creator** - 技能创建器
    - 提供创建有效 Claude Skills 的指导，扩展具有专业知识、工作流和工具集成的能力

23. **Skill Seekers** - 技能搜索器
    - 自动将任何文档网站转换为 Claude AI 技能，只需几分钟
    - 作者：@yusufkaraaslan

24. **software-architecture** - 软件架构
    - 实现设计模式，包括清洁架构、SOLID 原则和全面的软件设计最佳实践

25. **subagent-driven-development** - 子代理驱动开发
    - 为单个任务分派独立的子代理，在迭代之间进行代码审查检查点，实现快速、受控的开发

26. **test-driven-development** - 测试驱动开发
    - 在实现任何功能或修复错误之前使用，先编写测试

27. **using-git-worktrees** - 使用 Git Worktrees
    - 创建隔离的 git worktrees，具有智能目录选择和安全验证

28. **connect** / **connect-apps** - 连接应用
    - 将 Claude 连接到任何应用。发送电子邮件、创建问题、发布消息、更新数据库 - 在 Gmail、Slack、GitHub、Notion 和 1000+ 服务中执行真实操作

29. **Webapp Testing** - Web 应用测试
    - 使用 Playwright 测试本地 Web 应用程序，验证前端功能、调试 UI 行为并捕获截图

### 📊 数据分析 (4 个技能)

30. **CSV Data Summarizer** - CSV 数据汇总器
    - 自动分析 CSV 文件并生成带有可视化的全面洞察，无需用户提示
    - 作者：@coffeefuelbump

31. **deep-research** - 深度研究
    - 使用 Gemini Deep Research Agent 执行自主多步骤研究，用于市场分析、竞争格局分析和文献综述
    - 作者：@sanjay3290

32. **postgres** - PostgreSQL 数据库
    - 对 PostgreSQL 数据库执行安全的只读 SQL 查询，支持多连接和深度防御安全
    - 作者：@sanjay3290

33. **root-cause-tracing** - 根本原因追踪
    - 当错误在深层执行中发生时使用，需要追溯查找原始触发器

### 💼 商业与营销 (5 个技能)

34. **Brand Guidelines** - 品牌指南
    - 将 Anthropic 官方品牌颜色和排版应用于工件，实现一致的视觉识别和专业设计标准

35. **Competitive Ads Extractor** - 竞争广告提取器
    - 从广告库中提取和分析竞争对手的广告，了解引起共鸣的消息和创意方法

36. **Domain Name Brainstormer** - 域名头脑风暴
    - 生成创意域名想法并检查多个 TLD 的可用性，包括 .com、.io、.dev 和 .ai 扩展名

37. **Internal Comms** - 内部通信
    - 帮助编写内部通信，包括 3P 更新、公司通讯、常见问题、状态报告和项目更新，使用公司特定格式

38. **Lead Research Assistant** - 潜在客户研究助手
    - 通过分析您的产品、搜索目标公司并提供可操作的拓展策略来识别和评估高质量潜在客户

### ✍️ 沟通与写作 (7 个技能)

39. **article-extractor** - 文章提取器
    - 从网页中提取完整文章文本和元数据

40. **brainstorming** - 头脑风暴
    - 通过结构化提问和替代探索，将粗略想法转化为完整设计

41. **Content Research Writer** - 内容研究写作
    - 通过进行研究、添加引用、改进钩子和提供逐节反馈来协助撰写高质量内容

42. **family-history-research** - 家族历史研究
    - 为规划家族历史和家谱研究项目提供帮助

43. **Meeting Insights Analyzer** - 会议洞察分析器
    - 分析会议记录以发现行为模式，包括冲突回避、发言比例、填充词和领导风格

44. **NotebookLM Integration** - NotebookLM 集成
    - 让 Claude Code 直接与 NotebookLM 聊天，基于上传的文档提供源基础答案
    - 作者：@PleasePrompto

45. **Twitter Algorithm Optimizer** - Twitter 算法优化器
    - 使用 Twitter 开源算法洞察分析和优化推文以获得最大覆盖范围。重写和编辑推文以提高参与度和可见性

### 🎨 创意与媒体 (7 个技能)

46. **Canvas Design** - 画布设计
    - 使用设计哲学和美学原则在 PNG 和 PDF 文档中创建美丽的视觉艺术，用于海报、设计和静态作品

47. **imagen** - 图像生成
    - 使用 Google Gemini 的图像生成 API 生成图像，用于 UI  mockup、图标、插图和视觉资产
    - 作者：@sanjay3290

48. **Image Enhancer** - 图像增强器
    - 通过提高分辨率、锐度和清晰度来改善图像和截图质量，用于专业演示和文档

49. **Slack GIF Creator** - Slack GIF 创建器
    - 创建针对 Slack 优化的动画 GIF，具有大小约束验证器和可组合动画原语

50. **Theme Factory** - 主题工厂
    - 将专业字体和颜色主题应用于工件，包括幻灯片、文档、报告和 HTML 登录页面，提供 10 个预设主题

51. **Video Downloader** - 视频下载器
    - 从 YouTube 和其他平台下载视频，支持离线观看、编辑或归档，支持各种格式和质量选项

52. **youtube-transcript** - YouTube 转录
    - 从 YouTube 视频获取转录并准备摘要

### 📁 生产力与组织 (8 个技能)

53. **File Organizer** - 文件组织器
    - 通过理解上下文、查找重复项和建议更好的组织结构来智能组织文件和文件夹

54. **Invoice Organizer** - 发票组织器
    - 通过读取文件、提取信息和一致重命名来自动组织发票和收据以进行税务准备

55. **kaizen** - 持续改进
    - 应用持续改进方法论，具有多种分析方法，基于日本 Kaizen 哲学和精益方法论

56. **n8n-skills** - n8n 技能
    - 使 AI 助手能够直接理解和操作 n8n 工作流

57. **Raffle Winner Picker** - 抽奖获胜者选择器
    - 从列表、电子表格或 Google Sheets 中随机选择获胜者，用于赠品和竞赛，使用加密安全的随机性

58. **Tailored Resume Generator** - 定制简历生成器
    - 分析工作描述并生成定制简历，突出相关经验、技能和成就，以最大化面试机会

59. **ship-learn-next** - 下一步构建或学习
    - 基于反馈循环帮助迭代下一步要构建或学习的内容的技能

60. **tapestry** - 知识网络
    - 将相关文档互连并总结为知识网络

### 🤝 协作与项目管理 (5 个技能)

61. **git-pushing** - Git 推送
    - 自动化 Git 操作和仓库交互

62. **google-workspace-skills** - Google Workspace 技能
    - Google Workspace 集成套件：Gmail、Calendar、Chat、Docs、Sheets、Slides 和 Drive，支持跨平台 OAuth
    - 作者：@sanjay3290

63. **outline** - Outline 集成
    - 在 Outline wiki 实例（云或自托管）中搜索、读取、创建和管理文档
    - 作者：@sanjay3290

64. **review-implementing** - 审查实现
    - 评估代码实现计划并与规范对齐

65. **test-fixing** - 测试修复
    - 检测失败的测试并提出补丁或修复

### 🔒 安全与系统 (4 个技能)

66. **computer-forensics** - 计算机取证
    - 数字取证分析和调查技术

67. **file-deletion** - 文件删除
    - 安全文件删除和数据清理方法

68. **metadata-extraction** - 元数据提取
    - 提取和分析文件元数据用于取证目的

69. **threat-hunting-with-sigma-rules** - 使用 Sigma 规则进行威胁狩猎
    - 使用 Sigma 检测规则来狩猎威胁和分析安全事件

## 📊 统计信息

- **总技能数**: 69 个
- **文档处理**: 5 个
- **开发与代码工具**: 23 个
- **数据分析**: 4 个
- **商业与营销**: 5 个
- **沟通与写作**: 7 个
- **创意与媒体**: 7 个
- **生产力与组织**: 8 个
- **协作与项目管理**: 5 个
- **安全与系统**: 4 个

## 🎯 快速查找技能

### 按使用场景查找

**文档处理**
- 需要处理 Word 文档？ → **docx**
- 需要处理 PDF？ → **pdf**
- 需要创建演示文稿？ → **pptx**
- 需要处理 Excel？ → **xlsx**
- 需要转换电子书？ → **Markdown to EPUB Converter**

**开发工作**
- 需要创建前端应用？ → **artifacts-builder**
- 需要生成变更日志？ → **Changelog Generator**
- 需要测试 Web 应用？ → **Webapp Testing** 或 **Playwright Browser Automation**
- 需要测试驱动开发？ → **test-driven-development**
- 需要设计架构？ → **software-architecture**

**数据分析**
- 需要分析 CSV？ → **CSV Data Summarizer**
- 需要深度研究？ → **deep-research**
- 需要查询数据库？ → **postgres**

**内容创作**
- 需要撰写内容？ → **Content Research Writer**
- 需要优化推文？ → **Twitter Algorithm Optimizer**
- 需要创建设计？ → **Canvas Design** 或 **Theme Factory**

**生产力工具**
- 需要整理文件？ → **File Organizer**
- 需要整理发票？ → **Invoice Organizer**
- 需要生成简历？ → **Tailored Resume Generator**

**自动化**
- 需要连接多个应用？ → **connect-apps**
- 需要自动化工作流？ → **n8n-skills**

## 📚 如何使用

1. **查看安装指南**: 参考 `.cursor/awesome-claude-skills-setup.md`
2. **选择需要的技能**: 从上面的列表中选择
3. **安装技能**: 按照安装指南中的步骤操作
4. **使用技能**: 在 Claude Code 中直接描述任务，Claude 会自动激活相关技能

## 🔗 相关资源

- **GitHub 仓库**: https://github.com/ComposioHQ/awesome-claude-skills
- **官方文档**: https://docs.anthropic.com/claude/docs/skills
- **技能市场**: https://claude.ai/skills
- **社区讨论**: https://community.anthropic.com/

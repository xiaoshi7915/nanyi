# UI UX Pro Max Skill 安装和使用指南

## 📋 概述

**UI UX Pro Max** 是一个强大的 UI/UX 设计智能助手技能，提供专业的设计智能，帮助构建跨多个平台和框架的专业 UI/UX。

**GitHub 仓库**: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill

## ✨ 主要特性

### v2.0 新功能：智能设计系统生成器

- **自动设计系统生成**: AI 驱动的推理引擎，分析项目需求并生成完整的定制设计系统
- **100 个行业特定推理规则**: 涵盖科技、金融、医疗、电商、服务、创意等多个行业
- **多域搜索**: 5 个并行搜索（产品类型、风格推荐、颜色调色板、着陆页模式、字体配对）

### 核心功能

- **67 种 UI 风格**: Glassmorphism、Claymorphism、Minimalism、Brutalism、Neumorphism、Bento Grid、Dark Mode、AI-Native UI 等
- **96 种颜色调色板**: 行业特定的调色板（SaaS、电商、医疗、金融科技、美容等）
- **56 种字体配对**: 精选的字体组合，包含 Google Fonts 导入
- **25 种图表类型**: 仪表盘和分析推荐
- **13 种技术栈**: React、Next.js、Astro、Vue、Nuxt.js、Nuxt UI、Svelte、SwiftUI、React Native、Flutter、HTML+Tailwind、shadcn/ui、Jetpack Compose
- **98 条 UX 指南**: 最佳实践、反模式和无障碍规则
- **100 个推理规则**: 行业特定的设计系统生成（v2.0 新增）

## ✅ 安装状态

**已成功安装为全局技能！**

- **安装位置**: `~/.config/claude-code/skills/ui-ux-pro-max/`
- **安装方式**: 使用 uipro-cli 工具安装
- **状态**: ✅ 已激活

## 🚀 使用方法

### 在 Claude Code 中使用

技能会自动激活，只需自然对话即可：

```
构建一个 SaaS 产品的着陆页

为我的电商网站设计一个仪表盘

创建一个带有暗色主题的金融科技银行应用

设计一个移动应用的 UI
```

### 支持的提示词示例

```
构建一个 SaaS 产品的着陆页

创建医疗分析仪表盘

设计带有暗色模式的组合网站

制作电商移动应用 UI

构建带有暗色主题的金融科技银行应用
```

### 高级功能：设计系统生成器

#### 生成设计系统（命令行）

```bash
# 生成设计系统（ASCII 输出）
python3 ~/.config/claude-code/skills/ui-ux-pro-max/scripts/search.py "beauty spa wellness" --design-system -p "Serenity Spa"

# 生成 Markdown 输出
python3 ~/.config/claude-code/skills/ui-ux-pro-max/scripts/search.py "fintech banking" --design-system -f markdown

# 域特定搜索
python3 ~/.config/claude-code/skills/ui-ux-pro-max/scripts/search.py "glassmorphism" --domain style
python3 ~/.config/claude-code/skills/ui-ux-pro-max/scripts/search.py "elegant serif" --domain typography
python3 ~/.config/claude-code/skills/ui-ux-pro-max/scripts/search.py "dashboard" --domain chart

# 技术栈特定指南
python3 ~/.config/claude-code/skills/ui-ux-pro-max/scripts/search.py "form validation" --stack react
python3 ~/.config/claude-code/skills/ui-ux-pro-max/scripts/search.py "responsive layout" --stack html-tailwind
```

#### 持久化设计系统（Master + Overrides 模式）

保存设计系统到文件，实现跨会话的分层检索：

```bash
# 生成并保存到 design-system/MASTER.md
python3 ~/.config/claude-code/skills/ui-ux-pro-max/scripts/search.py "SaaS dashboard" --design-system --persist -p "MyApp"

# 创建页面特定的覆盖文件
python3 ~/.config/claude-code/skills/ui-ux-pro-max/scripts/search.py "SaaS dashboard" --design-system --persist -p "MyApp" --page "dashboard"
```

这会创建以下文件结构：

```
design-system/
├── MASTER.md           # 全局源（颜色、字体、间距、组件）
└── pages/
    └── dashboard.md    # 页面特定覆盖（仅与 Master 的偏差）
```

## 🎨 支持的 UI 风格（67 种）

### 通用风格（49 种）

1. Minimalism & Swiss Style - 企业应用、仪表盘、文档
2. Neumorphism - 健康/健康应用、冥想平台
3. Glassmorphism - 现代 SaaS、金融仪表盘
4. Brutalism - 设计组合、艺术项目
5. 3D & Hyperrealism - 游戏、产品展示、沉浸式体验
6. Vibrant & Block-based - 初创公司、创意机构、游戏
7. Dark Mode (OLED) - 夜间模式应用、编码平台
8. Accessible & Ethical - 政府、医疗、教育
9. Claymorphism - 教育应用、儿童应用、SaaS
10. Aurora UI - 现代 SaaS、创意机构
... 以及更多

### 着陆页风格（8 种）

1. Hero-Centric Design - 具有强烈视觉识别的产品
2. Conversion-Optimized - 潜在客户生成、销售页面
3. Feature-Rich Showcase - SaaS、复杂产品
4. Minimal & Direct - 简单产品、应用
5. Social Proof-Focused - 服务、B2C 产品
6. Interactive Product Demo - 软件、工具
7. Trust & Authority - B2B、企业、咨询
8. Storytelling-Driven - 品牌、机构、非营利组织

### BI/分析仪表盘风格（10 种）

1. Data-Dense Dashboard - 复杂数据分析
2. Heat Map & Heatmap Style - 地理/行为数据
3. Executive Dashboard - C 级摘要
4. Real-Time Monitoring - 运营、DevOps
5. Drill-Down Analytics - 详细探索
6. Comparative Analysis Dashboard - 并排比较
7. Predictive Analytics - 预测、ML 洞察
8. User Behavior Analytics - UX 研究、产品分析
9. Financial Dashboard - 金融、会计
10. Sales Intelligence Dashboard - 销售团队、CRM

## 🎨 支持的技术栈

| 类别 | 技术栈 |
|------|--------|
| **Web (HTML)** | HTML + Tailwind (默认) |
| **React 生态系统** | React, Next.js, shadcn/ui |
| **Vue 生态系统** | Vue, Nuxt.js, Nuxt UI |
| **其他 Web** | Svelte, Astro |
| **iOS** | SwiftUI |
| **Android** | Jetpack Compose |
| **跨平台** | React Native, Flutter |

只需在提示中提及您偏好的技术栈，或让它默认为 HTML + Tailwind。

## 🔧 工作原理

1. **您提问** - 请求任何 UI/UX 任务（构建、设计、创建、实现、审查、修复、改进）
2. **设计系统生成** - AI 自动使用推理引擎生成完整的设计系统
3. **智能推荐** - 根据您的产品类型和需求，找到最佳匹配的风格、颜色和字体
4. **代码生成** - 使用适当的颜色、字体、间距和最佳实践实现 UI
5. **交付前检查** - 针对常见的 UI/UX 反模式进行验证

## 📚 行业特定推理规则

推理引擎包含以下类别的专门规则：

| 类别 | 示例 |
|------|------|
| **科技与 SaaS** | SaaS、微 SaaS、B2B 企业、开发者工具、AI/聊天机器人平台 |
| **金融** | 金融科技、银行、加密货币、保险、交易仪表盘 |
| **医疗** | 医疗诊所、药房、牙科、兽医、心理健康 |
| **电商** | 通用、奢侈品、市场、订阅盒 |
| **服务** | 美容/水疗、餐厅、酒店、法律、咨询 |
| **创意** | 组合、机构、摄影、游戏、音乐流媒体 |
| **新兴科技** | Web3/NFT、空间计算、量子计算、自主系统 |

每个规则包括：
- **推荐模式** - 着陆页结构
- **风格优先级** - 最佳匹配的 UI 风格
- **颜色情绪** - 适合行业的调色板
- **字体情绪** - 匹配的字体个性
- **关键效果** - 动画和交互
- **反模式** - 不应该做什么（例如，银行应用避免"AI 紫色/粉色渐变"）

## 🔄 更新技能

### 使用 CLI 更新

```bash
uipro update
```

### 手动更新

```bash
cd ~/.config/claude-code/skills/ui-ux-pro-max
git pull  # 如果是从仓库克隆的
```

## 📖 相关资源

- **GitHub 仓库**: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- **官方网站**: https://ui-ux-pro-max-skill.nextlevelbuilder.io
- **CLI 工具**: `uipro-cli` (已安装)

## 💡 使用建议

1. **明确产品类型**: 在提示中明确说明您的产品类型（SaaS、电商、医疗等），以获得最佳推荐
2. **指定技术栈**: 如果您有偏好的技术栈，在提示中提及
3. **使用设计系统生成器**: 对于大型项目，使用设计系统生成器创建一致的设计系统
4. **持久化设计系统**: 使用 `--persist` 选项保存设计系统，实现跨会话的一致性

## 🐛 故障排除

### 问题 1：技能未激活

**解决方案：**
- 确保技能已正确安装到 `~/.config/claude-code/skills/ui-ux-pro-max/`
- 检查 `SKILL.md` 文件是否存在
- 重启 Claude Code

### 问题 2：Python 脚本无法运行

**解决方案：**
- 确保已安装 Python 3.x: `python3 --version`
- 检查脚本权限: `chmod +x ~/.config/claude-code/skills/ui-ux-pro-max/scripts/search.py`

### 问题 3：设计系统生成失败

**解决方案：**
- 检查网络连接（需要访问 GitHub 获取数据）
- 确保 Python 依赖已安装
- 查看错误消息以获取更多信息

---

**提示**: 此技能会自动激活，只需在对话中描述您的 UI/UX 需求即可。技能会根据您的需求自动选择合适的风格、颜色和字体。

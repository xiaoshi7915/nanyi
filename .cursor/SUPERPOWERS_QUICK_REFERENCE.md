# Superpowers 快速参考

## 🚀 核心工作流程

```
用户请求 → brainstorming → using-git-worktrees → writing-plans 
→ subagent-driven-development → test-driven-development 
→ requesting-code-review → finishing-a-development-branch
```

## 📋 14 个技能速查表

### 🧪 测试
- **test-driven-development** - RED-GREEN-REFACTOR 循环

### 🐛 调试
- **systematic-debugging** - 4 阶段根本原因分析
- **verification-before-completion** - 完成前验证

### 🤝 协作
- **brainstorming** - 设计完善（在编写代码前必须使用）
- **writing-plans** - 详细实施计划
- **executing-plans** - 分批执行，带检查点
- **subagent-driven-development** - 子代理驱动开发（推荐）
- **dispatching-parallel-agents** - 并行代理工作流
- **requesting-code-review** - 请求代码审查
- **receiving-code-review** - 接收代码审查
- **using-git-worktrees** - Git Worktrees（隔离分支）
- **finishing-a-development-branch** - 完成开发分支

### 📖 元技能
- **using-superpowers** - 技能系统介绍
- **writing-skills** - 创建新技能

## 💡 使用示例

### 构建新功能
```
我想添加用户登录功能
```
→ 自动触发完整工作流

### 修复错误
```
这个功能不工作了，帮我修复
```
→ 自动触发 systematic-debugging

### 代码审查
```
审查这段代码
```
→ 自动触发 requesting-code-review

## 🎯 关键原则

1. **技能自动触发** - 无需手动调用
2. **测试先行** - TDD 是强制性的
3. **系统化流程** - 遵循完整工作流
4. **证据优于声明** - 验证后再声明成功

## 📚 详细文档

- **完整指南**: `.cursor/superpowers-setup.md`
- **GitHub**: https://github.com/obra/superpowers

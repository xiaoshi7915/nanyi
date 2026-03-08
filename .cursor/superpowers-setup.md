# Superpowers 安装和使用指南

## 📋 概述

**Superpowers** 是一个完整的软件开发工作流框架，为您的编码代理构建，基于一组可组合的"技能"和确保代理使用它们的初始指令。

**GitHub 仓库**: https://github.com/obra/superpowers

## ✨ 核心理念

Superpowers 不是简单的代码生成工具，而是一个完整的软件开发方法论：

- **测试驱动开发 (TDD)** - 始终先写测试
- **系统化而非临时** - 流程优先于猜测
- **复杂性降低** - 简单性作为主要目标
- **证据优于声明** - 在声明成功之前验证

## ✅ 安装状态

**已成功安装为全局技能！**

- **安装位置**: `~/.config/claude-code/skills/`
- **技能数量**: 14 个核心技能
- **状态**: ✅ 已激活

## 🎯 基本工作流程

Superpowers 的工作流程是自动触发的，当您开始构建某些东西时，代理不会直接跳入编写代码，而是：

1. **brainstorming** - 在编写代码之前激活。通过提问完善粗略想法，探索替代方案，分部分呈现设计以供验证。保存设计文档。

2. **using-git-worktrees** - 设计批准后激活。在新分支上创建隔离的工作空间，运行项目设置，验证干净的测试基线。

3. **writing-plans** - 设计批准后激活。将工作分解为小块任务（每个 2-5 分钟）。每个任务都有确切的文件路径、完整代码、验证步骤。

4. **subagent-driven-development** 或 **executing-plans** - 计划激活后执行。为每个任务分派新的子代理，进行两阶段审查（规范合规性，然后代码质量），或分批执行并有人工检查点。

5. **test-driven-development** - 实施期间激活。强制执行 RED-GREEN-REFACTOR：编写失败测试，观察失败，编写最小代码，观察通过，提交。删除在测试之前编写的代码。

6. **requesting-code-review** - 任务之间激活。对照计划审查，按严重程度报告问题。关键问题阻止进度。

7. **finishing-a-development-branch** - 任务完成时激活。验证测试，呈现选项（合并/PR/保留/丢弃），清理工作树。

**代理在执行任何任务之前都会检查相关技能。** 这是强制性的工作流，不是建议。

## 📚 技能库（14 个技能）

### 🧪 测试技能

#### 1. **test-driven-development** - 测试驱动开发
- **功能**: RED-GREEN-REFACTOR 循环（包含测试反模式参考）
- **使用时机**: 在实施功能时自动激活
- **核心原则**: 
  - 先写失败测试
  - 观察测试失败
  - 编写最小代码使其通过
  - 观察测试通过
  - 提交
  - 删除在测试之前编写的代码

**使用示例**:
```
我要添加用户登录功能
```
→ 自动激活 TDD，先编写测试，然后实现功能

---

### 🐛 调试技能

#### 2. **systematic-debugging** - 系统化调试
- **功能**: 4 阶段根本原因分析过程
- **包含技术**: 
  - root-cause-tracing（根本原因追踪）
  - defense-in-depth（深度防御）
  - condition-based-waiting（基于条件的等待）
- **使用时机**: 遇到错误或问题时自动激活

**使用示例**:
```
这个功能不工作了，帮我修复
```
→ 自动激活系统化调试，进行 4 阶段分析

#### 3. **verification-before-completion** - 完成前验证
- **功能**: 确保问题真正被修复
- **使用时机**: 修复问题后自动验证

---

### 🤝 协作技能

#### 4. **brainstorming** - 头脑风暴
- **功能**: 苏格拉底式设计完善
- **使用时机**: 在编写代码之前自动激活
- **流程**:
  1. 理解当前项目状态
  2. 一次一个问题地提问以完善想法
  3. 探索 2-3 种不同方法
  4. 分部分呈现设计（每部分 200-300 字）
  5. 保存设计文档到 `docs/plans/YYYY-MM-DD-<topic>-design.md`

**使用示例**:
```
我想构建一个待办事项应用
```
→ 自动激活头脑风暴，通过提问完善设计

#### 5. **writing-plans** - 编写计划
- **功能**: 详细的实施计划
- **使用时机**: 设计批准后自动激活
- **特点**: 
  - 将工作分解为小块任务（每个 2-5 分钟）
  - 每个任务包含：确切文件路径、完整代码、验证步骤
  - 强调真正的红/绿 TDD、YAGNI、DRY

**使用示例**:
```
设计已完成，创建实施计划
```
→ 自动生成详细的实施计划

#### 6. **executing-plans** - 执行计划
- **功能**: 分批执行，带检查点
- **使用时机**: 有实施计划时，需要人工检查点

#### 7. **subagent-driven-development** - 子代理驱动开发
- **功能**: 快速迭代，两阶段审查（规范合规性，然后代码质量）
- **使用时机**: 执行实施计划，任务相对独立，在当前会话中
- **流程**:
  1. 为每个任务分派新的实现者子代理
  2. 实现者实现、测试、提交、自我审查
  3. 分派规范审查者子代理（检查是否符合规范）
  4. 分派代码质量审查者子代理（检查代码质量）
  5. 如果通过，继续下一个任务；如果失败，修复并重新审查

**使用示例**:
```
执行这个实施计划
```
→ 自动使用子代理驱动开发，逐个完成任务

#### 8. **dispatching-parallel-agents** - 分派并行代理
- **功能**: 并发子代理工作流
- **使用时机**: 有多个可以并行执行的任务

#### 9. **requesting-code-review** - 请求代码审查
- **功能**: 审查前检查清单
- **使用时机**: 任务之间自动激活
- **流程**: 对照计划审查，按严重程度报告问题

#### 10. **receiving-code-review** - 接收代码审查
- **功能**: 响应反馈
- **使用时机**: 收到代码审查反馈时

#### 11. **using-git-worktrees** - 使用 Git Worktrees
- **功能**: 并行开发分支
- **使用时机**: 设计批准后自动激活
- **流程**: 在新分支上创建隔离工作空间，运行项目设置，验证干净的测试基线

#### 12. **finishing-a-development-branch** - 完成开发分支
- **功能**: 合并/PR 决策工作流
- **使用时机**: 任务完成时自动激活
- **流程**: 验证测试，呈现选项（合并/PR/保留/丢弃），清理工作树

---

### 📖 元技能

#### 13. **using-superpowers** - 使用 Superpowers
- **功能**: 技能系统介绍
- **核心规则**: 
  - 如果认为有 1% 的机会技能可能适用，**必须**调用技能
  - 在响应或操作之前调用相关或请求的技能
  - 技能检查在澄清问题之前进行

#### 14. **writing-skills** - 编写技能
- **功能**: 遵循最佳实践创建新技能（包含测试方法论）
- **使用时机**: 需要创建新技能时

---

## 🚀 如何使用

### 自动激活（推荐）

Superpowers 的技能是**自动触发**的，您不需要做任何特殊操作。只需正常与 Claude 对话：

```
我想构建一个待办事项应用
```

Claude 会自动：
1. 激活 `brainstorming` 技能，通过提问完善设计
2. 激活 `using-git-worktrees` 创建隔离分支
3. 激活 `writing-plans` 创建实施计划
4. 激活 `subagent-driven-development` 执行计划
5. 激活 `test-driven-development` 确保测试先行
6. 激活 `requesting-code-review` 进行代码审查
7. 激活 `finishing-a-development-branch` 完成分支

### 手动触发（高级）

如果需要手动触发特定技能，可以在对话中明确提及：

```
使用 brainstorming 技能帮我设计一个用户认证系统

使用 systematic-debugging 技能修复这个错误

使用 test-driven-development 技能添加这个功能
```

### 查看可用命令

在 Claude Code 中，运行：

```
/help
```

应该看到：
```
/superpowers:brainstorm - Interactive design refinement
/superpowers:write-plan - Create implementation plan
/superpowers:execute-plan - Execute plan in batches
```

## 💡 使用示例

### 示例 1：构建新功能

**用户**: "我想添加用户登录功能"

**自动流程**:
1. `brainstorming` 激活 → 提问完善需求
2. 设计文档保存到 `docs/plans/`
3. `using-git-worktrees` 激活 → 创建隔离分支
4. `writing-plans` 激活 → 创建详细计划
5. `subagent-driven-development` 激活 → 执行计划
6. `test-driven-development` 激活 → 每个任务先写测试
7. `requesting-code-review` 激活 → 代码审查
8. `finishing-a-development-branch` 激活 → 完成分支

### 示例 2：修复错误

**用户**: "这个功能不工作了，帮我修复"

**自动流程**:
1. `systematic-debugging` 激活 → 4 阶段根本原因分析
2. `verification-before-completion` 激活 → 验证修复

### 示例 3：代码审查

**用户**: "审查这段代码"

**自动流程**:
1. `requesting-code-review` 激活 → 对照计划审查
2. 按严重程度报告问题

## 🔄 更新技能

技能会自动更新，当您更新插件时：

```bash
/plugin update superpowers
```

或者手动更新仓库：

```bash
cd ~/.config/claude-code/skills/
# 每个技能都是独立的，可以单独更新
cd brainstorming && git pull
```

## 📖 技能优先级

当多个技能可能适用时，使用此顺序：

1. **流程技能优先**（brainstorming, debugging）- 这些决定如何接近任务
2. **实施技能其次**（frontend-design, mcp-builder）- 这些指导执行

示例：
- "让我们构建 X" → 先 brainstorming，然后实施技能
- "修复这个错误" → 先 debugging，然后领域特定技能

## 🎯 技能类型

**严格型**（TDD, debugging）：严格遵循。不要偏离纪律。

**灵活型**（patterns）：根据上下文调整原则。

技能本身会告诉您是哪一种。

## 📚 相关资源

- **GitHub 仓库**: https://github.com/obra/superpowers
- **博客文章**: https://blog.fsck.com/2025/10/09/superpowers/
- **问题反馈**: https://github.com/obra/superpowers/issues
- **市场**: https://github.com/obra/superpowers-marketplace

## 🐛 故障排除

### 问题 1：技能未自动激活

**解决方案**:
- 确保技能已正确安装到 `~/.config/claude-code/skills/`
- 检查 `SKILL.md` 文件是否存在
- 重启 Claude Code
- 技能会在相关任务时自动激活，无需手动触发

### 问题 2：工作流程不符合预期

**解决方案**:
- Superpowers 强调流程和纪律
- 如果感觉"太正式"，这正是 Superpowers 的设计理念
- 遵循流程会带来更好的代码质量

### 问题 3：想跳过某些步骤

**解决方案**:
- Superpowers 的技能是强制性的工作流
- 如果确实需要跳过，可以在对话中明确说明
- 但建议遵循完整流程以获得最佳结果

## 💡 最佳实践

1. **信任流程**: Superpowers 的流程是经过验证的，遵循它会带来更好的结果
2. **不要跳过步骤**: 每个步骤都有其目的，跳过可能导致问题
3. **让技能自动工作**: 不需要手动触发，技能会在适当时机自动激活
4. **阅读设计文档**: 设计文档保存在 `docs/plans/`，定期查看以保持一致性
5. **使用 Git Worktrees**: 每个功能都在隔离分支上开发，保持主分支清洁

---

**提示**: Superpowers 是一个完整的软件开发方法论，不是简单的代码生成工具。遵循其流程会带来更高质量、更可维护的代码。

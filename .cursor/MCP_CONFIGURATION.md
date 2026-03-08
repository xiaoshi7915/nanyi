# MCP 服务器配置指南

## 📋 概述

本文档说明如何在 Cursor IDE 中配置 Claude Scientific Skills 的 MCP 服务器。

## 🔧 配置方法

### 方法一：通过 Cursor 设置界面（推荐）

1. **打开 Cursor 设置**
   - 按 `Ctrl+,` (Windows/Linux) 或 `Cmd+,` (macOS)
   - 或者点击菜单：`File` → `Preferences` → `Settings`

2. **搜索 MCP**
   - 在设置搜索框中输入 "MCP" 或 "Model Context Protocol"

3. **添加 MCP 服务器**
   - 找到 "MCP Servers" 或 "Model Context Protocol Servers" 配置项
   - 点击 "Edit in settings.json" 或直接编辑 JSON 配置

4. **添加配置**
   在配置文件中添加以下内容：

```json
{
  "mcpServers": {
    "claude-scientific-skills": {
      "url": "https://mcp.k-dense.ai/claude-scientific-skills/mcp"
    }
  }
}
```

### 方法二：直接编辑配置文件

#### Linux 系统
配置文件位置：
```
~/.config/Code/User/globalStorage/tencent-cloud.coding-copilot/settings/Craft_mcp_settings.json
```

或者项目级别的配置：
```
项目根目录/.cursor/mcp.json
```

#### macOS 系统
```
~/Library/Application Support/Code/User/globalStorage/tencent-cloud.coding-copilot/settings/Craft_mcp_settings.json
```

#### Windows 系统
```
%APPDATA%\Code\User\globalStorage\tencent-cloud.coding-copilot\settings\Craft_mcp_settings.json
```

### 方法三：使用一键安装链接

访问以下链接进行一键安装：
```
https://cursor.com/en-US/install-mcp?name=claude-scientific-skills&config=eyJ1cmwiOiJodHRwczovL21jcC5rLWRlbnNlLmFpL2NsYXVkZS1zY2llbnRpZmljLXNraWxscy9tY3AifQ%3D%3D
```

## 📝 完整配置示例

```json
{
  "mcpServers": {
    "claude-scientific-skills": {
      "url": "https://mcp.k-dense.ai/claude-scientific-skills/mcp",
      "description": "140 scientific skills for Claude AI covering biology, chemistry, medicine, and more"
    }
  }
}
```

## ✅ 验证配置

配置完成后，可以通过以下方式验证：

1. **重启 Cursor IDE**
   - 完全关闭并重新打开 Cursor

2. **检查 MCP 服务器状态**
   - 在 Cursor 中，查看 MCP 服务器连接状态
   - 应该能看到 "claude-scientific-skills" 服务器已连接

3. **测试技能**
   - 尝试使用一个简单的科学技能
   - 例如：查询 PubMed 数据库或使用 BioPython 处理序列

## 🔍 查看可用技能

配置成功后，你可以：

1. **查看技能列表**
   - 参考 `.cursor/claude-scientific-skills-list.md` 文件
   - 查看所有 140 个可用技能

2. **查看技能文档**
   - 每个技能都有详细的 `SKILL.md` 文档
   - 在 GitHub 仓库中查看：https://github.com/K-Dense-AI/claude-scientific-skills

3. **使用技能**
   - 在对话中直接描述你的科学任务
   - Claude 会自动选择合适的技能来执行

## 🐛 故障排除

### 问题 1：MCP 服务器无法连接

**解决方案：**
- 检查网络连接
- 验证 URL 是否正确：`https://mcp.k-dense.ai/claude-scientific-skills/mcp`
- 检查防火墙设置
- 尝试使用代理（如果需要）

### 问题 2：技能未显示

**解决方案：**
- 确保已正确配置 MCP 服务器
- 重启 Cursor IDE
- 检查 MCP 服务器连接状态
- 查看 Cursor 的日志文件

### 问题 3：技能执行失败

**解决方案：**
- 检查 Python 环境是否正确配置
- 确保已安装所需的 Python 包
- 查看错误消息以获取更多信息
- 参考特定技能的 `SKILL.md` 文档

## 📚 相关文档

- **安装指南**: `.cursor/claude-scientific-skills-setup.md`
- **技能列表**: `.cursor/claude-scientific-skills-list.md`
- **GitHub 仓库**: https://github.com/K-Dense-AI/claude-scientific-skills
- **官方文档**: https://github.com/K-Dense-AI/claude-scientific-skills/tree/main/docs

## 💡 使用建议

1. **从简单开始**：先尝试使用一些简单的数据库查询技能
2. **查看示例**：参考 GitHub 仓库中的示例工作流
3. **组合使用**：多个技能可以组合使用完成复杂任务
4. **阅读文档**：每个技能都有详细的文档和示例代码

## 🔄 更新配置

如果需要更新或修改配置：

1. 编辑配置文件（参考上面的位置）
2. 保存更改
3. 重启 Cursor IDE
4. 验证新配置是否生效

## 📞 获取帮助

如果遇到问题：

1. 查看故障排除部分
2. 查看 GitHub Issues：https://github.com/K-Dense-AI/claude-scientific-skills/issues
3. 查看官方文档
4. 联系 K-Dense 支持团队

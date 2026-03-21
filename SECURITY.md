# 安全说明

## 环境变量与密钥

- **切勿**将包含真实密码、API Key、OSS Secret 的 `.env` 文件提交到 Git。仓库中仅保留 `.env.example` 作为模板。
- 若密钥曾出现在版本库、截图或共享环境中，视为已泄露，须尽快**轮换**：
  - MySQL：修改 `DB_USER` 对应账号密码或新建账号并更新 `.env`。
  - 阿里云 OSS：在控制台轮换 `OSS_ACCESS_KEY_ID` / `OSS_ACCESS_KEY_SECRET`。
  - 火山方舟：`ARK_API_KEY` 在控制台作废并新建。
  - Flask：`SECRET_KEY` 使用强随机串替换（轮换后已登录会话会失效）。

## 试衣任务 `access_token`

- `POST /api/try-on/start` 返回的 `access_token` 仅用于同一浏览器会话内查询 `GET /api/try-on/status/<task_id>` 与 SSE `GET /api/try-on/stream/<task_id>`，勿写入可公开分享的链接或日志。

## 报告问题

发现新的安全问题请通过私有渠道联系维护者，勿在公开 issue 中粘贴密钥或完整 `.env`。

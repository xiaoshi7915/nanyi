# 南意秋棠 · 微信小程序 Code Review 报告

## 修复状态（2026-09-30 · 仅小程序端）

| 项 | 状态 | 说明 |
| --- | --- | --- |
| P0-1 微信登录接口缺失 | **需后端** + **已修(MP)** | 未实现后端接口；小程序降级提示改为明确引导手机号登录，「我的」增加备用入口；文档已写依赖 |
| P0-2 注册 phone 契约 | **已修(MP)** | `pages/login` + `utils/auth` 改为手机号注册；登录兼容 account/phone/email；找回密码仍用邮箱 |
| P0-3 touristappid | **文档已补** | 仍为占位（不编造 AppID）；`project.config.json` / README / `发布上架指南.md` 标明替换步骤 |
| P1-1 点赞 | **已修(MP)** | 对接 `GET/POST /api/like/card/{brand}` |
| P1-2 评价 | **已修(MP)** | 详情页评价列表+提交；`to=comment` 滚动定位；提交默认带 JWT |
| P1-3 「已同步」文案 | **已修(MP)** | 改为本机保存口径 |
| P1-4 试穿 token Query | **已修(MP)** | **保持 query**（后端只认）；本地任务态增加过期丢弃，缩小明文窗口 |
| P1-5 环境写死 | **已修(MP)** | `config.js` 支持 `prod`/`dev`，**默认 prod** |
| P2-1 英文副标 / 免责声明 | **已修(MP)** | `NANYI · QIU TANG`；「关闭弹窗后将无法再次查看」 |
| P2-1 客服微信 | **文档已补** | 未改号；注明以运营确认为准 |
| P2-1 首页客服 | **已修(MP)** | 复制微信号或跳转「我的」联系区 |
| P2-4 设计稿目录 / 1.jpeg | **已修(MP)** | `docs/设计稿/` 重命名；根目录 UI 包已补 `1.jpeg` |
| P2-6 X-Client | **已修(MP)** | 请求/上传头增加 `X-Client: miniprogram` |
| 上架文档 | **文档已补** | [`发布上架指南.md`](./发布上架指南.md) |

> 原审查正文保留下方，供对照。交付约束：**未改** backend / frontend / nginx / systemd / 数据库。

---

| 项 | 内容 |
| --- | --- |
| 审查日期 | 2026-09-30 |
| 审查范围 | 小程序 UI 还原度 + 代码质量 + API 契约 + 多端共享后端就绪 |
| 对照基准 | `docs/设计稿/1–5.jpeg`、`nanyi-qiutang-mp/`、`frontend/js/api.js`、Flask `/api` |
| 交付物 | 审查报告；小程序端已按上表修复（2026-09-30） |
| 结论 | **结构与 UI 主路径整体合格，可作 v1 提审候选；账号体系与多端一致性存在 P0/P1 阻断，上线前须处理** |

---

## GateGuard 事实陈述（写入前）

1. **谁会调用本文件**：无运行时调用方。本文件为人工阅读的审查交付物，计划路径为 `nanyi-qiutang-mp/CODE_REVIEW_REPORT.md`；不被 `app.js`、页面或后端 import。
2. **是否已有同用途文件**：仓库根有历史 [`CODE_REVIEW_SECURITY_REPORT.md`](../CODE_REVIEW_SECURITY_REPORT.md)（后端安全，2026-03），**不是**本小程序全链路审查。`nanyi-qiutang-mp/` 下仅有 `README.md`，不存在 `CODE_REVIEW_REPORT.md`。
3. **是否读写数据文件**：否。纯 Markdown 静态报告，无字段/日期格式读写。
4. **用户当前指令（原文）**：`Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.` — 计划要求输出 `nanyi-qiutang-mp/CODE_REVIEW_REPORT.md`。

---

## 一、总览

小程序为原生微信端，约 52 个工程文件，复用生产后端 `https://products.nanyiqiutang.cn/api`，与 Web 的目录/筛选/详情/试穿数据契约基本对齐。5 张设计稿对应页面的信息架构、色板与主交互还原度高。

主要风险集中在：**微信小程序登录未落地**、**邮箱注册与后端手机号契约错位**、**点赞/评价未真正接通**、**「登录后同步」文案与纯本地存储不符**、以及**无客户端标识导致多端运维盲区**。

线上只读探测（2026-09-30）：

| 请求 | 结果 |
| --- | --- |
| `GET /api/health` | 200，healthy |
| `GET /api/filters` | 200 |
| `POST /api/auth/wechat/miniprogram` | **404** `Not found` |
| `POST /api/auth/register`（仅 email+password） | **400** `phone_required` |

---

## 二、P0 阻断（上线 / 提审前必须处理）

### P0-1 微信小程序登录接口缺失

- **现象**：`POST /api/auth/wechat/miniprogram` 返回 404；「我的」页一键登录必然降级。
- **位置**：小程序 `utils/auth.js` `wechatLogin()`；后端 `backend/routes/auth.py` 仅有公众号 OAuth `/auth/wechat/authorize|callback`。
- **影响**：设计稿核心登录路径不可用；无法形成小程序 openid 账号；与 Web 微信用户无法合并。
- **建议**：后端新增接口（契约见第六节）；配置小程序 AppID/Secret；开放平台绑定后落 `unionid`；`OAuthBinding.provider` 与网页端区分（勿复用易混淆的 `"wechat_mp"` 语义，或拆 `wechat_oa` / `wechat_miniprogram`）。

### P0-2 邮箱注册与后端契约断裂

- **现象**：小程序 `pages/login/login.js` 注册只传 `{ email, password, nickname }`；后端强制 `phone`，缺则 `phone_required`。
- **位置**：MP `auth.register`；`backend/routes/auth.py` L94–103；Web 已改为手机号注册。
- **影响**：微信登录未开通时，**注册通道不可用**；仅存量邮箱账号可能登录。
- **建议（二选一，须统一）**：
  1. 小程序登录页改为手机号+密码（与 Web 对齐），或
  2. 后端恢复/兼容邮箱注册（多端明确约定）。

### P0-3 AppID 仍为占位

- **现象**：`project.config.json` `appid: "touristappid"`。
- **影响**：无法真机合法域名、正式微信登录、提审。
- **建议**：替换正式 AppID；公众平台配置 request / uploadFile / downloadFile → `https://products.nanyiqiutang.cn`。

---

## 三、P1 应修（功能正确性 / 多端口径 / 安全）

### P1-1 点赞为本地假交互，未走共享后端

- **现象**：`pages/detail/detail.js` `onToggleLike` 仅改本地 `liked`/`likeCount`；未调用 Web 已用的 `POST/GET /api/like/card/{brand}`。
- **影响**：多端 like_count 不一致；刷新即丢。
- **建议**：对接 `/api/like/card/<brand_name>`，与 Web 同源。

### P1-2 评价入口空转

- **现象**：卡片「评价」跳转 `detail?to=comment`；详情设置 `autoOpenComment` 但**无 UI、未调用** `getBrandReviews` / `submitReview`。
- **位置**：`pages/index/index.js` `onCardComment`；`pages/detail/detail.js`；`utils/api.js` 已声明接口。
- **影响**：设计与卡片承诺的评价能力缺失；`submitReview` 的 `auth: false` 若日后直接启用，与后端「可选登录」叠加易刷评（后端有限流，仍建议默认带 JWT）。
- **建议**：补评价列表+提交 UI，或暂时隐藏卡片「评价」；提交时默认 `auth: true`。

### P1-3 「登录后同步」文案与实现不符

- **现象**：设计稿与 `pages/mine/mine.js` 文案写「同步试穿与浏览记录」「已同步」；实现为本地 Storage（`nanyi_tryon_history_v1` / `nanyi_recent_views`）。登录后无云端列表拉取。
- **影响**：用户预期跨端/换机可见；实际清缓存即丢；与 Web「仅本次可见」部分一致但文案过度承诺。
- **建议**：短期改文案为「本机保存」；中期对接 `/me/browse` 读接口与 `/me/try-on-assets`（Web 已有）。

### P1-4 试穿 `access_token` 出现在 Query

- **现象**：`utils/api.js` `getTryOnStatus` → `/try-on/status/{id}?access_token=`；任务态本地明文持久化 `nanyi_try_on_task_state_v1`。与 Web 一致，但共享后端上更易进访问日志。
- **建议**：改为 Authorization / Header；轮询避免把 token 打进 URL；本地存储可考虑仅存 taskId + 短时效。

### P1-5 环境写死生产

- **现象**：`utils/config.js` `ENV = 'prod'`，无 staging/dev 切换。
- **影响**：联调只能打生产（试穿任务、浏览上报污染）。
- **建议**：按编译模式或本地覆盖切换 `apiBase`；文档标明禁止对生产做写压测。

---

## 四、P2 建议（体验 / 一致性 / 交付完整性）

### P2-1 UI 文案与细节偏差

| 项 | 设计稿 | 实现 | 建议 |
| --- | --- | --- | --- |
| 首页英文副标 | `NANYI · QIU TANG · 古典中式` | `NANYI QIU TANG · 古典中式`（缺点分） | 对齐设计 |
| 试穿免责声明 | 「关闭弹窗后将无法再次查看」 | 「关闭后将无法再次查看」 | 按设计统一 |
| 客服微信（染白） | 设计描述可见拼写变体 | config `moonsys511` | 与运营确认真号后统一 |
| 首页客服入口 | 设计有耳机图标 | 仅 toast 微信号，未跳转「我的」联系区 | 可跳转 mine 或复制 |

### P2-2 首页品牌栏 / Banner / 双列卡片 / 自定义 tabBar

整体与 `1.jpeg` 高度一致：米白底、朱红选中、墨绿 Banner、中间「试穿」强调 tab、`homePreviewCount=2`、「查看全部 N 款」均符合设计。色板集中在 `styles/theme.wxss`，做法正确。

### P2-3 筛选页 / 详情 / 试穿 / 我的

- **筛选 `2.jpeg`**：四维 chip、材质折叠、摘要卡、底部「重置 + 查看 N 款」还原良好。
- **详情 `3.jpeg`**：Hero swiper、参数四列、诗句/简述、猜你喜欢、底栏「分享卡片 / AI 试穿」结构对齐；点赞功能见 P1-1。
- **试穿 `4.jpeg`**：两步流程、虚线上传区、生成按钮、结果卡布局对齐；轮询替代 SSE 合理。
- **我的 `5.jpeg`**：登录卡、双入口、渠道/联系列表、ICP 齐全；登录能力见 P0。

### P2-4 设计稿交付编码

- `nanyi-qiutang-mp/docs/` 下「设计稿」目录名出现乱码，文件 `1–5.jpeg` 仍在。
- 仓库根目录 `南意秋棠 · 微信小程序 UI` 缺 `1.jpeg`（仅 2–5）。
- **建议**：统一 UTF-8 目录名 `docs/设计稿/`，并补齐根目录 UI 包的 `1.jpeg`。

### P2-5 全量 `load_all` 压力

首页/筛选/详情多处触发 `getAllBrands`（内存缓存 + 并发合并已做）。品牌量增长后 Web 与小程序会共同压垮共享 API。建议后续服务端分页筛选或 CDN 缓存全量清单。

### P2-6 无 `X-Client` / platform 请求头

除微信登录 body 的 `platform: 'miniprogram'` 外，常规请求无客户端标识，不利于限流、审计、灰度。建议统一加 `X-Client: miniprogram`（Web/App 同理）。

---

## 五、UI 还原度分页面小结

| 设计图 | 页面 | 还原度 | 主要缺口 |
| --- | --- | --- | --- |
| `1.jpeg` | `pages/index` | 高 | 英文副标点分；客服仅为 toast |
| `2.jpeg` | `pages/fabrics` | 高 | 无实质缺口 |
| `3.jpeg` | `pages/detail` | 高 | 点赞未落库；无评价区 |
| `4.jpeg` | `pages/tryon` | 高 | 免责声明措辞略异 |
| `5.jpeg` | `pages/mine` | 中高 | 微信登录不可用；「已同步」名不副实 |
| （补页） | `list` / `login` | 功能闭环 | 非设计稿范围；login 注册契约错误 |

---

## 六、多端共享后端待办

### 6.1 建议新增：小程序微信登录

```
POST /api/auth/wechat/miniprogram
Body: { "code": "<wx.login code>", "platform": "miniprogram" }
Resp: { "success": true, "data": { "access_token", "refresh_token", "user": {...} } }
```

服务端：`jscode2session` → openid/session_key/unionid → upsert User + OAuthBinding → 签发与 Web 同构的 JWT。

账号合并原则：

1. 有 `unionid`：与公众号/开放平台其他端同一用户。
2. 无 `unionid`：独立绑定，后续绑手机号合并。
3. `provider` 命名与现有网页 OAuth 写入的 `"wechat_mp"` 厘清，避免 openid 空间混淆。

### 6.2 注册 / 登录统一

| 端 | 现状 | 目标 |
| --- | --- | --- |
| Web | 手机号+密码 | 保持 |
| 小程序 | 邮箱表单（注册失败） | 与 Web 同契约，或后端双通道文档化 |
| App（未来） | — | 同一 JWT + 同一 User 表 |

### 6.3 行为数据跨端

| 能力 | Web | 小程序现状 | 建议 |
| --- | --- | --- | --- |
| 浏览上报 | `POST /me/browse` | 有（登录后） | 补读接口供「最近浏览」 |
| 试穿资产 | `/me/try-on-assets` | 仅本地 | 登录后上传/拉取 |
| 点赞 | `/like/card/*` | 本地假数据 | 对接 |
| 评价 | `/reviews` | API 有、UI 无 | 补 UI 或隐藏入口 |

### 6.4 运维

- 请求头 `X-Client: web | miniprogram | app`
- 小程序可切非生产 API
- CORS 仅影响 Web/WebView；小程序无关，但 App WebView 需纳入 `CORS_ORIGINS`

---

## 七、代码质量摘要（Standards）

**优点**

- 分层清晰：`config` / `request` / `api` / `auth` / `format` / `filter`
- 401 自动 refresh 重放、上传封装齐全
- 品牌全量缓存有并发合并；试穿轮询有超时与本地任务恢复
- 主题变量单一来源；图标 SVG mask 零位图资源
- `lazyCodeLoading`、自定义导航与安全区处理到位

**问题**

- 评价/点赞半成品；`autoOpenComment` 死字段
- 敏感 token 进 Query / Storage
- 注册契约过时；环境硬编码
- 卡片分享仅 toast 引导右上角，体验弱于设计预期的分享动作

---

## 八、提审前检查表

- [ ] 替换正式 `appid`
- [ ] 配置三类合法域名（request / uploadFile / downloadFile）
- [ ] 上线 `POST /api/auth/wechat/miniprogram` 并真机验证
- [ ] 统一注册契约（手机号或邮箱），验证 login/register 全路径
- [ ] 决定：隐藏「评价」或实现评价 UI；点赞是否对接后端
- [ ] 修正「已同步」文案或实现云端同步
- [ ] 客服微信号与运营确认一致
- [ ] 设计稿目录名 UTF-8 修复；UI 包补 `1.jpeg`
- [ ] 隐私协议 / 用户协议（微信提审常见要求，代码库未见页面入口，需产品确认）

---

## 九、严重级别统计

| 级别 | 数量 | 最严重项 |
| --- | --- | --- |
| P0 | 3 | 微信登录 404；注册 phone_required；touristappid |
| P1 | 5 | 点赞假数据；评价空转；同步文案；token Query；环境写死 |
| P2 | 6 | 文案/交付细节、load_all、客户端头等 |

**轴内最差问题**：Standards 侧为评价/点赞半成品与 token 暴露；Spec/多端侧为微信登录缺失 + 注册契约错位（阻断「设计图登录」与「邮箱降级」双路径）。

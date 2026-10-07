# 南意秋棠 · 微信小程序

按 UI 设计图实现的多端应用体系之小程序端，复用 Web 站（https://products.nanyiqiutang.cn）已上线的后端服务，数据与逻辑与 Web 端保持一致。

---

## 一、快速开始

1. 用微信开发者工具「导入项目」，目录选择本文件夹 `nanyi-qiutang-mp`
2. 在 `project.config.json` 中把 `appid` 换成正式小程序 AppID（当前为 `touristappid` **占位，切勿编造**；步骤见 [`发布上架指南.md`](./发布上架指南.md)）
3. 本地调试阶段可在开发者工具中勾选「不校验合法域名」；`utils/config.js` 默认 `ENV='prod'`，仅联调时可改为 `dev`
4. 正式提审前，在微信公众平台配置合法域名（见第四节与上架指南）

---

## 二、目录结构

```
nanyi-qiutang-mp/
├── app.js / app.json / app.wxss      全局入口、路由与全局样式
├── project.config.json               项目配置（appid 需替换）
├── sitemap.json
├── styles/
│   ├── theme.wxss                    设计变量（唯一色板来源）
│   └── icons.wxss                    30 个 SVG 遮罩图标（零图片资源）
├── utils/
│   ├── config.js                     环境、接口根地址、渠道与联系方式
│   ├── system.js                     导航栏 / 安全区度量
│   ├── request.js                    请求与上传封装（鉴权、超时、401 自动续期）
│   ├── api.js                        接口层，与 Web 端 js/api.js 一一对应
│   ├── auth.js                       登录态、JWT 持久化与续期
│   ├── format.js                     文案派生（拼音副标题、诗句、简述、展示名）
│   ├── filter.js                     四维筛选、搜索、猜你喜欢
│   └── pinyin.js                     330 字拼音映射（由线上品牌名语料生成）
├── custom-tab-bar/                   自定义 tabBar（首页 / 试穿 / 我的）
├── components/fabric-card/           布料卡片组件
└── pages/
    ├── index/                        首页
    ├── fabrics/                      全部布料（四维筛选）
    ├── list/                         布料结果列表
    ├── detail/                       款式详情
    ├── tryon/                        AI 试穿
    ├── mine/                         我的
    └── login/                        手机号登录 / 注册（找回密码仍走邮箱）
├── docs/设计稿/                      5 张 UI 设计稿（只作对照参考，不参与编译）
├── 发布上架指南.md                   注册、域名、审核、发版检查表
└── CODE_REVIEW_REPORT.md             审查报告与修复状态
```

---

## 三、页面与设计图对应关系

| 设计图 | 页面 | 路径 |
| --- | --- | --- |
| `1.jpeg` | 首页 | `pages/index/index` |
| `2.jpeg` | 全部布料（四维筛选） | `pages/fabrics/fabrics` |
| `3.jpeg` | 款式详情 | `pages/detail/detail` |
| `4.jpeg` | AI 试穿 | `pages/tryon/tryon` |
| `5.jpeg` | 我的 | `pages/mine/mine` |

设计稿原件随包提供，位于 `docs/设计稿/`（`1.jpeg` ~ `5.jpeg`），仅作还原对照，不参与编译。

设计图未覆盖、但功能闭环必需的补页：

- `pages/list/list` —— 「查看 N 款布料」的结果列表（首页仅展示 2 款，与设计图一致）
- `pages/login/login` —— 手机号登录 / 注册；找回密码仍用邮箱（与后端能力一致）；微信登录未开通时的等价入口

---

## 四、合法域名配置（提审前必做）

微信公众平台 → 开发管理 → 开发设置 → 服务器域名：

| 类型 | 域名 |
| --- | --- |
| request 合法域名 | `https://products.nanyiqiutang.cn` |
| uploadFile 合法域名 | `https://products.nanyiqiutang.cn` |
| downloadFile 合法域名 | `https://products.nanyiqiutang.cn` |

> `downloadFile` 是「保存到相册」与「生成分享卡片」拉取图片所必需，不可遗漏。
> `<image>` 组件的网络图片不校验域名，但 canvas 绘制与 `wx.downloadFile` 会校验。

---

## 五、后端接口对接

小程序全部复用 Web 端现有接口，未新增任何后端改动（微信登录除外，见第六节）。

| 小程序调用 | 后端接口 | 说明 |
| --- | --- | --- |
| `api.health()` | `GET /api/health` | 健康检查 |
| `api.getFilters()` | `GET /api/filters` | 年份 / 系列 / 材质 / 印制选项与计数 |
| `api.getImages()` | `GET /api/images` | 分页查询 |
| `api.getAllBrands()` | `GET /api/images?page=1&per_page=200&load_all=true` | 全量 176 款（与 Web 端 `load_all` 行为一致，前端内存缓存） |
| `api.getBrandDetail()` | `GET /api/brand/{name}` | 详情，字段展平口径与 Web 端一致 |
| `api.getBrandImages()` | `GET /api/brand/{name}/images` | 轻量图集 |
| `api.getTryOnStyles()` | `GET /api/try-on/styles` | 试穿款式（含 `?brand_name=` 过滤） |
| `api.startTryOn()` | `POST /api/try-on/start` | multipart：`brand_name` + `user_image` |
| `api.getTryOnStatus()` | `GET /api/try-on/status/{taskId}?access_token=` | 任务状态轮询 |
| `api.getBrandReviews()` | `GET /api/reviews/brand/{name}` | 评价列表 |
| `api.submitReview()` | `POST /api/reviews` | 提交评价 |
| `auth.login/register/forgotPassword/resetPassword` | `/api/auth/*` | 登录/注册与 Web 对齐（手机号）；找回密码仍按邮箱 |
| `api.getLikeStatus` / `api.toggleLike` | `GET/POST /api/like/card/{brand}` | 详情点赞，与 Web 同源 |
| `api.getBrandReviews` / `api.submitReview` | `/api/reviews*` | 评价列表与提交（提交默认带 JWT） |
| `auth.fetchMe()` | `GET /api/me` | 当前用户 |
| `auth.recordBrowse()` | `POST /api/me/browse` | 浏览上报（进详情页自动调用） |

图片与视频地址：`https://products.nanyiqiutang.cn` + `original`/`url` 字段，中文路径逐段编码（`utils/api.js` 的 `buildStaticUrl`）。

**未使用 SSE**：小程序不支持 `EventSource`，`/api/try-on/stream` 不可用，故试穿状态改为 3 秒间隔轮询，超时 5 分钟（`utils/config.js` 可调）。

---

## 六、需要后端补充的接口（1 个）

「我的」页设计为「微信一键登录」。当前后端仅有公众号 OAuth（`/api/auth/wechat/authorize`，返回 `wechat_oauth_not_configured`），**没有小程序登录路由**，实测 `POST /api/auth/wechat/miniprogram` 返回 404。

小程序端已按以下契约完成对接（`utils/auth.js` 的 `wechatLogin()`）：

```
POST /api/auth/wechat/miniprogram
Body: { "code": "<wx.login 返回的 code>", "platform": "miniprogram" }
响应: { "access_token": "...", "refresh_token": "...", "user": { ... } }
```

后端用 `code` 调微信 `code2session` 换取 `openid`/`unionid`，建立或复用账号后签发 JWT 即可。该接口上线前，小程序会**明确提示**并引导用户改用**手机号登录/注册**（`pages/login/login`）；「我的」页另有稳定入口，不影响浏览/试穿等功能。

详细上架步骤、域名、隐私与审核驳回点见 **[`发布上架指南.md`](./发布上架指南.md)**。

---

## 七、与 Web 端的一致性设计

### 1. 色板（`styles/theme.wxss`）

由 5 张设计图颜色量化得出，是唯一色值来源：

| 用途 | 色值 |
| --- | --- |
| 页面背景 | `#F4F0E4` |
| 卡片 | `#FCF8F0` / `#FFFDF7` |
| 主色 朱红 | `#9C2824` |
| 墨绿 | `#244048` |
| 金 | `#A98B4E` / `#C9AE74` |
| 正文 / 次要 / 弱化 | `#2A2521` / `#6B6257` / `#9A9184` |

### 2. 文案派生规则（`utils/format.js`）

设计图中的派生文案全部由接口原始字段计算，保证多端口径一致：

| 展示项 | 规则 | 实例 |
| --- | --- | --- |
| 卡片 / 详情主标题 | 品牌名去括号 + 主图颜色 | `碧梧(山雪/枫红/玉绿/翡翠)` + 主图色 `枫红` → **碧梧 · 枫红** |
| 详情副标题 | 品牌名拼音 + 花纹元素 | **HAN YING · 竹影月光** |
| 诗句 | 从 `inspiration_origin` 中识别「两分句 + 句号」成对诗句行，取前两行 | 独坐幽篁里，弹琴复长啸。／深林人不知，明月来相照。 |
| 灵感简述 | 正文首段前两句（若后端返回 `inspiration_brief` 则优先采用） | — |
| 参数「素材」 | `图{imageCount}·视{videoCount}` | 图20·视2 |
| 参数「印制」 | 短称映射（旗袍定位料 → 定位料） | 定位料 |
| 系列角标 | `theme_series` 去「系列」后缀 | 画韵春秋 |

### 3. 筛选逻辑

与 Web 端一致：一次拉取全量 176 款后在本地做四维筛选与关键词搜索，切换条件零网络请求。

---

## 八、关键实现说明

- **自定义 tabBar**：`app.json` 中 `"custom": true`，中间「试穿」图标按设计图放大，选中色为朱红。
- **图标系统**：`styles/icons.wxss` 用 SVG + `-webkit-mask` 实现，30 个图标零图片资源、可任意着色。若需替换为位图，把对应 `mask-image` 换成 `background-image` 即可。
- **首页展示数量**：设计图首页为 2 款，「查看全部 176 款布料」为全量入口。数量由 `utils/config.js` 的 `homePreviewCount` 控制。
- **分享卡片**：详情页「生成分享卡片」用 canvas 2d 离屏绘制（600×900），完成后调用 `wx.showShareImageMenu`，失败降级为保存到相册。
- **试穿结果**：任务状态本地持久化，冷启动可恢复进行中的任务；结果同时写入「我的试穿」本地记录（后端无该接口，与 Web 端「仅本次可见」口径一致）。
- **「最近浏览」**：本地记录，进详情页时写入。

---

## 九、待确认事项

1. **微信小程序登录接口**需后端补充（第六节），否则「我的」页一键登录会降级到手机号通道。
2. **正式 AppID**：当前 `touristappid` 为占位，提审前替换（见上架指南第二节）。
3. **客服微信号**以运营确认为准（`config.contacts`；设计稿有拼写变体，勿擅自改号）。
4. `homePreviewCount`、材质折叠条数、轮询间隔、`ENV` 等可调参数集中在 `utils/config.js`。
5. 完整发版检查表见 [`发布上架指南.md`](./发布上架指南.md) 第八节。

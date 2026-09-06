# 南意秋棠 v2 · 古典中式视觉改版

将 [Ardot 画布设计稿](https://ardot.tencent.com/file/722888797287131) 严格还原为可运行的 Web 应用。

## 6 个画框

| # | 画框                | 尺寸         | 内容                                       |
| - | ------------------- | ------------ | ------------------------------------------ |
| 0 | 设计系统 · 古典中式 | 540 wide     | 色板 / 字体 / 圆角 / 间距 / 组件示例       |
| 1 | 桌面 · 首页         | 1440 wide    | Header · Hero · 筛选 · 8 卡 · 分页 · Footer |
| 2 | 桌面 · 详情弹窗     | 1440 × 1000  | "凤麟" 详情（设计灵感 / 布料 / 模特 / CTA）|
| 3 | 桌面 · 客服弹窗     | 1440 × 1000  | 棠棠智能客服（消息流 / 快捷提问 / 输入）    |
| 4 | 移动 · 首页         | 390 wide     | 简化 Header · Hero · 搜索 · 4 卡 · FAB     |
| 5 | 移动 · 客服         | 390 × 780    | 全屏聊天面板                              |

## 文件结构

```
_v2/
├── index.html       # 应用入口（6 个画框 + 实时弹窗）
├── styles.css       # 全部样式 + 设计 token
├── app.js           # 弹窗 / 筛选 / 分页 / 发送 交互
└── assets/          # 8 张真实品牌模特图（来源 products.nanyiqiutang.cn）
    ├── feiyu.jpg         翡玉
    ├── zhaoyebai.jpg     照夜白
    ├── yunqi.jpg         云起
    ├── lansheng.jpg      澜生
    ├── zhaohun.jpg       招魂
    ├── wenling.jpg       问灵
    ├── buyuege.jpg       步月歌
    └── shishitongtang.jpg 柿柿同堂
```

## 启动

任选其一：

```bash
# 方式 1：Python 内置服务器（推荐）
cd _v2 && python -m http.server 9001
# 浏览器打开 http://127.0.0.1:9001/

# 方式 2：直接双击 index.html
# 浏览器会通过 file:// 打开（功能完整，相对路径 OK）
```

## 设计还原要点

### 色板（CSS 变量）
- `--c-paper: #F6F1E4` 宣纸
- `--c-moon: #FCFAF3` 月白
- `--c-ink-deep: #1C343B` 深黛
- `--c-ink: #2E4F58` 黛青
- `--c-rose: #9E2B25` 朱红
- `--c-gold: #C2A15A` 鎏金
- `--c-black: #1F1D1A` 墨

### 圆角
- `2px` 标签 / 按钮
- `3px` 卡片
- `4px` 弹窗
- `999px` 胶囊 / 头像

### 间距节奏
- 卡片之间 `16px`
- 区块之间 `32-48px`
- Section 内 padding `40px`

### 字体
- H1 / Hero 标题：**Zhi Mang Xing** (志莽行书)
- H2 / 正文：**Noto Serif SC** 400/600
- 小标签：同上

## 交互能力

- **品牌卡片** 点击 → 打开详情弹窗
- **Hero / 头部** "立即咨询" / "浏览全部" → 打开对应弹窗
- **FAB** 右下角 → 打开客服弹窗
- **客服弹窗** 模拟发送（Enter 也可）+ 自动回复
- **筛选 chip** 单选互斥（年份 / 主题 / 材质 / 印花）
- **分页** 点击切换 current，滚动回网格顶部
- **ESC** 关闭弹窗；点遮罩关闭
- **移动端** 自适应 390px，4 张单列卡 + FAB

## 与原画布差异

- 原画布的 hero 有真实的水墨远山 SVG + 鎏金菱纹 pattern（已还原）
- 详情弹窗中的"布料图 3 张"用前 3 张真实模特图代替（按设计意图是布料平铺图）
- 客服头像 "棠" 用行书 emoji 占位（live 系统会换真人头像）
- "NEW · 2025" 红色 ribbon 仅在 2025 新款上展示

## 设计稿对照

源画布：https://ardot.tencent.com/file/722888797287131

如需查看新设计稿/更新画布内容，请同步：

1. 改 `index.html` 对应 section
2. 改 `styles.css` 对应 token
3. 增量更新 `assets/` 目录新款式图片

/**
 * 环境与服务配置
 *
 * ⚠️ 微信后台「开发设置 - 服务器域名」需加入以下合法域名：
 *    request  合法域名：https://products.nanyiqiutang.cn
 *    uploadFile 合法域名：https://products.nanyiqiutang.cn
 *    downloadFile 合法域名：https://products.nanyiqiutang.cn
 *    业务域名（如使用 web-view）：https://products.nanyiqiutang.cn
 *
 * 接口根路径与 Web 端 js/api.js 保持完全一致（生产环境走 nginx 反代的 /api）。
 *
 * —— 环境切换 ——
 * 将下方 ENV 改为 'dev' 可指向本地/联调地址；**默认必须保持 'prod'**，
 * 以免误打生产写接口。禁止对生产环境做写压测。
 */

/** @type {'prod' | 'dev'} */
const ENV = 'prod';

const ENV_MAP = {
  prod: {
    apiBase: 'https://products.nanyiqiutang.cn/api',
    staticBase: 'https://products.nanyiqiutang.cn'
  },
  // 本地联调：开发者工具勾选「不校验合法域名」后可改 ENV='dev'
  dev: {
    apiBase: 'http://127.0.0.1:5000/api',
    staticBase: 'http://127.0.0.1:5000'
  }
};

const active = ENV_MAP[ENV] || ENV_MAP.prod;

const CONFIG = {
  env: ENV,

  /** 接口根地址 */
  apiBase: active.apiBase,

  /** 静态资源根地址（图片 / 视频） */
  staticBase: active.staticBase,

  /** 请求超时（毫秒），与 Web 端一致支持 AI 试衣长轮询 */
  timeout: 60000,

  /** 品牌列表分页：首页与筛选页均一次拉全量，与 Web 端 load_all 行为一致 */
  brandPageSize: 200,

  /** 首页首屏展示的款式数量（UI 设计图为 2 款） */
  homePreviewCount: 2,

  /** AI 试穿页可选款式数量上限 */
  tryOnStyleLimit: 12,

  /** 本地存储 key */
  storage: {
    accessToken: 'nanyi_jwt_access_v1',
    refreshToken: 'nanyi_jwt_refresh_v1',
    userInfo: 'nanyi_user_info_v1',
    recentViews: 'nanyi_recent_views',
    tryOnHistory: 'nanyi_tryon_history_v1'
  },

  /** 最近浏览最多保留条数 */
  recentViewLimit: 20,

  /** AI 试穿：最大上传体积 10MB */
  tryOnMaxSize: 10 * 1024 * 1024,

  /** AI 试穿：状态轮询间隔（毫秒） */
  tryOnPollInterval: 3000,

  /** AI 试穿：轮询超时上限（毫秒） */
  tryOnTimeout: 5 * 60 * 1000,

  /**
   * 试穿任务态本地缓存最长保留时间（毫秒）。
   * 超时后丢弃明文 access_token，避免长期落盘。
   * 后端轮询仍要求 query 带 token，此处只控制本地窗口。
   */
  tryOnTaskMaxAge: 10 * 60 * 1000,

  /** 购买渠道（与 Web 端 / 品牌资料一致） */
  channels: [
    { key: 'taobao', icon: 'shop', label: '淘宝 · nanyiqiutang', value: 'nanyiqiutang', copyable: false },
    { key: 'weidian', icon: 'bag', label: '微店 · 南意秋棠', value: '南意秋棠', copyable: false },
    { key: 'xiaohongshu', icon: 'book', label: '小红书 @南意秋棠', value: '南意秋棠', copyable: false },
    { key: 'showroom', icon: 'pin', label: '线下展厅', value: '', copyable: false }
  ],

  /**
   * 联系方式
   * 客服微信号以运营确认为准；设计稿曾出现拼写变体，勿擅自改号。
   */
  contacts: [
    { key: 'service-nan', icon: 'chat', label: '客服微信（小南）', value: 'LPumpkin0217', copyable: true },
    { key: 'service-ran', icon: 'chat', label: '客服微信（染白）', value: 'moonsys511', copyable: true },
    { key: 'email', icon: 'mail', label: '邮箱', value: '502517787@qq.com', copyable: false }
  ],

  brand: {
    name: '南意秋棠',
    enName: 'NANYI · QIU TANG',
    slogan: '古典中式',
    copyright: '© 2017 - 2026 南意秋棠',
    icp: '浙ICP备2024081979号'
  }
};

module.exports = CONFIG;

/**
 * 南意秋棠 · 微信小程序
 * 全局入口：初始化导航栏度量、预热筛选与品牌数据
 */
const system = require('./utils/system');
const api = require('./utils/api');

App({
  globalData: {
    /** 状态栏高度 px */
    statusBarHeight: 20,
    /** 自定义导航栏内容区高度 px */
    navBarHeight: 44,
    /** 状态栏 + 导航栏 总高度 px */
    navTotalHeight: 64,
    /** 胶囊按钮左边界距屏幕右侧距离 px */
    capsuleGap: 10,
    /** 胶囊按钮区域宽度 px（含左右留白） */
    capsuleWidth: 95,
    /** 屏幕宽度 px */
    windowWidth: 375,
    /** 安全区底部高度 px */
    safeBottom: 0,
    /** 「我的」页登录态用户信息 */
    userInfo: null,
    /** 最近浏览（本地缓存） */
    recentViews: [],
    /** 页面间传参：首页 / 筛选页 -> 结果列表 的筛选条件 */
    pendingFilters: null,
    /** 页面间传参：卡片试穿 -> AI 试穿页 的款式名 */
    tryOnBrand: ''
  },

  onLaunch() {
    this.initSystemMetrics();
    this.restoreLocalState();
    this.prewarm();
  },

  /** 计算自定义导航栏尺寸 */
  initSystemMetrics() {
    const metrics = system.getNavMetrics();
    Object.assign(this.globalData, metrics);
  },

  /** 恢复本地态：最近浏览 */
  restoreLocalState() {
    try {
      const recent = wx.getStorageSync('nanyi_recent_views');
      if (Array.isArray(recent)) {
        this.globalData.recentViews = recent;
      }
    } catch (e) {
      // 忽略读取失败
    }
  },

  /** 预热门数据，减少首屏等待 */
  prewarm() {
    api.getFilters().catch(() => {});
  }
});

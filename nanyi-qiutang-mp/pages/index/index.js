/**
 * 首页
 * 数据来源：GET /api/filters + GET /api/images?load_all=true（与 Web 端一致）
 */
const CONFIG = require('../../utils/config');
const api = require('../../utils/api');
const fmt = require('../../utils/format');
const filt = require('../../utils/filter');

Page({
  data: {
    statusBarHeight: 20,
    navBarHeight: 44,
    navTotalHeight: 64,
    capsuleGap: 10,

    brand: CONFIG.brand,
    years: [],
    activeYear: filt.ALL,
    keyword: '',

    cards: [],
    totalBrands: 0,
    matchCount: 0,
    loading: true,
    error: ''
  },

  onLoad() {
    const g = getApp().globalData || {};
    this.setData({
      statusBarHeight: g.statusBarHeight || 20,
      navBarHeight: g.navBarHeight || 44,
      navTotalHeight: g.navTotalHeight || 64,
      capsuleGap: g.capsuleGap || 10
    });
    this.brands = [];
    this.loadData();
  },

  onShow() {
    this.syncTabBar();
  },

  onPullDownRefresh() {
    this.loadData(true).then(
      () => wx.stopPullDownRefresh(),
      () => wx.stopPullDownRefresh()
    );
  },

  /** 同步 tabBar 选中态 */
  syncTabBar() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 0 });
    }
  },

  /* ---------------- 数据 ---------------- */

  loadData(force) {
    if (this.brands && this.brands.length && !force) {
      this.render();
      return Promise.resolve();
    }
    this.setData({ loading: true, error: '' });

    return Promise.all([api.getFilters(), api.getAllBrands(!!force)]).then(
      results => {
        const filters = results[0];
        const res = results[1];
        this.brands = res.brands || [];
        this.setData({
          years: this.normalizeYears(filters.years),
          totalBrands: (res.pagination && res.pagination.total_brands) || this.brands.length,
          loading: false
        });
        this.render();
      },
      err => {
        this.setData({
          loading: false,
          error: (err && err.message) || '数据加载失败，请下拉刷新重试'
        });
      }
    );
  },

  /** 年份选项：全部 + 年份倒序 */
  normalizeYears(list) {
    const arr = (list || []).filter(Boolean).map(String);
    const nums = arr
      .filter(y => y !== filt.ALL)
      .sort((a, b) => Number(b) - Number(a));
    return [filt.ALL].concat(nums);
  },

  render() {
    const all = this.brands || [];
    const filtered = filt.applyFilters(all, {
      year: this.data.activeYear,
      keyword: this.data.keyword
    });
    const limit = CONFIG.homePreviewCount;
    this.setData({
      cards: filtered.slice(0, limit),
      matchCount: filtered.length
    });
  },

  /* ---------------- 交互 ---------------- */

  onYearChange(e) {
    const year = e.currentTarget.dataset.year;
    if (year === this.data.activeYear) return;
    this.setData({ activeYear: year }, () => this.render());
  },

  onKeywordInput(e) {
    this.setData({ keyword: e.detail.value || '' }, () => this.render());
  },

  onSearch() {
    this.render();
  },

  onClearKeyword() {
    this.setData({ keyword: '' }, () => this.render());
  },

  /** 跳转全部布料（携带当前筛选，保证与首页所见一致） */
  onViewAll() {
    getApp().globalData.pendingFilters = {
      year: this.data.activeYear,
      keyword: this.data.keyword
    };
    wx.navigateTo({ url: '/pages/fabrics/fabrics' });
  },

  onKnowSeries() {
    getApp().globalData.pendingFilters = { year: filt.ALL, keyword: '', focusSeries: true };
    wx.navigateTo({ url: '/pages/fabrics/fabrics' });
  },

  onTapCard(e) {
    const brand = e.detail.brand || {};
    const name = brand.name || brand.brand_name || '';
    if (!name) return;
    wx.navigateTo({ url: '/pages/detail/detail?name=' + encodeURIComponent(name) });
  },

  onCardTryOn(e) {
    const brand = e.detail.brand || {};
    const name = fmt.getBaseName(brand.name || brand.brand_name || '');
    getApp().globalData.tryOnBrand = name;
    wx.switchTab({ url: '/pages/tryon/tryon' });
  },

  onCardShare() {
    wx.showToast({ title: '点击右上角 · · · 分享给好友', icon: 'none', duration: 2000 });
  },

  onCardComment(e) {
    const brand = e.detail.brand || {};
    const name = brand.name || brand.brand_name || '';
    if (!name) return;
    wx.navigateTo({ url: '/pages/detail/detail?name=' + encodeURIComponent(name) + '&to=comment' });
  },

  onTapService() {
    const contacts = CONFIG.contacts || [];
    const primary = (contacts.find(c => c.copyable) || contacts[0] || {}).value || '';
    wx.showActionSheet({
      itemList: ['复制客服微信号（小南）', '前往「我的」联系区'],
      success: r => {
        if (r.tapIndex === 0) {
          if (!primary) {
            wx.showToast({ title: '暂无客服微信号', icon: 'none' });
            return;
          }
          wx.setClipboardData({
            data: primary,
            success() {
              wx.showToast({ title: '已复制微信号', icon: 'success' });
            }
          });
        } else if (r.tapIndex === 1) {
          getApp().globalData.scrollToContact = true;
          wx.switchTab({ url: '/pages/mine/mine' });
        }
      }
    });
  },

  onTapMine() {
    wx.switchTab({ url: '/pages/mine/mine' });
  },

  onShareAppMessage() {
    return {
      title: CONFIG.brand.name + ' · ' + CONFIG.brand.slogan,
      path: '/pages/index/index'
    };
  },

  onShareTimeline() {
    return { title: CONFIG.brand.name + ' · ' + CONFIG.brand.slogan };
  }
});

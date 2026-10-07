/**
 * 布料结果列表
 * 由「全部布料」筛选页提交筛选条件后进入，展示匹配结果（滚动分页渲染）
 */
const api = require('../../utils/api');
const fmt = require('../../utils/format');
const filt = require('../../utils/filter');

const PAGE_SIZE = 20;

Page({
  data: {
    statusBarHeight: 20,
    navBarHeight: 44,
    navTotalHeight: 64,
    capsuleGap: 10,
    safeBottom: 0,

    summaryText: '',
    total: 0,
    cards: [],
    hasMore: false,
    loading: true,
    error: ''
  },

  onLoad() {
    const g = getApp().globalData || {};
    this.setData({
      statusBarHeight: g.statusBarHeight || 20,
      navBarHeight: g.navBarHeight || 44,
      navTotalHeight: g.navTotalHeight || 64,
      capsuleGap: g.capsuleGap || 10,
      safeBottom: g.safeBottom || 0
    });
    this.page = 1;
    this.all = [];
    this.filters = g.pendingFilters || null;
    this.load();
  },

  load() {
    this.setData({ loading: true, error: '' });
    api.getAllBrands().then(
      res => {
        const all = res.brands || [];
        // 筛选条件来自「全部布料」页；无条件下展示全部
        this.all = this.filters ? filt.applyFilters(all, this.filters) : all;
        this.setData({
          loading: false,
          total: this.all.length,
          summaryText: this.filters ? filt.describeFilters(this.filters) : '全部款式'
        });
        this.appendPage();
      },
      err => {
        this.setData({ loading: false, error: (err && err.message) || '加载失败' });
      }
    );
  },

  appendPage() {
    const start = (this.page - 1) * PAGE_SIZE;
    const next = this.all.slice(start, start + PAGE_SIZE);
    const cards = this.data.cards.concat(next);
    this.setData({
      cards,
      hasMore: cards.length < this.all.length
    });
    this.page += 1;
  },

  onReachBottom() {
    if (!this.data.hasMore) return;
    this.appendPage();
  },

  onTapCard(e) {
    const brand = e.detail.brand || {};
    const name = brand.name || brand.brand_name || '';
    if (!name) return;
    wx.navigateTo({ url: '/pages/detail/detail?name=' + encodeURIComponent(name) });
  },

  onCardTryOn(e) {
    const brand = e.detail.brand || {};
    getApp().globalData.tryOnBrand = fmt.getBaseName(brand.name || brand.brand_name || '');
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

  onBack() {
    wx.navigateBack({
      fail() {
        wx.switchTab({ url: '/pages/index/index' });
      }
    });
  },

  onShareAppMessage() {
    return { title: '南意秋棠 · 布料列表', path: '/pages/index/index' };
  }
});

/**
 * 全部布料 · 四维筛选
 * 选项来自 GET /api/filters，匹配计数为本地实时计算（与 Web 端一致）
 */
const api = require('../../utils/api');
const filt = require('../../utils/filter');

/** 材质默认展示条数（含「全部」），超出折叠 */
const MATERIAL_LIMIT = 11;

Page({
  data: {
    statusBarHeight: 20,
    navBarHeight: 44,
    navTotalHeight: 64,
    capsuleGap: 10,
    safeBottom: 0,

    years: [],
    seriesList: [],
    materials: [],
    displayMaterials: [],
    printSizes: [],

    showAllMaterials: false,
    materialMoreCount: 0,

    current: {
      year: filt.ALL,
      series: filt.ALL,
      material: filt.ALL,
      printSize: filt.ALL
    },

    summaryText: '',
    matchCount: 0,
    totalBrands: 0,
    loading: true,
    error: '',
    shouldReturn: false
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

    const pending = g.pendingFilters || {};
    const current = Object.assign({}, this.data.current);
    if (pending.year) current.year = pending.year;
    if (pending.focusSeries) current.series = filt.ALL;

    this.brands = [];
    this.loadData(current);
  },

  loadData(current) {
    this.setData({ loading: true, error: '' });
    Promise.all([api.getFilters(), api.getAllBrands()]).then(
      results => {
        const filters = results[0];
        const res = results[1];
        this.brands = res.brands || [];

        const years = this.normalizeYears(filters.years);
        const seriesList = (filters.themeSeries || []).map(s => String(s));
        const materials = (filters.materials || []).map(s => String(s));
        const printSizes = (filters.printSizes || []).map(s => String(s));

        this.materials = materials;
        this.setData(
          {
            years,
            seriesList,
            materials,
            displayMaterials: materials.slice(0, MATERIAL_LIMIT),
            printSizes,
            materialMoreCount: Math.max(0, materials.length - MATERIAL_LIMIT),
            totalBrands: (res.pagination && res.pagination.total_brands) || this.brands.length,
            current,
            loading: false
          },
          () => this.recompute()
        );
      },
      err => {
        this.setData({ loading: false, error: (err && err.message) || '加载失败，请返回重试' });
      }
    );
  },

  normalizeYears(list) {
    const arr = (list || []).filter(Boolean).map(String);
    const nums = arr.filter(y => y !== filt.ALL).sort((a, b) => Number(b) - Number(a));
    return [filt.ALL].concat(nums);
  },

  /** 重新计算匹配数与摘要 */
  recompute() {
    const c = this.data.current;
    const matched = filt.applyFilters(this.brands, {
      year: c.year,
      series: c.series,
      material: c.material,
      printSize: c.printSize
    });
    this.setData({
      matchCount: matched.length,
      summaryText: filt.describeFilters(c)
    });
    this.matched = matched;
  },

  /* ---------------- 交互 ---------------- */

  onSelect(e) {
    const field = e.currentTarget.dataset.field;
    const value = e.currentTarget.dataset.value;
    const current = Object.assign({}, this.data.current);
    current[field] = value;
    this.setData({ current }, () => this.recompute());
  },

  onToggleMaterials() {
    const showAll = !this.data.showAllMaterials;
    this.setData({
      showAllMaterials: showAll,
      displayMaterials: showAll ? this.materials : this.materials.slice(0, MATERIAL_LIMIT)
    });
  },

  onReset() {
    this.setData({ current: filt.emptyFilters() }, () => this.recompute());
  },

  onSubmit() {
    // 只传递筛选条件，结果页复用全量缓存自行筛选，避免在 globalData 中搬运大对象
    getApp().globalData.pendingFilters = {
      year: this.data.current.year,
      series: this.data.current.series,
      material: this.data.current.material,
      printSize: this.data.current.printSize
    };
    wx.navigateTo({ url: '/pages/list/list' });
  },

  onBack() {
    wx.navigateBack({
      fail() {
        wx.switchTab({ url: '/pages/index/index' });
      }
    });
  },

  onShareAppMessage() {
    return {
      title: '南意秋棠 · 全部布料',
      path: '/pages/index/index'
    };
  }
});

/**
 * 自定义 tabBar
 * 首页 / 试穿（图标突出）/ 我的
 */
Component({
  data: {
    selected: 0,
    safeBottom: 0,
    list: [
      { pagePath: '/pages/index/index', text: '首页', icon: 'home' },
      { pagePath: '/pages/tryon/tryon', text: '试穿', icon: 'dress', emphasize: true },
      { pagePath: '/pages/mine/mine', text: '我的', icon: 'user' }
    ]
  },

  attached() {
    const app = getApp();
    if (app && app.globalData) {
      this.setData({ safeBottom: app.globalData.safeBottom || 0 });
    }
  },

  methods: {
    onTap(e) {
      const index = Number(e.currentTarget.dataset.index);
      const item = this.data.list[index];
      if (!item) return;
      if (index === this.data.selected) return;
      wx.switchTab({
        url: item.pagePath,
        fail() {
          // 兜底：部分场景 switchTab 失败时用 reLaunch
          wx.reLaunch({ url: item.pagePath });
        }
      });
    }
  }
});

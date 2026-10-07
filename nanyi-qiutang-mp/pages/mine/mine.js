/**
 * 我的
 * 登录态接口：POST /auth/wechat/miniprogram（小程序）· GET /me · POST /me/browse
 * 「我的试穿」「最近浏览」为本机保存（清缓存即丢；登录后暂无云端列表）
 */
const CONFIG = require('../../utils/config');
const auth = require('../../utils/auth');

Page({
  data: {
    statusBarHeight: 20,
    navBarHeight: 44,
    navTotalHeight: 64,
    safeBottom: 0,

    brand: CONFIG.brand,
    channels: CONFIG.channels,
    contacts: CONFIG.contacts,

    logged: false,
    user: null,
    userLabel: '微信一键登录',
    userDesc: '登录后可评价与上报浏览；试穿记录本机保存',

    tryOnThumbs: [],
    recentThumbs: []
  },

  onLoad() {
    const g = getApp().globalData || {};
    this.setData({
      statusBarHeight: g.statusBarHeight || 20,
      navBarHeight: g.navBarHeight || 44,
      navTotalHeight: g.navTotalHeight || 64,
      safeBottom: g.safeBottom || 0
    });
  },

  onShow() {
    this.syncTabBar();
    this.refresh();
    this.maybeScrollToContact();
  },

  onPullDownRefresh() {
    this.refresh().then(() => wx.stopPullDownRefresh(), () => wx.stopPullDownRefresh());
  },

  syncTabBar() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 2 });
    }
  },

  /** 首页客服入口跳转时滚到联系区 */
  maybeScrollToContact() {
    const app = getApp();
    if (!(app.globalData && app.globalData.scrollToContact)) return;
    app.globalData.scrollToContact = false;
    setTimeout(() => {
      wx.pageScrollTo({
        selector: '#contact-section',
        duration: 300,
        fail() {
          // 部分基础库不支持 selector，忽略
        }
      });
    }, 200);
  },

  /* ---------------- 数据 ---------------- */

  refresh() {
    const logged = auth.isLogged();
    const cached = auth.getCachedUser() || {};
    const localHint = '试穿与浏览记录保存在本机';
    this.setData({
      logged,
      user: logged ? cached : null,
      userLabel: logged
        ? cached.nickname || cached.username || cached.phone || cached.email || '南意秋棠用户'
        : '微信一键登录',
      userDesc: logged ? localHint : '登录后可评价与上报浏览；试穿记录本机保存'
    });

    this.loadLocalThumbs();

    if (logged) {
      return auth.fetchMe().then(
        user => {
          if (user) {
            this.setData({
              user,
              userLabel: user.nickname || user.username || user.phone || user.email || '南意秋棠用户',
              userDesc: localHint
            });
          }
          return user;
        },
        () => null
      );
    }
    return Promise.resolve(null);
  },

  /** 本地缩略图：我的试穿 + 最近浏览 */
  loadLocalThumbs() {
    let tryOns = [];
    try {
      tryOns = wx.getStorageSync(CONFIG.storage.tryOnHistory) || [];
    } catch (e) {
      tryOns = [];
    }
    const recent = (getApp().globalData || {}).recentViews || [];

    this.tryOnList = tryOns;
    this.recentList = recent;

    this.setData({
      tryOnThumbs: tryOns.slice(0, 2).map(i => i.resultUrl).filter(Boolean),
      recentThumbs: recent.slice(0, 2).map(i => i.cover).filter(Boolean)
    });
  },

  /* ---------------- 登录 ---------------- */

  onLoginTap() {
    if (this.data.logged) {
      wx.showActionSheet({
        itemList: ['退出登录'],
        success: r => {
          if (r.tapIndex === 0) this.doLogout();
        }
      });
      return;
    }

    wx.showLoading({ title: '登录中…', mask: true });
    auth
      .wechatLogin()
      .then(
        () => {
          wx.hideLoading();
          wx.showToast({ title: '登录成功', icon: 'success' });
          this.refresh();
        },
        err => {
          wx.hideLoading();
          // 后端未提供小程序登录路由时，明确降级到手机号登录
          if (auth.isWechatLoginUnavailable(err)) {
            wx.showModal({
              title: '微信登录暂不可用',
              content:
                '服务端尚未开通小程序微信登录接口（POST /api/auth/wechat/miniprogram）。请改用手机号登录或注册，与网页端账号体系一致。',
              confirmText: '手机号登录',
              cancelText: '稍后',
              success: r => {
                if (r.confirm) wx.navigateTo({ url: '/pages/login/login' });
              }
            });
            return;
          }
          wx.showModal({
            title: '登录失败',
            content: ((err && err.message) || '请稍后重试') + '。也可使用手机号登录。',
            confirmText: '手机号登录',
            cancelText: '取消',
            success: r => {
              if (r.confirm) wx.navigateTo({ url: '/pages/login/login' });
            }
          });
        }
      );
  },

  doLogout() {
    auth.logout();
    this.setData({
      logged: false,
      user: null,
      userLabel: '微信一键登录',
      userDesc: '登录后可评价与上报浏览；试穿记录本机保存'
    });
    wx.showToast({ title: '已退出登录', icon: 'none' });
  },

  /** 稳定入口：手机号 / 账号登录 */
  onPhoneLogin() {
    wx.navigateTo({ url: '/pages/login/login' });
  },

  /* ---------------- 我的试穿 / 最近浏览 ---------------- */

  onTapTryOns() {
    const list = this.tryOnList || [];
    if (!list.length) {
      wx.showToast({ title: '还没有试穿记录（本机）', icon: 'none' });
      return;
    }
    wx.previewImage({
      current: list[0].resultUrl,
      urls: list.map(i => i.resultUrl).filter(Boolean)
    });
  },

  onTapRecent() {
    const list = this.recentList || [];
    if (!list.length) {
      wx.showToast({ title: '还没有浏览记录（本机）', icon: 'none' });
      return;
    }
    const name = list[0].name;
    wx.navigateTo({ url: '/pages/detail/detail?name=' + encodeURIComponent(name) });
  },

  /* ---------------- 渠道与联系 ---------------- */

  onChannelTap(e) {
    const key = e.currentTarget.dataset.key;
    const map = {
      taobao: '淘宝搜索：nanyiqiutang',
      weidian: '微店搜索：南意秋棠',
      xiaohongshu: '小红书搜索：南意秋棠',
      showroom: '线下展厅地址请联系客服获取'
    };
    if (key === 'showroom') {
      wx.showToast({ title: map[key], icon: 'none', duration: 2400 });
      return;
    }
    wx.setClipboardData({
      data: key === 'taobao' ? 'nanyiqiutang' : '南意秋棠',
      success() {
        wx.showToast({ title: '已复制，可在对应平台搜索', icon: 'none', duration: 2200 });
      }
    });
  },

  onCopy(e) {
    const value = e.currentTarget.dataset.value;
    if (!value) return;
    wx.setClipboardData({
      data: value,
      success() {
        wx.showToast({ title: '已复制', icon: 'success' });
      }
    });
  },

  onTapContact(e) {
    const value = e.currentTarget.dataset.value;
    if (!value) return;
    if (value.indexOf('@') > -1) {
      wx.setClipboardData({
        data: value,
        success() {
          wx.showToast({ title: '邮箱已复制', icon: 'none' });
        }
      });
    }
  },

  onShareAppMessage() {
    return {
      title: CONFIG.brand.name + ' · ' + CONFIG.brand.slogan,
      path: '/pages/index/index'
    };
  }
});

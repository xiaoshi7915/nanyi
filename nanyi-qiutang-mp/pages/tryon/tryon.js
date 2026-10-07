/**
 * AI 试穿
 * 接口：GET /try-on/styles · POST /try-on/start · GET /try-on/status/{taskId}
 * 小程序不支持 SSE，改用状态轮询（间隔与超时见 utils/config.js）
 */
const CONFIG = require('../../utils/config');
const api = require('../../utils/api');
const fmt = require('../../utils/format');

const TASK_STORAGE_KEY = 'nanyi_try_on_task_state_v1';

Page({
  data: {
    statusBarHeight: 20,
    navBarHeight: 44,
    navTotalHeight: 64,
    safeBottom: 0,

    styles: [],
    displayStyles: [],
    showAllStyles: false,
    activeStyle: null,

    photoPath: '',
    photoName: '',

    submitting: false,
    status: '', // '' | 'processing' | 'completed' | 'failed'
    progress: 0,
    statusText: '',
    resultUrl: '',
    errorMessage: '',
    loadingStyles: true
  },

  onLoad() {
    const g = getApp().globalData || {};
    this.setData({
      statusBarHeight: g.statusBarHeight || 20,
      navBarHeight: g.navBarHeight || 44,
      navTotalHeight: g.navTotalHeight || 64,
      safeBottom: g.safeBottom || 0
    });
    this.loadStyles();
    this.restoreTask();
  },

  onShow() {
    this.syncTabBar();
    this.applyPendingBrand();
  },

  onUnload() {
    this.stopPolling();
  },

  onHide() {
    this.stopPolling();
  },

  syncTabBar() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 1 });
    }
  },

  /* ---------------- 款式 ---------------- */

  loadStyles() {
    this.setData({ loadingStyles: true });
    api.getTryOnStyles().then(
      list => {
        this.allStyles = list || [];
        this.setData(
          {
            loadingStyles: false,
            styles: this.allStyles,
            displayStyles: this.allStyles.slice(0, CONFIG.tryOnStyleLimit)
          },
          () => this.applyPendingBrand()
        );
      },
      () => {
        this.setData({ loadingStyles: false });
        wx.showToast({ title: '款式加载失败，请下拉重试', icon: 'none' });
      }
    );
  },

  /** 应用从详情页 / 卡片带入的预选款式 */
  applyPendingBrand() {
    if (this._appliedBrand) return;
    const want = ((getApp().globalData || {}).tryOnBrand || '').trim();
    if (!want || !this.allStyles || !this.allStyles.length) return;

    const idx = this.allStyles.findIndex(s => s.baseBrand === want || s.brandName === want);
    if (idx < 0) return;

    const picked = this.allStyles[idx];
    const rest = this.allStyles.filter(s => s.brandName !== picked.brandName);
    const merged = [picked].concat(rest);
    this._appliedBrand = true;
    this.setData({
      styles: merged,
      displayStyles: this.data.showAllStyles ? merged : merged.slice(0, CONFIG.tryOnStyleLimit),
      activeStyle: picked
    });
  },

  onSelectStyle(e) {
    const index = Number(e.currentTarget.dataset.index);
    const style = this.data.displayStyles[index];
    if (!style) return;
    this.setData({ activeStyle: style });
  },

  onToggleAllStyles() {
    const showAll = !this.data.showAllStyles;
    this.setData({
      showAllStyles: showAll,
      displayStyles: showAll ? this.data.styles : this.data.styles.slice(0, CONFIG.tryOnStyleLimit)
    });
  },

  /* ---------------- 照片 ---------------- */

  onChoosePhoto() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      sizeType: ['compressed'],
      success: res => {
        const file = (res.tempFiles && res.tempFiles[0]) || null;
        if (!file) return;
        if (file.size && file.size > CONFIG.tryOnMaxSize) {
          wx.showToast({ title: '照片超过 10MB，请重新选择', icon: 'none' });
          return;
        }
        this.setData({
          photoPath: file.tempFilePath,
          photoName: file.tempFilePath.split('/').pop() || 'photo.jpg',
          status: '',
          resultUrl: '',
          errorMessage: ''
        });
      }
    });
  },

  onPreviewPhoto() {
    if (!this.data.photoPath) return;
    wx.previewImage({ urls: [this.data.photoPath] });
  },

  onRemovePhoto() {
    this.setData({ photoPath: '', photoName: '', status: '', resultUrl: '', errorMessage: '' });
  },

  /* ---------------- 生成 ---------------- */

  onStart() {
    const style = this.data.activeStyle;
    if (!style) {
      wx.showToast({ title: '请先选择款式', icon: 'none' });
      return;
    }
    if (!this.data.photoPath) {
      wx.showToast({ title: '请先上传照片', icon: 'none' });
      return;
    }
    if (this.data.submitting || this.data.status === 'processing') return;

    this.setData({
      submitting: true,
      status: 'processing',
      progress: 0,
      statusText: '正在提交任务…',
      resultUrl: '',
      errorMessage: ''
    });

    api
      .startTryOn(this.data.photoPath, style.brandName)
      .then(res => {
        const data = res || {};
        const taskId = data.task_id || data.taskId || (data.data && data.data.task_id);
        const token = data.access_token || data.accessToken || (data.data && data.data.access_token);
        if (!taskId || !token) throw new Error('任务创建失败，请稍后重试');

        this.setData({ taskId, accessToken: token, submitting: false, statusText: '生成中，请耐心等待…' });
        this.persistTask(taskId, token, style.brandName);
        this.startPolling();
      })
      .catch(err => {
        this.setData({
          submitting: false,
          status: 'failed',
          errorMessage: (err && err.message) || '生成失败，请重试'
        });
      });
  },

  startPolling() {
    this.stopPolling();
    const startedAt = Date.now();
    const timeout = CONFIG.tryOnTimeout;

    const tick = () => {
      const taskId = this.data.taskId;
      const token = this.data.accessToken;
      if (!taskId || !token) return;

      api.getTryOnStatus(taskId, token).then(
        res => {
          const raw = (res && (res.status || (res.data && res.data.status))) || 'processing';
          const status = raw === 'pending' ? 'processing' : raw;
          const progress =
            (res && (res.progress || (res.data && res.data.progress))) || (status === 'processing' ? 30 : 0);
          const resultUrl =
            (res && (res.result_image_url || res.result_url || res.image_url)) ||
            (res && res.data && (res.data.result_image_url || res.data.result_url));

          if (status === 'completed' || status === 'success' || status === 'done') {
            this.stopPolling();
            this.setData({
              status: 'completed',
              progress: 100,
              statusText: '已生成',
              resultUrl: this.resolveResultUrl(resultUrl)
            });
            this.saveToHistory();
            this.clearTask();
            return;
          }

          if (status === 'failed' || status === 'error') {
            this.stopPolling();
            this.setData({
              status: 'failed',
              errorMessage: (res && res.error_message) || '生成失败，请重试'
            });
            this.clearTask();
            return;
          }

          this.setData({ status: 'processing', progress, statusText: '生成中，请耐心等待…' });

          if (Date.now() - startedAt > timeout) {
            this.stopPolling();
            this.setData({ status: 'failed', errorMessage: '生成超时，请稍后重试' });
            this.clearTask();
            return;
          }
          this.timer = setTimeout(tick, CONFIG.tryOnPollInterval);
        },
        err => {
          // 网络抖动时退避重试，超时后报错
          if (Date.now() - startedAt > timeout) {
            this.stopPolling();
            this.setData({
              status: 'failed',
              errorMessage: (err && err.message) || '生成失败，请重试'
            });
            this.clearTask();
            return;
          }
          this.timer = setTimeout(tick, CONFIG.tryOnPollInterval * 2);
        }
      );
    };

    tick();
  },

  stopPolling() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  },

  /** 结果地址归一化：支持绝对地址、/static 与 /api 前缀 */
  resolveResultUrl(url) {
    const u = String(url || '');
    if (!u) return '';
    if (/^https?:\/\//.test(u)) return u;
    if (u.indexOf('/api/') === 0) return CONFIG.staticBase + u;
    return api.buildStaticUrl(u);
  },

  /* ---------------- 结果操作 ---------------- */

  onPreviewResult() {
    if (!this.data.resultUrl) return;
    wx.previewImage({ urls: [this.data.resultUrl] });
  },

  onRegenerate() {
    this.setData({ status: '', progress: 0, resultUrl: '', errorMessage: '', statusText: '' });
    this.onStart();
  },

  onSaveToAlbum() {
    const url = this.data.resultUrl;
    if (!url) return;
    wx.showLoading({ title: '保存中…', mask: true });
    wx.downloadFile({
      url,
      success: res => {
        if (res.statusCode !== 200) {
          wx.hideLoading();
          wx.showToast({ title: '图片下载失败', icon: 'none' });
          return;
        }
        wx.saveImageToPhotosAlbum({
          filePath: res.tempFilePath,
          success: () => {
            wx.hideLoading();
            wx.showToast({ title: '已保存到相册', icon: 'success' });
          },
          fail: err => {
            wx.hideLoading();
            const msg = (err && err.errMsg) || '';
            if (msg.indexOf('auth deny') > -1 || msg.indexOf('authorize') > -1) {
              wx.showModal({
                title: '需要相册权限',
                content: '请在设置中开启「保存到相册」权限后重试',
                confirmText: '去设置',
                success: r => {
                  if (r.confirm) wx.openSetting({});
                }
              });
            } else {
              wx.showToast({ title: '保存失败，请重试', icon: 'none' });
            }
          }
        });
      },
      fail: () => {
        wx.hideLoading();
        wx.showToast({ title: '图片下载失败，请检查网络', icon: 'none' });
      }
    });
  },

  /* ---------------- 本地记录 ---------------- */

  /**
   * 任务态本地短时缓存。
   * 后端轮询仍要求 query 带 access_token（勿改 Header）；
   * 此处写入明文 token，但附带过期时间，超时自动丢弃以缩小落盘窗口。
   */
  persistTask(taskId, accessToken, brandName) {
    try {
      wx.setStorageSync(TASK_STORAGE_KEY, {
        taskId,
        accessToken,
        brandName,
        time: Date.now(),
        expiresAt: Date.now() + (CONFIG.tryOnTaskMaxAge || 10 * 60 * 1000)
      });
    } catch (e) {
      // 忽略
    }
  },

  clearTask() {
    try {
      wx.removeStorageSync(TASK_STORAGE_KEY);
    } catch (e) {
      // 忽略
    }
  },

  /** 冷启动时恢复未完成的任务（超时则丢弃本地明文 token） */
  restoreTask() {
    try {
      const state = wx.getStorageSync(TASK_STORAGE_KEY);
      if (!state || !state.taskId || !state.accessToken) return;
      const maxAge = CONFIG.tryOnTaskMaxAge || 10 * 60 * 1000;
      const expired =
        (state.expiresAt && Date.now() > state.expiresAt) ||
        (state.time && Date.now() - state.time > maxAge);
      if (expired) {
        this.clearTask();
        return;
      }
      this.setData({
        taskId: state.taskId,
        accessToken: state.accessToken,
        status: 'processing',
        statusText: '正在恢复生成进度…'
      });
      this.pendingBrand = state.brandName || '';
      setTimeout(() => {
        if (this.pendingBrand) {
          getApp().globalData.tryOnBrand = this.pendingBrand;
          this.applyPendingBrand();
        }
        this.startPolling();
      }, 300);
    } catch (e) {
      // 忽略
    }
  },

  /** 记录到「我的试穿」本地列表（与 Web 端一致：结果仅本地可见） */
  saveToHistory() {
    const style = this.data.activeStyle || {};
    const url = this.data.resultUrl;
    if (!url) return;
    try {
      const list = wx.getStorageSync(CONFIG.storage.tryOnHistory) || [];
      list.unshift({
        brandName: style.baseBrand || style.brandName || '',
        displayName: fmt.getDisplayName({ name: style.brandName }),
        resultUrl: url,
        time: Date.now()
      });
      wx.setStorageSync(CONFIG.storage.tryOnHistory, list.slice(0, 20));
    } catch (e) {
      // 忽略
    }
  },

  onShareAppMessage() {
    const style = this.data.activeStyle || {};
    return {
      title: (style.baseBrand || '南意秋棠') + ' · AI 试穿',
      path: '/pages/tryon/tryon'
    };
  }
});

/**
 * 款式详情
 * 数据来源：GET /api/brand/{name}（展平后与 Web 端详情字段一致）
 * 派生文案（拼音副标题 / 诗句 / 简述）由 utils/format.js 统一处理，保证多端口径一致
 */
const CONFIG = require('../../utils/config');
const api = require('../../utils/api');
const fmt = require('../../utils/format');
const filt = require('../../utils/filter');
const auth = require('../../utils/auth');

Page({
  data: {
    statusBarHeight: 20,
    navBarHeight: 44,
    navTotalHeight: 64,
    capsuleGap: 10,
    safeBottom: 0,

    name: '',
    loading: true,
    error: '',

    displayName: '',
    subtitle: '',
    tags: [],
    params: [],
    verses: [],
    brief: '',
    gallery: [],
    galleryIndex: 0,
    likeCount: 0,
    liked: false,
    likeBusy: false,
    related: [],
    canShareCard: false,

    // 评价区
    reviews: [],
    reviewStats: { count: 0, avg_rating: null },
    reviewLoading: false,
    reviewSubmitting: false,
    reviewRating: 0,
    reviewContent: '',
    reviewHasMore: false,
    reviewPage: 1
  },

  onLoad(options) {
    const g = getApp().globalData || {};
    this.setData({
      statusBarHeight: g.statusBarHeight || 20,
      navBarHeight: g.navBarHeight || 44,
      navTotalHeight: g.navTotalHeight || 64,
      capsuleGap: g.capsuleGap || 10,
      safeBottom: g.safeBottom || 0
    });

    const name = decodeURIComponent(options.name || options.brand || '');
    if (!name) {
      this.setData({ loading: false, error: '缺少款式参数' });
      return;
    }
    this.setData({ name });
    this.load(name);

    if (options.to === 'comment') {
      this.autoOpenComment = true;
    }
  },

  load(name) {
    this.setData({ loading: true, error: '' });

    Promise.all([api.getBrandDetail(name), api.getAllBrands().catch(() => ({ brands: [] }))]).then(
      results => {
        const detail = results[0];
        const all = (results[1] && results[1].brands) || [];
        const info = detail.brandInfo || {};

        const gallery = this.buildGallery(detail, info);
        const imageCount = detail.imageCount || 0;
        const videoCount = detail.videoCount || 0;
        const inspiration = info.inspiration_origin || '';

        this.brandInfo = info;

        this.setData({
          loading: false,
          displayName: fmt.getDisplayName({
            name: info.name || info.brand_name || name,
            preview_images: (detail.images || []).slice(0, 1)
          }),
          subtitle: fmt.getSubtitle(info.name || info.brand_name || name, inspiration),
          tags: fmt.getDetailTags(info),
          params: [
            { label: '年份', value: info.year ? String(info.year) : '—' },
            {
              label: '材质',
              value: info.material && info.material !== 'N/A' ? info.material : '—'
            },
            {
              label: '印制',
              value: info.print_size && info.print_size !== 'N/A' ? fmt.getPrintShort(info.print_size) : '—'
            },
            { label: '素材', value: '图' + imageCount + '·视' + videoCount }
          ],
          verses: fmt.getVerseLines(inspiration),
          brief: info.inspiration_brief || fmt.getBrief(inspiration),
          gallery,
          galleryIndex: 0,
          likeCount: fmt.formatCount(info.like_count),
          related: this.buildRelated(all, info)
        });

        // 上报浏览（未登录静默跳过）
        const brandKey = info.brand_name || info.name || name;
        auth.recordBrowse(brandKey);
        this.pushRecent(info);
        this.fetchLikeStatus(brandKey);
        this.loadReviews(1, false).then(() => {
          if (this.autoOpenComment) {
            this.autoOpenComment = false;
            setTimeout(() => {
              wx.pageScrollTo({ selector: '#review-section', duration: 320 });
            }, 280);
          }
        });
      },
      err => {
        this.setData({ loading: false, error: (err && err.message) || '款式加载失败' });
      }
    );
  },

  /** 轮播图：优先 preview_images，回退 images 中的概念图/设计图 */
  buildGallery(detail, info) {
    const prefer = (info.preview_images && info.preview_images.length ? info.preview_images : null) || [];
    const images = detail.images || [];
    let source = prefer.length ? prefer : images;
    if (!source.length) {
      source = (images || []).filter(i => i.media_type !== 'video');
    }
    const urls = [];
    source.forEach(item => {
      const url = api.buildStaticUrl(item);
      if (url && urls.indexOf(url) === -1) urls.push(url);
    });
    return urls.slice(0, 9);
  },

  /** 猜你也喜欢 */
  buildRelated(all, info) {
    if (!all || !all.length) return [];
    return filt.pickRelated(all, info, 3).map(b => ({
      name: fmt.getBaseName(b.name || b.brand_name || ''),
      rawName: b.name || b.brand_name || '',
      cover: api.pickPreviewImage(b)
    }));
  },

  /** 写入最近浏览（本地） */
  pushRecent(info) {
    try {
      const app = getApp();
      const key = CONFIG.storage.recentViews;
      const list = (app.globalData.recentViews || []).filter(
        item => item.name !== (info.brand_name || info.name)
      );
      list.unshift({
        name: info.brand_name || info.name || '',
        displayName: fmt.getDisplayName({ name: info.name || info.brand_name }),
        cover: api.pickPreviewImage({ preview_images: info.images || [] }),
        time: Date.now()
      });
      const trimmed = list.slice(0, CONFIG.recentViewLimit);
      app.globalData.recentViews = trimmed;
      wx.setStorageSync(key, trimmed);
    } catch (e) {
      // 忽略本地存储异常
    }
  },

  /* ---------------- 交互 ---------------- */

  onSwiperChange(e) {
    this.setData({ galleryIndex: e.detail.current });
  },

  onPreviewImage(e) {
    const index = Number(e.currentTarget.dataset.index) || 0;
    if (!this.data.gallery.length) return;
    wx.previewImage({
      current: this.data.gallery[index],
      urls: this.data.gallery
    });
  },

  onPreviewGallery() {
    if (!this.data.gallery.length) {
      wx.showToast({ title: '暂无图集', icon: 'none' });
      return;
    }
    wx.previewImage({ current: this.data.gallery[0], urls: this.data.gallery });
  },

  onTapTag(e) {
    const value = e.currentTarget.dataset.value || '';
    if (!value) return;
    getApp().globalData.pendingFilters = { year: value.replace(/[^0-9]/g, '') || filt.ALL };
    wx.navigateTo({ url: '/pages/fabrics/fabrics' });
  },

  fetchLikeStatus(brandName) {
    if (!brandName) return;
    api.getLikeStatus(brandName).then(
      res => {
        this.setData({
          liked: !!res.liked,
          likeCount: fmt.formatCount(res.likeCount)
        });
      },
      () => {
        // 失败时保留详情接口带来的 like_count
      }
    );
  },

  onToggleLike() {
    if (this.data.likeBusy) return;
    const info = this.brandInfo || {};
    const brandName = info.brand_name || info.name || this.data.name;
    if (!brandName) return;
    this.setData({ likeBusy: true });
    api
      .toggleLike(brandName)
      .then(res => {
        this.setData({
          likeBusy: false,
          liked: !!res.liked,
          likeCount: fmt.formatCount(res.likeCount)
        });
        wx.showToast({
          title: res.message || (res.liked ? '点赞成功' : '已取消点赞'),
          icon: 'none',
          duration: 1200
        });
      })
      .catch(err => {
        this.setData({ likeBusy: false });
        wx.showToast({ title: (err && err.message) || '点赞失败', icon: 'none' });
      });
  },

  /* ---------------- 评价 ---------------- */

  loadReviews(page, append) {
    const info = this.brandInfo || {};
    const brandName = info.brand_name || info.name || this.data.name;
    if (!brandName) return Promise.resolve();
    this.setData({ reviewLoading: !append });
    return api.getBrandReviews(brandName, page, 10).then(
      payload => {
        const data = payload || {};
        const list = (data.reviews || []).map(r => ({
          id: r.id || r._id || Math.random(),
          rating: r.rating || 0,
          content: r.content || '',
          nickname: r.is_anonymous
            ? '匿名用户'
            : r.nickname || r.user_nickname || r.username || '用户',
          time: this.formatReviewTime(r.created_at || r.createdAt || '')
        }));
        const stats = data.stats || {};
        const pagination = data.pagination || {};
        this.setData({
          reviewLoading: false,
          reviews: append ? (this.data.reviews || []).concat(list) : list,
          reviewStats: {
            count: stats.count != null ? stats.count : list.length,
            avg_rating: stats.avg_rating != null ? stats.avg_rating : null
          },
          reviewPage: page,
          reviewHasMore: !!pagination.has_more
        });
      },
      () => {
        this.setData({ reviewLoading: false });
        if (!append) {
          wx.showToast({ title: '评价加载失败', icon: 'none' });
        }
      }
    );
  },

  formatReviewTime(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return String(iso).slice(0, 10);
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return d.getFullYear() + '-' + m + '-' + day;
  },

  onLoadMoreReviews() {
    if (!this.data.reviewHasMore || this.data.reviewLoading) return;
    this.loadReviews((this.data.reviewPage || 1) + 1, true);
  },

  onPickRating(e) {
    const rating = Number(e.currentTarget.dataset.rating) || 0;
    this.setData({ reviewRating: rating });
  },

  onReviewInput(e) {
    this.setData({ reviewContent: e.detail.value || '' });
  },

  onSubmitReview() {
    if (this.data.reviewSubmitting) return;
    if (!auth.isLogged()) {
      wx.showModal({
        title: '需要登录',
        content: '提交评价请先登录。微信登录暂未开通时可使用手机号登录。',
        confirmText: '去登录',
        success: r => {
          if (r.confirm) wx.navigateTo({ url: '/pages/login/login' });
        }
      });
      return;
    }
    const rating = this.data.reviewRating || 0;
    const content = String(this.data.reviewContent || '').trim();
    if (!rating && !content) {
      wx.showToast({ title: '请评分或填写内容', icon: 'none' });
      return;
    }
    const info = this.brandInfo || {};
    const brandName = info.brand_name || info.name || this.data.name;
    this.setData({ reviewSubmitting: true });
    api
      .submitReview({
        brand_name: brandName,
        rating: rating || undefined,
        content: content || undefined,
        is_anonymous: true
      })
      .then(() => {
        this.setData({ reviewSubmitting: false, reviewRating: 0, reviewContent: '' });
        wx.showToast({ title: '评价已提交', icon: 'success' });
        this.loadReviews(1, false);
      })
      .catch(err => {
        this.setData({ reviewSubmitting: false });
        const status = err && err.statusCode;
        if (status === 401) {
          wx.showModal({
            title: '登录已过期',
            content: '请重新登录后再提交评价。',
            confirmText: '去登录',
            success: r => {
              if (r.confirm) wx.navigateTo({ url: '/pages/login/login' });
            }
          });
          return;
        }
        wx.showToast({ title: (err && err.message) || '提交失败', icon: 'none' });
      });
  },

  onTapRelated(e) {
    const name = e.currentTarget.dataset.name;
    if (!name) return;
    wx.navigateTo({ url: '/pages/detail/detail?name=' + encodeURIComponent(name) });
  },

  /** 底部主按钮：AI 试穿 */
  onGoTryOn() {
    const info = this.brandInfo || {};
    getApp().globalData.tryOnBrand = fmt.getBaseName(info.name || info.brand_name || this.data.name);
    wx.switchTab({ url: '/pages/tryon/tryon' });
  },

  onBack() {
    wx.navigateBack({
      fail() {
        wx.switchTab({ url: '/pages/index/index' });
      }
    });
  },

  /** 生成分享卡片图片（canvas 2d 绘制，与 Web 端 share-card 功能对齐） */
  onShareCard() {
    if (this.generating) return;
    this.generating = true;
    wx.showLoading({ title: '生成中…', mask: true });

    this.drawShareCard()
      .then(path => {
        wx.hideLoading();
        this.generating = false;
        if (typeof wx.showShareImageMenu === 'function') {
          wx.showShareImageMenu({
            path,
            fail: () => this.saveToAlbum(path)
          });
        } else {
          this.saveToAlbum(path);
        }
      })
      .catch(() => {
        wx.hideLoading();
        this.generating = false;
        wx.showToast({ title: '生成失败，请稍后重试', icon: 'none' });
      });
  },

  /** 兜底：保存到相册 */
  saveToAlbum(path) {
    wx.saveImageToPhotosAlbum({
      filePath: path,
      success() {
        wx.showToast({ title: '已保存到相册', icon: 'none' });
      },
      fail() {
        wx.showToast({ title: '长按图片可保存 / 分享', icon: 'none' });
      }
    });
  },

  /** canvas 2d 绘制分享卡片 */
  drawShareCard() {
    const info = this.brandInfo || {};
    const data = this.data;

    return new Promise((resolve, reject) => {
      const query = wx.createSelectorQuery();
      query
        .select('#shareCard')
        .fields({ node: true, size: true })
        .exec(res => {
          const item = res && res[0];
          if (!item || !item.node) {
            reject(new Error('画布未就绪'));
            return;
          }
          const canvas = item.node;
          const W = 600;
          const H = 900;
          const dpr = Math.min(((wx.getWindowInfo ? wx.getWindowInfo().pixelRatio : 2) || 2), 3);
          canvas.width = W * dpr;
          canvas.height = H * dpr;
          const ctx = canvas.getContext('2d');
          ctx.scale(dpr, dpr);

          const paint = img => {
            try {
              // 背景
              ctx.fillStyle = '#F4F0E4';
              ctx.fillRect(0, 0, W, H);

              // 主图（居中裁剪）
              const imgH = 470;
              if (img) {
                this.drawCover(ctx, img, 0, 0, W, imgH);
              } else {
                ctx.fillStyle = '#E6E1D4';
                ctx.fillRect(0, 0, W, imgH);
              }

              // 金线
              ctx.fillStyle = '#C9AE74';
              ctx.fillRect(0, imgH, W, 3);

              const cx = W / 2;
              ctx.textAlign = 'center';

              // 名称
              ctx.fillStyle = '#191512';
              ctx.font = '600 42px serif';
              ctx.fillText(data.displayName || data.name, cx, imgH + 76);

              // 副标题
              if (data.subtitle) {
                ctx.fillStyle = '#A98B4E';
                ctx.font = '17px sans-serif';
                ctx.fillText(data.subtitle.split('').join(' '), cx, imgH + 112);
              }

              // 分隔线
              ctx.fillStyle = '#DCD3BF';
              ctx.fillRect(cx - 40, imgH + 138, 80, 1);

              // 诗句
              if (data.verses && data.verses.length) {
                ctx.fillStyle = '#4A4239';
                ctx.font = '20px serif';
                data.verses.forEach((line, i) => {
                  ctx.fillText(line, cx, imgH + 186 + i * 36);
                });
              }

              // 参数行
              ctx.fillStyle = '#6B6257';
              ctx.font = '15px sans-serif';
              const meta = [info.year, info.material, info.print_size].filter(Boolean).join(' · ');
              if (meta) ctx.fillText(meta, cx, H - 120);

              // 落款
              ctx.fillStyle = '#9A9184';
              ctx.font = '14px sans-serif';
              ctx.fillText('南 意 秋 棠 · 古 典 中 式', cx, H - 78);

              // 底部细线
              ctx.fillStyle = '#DCD3BF';
              ctx.fillRect(cx - 30, H - 56, 60, 1);

              ctx.fillStyle = '#B4AA9A';
              ctx.font = '13px sans-serif';
              ctx.fillText('products.nanyiqiutang.cn', cx, H - 30);
            } catch (e) {
              reject(e);
              return;
            }

            wx.canvasToTempFilePath(
              {
                canvas,
                x: 0,
                y: 0,
                width: W,
                height: H,
                destWidth: W * dpr,
                destHeight: H * dpr,
                success: r => resolve(r.tempFilePath),
                fail: reject
              },
              this
            );
          };

          const cover = data.gallery[0];
          if (!cover) {
            paint(null);
            return;
          }
          const img = canvas.createImage();
          img.onload = () => paint(img);
          img.onerror = () => paint(null);
          img.src = cover;
        });
    });
  },

  /** 居中裁剪绘制（等价于 aspectFill） */
  drawCover(ctx, img, x, y, w, h) {
    const iw = img.width;
    const ih = img.height;
    if (!iw || !ih) return;
    const ir = iw / ih;
    const r = w / h;
    let sx = 0;
    let sy = 0;
    let sw = iw;
    let sh = ih;
    if (ir > r) {
      sh = ih;
      sw = sh * r;
      sx = (iw - sw) / 2;
    } else {
      sw = iw;
      sh = sw / r;
      sy = (ih - sh) / 2;
    }
    ctx.drawImage(img, sx, sy, sw, sh, x, y, w, h);
  },

  onShareAppMessage() {
    const info = this.brandInfo || {};
    const title = info.title || (this.data.displayName + ' · ' + CONFIG.brand.name);
    return {
      title,
      path: '/pages/detail/detail?name=' + encodeURIComponent(info.brand_name || this.data.name),
      imageUrl: this.data.gallery[0] || ''
    };
  }
});

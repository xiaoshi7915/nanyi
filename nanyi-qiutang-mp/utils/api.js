/**
 * 南意秋棠 · 接口层
 * 与 Web 端 js/api.js 一一对应，保证多端数据与逻辑一致
 */
const CONFIG = require('./config');
const { request, upload } = require('./request');

/* ------------------------------------------------------------------ *
 * 静态资源地址
 * ------------------------------------------------------------------ */

/** 将静态路径规范为可直接访问的绝对地址 */
function buildStaticUrl(input) {
  let p = '';
  if (typeof input === 'string') {
    p = input;
  } else if (input && typeof input === 'object') {
    p = input.original || input.url || input.thumbnail || input.relative_path || '';
  }
  if (!p) return '';
  if (/^https?:\/\//.test(p)) return p;

  if (p.indexOf('/static/') !== 0) {
    p = '/static/images/' + (p.charAt(0) === '/' ? p.slice(1) : p);
  }

  // 逐段编码：中文段需要编码，已编码段保持原样
  p = p
    .split('/')
    .map(seg => {
      if (!seg) return seg;
      if (/[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef（）]/.test(seg)) {
        return encodeURIComponent(seg);
      }
      return seg;
    })
    .join('/');

  return CONFIG.staticBase + p;
}

/** 取品牌主图（优先 preview_images，回退 images） */
function pickPreviewImage(brand) {
  if (!brand) return '';
  const pv = brand.preview_images || [];
  let raw = '';
  if (pv.length) {
    raw = pv[0];
  } else if (brand.images && brand.images.length) {
    raw = brand.images[0];
  } else if (brand.preview_image) {
    raw = brand.preview_image;
  }
  return buildStaticUrl(raw);
}

/** 取品牌预览图数组（最多 count 张） */
function pickPreviewImages(brand, count) {
  if (!brand) return [];
  const n = count || 3;
  const list = (brand.preview_images && brand.preview_images.length ? brand.preview_images : brand.images) || [];
  const out = [];
  for (let i = 0; i < list.length && out.length < n; i++) {
    const url = buildStaticUrl(list[i]);
    if (url && out.indexOf(url) === -1) out.push(url);
  }
  return out;
}

/* ------------------------------------------------------------------ *
 * 统一响应解包
 * 后端响应形如 { success, message, data }
 * ------------------------------------------------------------------ */

function unwrap(body) {
  if (body && typeof body === 'object' && body.success === false) {
    const err = new Error(body.message || body.error || '接口返回失败');
    err.isApiError = true;
    err.body = body;
    throw err;
  }
  if (body && typeof body === 'object' && body.data !== undefined) {
    return body.data;
  }
  return body;
}

/* ------------------------------------------------------------------ *
 * 全量品牌内存缓存（首页 / 筛选页 / 列表页 / 详情页共用，避免重复拉取 800KB）
 * ------------------------------------------------------------------ */

let _brandsCache = null;
let _brandsPromise = null;

/** 清空品牌缓存（下拉刷新时调用） */
function clearBrandCache() {
  _brandsCache = null;
  _brandsPromise = null;
}

/** 读取全量品牌（带缓存与并发合并） */
function getAllBrands(force) {
  if (force) clearBrandCache();
  if (_brandsCache) return Promise.resolve(_brandsCache);
  if (_brandsPromise) return _brandsPromise;

  _brandsPromise = api
    .getImages({ page: 1, perPage: CONFIG.brandPageSize, loadAll: true })
    .then(res => {
      _brandsCache = res;
      _brandsPromise = null;
      return res;
    })
    .catch(err => {
      _brandsPromise = null;
      throw err;
    });

  return _brandsPromise;
}

/* ------------------------------------------------------------------ *
 * 接口定义
 * ------------------------------------------------------------------ */

const api = {
  buildStaticUrl,
  pickPreviewImage,
  pickPreviewImages,

  /** 健康检查 GET /health */
  health() {
    return request({ url: '/health', auth: false });
  },

  /** 筛选选项 GET /filters —— 返回 { years, materials, theme_series, print_sizes, brand_counts } */
  getFilters() {
    return request({ url: '/filters', auth: false }).then(body => {
      const data = (body && body.data) || {};
      const inner = data.filters || {};
      return {
        years: data.years || inner.years || [],
        materials: data.materials || inner.materials || [],
        themeSeries: data.theme_series || inner.theme_series || [],
        printSizes: data.print_sizes || inner.print_sizes || [],
        brandCounts: data.brand_counts || inner.brand_counts || {}
      };
    });
  },

  /** 图片/品牌列表 GET /images */
  getImages(params) {
    const p = params || {};
    const query = [];
    query.push('page=' + (p.page || 1));
    query.push('per_page=' + (p.perPage || CONFIG.brandPageSize));
    if (p.loadAll) query.push('load_all=true');
    if (p.year) query.push('year=' + encodeURIComponent(p.year));
    if (p.material) query.push('material=' + encodeURIComponent(p.material));
    if (p.themeSeries) query.push('theme_series=' + encodeURIComponent(p.themeSeries));
    if (p.printSize) query.push('print_size=' + encodeURIComponent(p.printSize));

    return request({ url: '/images?' + query.join('&'), auth: false }).then(body => {
      const brands = (body && body.brands) || [];
      return {
        brands,
        total: (body && body.total) || 0,
        pagination: (body && body.pagination) || {}
      };
    });
  },

  /** 全量品牌（与 Web 端 load_all 行为一致，一次取回 176 款，带内存缓存） */
  getAllBrands,
  clearBrandCache,

  /** 品牌详情 GET /brand/{name} —— 展平 data，字段与 Web 端保持一致 */
  getBrandDetail(brandName) {
    const name = encodeURIComponent(brandName);
    return request({ url: '/brand/' + name, auth: false }).then(body => {
      const data = (body && body.data) || {};
      const info = data.brand_info || {};
      const images = data.images || info.images || [];
      const videos = data.videos || info.videos || [];
      return {
        success: true,
        message: body && body.message,
        brandInfo: info,
        images,
        videos,
        imageCount: data.imageCount != null ? data.imageCount : info.imageCount || images.length,
        videoCount: data.videoCount != null ? data.videoCount : videos.length
      };
    });
  },

  /** 品牌图片 GET /brand/{name}/images */
  getBrandImages(brandName) {
    const name = encodeURIComponent(brandName);
    return request({ url: '/brand/' + name + '/images', auth: false }).then(body => {
      const data = (body && body.data) || {};
      return {
        images: data.images || [],
        videos: data.videos || [],
        imageCount: data.imageCount || 0,
        videoCount: data.videoCount || 0
      };
    });
  },

  /** AI 试穿款式 GET /try-on/styles */
  getTryOnStyles(brandName) {
    let url = '/try-on/styles';
    if (brandName) url += '?brand_name=' + encodeURIComponent(brandName);
    return request({ url, auth: false }).then(body => {
      const data = (body && body.data) || {};
      const styles = data.styles || (body && body.styles) || [];
      return styles.map(s => ({
        brandName: s.brand_name || s.base_brand || '',
        baseBrand: s.base_brand || s.brand_name || '',
        color: s.color || '',
        hasColor: !!s.has_color,
        previewImage: buildStaticUrl(s.preview_image)
      }));
    });
  },

  /** 启动 AI 试衣 POST /try-on/start（multipart，字段 brand_name + user_image） */
  startTryOn(filePath, brandName) {
    return upload({
      url: '/try-on/start',
      filePath,
      name: 'user_image',
      formData: { brand_name: brandName },
      timeout: 120000
    }).then(body => unwrap(body));
  },

  /**
   * 查询 AI 试衣任务状态
   * 注意：后端当前只认 query 参数 access_token，勿擅自改为 Header，以免破坏联调。
   * GET /try-on/status/{taskId}?access_token=
   */
  getTryOnStatus(taskId, accessToken) {
    const url =
      '/try-on/status/' + encodeURIComponent(taskId) + '?access_token=' + encodeURIComponent(accessToken || '');
    return request({ url, auth: false, timeout: 60000 }).then(body => unwrap(body));
  },

  /** 品牌评价列表 GET /reviews/brand/{name} */
  getBrandReviews(brandName, page, limit) {
    const name = encodeURIComponent(brandName);
    const p = page || 1;
    const l = limit || 20;
    return request({ url: '/reviews/brand/' + name + '?page=' + p + '&limit=' + l, auth: false }).then(body =>
      unwrap(body)
    );
  },

  /**
   * 提交评价 POST /reviews
   * 默认带 JWT（auth: true）；未登录时由页面拦截并引导登录。
   */
  submitReview(payload) {
    return request({ url: '/reviews', method: 'POST', data: payload, auth: true }).then(body => unwrap(body));
  },

  /** 点赞状态 GET /like/card/{brand} —— 与 Web 同源 */
  getLikeStatus(brandName) {
    const name = encodeURIComponent(brandName);
    return request({ url: '/like/card/' + name, auth: false }).then(body => {
      const data = (body && body.data) || body || {};
      return {
        liked: !!(data.liked || data.user_liked),
        likeCount: data.like_count != null ? data.like_count : 0
      };
    });
  },

  /** 切换点赞 POST /like/card/{brand} —— 与 Web 同源 */
  toggleLike(brandName) {
    const name = encodeURIComponent(brandName);
    return request({ url: '/like/card/' + name, method: 'POST', auth: false }).then(body => {
      const data = (body && body.data) || body || {};
      return {
        liked: !!(data.liked || data.user_liked),
        likeCount: data.like_count != null ? data.like_count : 0,
        message: (body && body.message) || ''
      };
    });
  }
};

module.exports = api;

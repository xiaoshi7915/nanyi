/**
 * 网络请求封装
 * 统一处理：基础域名拼接、鉴权头、超时、错误码、401 自动续期重试
 */
const CONFIG = require('./config');

/** 读取本地 access token */
function readToken() {
  try {
    return wx.getStorageSync(CONFIG.storage.accessToken) || '';
  } catch (e) {
    return '';
  }
}

/** 拼接完整 URL */
function buildUrl(path) {
  if (/^https?:\/\//.test(path)) return path;
  return CONFIG.apiBase + (path.charAt(0) === '/' ? path : '/' + path);
}

/** 业务错误对象 */
function makeError(message, extra) {
  const err = new Error(message || '请求失败');
  err.isApiError = true;
  if (extra) Object.assign(err, extra);
  return err;
}

/**
 * 发起请求
 * @param {object} options
 * @param {string} options.url 接口路径，如 '/images'
 * @param {string} [options.method] 默认 GET
 * @param {object} [options.data] 请求数据
 * @param {object} [options.header] 额外请求头
 * @param {boolean} [options.auth] 是否强制携带 token，默认自动
 * @param {boolean} [options.silent] 是否静默（不弹 toast）
 * @param {boolean} [options.raw] 是否返回原始响应体（含 success/message/data），默认 true
 * @param {number} [options.timeout]
 * @param {boolean} [options._retried] 内部标记，防止无限重试
 */
function request(options) {
  const opts = options || {};
  const url = buildUrl(opts.url);
  const method = (opts.method || 'GET').toUpperCase();

  const header = Object.assign(
    {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      // 多端审计/限流标识；后端未强制校验，仅作客户端声明
      'X-Client': 'miniprogram'
    },
    opts.header || {}
  );

  if (opts.auth !== false) {
    const token = readToken();
    if (token) header.Authorization = 'Bearer ' + token;
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url,
      method,
      data: opts.data || undefined,
      header,
      timeout: opts.timeout || CONFIG.timeout,
      success(res) {
        const status = res.statusCode;

        if (status >= 200 && status < 300) {
          resolve(res.data);
          return;
        }

        if (status === 401 && !opts._retried && opts.auth !== false) {
          // 尝试用 refresh token 续期后重放一次
          let auth = null;
          try {
            auth = require('./auth');
          } catch (e) {
            auth = null;
          }
          if (auth && typeof auth.refreshTokens === 'function') {
            auth
              .refreshTokens()
              .then(ok => {
                if (ok) {
                  request(Object.assign({}, opts, { _retried: true })).then(resolve, reject);
                } else {
                  reject(makeError('登录已过期，请重新登录', { statusCode: 401, code: 'AUTH_EXPIRED' }));
                }
              })
              .catch(() => {
                reject(makeError('登录已过期，请重新登录', { statusCode: 401, code: 'AUTH_EXPIRED' }));
              });
            return;
          }
          reject(makeError('登录已过期，请重新登录', { statusCode: 401, code: 'AUTH_EXPIRED' }));
          return;
        }

        let msg = '请求失败（' + status + '）';
        const body = res.data;
        if (body && typeof body === 'object') {
          msg = body.message || body.error || body.msg || msg;
        }
        reject(makeError(msg, { statusCode: status, body }));
      },
      fail(err) {
        const raw = (err && err.errMsg) || '';
        let msg = '网络连接失败，请检查网络后重试';
        if (raw.indexOf('timeout') > -1) msg = '请求超时，请稍后重试';
        reject(makeError(msg, { isNetworkError: true, raw }));
      }
    });
  });
}

/** 上传文件（multipart/form-data） */
function upload(options) {
  const opts = options || {};
  const header = Object.assign({ 'X-Client': 'miniprogram' }, opts.header || {});
  if (opts.auth !== false) {
    const token = readToken();
    if (token) header.Authorization = 'Bearer ' + token;
  }

  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: buildUrl(opts.url),
      filePath: opts.filePath,
      name: opts.name || 'file',
      formData: opts.formData || {},
      header,
      timeout: opts.timeout || CONFIG.timeout,
      success(res) {
        const status = res.statusCode;
        let body = res.data;
        if (typeof body === 'string') {
          try {
            body = JSON.parse(body);
          } catch (e) {
            body = { message: body };
          }
        }
        if (status >= 200 && status < 300) {
          resolve(body);
          return;
        }
        const msg = (body && (body.message || body.error)) || '上传失败（' + status + '）';
        reject(makeError(msg, { statusCode: status, body }));
      },
      fail(err) {
        reject(makeError('上传失败，请重试', { isNetworkError: true, raw: (err && err.errMsg) || '' }));
      }
    });
  });
}

/** 轻提示 */
function toast(title, icon) {
  wx.showToast({ title: title || '操作失败', icon: icon || 'none', duration: 1800 });
}

/** 带 loading 的请求包装 */
function withLoading(promise, title) {
  wx.showLoading({ title: title || '加载中', mask: true });
  return promise.then(
    res => {
      wx.hideLoading();
      return res;
    },
    err => {
      wx.hideLoading();
      throw err;
    }
  );
}

module.exports = {
  request,
  upload,
  buildUrl,
  toast,
  withLoading,
  readToken,
  makeError
};

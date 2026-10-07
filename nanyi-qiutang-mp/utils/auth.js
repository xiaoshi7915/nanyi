/**
 * 登录态与用户中心
 *
 * 复用 Web 端同名接口：
 *   POST /auth/register | /auth/login | /auth/refresh
 *   POST /auth/forgot-password | /auth/reset-password
 *   GET  /me
 *   POST /me/browse
 *
 * 注册契约与 Web 对齐：手机号 + 密码（必填）；昵称可选。
 * 登录可用 account / phone / email，兼容后端 `_find_account`。
 * 找回密码仍按邮箱（后端 forgot-password 仅支持 email）。
 *
 * 小程序端微信登录走 POST /auth/wechat/miniprogram（code 换 token）。
 * 该路由需后端提供；未开通时降级引导手机号登录。
 */
const CONFIG = require('./config');
const { request } = require('./request');

const S = CONFIG.storage;

const PHONE_RE = /^1[3-9]\d{9}$/;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/* ---------------- token 存取 ---------------- */

function getAccessToken() {
  try {
    return wx.getStorageSync(S.accessToken) || '';
  } catch (e) {
    return '';
  }
}

function getRefreshToken() {
  try {
    return wx.getStorageSync(S.refreshToken) || '';
  } catch (e) {
    return '';
  }
}

function setTokens(accessToken, refreshToken) {
  try {
    if (accessToken) wx.setStorageSync(S.accessToken, accessToken);
    if (refreshToken) wx.setStorageSync(S.refreshToken, refreshToken);
  } catch (e) {
    // 忽略写入失败
  }
}

function clearTokens() {
  try {
    wx.removeStorageSync(S.accessToken);
    wx.removeStorageSync(S.refreshToken);
    wx.removeStorageSync(S.userInfo);
  } catch (e) {
    // 忽略
  }
}

function isLogged() {
  return !!getAccessToken();
}

/* ---------------- 会话 ---------------- */

/** 刷新 access token */
function refreshTokens() {
  const rt = getRefreshToken();
  if (!rt) return Promise.resolve(false);
  return request({
    url: '/auth/refresh',
    method: 'POST',
    data: { refresh_token: rt },
    auth: false
  })
    .then(body => {
      if (body && body.access_token && body.refresh_token) {
        setTokens(body.access_token, body.refresh_token);
        return true;
      }
      const data = (body && body.data) || {};
      if (data.access_token) {
        setTokens(data.access_token, data.refresh_token);
        return true;
      }
      return false;
    })
    .catch(() => false);
}

/** 获取当前用户 GET /me */
function fetchMe() {
  if (!isLogged()) return Promise.resolve(null);
  return request({ url: '/me' })
    .then(body => {
      const data = (body && body.data) || body;
      if (data && (data.id || data.email || data.phone || data.user_id)) {
        try {
          wx.setStorageSync(S.userInfo, data);
        } catch (e) {
          // 忽略
        }
        return data;
      }
      return null;
    })
    .catch(() => null);
}

/** 读取缓存的用户信息 */
function getCachedUser() {
  try {
    return wx.getStorageSync(S.userInfo) || null;
  } catch (e) {
    return null;
  }
}

/* ---------------- 账号登录 / 注册 ---------------- */

/**
 * 登录：兼容后端 account / phone / email 三种字段
 * @param {string} account 手机号或邮箱
 * @param {string} password
 */
function login(account, password) {
  const acc = String(account || '').trim();
  const data = { account: acc, password };
  if (PHONE_RE.test(acc)) data.phone = acc;
  if (EMAIL_RE.test(acc)) data.email = acc;
  return request({ url: '/auth/login', method: 'POST', data, auth: false }).then(body => {
    const result = (body && body.data) || body;
    if (result && result.access_token) setTokens(result.access_token, result.refresh_token);
    return result;
  });
}

/**
 * 注册：与 Web 对齐，必填 phone + password
 * @param {{ phone: string, password: string, nickname?: string, email?: string }} payload
 */
function register(payload) {
  const body = {
    phone: String((payload && payload.phone) || '').trim(),
    password: (payload && payload.password) || ''
  };
  if (payload && payload.nickname) body.nickname = payload.nickname;
  if (payload && payload.email) body.email = String(payload.email).trim().toLowerCase();
  return request({ url: '/auth/register', method: 'POST', data: body, auth: false }).then(res => {
    const data = (res && res.data) || res;
    if (data && data.access_token) setTokens(data.access_token, data.refresh_token);
    return data;
  });
}

/** 找回密码：后端仅支持 email */
function forgotPassword(email) {
  return request({
    url: '/auth/forgot-password',
    method: 'POST',
    data: { email: String(email || '').trim().toLowerCase() },
    auth: false
  });
}

function resetPassword(token, password) {
  return request({
    url: '/auth/reset-password',
    method: 'POST',
    data: { token, password },
    auth: false
  }).then(body => {
    const data = (body && body.data) || body;
    if (data && data.access_token) setTokens(data.access_token, data.refresh_token);
    return data;
  });
}

/* ---------------- 微信登录 ---------------- */

/** 调用 wx.login 获取临时 code */
function wxLoginCode() {
  return new Promise((resolve, reject) => {
    wx.login({
      success(res) {
        if (res && res.code) resolve(res.code);
        else reject(new Error('微信登录失败，请重试'));
      },
      fail() {
        reject(new Error('微信登录失败，请重试'));
      }
    });
  });
}

/**
 * 微信一键登录
 * 后端需实现 POST /auth/wechat/miniprogram：用 code 调 code2session 换取 openid，
 * 建立/复用账号并返回 { access_token, refresh_token, user }
 * 未开通时抛出带 statusCode 的错误，由页面降级到手机号登录。
 */
function wechatLogin(extraProfile) {
  return wxLoginCode().then(code =>
    request({
      url: '/auth/wechat/miniprogram',
      method: 'POST',
      data: Object.assign({ code, platform: 'miniprogram' }, extraProfile || {}),
      auth: false
    }).then(body => {
      const data = (body && body.data) || body;
      if (data && data.access_token) setTokens(data.access_token, data.refresh_token);
      if (data && data.user) {
        try {
          wx.setStorageSync(S.userInfo, data.user);
        } catch (e) {
          // 忽略
        }
      }
      return data;
    })
  );
}

/**
 * 判断是否为「微信登录接口未开通」类错误（需引导手机号登录）
 */
function isWechatLoginUnavailable(err) {
  const status = err && err.statusCode;
  return status === 404 || status === 405 || status === 501 || status === 503;
}

/* ---------------- 行为上报 ---------------- */

/** 记录浏览 POST /me/browse（未登录静默跳过，与 Web 端一致） */
function recordBrowse(brandName) {
  if (!isLogged() || !brandName) return Promise.resolve(null);
  return request({ url: '/me/browse', method: 'POST', data: { brand_name: brandName } }).catch(() => null);
}

/** 退出登录 */
function logout() {
  clearTokens();
}

module.exports = {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
  isLogged,
  refreshTokens,
  fetchMe,
  getCachedUser,
  login,
  register,
  forgotPassword,
  resetPassword,
  wxLoginCode,
  wechatLogin,
  isWechatLoginUnavailable,
  recordBrowse,
  logout,
  PHONE_RE,
  EMAIL_RE
};

/**
 * 手机号登录 / 注册 / 邮箱找回密码
 * 注册与 Web 对齐：phone + password；登录兼容 account/phone/email。
 * 找回密码仍走邮箱（后端 forgot-password 仅支持 email）。
 * 作为「微信一键登录」未开通时的等价登录通道。
 */
const CONFIG = require('../../utils/config');
const auth = require('../../utils/auth');

const MODE_TEXT = {
  login: { title: '手机号登录', submit: '登 录', tip: '也可使用已绑定邮箱登录' },
  register: { title: '注册账号', submit: '注册并登录', tip: '请使用手机号注册（与网页端一致）' },
  forgot: { title: '找回密码', submit: '发送重置邮件', tip: '重置链接将发送到注册邮箱（后端按邮箱找回）' }
};

Page({
  data: {
    statusBarHeight: 20,
    navBarHeight: 44,
    navTotalHeight: 64,
    capsuleGap: 10,

    brand: CONFIG.brand,
    mode: 'login',
    title: MODE_TEXT.login.title,
    submitText: MODE_TEXT.login.submit,
    tip: MODE_TEXT.login.tip,

    account: '',
    phone: '',
    email: '',
    password: '',
    confirm: '',
    nickname: '',
    submitting: false,
    error: ''
  },

  onLoad(options) {
    const g = getApp().globalData || {};
    this.setData({
      statusBarHeight: g.statusBarHeight || 20,
      navBarHeight: g.navBarHeight || 44,
      navTotalHeight: g.navTotalHeight || 64,
      capsuleGap: g.capsuleGap || 10
    });
    if (options.mode && MODE_TEXT[options.mode]) this.switchMode(options.mode);
  },

  switchMode(mode) {
    const conf = MODE_TEXT[mode] || MODE_TEXT.login;
    this.setData({
      mode,
      title: conf.title,
      submitText: conf.submit,
      tip: conf.tip,
      error: '',
      password: '',
      confirm: ''
    });
  },

  onModeTap(e) {
    this.switchMode(e.currentTarget.dataset.mode);
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field;
    const value = e.detail.value;
    const patch = {};
    patch[field] = value;
    patch.error = '';
    this.setData(patch);
  },

  validate() {
    const { mode, account, phone, email, password, confirm } = this.data;
    if (mode === 'forgot') {
      if (!auth.EMAIL_RE.test(String(email || '').trim())) return '请输入正确的邮箱地址';
      return '';
    }
    if (mode === 'register') {
      if (!auth.PHONE_RE.test(String(phone || '').trim())) return '请输入正确的 11 位手机号';
      if (!password || password.length < 6) return '密码至少 6 位';
      if (password !== confirm) return '两次输入的密码不一致';
      return '';
    }
    // login：手机号或邮箱
    const acc = String(account || '').trim();
    if (!acc) return '请输入手机号或邮箱';
    if (!auth.PHONE_RE.test(acc) && !auth.EMAIL_RE.test(acc)) {
      return '请输入正确的手机号或邮箱';
    }
    if (!password || password.length < 6) return '密码至少 6 位';
    return '';
  },

  onSubmit() {
    if (this.data.submitting) return;
    const err = this.validate();
    if (err) {
      this.setData({ error: err });
      return;
    }

    const { mode, account, phone, email, password, nickname } = this.data;
    this.setData({ submitting: true, error: '' });

    let task;
    if (mode === 'login') {
      task = auth.login(String(account).trim(), password);
    } else if (mode === 'register') {
      task = auth.register({
        phone: String(phone).trim(),
        password,
        nickname: nickname || undefined
      });
    } else {
      task = auth.forgotPassword(email);
    }

    task.then(
      () => {
        this.setData({ submitting: false });
        if (mode === 'forgot') {
          wx.showModal({
            title: '邮件已发送',
            content: '若该邮箱已注册，将收到重置链接；请按提示重置密码后返回登录。',
            showCancel: false,
            success: () => wx.navigateBack()
          });
          return;
        }
        wx.showToast({ title: mode === 'login' ? '登录成功' : '注册成功', icon: 'success' });
        setTimeout(() => {
          wx.navigateBack({
            fail() {
              wx.switchTab({ url: '/pages/mine/mine' });
            }
          });
        }, 800);
      },
      e => {
        this.setData({
          submitting: false,
          error: (e && e.message) || '操作失败，请重试'
        });
      }
    );
  },

  onBack() {
    wx.navigateBack({
      fail() {
        wx.switchTab({ url: '/pages/mine/mine' });
      }
    });
  }
});

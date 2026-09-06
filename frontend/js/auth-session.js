/**
 * 用户 JWT：本地持久化 + 静默续期 + 注册/登录/忘记密码 API
 */
(function () {
    var STORAGE_ACCESS = 'nanyi_jwt_access_v1';
    var STORAGE_REFRESH = 'nanyi_jwt_refresh_v1';

    function baseApi() {
        if (window.api && window.api.baseURL) {
            return String(window.api.baseURL).replace(/\/$/, '');
        }
        return '';
    }

    function consumeOAuthHash() {
        var raw = window.location.hash || '';
        if (raw.charAt(0) === '#') raw = raw.slice(1);
        if (!raw) return;
        var sp = new URLSearchParams(raw);
        var err = sp.get('wechat_oauth_error');
        if (err) {
            console.warn('微信授权未成功:', err);
            history.replaceState(null, '', window.location.pathname + window.location.search);
            return;
        }
        var at = sp.get('access_token');
        var rt = sp.get('refresh_token');
        if (at && rt) {
            localStorage.setItem(STORAGE_ACCESS, at);
            localStorage.setItem(STORAGE_REFRESH, rt);
            history.replaceState(null, '', window.location.pathname + window.location.search);
        }
    }

    function getAccessToken() {
        return localStorage.getItem(STORAGE_ACCESS);
    }

    function getRefreshToken() {
        return localStorage.getItem(STORAGE_REFRESH);
    }

    function setTokens(at, rt) {
        if (at) localStorage.setItem(STORAGE_ACCESS, at);
        if (rt) localStorage.setItem(STORAGE_REFRESH, rt);
    }

    function clearTokens() {
        localStorage.removeItem(STORAGE_ACCESS);
        localStorage.removeItem(STORAGE_REFRESH);
    }

    async function refreshTokens() {
        var rt = getRefreshToken();
        if (!rt) return false;
        var url = baseApi() + '/auth/refresh';
        try {
            var res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: rt }),
            });
            if (!res.ok) return false;
            var data = await res.json();
            if (data.access_token && data.refresh_token) {
                setTokens(data.access_token, data.refresh_token);
                return true;
            }
        } catch (e) {
            console.warn('refresh token 失败', e);
        }
        return false;
    }

    async function fetchMe() {
        var apiRoot = baseApi();
        if (!apiRoot) return null;
        var at = getAccessToken();
        if (!at) return null;
        var url = apiRoot + '/me';
        var res = await fetch(url, { headers: { Authorization: 'Bearer ' + at } });
        if (res.status === 401) {
            var ok = await refreshTokens();
            if (!ok) return null;
            at = getAccessToken();
            res = await fetch(url, { headers: { Authorization: 'Bearer ' + at } });
        }
        if (!res.ok) return null;
        return res.json();
    }

    async function apiPost(path, body) {
        var res = await fetch(baseApi() + path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body || {}),
        });
        var data = await res.json().catch(function () { return {}; });
        return { ok: res.ok, status: res.status, data: data };
    }

    async function register(payload) {
        var r = await apiPost('/auth/register', payload);
        if (r.ok && r.data.access_token) setTokens(r.data.access_token, r.data.refresh_token);
        return r;
    }

    async function login(payload) {
        var r = await apiPost('/auth/login', payload);
        if (r.ok && r.data.access_token) setTokens(r.data.access_token, r.data.refresh_token);
        return r;
    }

    async function forgotPassword(email) {
        return apiPost('/auth/forgot-password', { email: email });
    }

    async function resetPassword(token, password) {
        var r = await apiPost('/auth/reset-password', { token: token, password: password });
        if (r.ok && r.data.access_token) setTokens(r.data.access_token, r.data.refresh_token);
        return r;
    }

    function wechatLoginUrl() {
        return baseApi() + '/auth/wechat/authorize';
    }

    function isWeChatUA() {
        return /MicroMessenger/i.test(navigator.userAgent || '');
    }

    async function recordBrowse(brandName) {
        var at = getAccessToken();
        if (!at || !brandName) return;
        try {
            await fetch(baseApi() + '/me/browse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: 'Bearer ' + at,
                },
                body: JSON.stringify({ brand_name: brandName }),
            });
        } catch (e) {}
    }

    async function bootstrap() {
        try {
            return await fetchMe();
        } catch (e) {
            return null;
        }
    }

    window.NanyiAuth = {
        STORAGE_ACCESS: STORAGE_ACCESS,
        STORAGE_REFRESH: STORAGE_REFRESH,
        getAccessToken: getAccessToken,
        getRefreshToken: getRefreshToken,
        setTokens: setTokens,
        clearTokens: clearTokens,
        refreshTokens: refreshTokens,
        fetchMe: fetchMe,
        bootstrap: bootstrap,
        register: register,
        login: login,
        forgotPassword: forgotPassword,
        resetPassword: resetPassword,
        wechatLoginUrl: wechatLoginUrl,
        isWeChatUA: isWeChatUA,
        recordBrowse: recordBrowse,
    };

    consumeOAuthHash();
})();

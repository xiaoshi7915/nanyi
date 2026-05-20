/**
 * 用户 JWT：本地持久化 + 静默续期（回访不重复打开微信授权页）
 * 依赖 window.api.baseURL（由 js/api.js 先加载）
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
        if (raw.charAt(0) === '#') {
            raw = raw.slice(1);
        }
        if (!raw) {
            return;
        }
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

    function clearTokens() {
        localStorage.removeItem(STORAGE_ACCESS);
        localStorage.removeItem(STORAGE_REFRESH);
    }

    async function refreshTokens() {
        var rt = getRefreshToken();
        if (!rt) {
            return false;
        }
        var url = baseApi() + '/auth/refresh';
        try {
            var res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: rt }),
            });
            if (!res.ok) {
                return false;
            }
            var data = await res.json();
            if (data.access_token && data.refresh_token) {
                localStorage.setItem(STORAGE_ACCESS, data.access_token);
                localStorage.setItem(STORAGE_REFRESH, data.refresh_token);
                return true;
            }
        } catch (e) {
            console.warn('refresh token 失败', e);
        }
        return false;
    }

    /** 带 Bearer 请求 /me；401 时尝试 refresh 一次 */
    async function fetchMe() {
        var apiRoot = baseApi();
        if (!apiRoot) {
            return null;
        }
        var at = getAccessToken();
        if (!at) {
            return null;
        }
        var url = apiRoot + '/me';
        var res = await fetch(url, {
            headers: { Authorization: 'Bearer ' + at },
        });
        if (res.status === 401) {
            var ok = await refreshTokens();
            if (!ok) {
                return null;
            }
            at = getAccessToken();
            res = await fetch(url, {
                headers: { Authorization: 'Bearer ' + at },
            });
        }
        if (!res.ok) {
            return null;
        }
        return res.json();
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
        clearTokens: clearTokens,
        refreshTokens: refreshTokens,
        fetchMe: fetchMe,
        bootstrap: bootstrap,
    };

    consumeOAuthHash();
})();

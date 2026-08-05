/**
 * AI 试衣前端辅助（从 index.html 抽出的纯函数/存储层，供 Vue 方法复用）
 * Phase C / Q1：不改动业务流，仅外置可独立测试的逻辑。
 */
(function (window) {
    'use strict';

    var STORAGE_KEY = 'nanyi_try_on_task_state_v2';

    function normalizeTryOnStatus(status) {
        return status === 'pending' ? 'processing' : (status || 'processing');
    }

    /**
     * 从完整品牌名提取基础品牌名（去掉颜色/括号后缀）
     */
    function extractBaseBrandName(fullName) {
        if (!fullName || typeof fullName !== 'string') {
            return null;
        }
        var name = fullName.trim();
        if (name.indexOf('(') !== -1) {
            return name.split('(')[0].trim();
        }
        if (name.indexOf('（') !== -1) {
            return name.split('（')[0].trim();
        }
        return name;
    }

    function toAbsoluteUrl(url) {
        if (!url) return '';
        if (url.indexOf('http://') === 0 || url.indexOf('https://') === 0) {
            return url;
        }
        return window.location.origin + url;
    }

    function filenameFromUrl(url) {
        if (!url) return 'tryon.jpg';
        return (url.split('/').pop() || 'tryon.jpg').replace(/\\?.*$/, '');
    }

    function buildTaskStatePayload(state) {
        return {
            task_id: state.task_id,
            access_token: state.access_token || null,
            status: state.status,
            result_image_url: state.result_image_url || null,
            error_message: state.error_message || null,
            progress: state.progress || 0,
            updated_at: Date.now()
        };
    }

    function persistTaskState(state, storageKey) {
        try {
            if (!state || !state.task_id) return false;
            var key = storageKey || STORAGE_KEY;
            localStorage.setItem(key, JSON.stringify(buildTaskStatePayload(state)));
            return true;
        } catch (e) {
            return false;
        }
    }

    function clearTaskState(storageKey) {
        try {
            localStorage.removeItem(storageKey || STORAGE_KEY);
        } catch (e) {
            // ignore
        }
    }

    /**
     * @returns {object|null} 解析后的任务状态，无效则返回 null 并清理
     */
    function loadTaskState(storageKey) {
        try {
            var raw = localStorage.getItem(storageKey || STORAGE_KEY);
            if (!raw) return null;
            var state = JSON.parse(raw);
            if (!state || !state.task_id || !state.access_token) {
                clearTaskState(storageKey);
                return null;
            }
            state.status = normalizeTryOnStatus(state.status);
            return state;
        } catch (e) {
            clearTaskState(storageKey);
            return null;
        }
    }

    window.NanyiTryOnHelpers = {
        STORAGE_KEY: STORAGE_KEY,
        normalizeTryOnStatus: normalizeTryOnStatus,
        extractBaseBrandName: extractBaseBrandName,
        toAbsoluteUrl: toAbsoluteUrl,
        filenameFromUrl: filenameFromUrl,
        persistTaskState: persistTaskState,
        clearTaskState: clearTaskState,
        loadTaskState: loadTaskState
    };
})(window);

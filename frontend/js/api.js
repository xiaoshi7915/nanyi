/**
 * 南意秋棠 API 客户端
 */

class NanyiAPI {
    constructor() {
        // 自动检测当前域名
        const currentHost = window.location.hostname;
        const protocol = window.location.protocol;
        
        // 智能API路径配置
        if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
            // 本地开发环境，直接连接后端端口
            this.baseURL = `${protocol}//${currentHost}:5432/api`;
        } else if (currentHost.includes('nanyiqiutang.cn') || currentHost.includes('chenxiaoshivivid.com.cn')) {
            // 域名访问，使用相对路径让nginx代理处理
            this.baseURL = '/api';
        } else {
            // IP访问，直接连接后端端口
            this.baseURL = 'http://121.36.205.70:5432/api';
        }
        
        // 只在调试模式下输出API基础URL
        if (window.PerformanceConfig && window.PerformanceConfig.performanceMonitoring.verboseLogging) {
            // 移除调试日志
        }
        this.timeout = 60000; // 增加到60秒超时（支持AI试衣任务状态查询）
    }

    /**
     * 发送HTTP请求
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout: this.timeout,
            ...options
        };

        try {
            // 只在调试模式下输出请求日志
            if (window.PerformanceConfig && window.PerformanceConfig.performanceMonitoring.verboseLogging) {
                // 移除调试日志
            }
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);
            
            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // 只在调试模式下输出响应日志
            if (window.PerformanceConfig && window.PerformanceConfig.performanceMonitoring.verboseLogging) {
                // 移除调试日志
            }
            
            return data;
            
        } catch (error) {
            console.error(`API请求失败 ${url}:`, error);
            
            if (error.name === 'AbortError') {
                throw new Error('请求超时，请检查网络连接');
            }
            
            throw error;
        }
    }

    /**
     * 获取所有图片信息
     */
    async getImages() {
        return this.request('/images');
    }

    /**
     * 获取筛选选项
     */
    async getFilters() {
        return this.request('/filters');
    }

    /**
     * 获取品牌详情
     */
    async getBrandDetail(brandName) {
        const encodedName = encodeURIComponent(brandName);
        return this.request(`/brand/${encodedName}`);
    }

    /**
     * 获取图片查看URL
     */
    getImageViewURL(relativePath) {
        // 处理中文路径编码
        const encodedPath = relativePath.split('/').map(part => encodeURIComponent(part)).join('/');
        
        // 使用相对路径，让nginx代理处理
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            // 本地开发环境
            return `${this.baseURL}/view/${encodedPath}`;
        } else {
            // 生产环境，使用相对路径
            return `/api/view/${encodedPath}`;
        }
    }

    /**
     * 获取图片下载URL
     */
    getImageDownloadURL(relativePath) {
        const encodedPath = relativePath.split('/').map(part => encodeURIComponent(part)).join('/');
        
        // 使用相对路径，让nginx代理处理
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            // 本地开发环境
            return `${this.baseURL}/download/${encodedPath}`;
        } else {
            // 生产环境，使用相对路径
            return `/api/download/${encodedPath}`;
        }
    }

    /**
     * 健康检查
     */
    async healthCheck() {
        return this.request('/health');
    }

    /**
     * 重试机制的请求
     */
    async requestWithRetry(endpoint, options = {}, maxRetries = 3) {
        let lastError;
        
        for (let i = 0; i < maxRetries; i++) {
            try {
                return await this.request(endpoint, options);
            } catch (error) {
                lastError = error;
                console.warn(`请求失败，重试 ${i + 1}/${maxRetries}:`, error.message);
                
                if (i < maxRetries - 1) {
                    // 指数退避重试
                    await this.sleep(Math.pow(2, i) * 1000);
                }
            }
        }
        
        throw lastError;
    }

    /**
     * 延迟函数
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * 批量获取图片信息
     */
    async getBatchImages(brandNames) {
        const promises = brandNames.map(name => this.getBrandDetail(name));
        const results = await Promise.allSettled(promises);
        
        return results.map((result, index) => {
            if (result.status === 'fulfilled') {
                return result.value;
            } else {
                console.error(`获取品牌 ${brandNames[index]} 失败:`, result.reason);
                return null;
            }
        }).filter(Boolean);
    }

    /**
     * 获取可用款式列表（品牌+颜色组合）
     * @param {string} brandName - 可选的基础品牌名，如果提供则只返回该品牌的款式
     */
    async getTryOnStyles(brandName = null) {
        const endpoint = brandName 
            ? `/try-on/styles?brand_name=${encodeURIComponent(brandName)}`
            : '/try-on/styles';
        return this.request(endpoint);
    }

    /**
     * 启动AI试衣任务
     * @param {FormData} formData - 包含brand_name和user_image的表单数据
     */
    async startTryOn(formData) {
        const url = `${this.baseURL}/try-on/start`;
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                timeout: this.timeout
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`启动试衣任务失败 ${url}:`, error);
            throw error;
        }
    }

    /**
     * 查询试衣任务状态
     * @param {string} taskId - 任务ID
     */
    async getTryOnStatus(taskId) {
        // 状态查询使用更长的超时时间（60秒）
        const url = `${this.baseURL}/try-on/status/${taskId}`;
        
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000); // 60秒超时
            
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`查询任务状态失败 ${url}:`, error);
            
            if (error.name === 'AbortError') {
                throw new Error('请求超时，请稍后重试');
            }
            
            throw error;
        }
    }

    /**
     * 订阅试衣任务状态（SSE）
     * @param {string} taskId - 任务ID
     * @param {function} onMessage - 收到消息回调
     * @param {function} onError - 错误回调
     * @returns {EventSource}
     */
    subscribeTryOnStatus(taskId, onMessage, onError) {
        const url = `${this.baseURL}/try-on/stream/${taskId}`;
        const eventSource = new EventSource(url);

        eventSource.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                if (typeof onMessage === 'function') {
                    onMessage(payload);
                }
            } catch (e) {
                if (typeof onError === 'function') {
                    onError(e);
                }
            }
        };

        eventSource.onerror = (event) => {
            if (typeof onError === 'function') {
                onError(event);
            }
        };

        return eventSource;
    }
}

// 创建全局API实例
const api = new NanyiAPI();

// 导出API实例
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NanyiAPI, api };
} else {
    // 浏览器环境，添加到全局对象
    window.api = api;
    window.NanyiAPI = NanyiAPI;
} 
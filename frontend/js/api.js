/**
 * 南意秋棠 API 客户端
 */

class NanyiAPI {
    constructor() {
        // 自动检测当前域名
        const currentHost = window.location.hostname;
        const protocol = window.location.protocol;
        
        // 如果是域名访问，使用域名；否则使用IP
        if (currentHost === 'chenxiaoshivivid.com.cn') {
            this.baseURL = `${protocol}//${currentHost}:5001/api`;
        } else if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
            this.baseURL = `${protocol}//${currentHost}:5001/api`;
        } else {
            // 默认使用IP地址
            this.baseURL = 'http://121.36.205.70:5001/api';
        }
        
        console.log('API Base URL:', this.baseURL);
        this.timeout = 30000; // 增加到30秒超时
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
            console.log(`请求API: ${url}`);
            
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
            console.log(`API响应:`, data);
            
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
        return `${this.baseURL}/view/${encodedPath}`;
    }

    /**
     * 获取图片下载URL
     */
    getImageDownloadURL(relativePath) {
        const encodedPath = relativePath.split('/').map(part => encodeURIComponent(part)).join('/');
        return `${this.baseURL}/download/${encodedPath}`;
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
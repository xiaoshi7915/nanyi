/**
 * 南意秋棠 - 性能优化配置
 * 用于提升网站加载速度和用户体验
 */

// 性能优化配置
const PerformanceConfig = {
    // 图片优化配置
    imageOptimization: {
        // 图片质量压缩
        quality: 0.8,
        // 最大宽度（像素）
        maxWidth: 1200,
        // 最大高度（像素）
        maxHeight: 1200,
        // 支持的图片格式
        supportedFormats: ['jpg', 'jpeg', 'png', 'webp'],
        // 懒加载配置
        lazyLoading: {
            rootMargin: '50px 0px',
            threshold: 0.1
        }
    },

    // 缓存策略配置
    cacheStrategy: {
        // 静态资源缓存时间（毫秒）
        staticAssets: 60 * 1000, // 1分钟
        // API数据缓存时间
        apiData: 60 * 1000, // 1分钟
        // 图片缓存时间
        images: 60 * 1000, // 1分钟
        // 品牌详情缓存时间
        brandDetails: 60 * 1000 // 1分钟
    },

    // 网络请求优化
    networkOptimization: {
        // 请求超时时间（毫秒）
        timeout: 30000,
        // 最大重试次数
        maxRetries: 3,
        // 重试延迟（毫秒）
        retryDelay: 1000,
        // 并发请求限制
        maxConcurrentRequests: 6
    },

    // 图片加载优化
    imageLoading: {
        enablePreload: true,
        lazyLoadThreshold: 200,
        loadTimeout: 8000,
        retryCount: 2,
        preloadCount: 6
    },
    
    // 缓存策略优化
    caching: {
        enableAggressiveCaching: true,
        imageCacheTTL: 24,
        apiCacheTTL: 30,
        brandDetailCacheTTL: 6
    },

    // 性能监控配置
    performanceMonitoring: {
        // 是否启用性能监控（生产环境建议关闭详细日志）
        enabled: true,
        // 监控指标
        metrics: {
            // 首次内容绘制
            fcp: true,
            // 最大内容绘制
            lcp: true,
            // 首次输入延迟
            fid: true,
            // 累积布局偏移
            cls: true
        },
        // 是否输出详细日志
        verboseLogging: false,
        slowQueryThreshold: 2000
    }
};

// 性能监控工具
class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.observers = [];
        this.init();
    }

    init() {
        if (!PerformanceConfig.performanceMonitoring.enabled) {
            return;
        }

        // 监控页面加载性能
        this.observePageLoad();
        
        // 监控Core Web Vitals
        this.observeCoreWebVitals();
        
        // 监控资源加载
        this.observeResourceLoading();
    }

    observePageLoad() {
        window.addEventListener('load', () => {
            const navigation = performance.getEntriesByType('navigation')[0];
            if (navigation) {
                this.metrics.pageLoad = {
                    domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                    loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                    totalTime: navigation.loadEventEnd - navigation.fetchStart
                };
                
                // 移除调试日志（保留错误日志）
            }
        });
    }

    observeCoreWebVitals() {
        // 观察最大内容绘制 (LCP)
        if ('PerformanceObserver' in window) {
            try {
                const lcpObserver = new PerformanceObserver((entryList) => {
                    const entries = entryList.getEntries();
                                         const lastEntry = entries[entries.length - 1];
                     this.metrics.lcp = lastEntry.startTime;
                     if (PerformanceConfig.performanceMonitoring.verboseLogging) {
                         // 移除调试日志
                     }
                });
                lcpObserver.observe({entryTypes: ['largest-contentful-paint']});
                this.observers.push(lcpObserver);
            } catch (e) {
                console.warn('LCP监控不支持:', e);
            }

            // 观察首次输入延迟 (FID)
            try {
                const fidObserver = new PerformanceObserver((entryList) => {
                    const entries = entryList.getEntries();
                                         entries.forEach(entry => {
                         this.metrics.fid = entry.processingStart - entry.startTime;
                         if (PerformanceConfig.performanceMonitoring.verboseLogging) {
                             // 移除调试日志
                         }
                     });
                });
                fidObserver.observe({entryTypes: ['first-input']});
                this.observers.push(fidObserver);
            } catch (e) {
                console.warn('FID监控不支持:', e);
            }

            // 观察累积布局偏移 (CLS)
            try {
                let clsValue = 0;
                const clsObserver = new PerformanceObserver((entryList) => {
                    const entries = entryList.getEntries();
                    entries.forEach(entry => {
                        if (!entry.hadRecentInput) {
                            clsValue += entry.value;
                        }
                                         });
                     this.metrics.cls = clsValue;
                     if (PerformanceConfig.performanceMonitoring.verboseLogging) {
                         // 移除调试日志
                     }
                });
                clsObserver.observe({entryTypes: ['layout-shift']});
                this.observers.push(clsObserver);
            } catch (e) {
                console.warn('CLS监控不支持:', e);
            }
        }
    }

    observeResourceLoading() {
        // 监控资源加载性能
        window.addEventListener('load', () => {
            const resources = performance.getEntriesByType('resource');
            const imageResources = resources.filter(resource => 
                resource.name.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i)
            );
            
            this.metrics.imageLoading = {
                totalImages: imageResources.length,
                averageLoadTime: imageResources.reduce((sum, img) => sum + img.duration, 0) / imageResources.length,
                slowImages: imageResources.filter(img => img.duration > 1000).length
            };
            
            // 移除调试日志（保留错误日志）
        });
    }

    getMetrics() {
        return this.metrics;
    }

    destroy() {
        this.observers.forEach(observer => observer.disconnect());
        this.observers = [];
    }
}

// 图片优化工具
class ImageOptimizer {
    static async compressImage(file, options = {}) {
        const config = { ...PerformanceConfig.imageOptimization, ...options };
        
        return new Promise((resolve) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();
            
            img.onload = () => {
                // 计算压缩后的尺寸
                let { width, height } = img;
                const maxWidth = config.maxWidth;
                const maxHeight = config.maxHeight;
                
                if (width > maxWidth || height > maxHeight) {
                    const ratio = Math.min(maxWidth / width, maxHeight / height);
                    width = width * ratio;
                    height = height * ratio;
                }
                
                canvas.width = width;
                canvas.height = height;
                
                // 绘制压缩后的图片
                ctx.drawImage(img, 0, 0, width, height);
                
                // 转换为Blob
                canvas.toBlob(resolve, 'image/jpeg', config.quality);
            };
            
            img.src = URL.createObjectURL(file);
        });
    }

    static isImageFormat(filename) {
        const config = PerformanceConfig.imageOptimization;
        const extension = filename.split('.').pop().toLowerCase();
        return config.supportedFormats.includes(extension);
    }
}

// 基础缓存管理器
class OptimizedCacheManager {
    constructor() {
        this.cachePrefix = 'nanyi_cache_';
        this.versionKey = 'nanyi_version';
        this.defaultTTL = 60 * 1000; // 1分钟默认缓存时间
        
        // 优化的缓存策略 - 统一1分钟缓存时间
        this.cacheStrategies = {
            'brands': {
                ttl: 60 * 1000,               // 1分钟 - 品牌数据
                checkUpdate: false,               // 不主动检查更新，减少请求
                priority: 'high'                  // 高优先级缓存
            },
            'images': {
                ttl: 60 * 1000,               // 1分钟 - 图片列表
                checkUpdate: false,               // 不主动检查更新
                priority: 'high'
            },
            'filters': {
                ttl: 60 * 1000,               // 1分钟 - 筛选选项
                checkUpdate: false,
                priority: 'medium'
            },
            'brand_detail': {
                ttl: 30 * 60 * 1000,          // 30分钟 - 品牌详情（与后端长缓存对齐）
                checkUpdate: false,               // 不主动检查更新
                priority: 'high'
            },
            'brand_images': {
                ttl: 30 * 60 * 1000,          // 30分钟 - 品牌图片轻量接口
                checkUpdate: false,
                priority: 'high'
            }
        };
        
        this.init();
    }
    
    init() {
        // 检查应用版本，如果版本变化则清空所有缓存
        this.checkAppVersion();
        
        // 定期清理过期缓存（降低频率）
        setInterval(() => {
            this.cleanExpiredCache();
        }, 5 * 60000); // 每5分钟清理一次
    }
    
    /**
     * 检查应用版本（降低检查频率）
     */
    checkAppVersion() {
        const currentVersion = this.getAppVersion();
        const cachedVersion = localStorage.getItem(this.versionKey);

        if (cachedVersion && cachedVersion !== currentVersion) {
            this.clearAllCache();
            this._onAppVersionChanged(currentVersion);
            return;
        }

        localStorage.setItem(this.versionKey, currentVersion);
    }

    /** 发布号变更：清 SW/Cache API 并自动刷新一次，避免旧缓存继续展示错误图片 */
    _onAppVersionChanged(currentVersion) {
        localStorage.setItem(this.versionKey, currentVersion);
        const onceKey = `nanyi_version_reload_${currentVersion}`;
        if (sessionStorage.getItem(onceKey)) {
            return;
        }
        sessionStorage.setItem(onceKey, '1');

        const finishReload = () => window.location.reload();
        if (typeof caches !== 'undefined') {
            caches.keys()
                .then((names) => Promise.all(names.map((name) => caches.delete(name))))
                .finally(finishReload);
            return;
        }
        finishReload();
    }
    
    /**
     * 获取应用版本（与 app-version.js 发布号一致，变更时清空 localStorage 业务缓存）
     */
    getAppVersion() {
        if (typeof window !== 'undefined' && window.APP_RELEASE_VERSION) {
            return String(window.APP_RELEASE_VERSION);
        }
        return Math.floor(Date.now() / (60 * 60 * 1000)).toString();
    }
    
    /**
     * 生成缓存键
     */
    generateKey(type, identifier = '') {
        return `${this.cachePrefix}${type}_${identifier}`;
    }
    
    /**
     * 设置缓存
     */
    set(type, data, identifier = '') {
        const strategy = this.cacheStrategies[type] || { ttl: this.defaultTTL };
        const key = this.generateKey(type, identifier);
        const now = Date.now();
        
        const cacheData = {
            data: data,
            timestamp: now,
            expires: now + strategy.ttl,
            etag: this.generateETag(data),
            type: type,
            priority: strategy.priority || 'medium'
        };
        
                         try {
                     localStorage.setItem(key, JSON.stringify(cacheData));
                     // 只在调试模式下输出缓存日志
                     if (PerformanceConfig.performanceMonitoring.verboseLogging) {
                         // 移除调试日志
                     }
                 } catch (e) {
            console.warn('缓存设置失败:', e);
            // 如果存储空间不足，清理低优先级缓存
            this.cleanLowPriorityCache();
            try {
                localStorage.setItem(key, JSON.stringify(cacheData));
            } catch (e2) {
                console.error('缓存设置最终失败:', e2);
            }
        }
    }
    
    /**
     * 获取缓存
     */
    get(type, identifier = '') {
        const key = this.generateKey(type, identifier);
        
        try {
            const cached = localStorage.getItem(key);
            if (!cached) {
                return null;
            }
            
            const cacheData = JSON.parse(cached);
            const now = Date.now();
            
            // 检查是否过期
            if (now > cacheData.expires) {
                // 移除调试日志
                localStorage.removeItem(key);
                return null;
            }
            
                                 const remainingMinutes = Math.round((cacheData.expires - now) / 60000);
                     // 只在调试模式下输出缓存命中日志
                     if (PerformanceConfig.performanceMonitoring.verboseLogging) {
                         // 移除调试日志
                     }
                     return cacheData.data;
        } catch (e) {
            console.warn('缓存读取失败:', e);
            localStorage.removeItem(key);
            return null;
        }
    }
    
    /**
     * 智能获取数据（缓存优先，不主动更新）
     */
    async getOrFetch(type, fetchFunction, identifier = '') {
        // 先尝试从缓存获取
        const cached = this.get(type, identifier);
        
        if (cached) {
            // 对于稳定资源，直接返回缓存，不进行后台更新
            return cached;
        }
        
        // 缓存未命中，直接获取数据
        try {
            const data = await fetchFunction();
            if (data) {
                this.set(type, data, identifier);
            }
            return data;
        } catch (e) {
            console.error('数据获取失败:', e);
            throw e;
        }
    }
    
    /**
     * 生成数据的ETag
     */
    generateETag(data) {
        const str = JSON.stringify(data);
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // 转换为32位整数
        }
        return hash.toString(36);
    }
    
    /**
     * 清理过期缓存
     */
    cleanExpiredCache() {
        const now = Date.now();
        const keysToRemove = [];
        
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith(this.cachePrefix)) {
                try {
                    const cached = localStorage.getItem(key);
                    const cacheData = JSON.parse(cached);
                    
                    if (now > cacheData.expires) {
                        keysToRemove.push(key);
                    }
                } catch (e) {
                    keysToRemove.push(key); // 损坏的缓存也删除
                }
            }
        }
        
        keysToRemove.forEach(key => {
            localStorage.removeItem(key);
        });
        
        if (keysToRemove.length > 0) {
            // 移除调试日志
        }
    }
    
    /**
     * 清理低优先级缓存
     */
    cleanLowPriorityCache() {
        const cacheItems = [];
        
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith(this.cachePrefix)) {
                try {
                    const cached = localStorage.getItem(key);
                    const cacheData = JSON.parse(cached);
                    cacheItems.push({
                        key: key,
                        timestamp: cacheData.timestamp,
                        priority: cacheData.priority || 'medium'
                    });
                } catch (e) {
                    localStorage.removeItem(key);
                }
            }
        }
        
        // 按优先级和时间排序，删除低优先级的旧缓存
        cacheItems.sort((a, b) => {
            const priorityOrder = { 'low': 0, 'medium': 1, 'high': 2 };
            const aPriority = priorityOrder[a.priority] || 1;
            const bPriority = priorityOrder[b.priority] || 1;
            
            if (aPriority !== bPriority) {
                return aPriority - bPriority; // 低优先级在前
            }
            return a.timestamp - b.timestamp; // 旧的在前
        });
        
        const toDelete = cacheItems.slice(0, Math.floor(cacheItems.length / 3));
        
        toDelete.forEach(item => {
            localStorage.removeItem(item.key);
        });
        
        // 移除调试日志
    }
    
    /**
     * 清空所有缓存
     */
    clearAllCache() {
        const keysToRemove = [];
        
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith(this.cachePrefix)) {
                keysToRemove.push(key);
            }
        }
        
        keysToRemove.forEach(key => {
            localStorage.removeItem(key);
        });
        
        // 移除调试日志
    }
}

// 缓存管理增强
class EnhancedCacheManager extends OptimizedCacheManager {
    constructor() {
        super();
        this.performanceConfig = PerformanceConfig.cacheStrategy;
    }

    // 预加载关键资源
    async preloadCriticalResources() {
        // 移除调试日志
        
        try {
            // 预加载品牌数据
            await this.getOrFetch('brands', async () => {
                const response = await window.api.getImages();
                return response;
            });
            
            // 移除调试日志
        } catch (error) {
            console.warn('关键资源预加载失败:', error);
        }
    }

    // 智能缓存清理
    smartCleanup() {
        const now = Date.now();
        const keys = Object.keys(localStorage);
        let cleanedCount = 0;
        
        keys.forEach(key => {
            if (key.startsWith(this.cachePrefix)) {
                try {
                    const data = JSON.parse(localStorage.getItem(key));
                    
                    // 检查是否过期
                    if (data.expires && now > data.expires) {
                        localStorage.removeItem(key);
                        cleanedCount++;
                    }
                    // 检查是否为低优先级且空间不足
                    else if (data.priority === 'low' && this.isStorageNearLimit()) {
                        localStorage.removeItem(key);
                        cleanedCount++;
                    }
                } catch (e) {
                    // 损坏的缓存数据，直接删除
                    localStorage.removeItem(key);
                    cleanedCount++;
                }
            }
        });
        
        if (cleanedCount > 0) {
            // 移除调试日志
        }
    }

    isStorageNearLimit() {
        try {
            const testKey = 'storage_test';
            const testValue = 'x'.repeat(1024); // 1KB
            localStorage.setItem(testKey, testValue);
            localStorage.removeItem(testKey);
            return false;
        } catch (e) {
            return true; // 存储空间不足
        }
    }
}

// 性能优化器
class PerformanceOptimizer {
    constructor() {
        this.config = PerformanceConfig;
        // 移除调试日志
    }
}

// 导出配置和工具
if (typeof window !== 'undefined') {
    window.PerformanceConfig = PerformanceConfig;
    window.PerformanceMonitor = PerformanceMonitor;
    window.ImageOptimizer = ImageOptimizer;
    window.OptimizedCacheManager = OptimizedCacheManager;
    window.EnhancedCacheManager = EnhancedCacheManager;
    window.performanceOptimizer = new PerformanceOptimizer();
}

// Node.js环境导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        PerformanceConfig,
        PerformanceMonitor,
        ImageOptimizer,
        OptimizedCacheManager,
        EnhancedCacheManager
    };
} 
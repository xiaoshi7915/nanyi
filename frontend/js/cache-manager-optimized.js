/**
 * 优化的前端缓存管理器
 * 针对稳定的图片资源进行长期缓存，提升性能
 */

class OptimizedCacheManager {
    constructor() {
        this.cachePrefix = 'nanyi_cache_';
        this.versionKey = 'nanyi_version';
        this.defaultTTL = 60 * 1000; // 1分钟默认缓存时间
        
        // 优化的缓存策略 - 统一1分钟缓存时间
        this.cacheStrategies = {
            'brands': {
                ttl: 60 * 1000,              // 1分钟 - 品牌数据
                checkUpdate: false,           // 不主动检查更新，减少请求
                priority: 'high'              // 高优先级缓存
            },
            'images': {
                ttl: 60 * 1000,              // 1分钟 - 图片列表
                checkUpdate: false,           // 不主动检查更新
                priority: 'high'
            },
            'filters': {
                ttl: 60 * 1000,              // 1分钟 - 筛选选项
                checkUpdate: false,
                priority: 'medium'
            },
            'brand_detail': {
                ttl: 60 * 1000,              // 1分钟 - 品牌详情
                checkUpdate: false,           // 不主动检查更新
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
        
        // 预加载关键缓存
        this.preloadCriticalCache();
    }
    
    /**
     * 预加载关键缓存
     */
    preloadCriticalCache() {
        // 在空闲时预加载品牌数据
        if (window.requestIdleCallback) {
            window.requestIdleCallback(() => {
                this.preloadBrandsData();
            });
        } else {
            // 降级方案
            setTimeout(() => {
                this.preloadBrandsData();
            }, 1000);
        }
    }
    
    /**
     * 预加载品牌数据
     */
    async preloadBrandsData() {
        try {
            const cached = this.get('brands');
            if (!cached && window.api) {
                console.log('🚀 预加载品牌数据...');
                const response = await window.api.getImages();
                if (response && response.success) {
                    this.set('brands', {
                        images: response.images || [],
                        brands: response.brands || []
                    });
                    console.log('✅ 品牌数据预加载完成');
                }
            }
        } catch (e) {
            console.log('预加载失败，将在用户访问时正常加载');
        }
    }
    
    /**
     * 检查应用版本（降低检查频率）
     */
    checkAppVersion() {
        const currentVersion = this.getAppVersion();
        const cachedVersion = localStorage.getItem(this.versionKey);
        
        if (cachedVersion && cachedVersion !== currentVersion) {
            console.log('检测到应用版本更新，清空缓存');
            this.clearAllCache();
        }
        
        localStorage.setItem(this.versionKey, currentVersion);
    }
    
    /**
     * 获取应用版本（基于当前时间戳的小时数，每小时检查一次更新）
     */
    getAppVersion() {
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
            console.log(`✅ 缓存已设置: ${type} (${identifier}), TTL: ${Math.round(strategy.ttl / 60000)}分钟`);
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
                console.log(`⏰ 缓存已过期: ${type} (${identifier})`);
                localStorage.removeItem(key);
                return null;
            }
            
            const remainingMinutes = Math.round((cacheData.expires - now) / 60000);
            console.log(`✅ 缓存命中: ${type} (${identifier}), 剩余: ${remainingMinutes}分钟`);
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
            const strategy = this.cacheStrategies[type];
            if (!strategy || !strategy.checkUpdate) {
                return cached;
            }
            
            // 只有需要检查更新的资源才进行后台更新
            this.backgroundUpdate(type, fetchFunction, identifier);
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
     * 后台更新（降低频率）
     */
    async backgroundUpdate(type, fetchFunction, identifier = '') {
        const key = this.generateKey(type, identifier);
        const lastUpdateKey = `${key}_last_update`;
        const now = Date.now();
        const lastUpdate = localStorage.getItem(lastUpdateKey);
        
        // 限制后台更新频率（至少间隔30分钟）
        if (lastUpdate && (now - parseInt(lastUpdate)) < 30 * 60 * 1000) {
            return;
        }
        
        try {
            console.log(`🔄 后台更新缓存: ${type} (${identifier})`);
            const newData = await fetchFunction();
            if (newData) {
                this.set(type, newData, identifier);
                localStorage.setItem(lastUpdateKey, now.toString());
                // 触发数据更新事件
                this.notifyDataUpdate(type, newData, identifier);
            }
        } catch (e) {
            console.warn('后台更新失败:', e);
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
            console.log(`🧹 清理了 ${keysToRemove.length} 个过期缓存`);
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
        
        console.log(`🧹 清理了 ${toDelete.length} 个低优先级缓存`);
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
        
        console.log(`🧹 清空了所有缓存 (${keysToRemove.length} 项)`);
    }
    
    /**
     * 删除特定类型的缓存
     */
    clearCache(type, identifier = '') {
        if (identifier) {
            const key = this.generateKey(type, identifier);
            localStorage.removeItem(key);
            console.log(`🗑️ 删除缓存: ${type} (${identifier})`);
        } else {
            // 删除该类型的所有缓存
            const keysToRemove = [];
            const prefix = this.generateKey(type, '');
            
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key && key.startsWith(prefix)) {
                    keysToRemove.push(key);
                }
            }
            
            keysToRemove.forEach(key => {
                localStorage.removeItem(key);
            });
            
            console.log(`🗑️ 删除 ${type} 类型的所有缓存 (${keysToRemove.length} 项)`);
        }
    }
    
    /**
     * 通知数据更新
     */
    notifyDataUpdate(type, data, identifier = '') {
        const event = new CustomEvent('cacheDataUpdate', {
            detail: {
                type: type,
                identifier: identifier,
                data: data
            }
        });
        window.dispatchEvent(event);
    }
    
    /**
     * 获取缓存统计信息
     */
    getStats() {
        let totalSize = 0;
        let itemCount = 0;
        const typeStats = {};
        
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith(this.cachePrefix)) {
                const value = localStorage.getItem(key);
                totalSize += key.length + value.length;
                itemCount++;
                
                try {
                    const cacheData = JSON.parse(value);
                    const type = cacheData.type || 'unknown';
                    typeStats[type] = (typeStats[type] || 0) + 1;
                } catch (e) {
                    typeStats['corrupted'] = (typeStats['corrupted'] || 0) + 1;
                }
            }
        }
        
        return {
            totalSize: totalSize,
            itemCount: itemCount,
            typeStats: typeStats,
            sizeFormatted: this.formatBytes(totalSize)
        };
    }
    
    /**
     * 格式化字节数
     */
    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// 创建全局优化缓存管理器实例
window.cacheManager = new OptimizedCacheManager();

// 导出给其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OptimizedCacheManager;
} 
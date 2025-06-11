/**
 * 前端缓存管理器
 * 实现智能缓存策略，平衡性能和内容更新
 */

class CacheManager {
    constructor() {
        this.cachePrefix = 'nanyi_cache_';
        this.versionKey = 'nanyi_version';
        this.defaultTTL = 5 * 60 * 1000; // 5分钟默认缓存时间
        
        // 不同类型数据的缓存策略
        this.cacheStrategies = {
            'brands': {
                ttl: 60 * 60 * 1000,     // 1小时 - 品牌数据稳定，延长缓存
                checkUpdate: true         // 需要检查更新
            },
            'images': {
                ttl: 2 * 60 * 60 * 1000, // 2小时 - 图片列表很稳定
                checkUpdate: false        // 不主动检查更新，减少请求
            },
            'filters': {
                ttl: 4 * 60 * 60 * 1000, // 4小时 - 筛选选项很少变化
                checkUpdate: false
            },
            'brand_detail': {
                ttl: 2 * 60 * 60 * 1000, // 2小时 - 品牌详情稳定
                checkUpdate: false        // 不主动检查更新
            }
        };
        
        this.init();
    }
    
    init() {
        // 检查应用版本，如果版本变化则清空所有缓存
        this.checkAppVersion();
        
        // 定期清理过期缓存
        setInterval(() => {
            this.cleanExpiredCache();
        }, 60000); // 每分钟清理一次
    }
    
    /**
     * 检查应用版本
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
            type: type
        };
        
        try {
            localStorage.setItem(key, JSON.stringify(cacheData));
            console.log(`✅ 缓存已设置: ${type} (${identifier}), TTL: ${strategy.ttl / 1000}s`);
        } catch (e) {
            console.warn('缓存设置失败:', e);
            // 如果存储空间不足，清理旧缓存
            this.cleanOldCache();
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
            
            console.log(`✅ 缓存命中: ${type} (${identifier}), 剩余: ${Math.round((cacheData.expires - now) / 1000)}s`);
            return cacheData.data;
        } catch (e) {
            console.warn('缓存读取失败:', e);
            localStorage.removeItem(key);
            return null;
        }
    }
    
    /**
     * 检查缓存是否需要更新
     */
    async shouldUpdate(type, identifier = '', serverETag = null) {
        const strategy = this.cacheStrategies[type];
        if (!strategy || !strategy.checkUpdate) {
            return false;
        }
        
        const key = this.generateKey(type, identifier);
        const cached = localStorage.getItem(key);
        
        if (!cached) {
            return true; // 没有缓存，需要获取
        }
        
        try {
            const cacheData = JSON.parse(cached);
            
            // 如果有服务器ETag，比较ETag
            if (serverETag && cacheData.etag !== serverETag) {
                console.log(`🔄 ETag不匹配，需要更新: ${type} (${identifier})`);
                return true;
            }
            
            // 检查是否接近过期（剩余时间少于总时间的20%）
            const now = Date.now();
            const totalTTL = strategy.ttl;
            const remainingTime = cacheData.expires - now;
            
            if (remainingTime < totalTTL * 0.2) {
                console.log(`🔄 缓存即将过期，预加载: ${type} (${identifier})`);
                return true;
            }
            
            return false;
        } catch (e) {
            return true;
        }
    }
    
    /**
     * 智能获取数据（缓存优先，后台更新）
     */
    async getOrFetch(type, fetchFunction, identifier = '') {
        // 先尝试从缓存获取
        const cached = this.get(type, identifier);
        
        if (cached) {
            // 后台检查是否需要更新
            this.shouldUpdate(type, identifier).then(needUpdate => {
                if (needUpdate) {
                    console.log(`🔄 后台更新缓存: ${type} (${identifier})`);
                    fetchFunction().then(newData => {
                        if (newData) {
                            this.set(type, newData, identifier);
                            // 触发数据更新事件
                            this.notifyDataUpdate(type, newData, identifier);
                        }
                    }).catch(e => {
                        console.warn('后台更新失败:', e);
                    });
                }
            });
            
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
            console.log(`🧹 清理了 ${keysToRemove.length} 个过期缓存`);
        }
    }
    
    /**
     * 清理旧缓存（按时间排序，删除最旧的）
     */
    cleanOldCache() {
        const cacheItems = [];
        
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith(this.cachePrefix)) {
                try {
                    const cached = localStorage.getItem(key);
                    const cacheData = JSON.parse(cached);
                    cacheItems.push({
                        key: key,
                        timestamp: cacheData.timestamp
                    });
                } catch (e) {
                    localStorage.removeItem(key);
                }
            }
        }
        
        // 按时间排序，删除最旧的50%
        cacheItems.sort((a, b) => a.timestamp - b.timestamp);
        const toDelete = cacheItems.slice(0, Math.floor(cacheItems.length / 2));
        
        toDelete.forEach(item => {
            localStorage.removeItem(item.key);
        });
        
        console.log(`🧹 清理了 ${toDelete.length} 个旧缓存`);
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

// 创建全局缓存管理器实例
window.cacheManager = new CacheManager();

// 导出给其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CacheManager;
} 
/**
 * 图片预加载管理器
 * 实现智能图片预加载，提升用户体验
 */

class ImagePreloader {
    constructor() {
        this.preloadQueue = new Set(); // 预加载队列
        this.preloadedImages = new Map(); // 已预加载的图片缓存
        this.maxConcurrent = 3; // 最大并发预加载数
        this.currentLoading = 0; // 当前正在加载的数量
        this.pendingQueue = []; // 待加载队列
    }

    /**
     * 预加载单张图片
     * @param {string} url - 图片URL
     * @param {Function} onLoad - 加载成功回调
     * @param {Function} onError - 加载失败回调
     */
    preloadImage(url, onLoad = null, onError = null) {
        // 如果已经在缓存中，直接返回
        if (this.preloadedImages.has(url)) {
            if (onLoad) onLoad();
            return Promise.resolve();
        }

        // 如果正在预加载队列中，跳过
        if (this.preloadQueue.has(url)) {
            return Promise.resolve();
        }

        return new Promise((resolve, reject) => {
            // 添加到预加载队列
            this.preloadQueue.add(url);

            const img = new Image();
            
            img.onload = () => {
                this.preloadedImages.set(url, img);
                this.preloadQueue.delete(url);
                this.currentLoading--;
                
                // 处理下一个待加载的图片
                this.processQueue();
                
                if (onLoad) onLoad();
                resolve(img);
            };

            img.onerror = () => {
                this.preloadQueue.delete(url);
                this.currentLoading--;
                
                // 处理下一个待加载的图片
                this.processQueue();
                
                if (onError) onError();
                reject(new Error(`Failed to load image: ${url}`));
            };

            // 如果未达到最大并发数，立即加载
            if (this.currentLoading < this.maxConcurrent) {
                this.currentLoading++;
                img.src = url;
            } else {
                // 否则加入待加载队列
                this.pendingQueue.push({ img, url });
            }
        });
    }

    /**
     * 处理待加载队列
     */
    processQueue() {
        if (this.pendingQueue.length === 0 || this.currentLoading >= this.maxConcurrent) {
            return;
        }

        const { img, url } = this.pendingQueue.shift();
        this.currentLoading++;
        img.src = url;
    }

    /**
     * 批量预加载图片
     * @param {Array<string>} urls - 图片URL数组
     * @param {Function} onProgress - 进度回调 (loaded, total)
     */
    async preloadImages(urls, onProgress = null) {
        const total = urls.length;
        let loaded = 0;

        const promises = urls.map(url => 
            this.preloadImage(url)
                .then(() => {
                    loaded++;
                    if (onProgress) {
                        onProgress(loaded, total);
                    }
                })
                .catch(() => {
                    loaded++;
                    if (onProgress) {
                        onProgress(loaded, total);
                    }
                })
        );

        await Promise.allSettled(promises);
        return { loaded, total };
    }

    /**
     * 预加载品牌详情图片
     * @param {Object} brand - 品牌对象
     * @param {Function} getImageURL - 获取图片URL的函数
     */
    async preloadBrandImages(brand, getImageURL) {
        if (!brand || !brand.images || brand.images.length === 0) {
            return;
        }

        // 优先预加载概念图和设计图（首屏显示）
        const priorityImages = brand.images.filter(img => 
            img.image_type === '概念图' || img.image_type === '设计图'
        );

        // 其他图片
        const otherImages = brand.images.filter(img => 
            img.image_type !== '概念图' && img.image_type !== '设计图'
        );

        // 先预加载优先级图片
        const priorityUrls = priorityImages.map(img => getImageURL(img));
        await this.preloadImages(priorityUrls);

        // 然后预加载其他图片（延迟加载）
        setTimeout(() => {
            const otherUrls = otherImages.map(img => getImageURL(img));
            this.preloadImages(otherUrls);
        }, 500);
    }

    /**
     * 清除缓存
     */
    clearCache() {
        this.preloadedImages.clear();
        this.preloadQueue.clear();
        this.pendingQueue = [];
        this.currentLoading = 0;
    }

    /**
     * 获取缓存统计
     */
    getStats() {
        return {
            cached: this.preloadedImages.size,
            loading: this.preloadQueue.size,
            pending: this.pendingQueue.length
        };
    }
}

// 创建全局实例
window.imagePreloader = new ImagePreloader();

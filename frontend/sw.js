/**
 * Service Worker - PWA缓存策略
 * 实现离线缓存和资源预缓存，提升性能和用户体验
 */

// 版本号：每次更新时修改此版本号，会自动清除旧缓存
const SW_VERSION = 'v1.0.2';
const CACHE_NAME = `nanyi-products-${SW_VERSION}`;
const STATIC_CACHE_NAME = `nanyi-static-${SW_VERSION}`;
const DYNAMIC_CACHE_NAME = `nanyi-dynamic-${SW_VERSION}`;

// 需要预缓存的静态资源
// 注意：api.js 不预缓存，因为经常更新，使用网络优先策略
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/css/main.css',
    '/css/skeleton.css',
    '/static/css/responsive.css',
    // '/js/api.js', // 不预缓存，使用网络优先
    '/js/performance-config.js',
    '/js/image-preloader.js',
    '/static/lib/vue.global.prod.js',
    '/static/lib/all.min.css'
];

// 需要缓存的API路径模式
const API_CACHE_PATTERNS = [
    '/api/images',
    '/api/brand/',
    '/api/share/card/',
    '/api/filters'
];

// 安装Service Worker
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS);
        }).then(() => {
            // 不立即激活，等待旧版本关闭后再激活，避免频繁刷新
            // return self.skipWaiting(); // 注释掉，让浏览器自然更新
        })
    );
});

// 激活Service Worker
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    // 删除所有旧版本的缓存（只要不是当前版本的缓存都删除）
                    if (!cacheName.includes(SW_VERSION)) {
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            // 强制更新所有客户端
            return self.clients.claim().then(() => {
                // 通知所有客户端刷新
                return self.clients.matchAll().then(clients => {
                    clients.forEach(client => {
                        client.postMessage({ type: 'SW_UPDATED', version: SW_VERSION });
                    });
                });
            });
        })
    );
});

// 拦截网络请求
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // 跳过非GET请求
    if (request.method !== 'GET') {
        return;
    }
    
    // 跳过chrome-extension等协议
    if (!url.protocol.startsWith('http')) {
        return;
    }
    
    // 静态资源：缓存优先策略
    if (isStaticAsset(url.pathname)) {
        event.respondWith(cacheFirst(request));
        return;
    }
    
    // API请求：网络优先，失败时使用缓存
    if (isAPIRequest(url.pathname)) {
        event.respondWith(networkFirst(request));
        return;
    }
    
    // 其他请求：网络优先
    event.respondWith(networkFirst(request));
});

/**
 * 判断是否为静态资源
 */
function isStaticAsset(pathname) {
    // api.js 使用网络优先策略，不缓存
    if (pathname.includes('api.js')) {
        return false;
    }
    return pathname.match(/\.(js|css|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot)$/i) ||
           pathname.startsWith('/static/') ||
           pathname.startsWith('/css/') ||
           (pathname.startsWith('/js/') && !pathname.includes('api.js'));
}

/**
 * 判断是否为API请求
 */
function isAPIRequest(pathname) {
    return pathname.startsWith('/api/');
}

/**
 * 缓存优先策略：先查缓存，缓存未命中时请求网络
 */
async function cacheFirst(request) {
    const cache = await caches.open(STATIC_CACHE_NAME);
    const cached = await cache.match(request);
    
    if (cached) {
        return cached;
    }
    
    try {
        const response = await fetch(request);
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        // 网络失败时返回缓存（如果有）
        return cached || new Response('网络错误', { status: 503 });
    }
}

/**
 * 网络优先策略：先请求网络，失败时使用缓存
 */
async function networkFirst(request) {
    const cache = await caches.open(DYNAMIC_CACHE_NAME);
    
    try {
        const response = await fetch(request);
        
        // 只缓存成功的响应
        if (response.ok) {
            // 对于API请求，设置较短的缓存时间
            if (isAPIRequest(new URL(request.url).pathname)) {
                // 克隆响应并添加缓存头
                const responseToCache = response.clone();
                cache.put(request, responseToCache);
            } else {
                cache.put(request, response.clone());
            }
        }
        
        return response;
    } catch (error) {
        // 网络失败，尝试从缓存获取
        const cached = await cache.match(request);
        if (cached) {
            return cached;
        }
        
        // 如果都没有，返回错误响应
        return new Response('网络错误，且无缓存', { 
            status: 503,
            headers: { 'Content-Type': 'text/plain; charset=utf-8' }
        });
    }
}

/**
 * 清理过期缓存
 */
async function cleanOldCache() {
    const cache = await caches.open(DYNAMIC_CACHE_NAME);
    const keys = await cache.keys();
    
    // 只保留最近100个API请求的缓存
    if (keys.length > 100) {
        const keysToDelete = keys.slice(0, keys.length - 100);
        await Promise.all(keysToDelete.map(key => cache.delete(key)));
    }
}

// 定期清理缓存
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'CLEAN_CACHE') {
        cleanOldCache();
    }
});

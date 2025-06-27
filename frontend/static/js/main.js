/**
 * 南意秋棠 - 主应用入口
 */

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('南意秋棠应用正在初始化...');
    
    // 初始化主应用
    initMainApp();
    
    // 添加页面可见性监听
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // 添加错误处理
    window.addEventListener('error', handleGlobalError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);
});

/**
 * 初始化主应用
 */
function initMainApp() {
    try {
        // 检查Vue是否可用
        if (typeof Vue === 'undefined') {
            throw new Error('Vue.js 未加载');
        }
        
        // 检查API客户端是否可用
        if (typeof api === 'undefined') {
            throw new Error('API客户端未加载');
        }
        
        console.log('所有依赖已加载，应用初始化成功');
        
        // 预加载关键资源
        preloadCriticalResources();
        
    } catch (error) {
        console.error('应用初始化失败:', error);
        showErrorMessage('应用初始化失败，请刷新页面重试');
    }
}

/**
 * 预加载关键资源
 */
function preloadCriticalResources() {
    // 预加载占位图片
    const placeholderImg = new Image();
    placeholderImg.src = '/static/images/placeholder.jpg';
    
    // 预加载英雄区图片（如果存在）
    const heroImg = new Image();
    heroImg.src = '/static/images/hero-banner.jpg';
    heroImg.onerror = () => {
        console.log('英雄区图片未找到，将使用默认样式');
    };
}

/**
 * 页面可见性变化处理
 */
function handleVisibilityChange() {
    if (document.hidden) {
        console.log('页面隐藏');
    } else {
        console.log('页面显示');
        // 页面重新可见时可以刷新数据
    }
}

/**
 * 全局错误处理
 */
function handleGlobalError(event) {
    console.error('全局错误:', event.error);
    
    // 避免显示太多错误提示
    if (!window.errorShown) {
        showErrorMessage('页面出现错误，请刷新页面');
        window.errorShown = true;
        
        // 5秒后重置错误状态
        setTimeout(() => {
            window.errorShown = false;
        }, 5000);
    }
}

/**
 * 未处理的Promise拒绝
 */
function handleUnhandledRejection(event) {
    console.error('未处理的Promise拒绝:', event.reason);
    
    // 如果是网络错误，给出特定提示
    if (event.reason && event.reason.message && 
        (event.reason.message.includes('fetch') || 
         event.reason.message.includes('网络') ||
         event.reason.message.includes('timeout'))) {
        showErrorMessage('网络连接异常，请检查网络后重试');
    }
}

/**
 * 显示错误消息
 */
function showErrorMessage(message) {
    // 创建错误提示元素
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-toast';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #f56565;
        color: white;
        padding: 12px 20px;
        border-radius: 6px;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        font-size: 14px;
        max-width: 300px;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    
    document.body.appendChild(errorDiv);
    
    // 动画显示
    setTimeout(() => {
        errorDiv.style.transform = 'translateX(0)';
    }, 100);
    
    // 3秒后自动隐藏
    setTimeout(() => {
        errorDiv.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 300);
    }, 3000);
}

/**
 * 工具函数
 */

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// 检查是否为移动设备
function isMobile() {
    return window.innerWidth <= 768;
}

// 检查元素是否在视口中
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// 平滑滚动到顶部
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 导出工具函数到全局
window.utils = {
    debounce,
    throttle,
    isMobile,
    isInViewport,
    scrollToTop,
    formatFileSize,
    showErrorMessage
};

console.log('主应用脚本加载完成'); 
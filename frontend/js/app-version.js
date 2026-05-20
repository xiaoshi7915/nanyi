/**
 * 应用发布版本号（唯一需要手动修改的地方）
 * 每次上线前请递增，并同步 index.html 中 CSS/JS 的 ?v= 参数
 */
var APP_RELEASE_VERSION = '20260520-2';

if (typeof window !== 'undefined') {
    window.APP_RELEASE_VERSION = APP_RELEASE_VERSION;
}

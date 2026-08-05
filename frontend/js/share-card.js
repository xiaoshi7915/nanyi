/**
 * 品牌分享卡片统一工具：分享出去为链接卡片预览，而非裸 URL 文本
 */
(function (window) {
    const SITE_SLOGAN = '传承经典 美美与共';

    function isWeChatBrowser() {
        return /MicroMessenger/i.test(navigator.userAgent);
    }

    function getShareCardPageUrl(brandName) {
        const origin = window.location.origin;
        const basePath = window.location.pathname.replace(/[^/]*$/, '');
        return `${origin}${basePath}card.html?brand=${encodeURIComponent(brandName)}`;
    }

    function stripHtml(text) {
        return String(text || '').replace(/<[^>]+>/g, '').trim();
    }

    function pickShareImage(cardData) {
        const origin = window.location.origin;
        let shareImage = `${origin}/static/images/牡丹亭/牡丹亭-概念图-01.jpg`;
        const images = (cardData && cardData.images) || [];
        if (!images.length) return shareImage;

        const firstImage = images[0];
        if (firstImage.medium_url && firstImage.medium_url.startsWith('http')) {
            return firstImage.medium_url;
        }
        if (firstImage.url && firstImage.url.startsWith('http')) {
            return firstImage.url;
        }
        if (firstImage.relative_path) {
            const encodedPath = firstImage.relative_path
                .split('/')
                .map((part) => encodeURIComponent(part))
                .join('/');
            return `${origin}/static/images/${encodedPath}`;
        }
        if (firstImage.filename) {
            return `${origin}/static/images/${encodeURIComponent(firstImage.filename)}`;
        }
        return shareImage;
    }

    function normalizeShareText(text, maxLen) {
        const limit = maxLen || 80;
        let body = stripHtml(text).replace(/\s+/g, ' ').trim();
        if (body.length > limit) body = `${body.substring(0, limit)}...`;
        return body;
    }

    function buildSharePreview(cardData) {
        const brandName = (cardData && (cardData.brand_name || cardData.name)) || '南意秋棠布料';
        const raw = (cardData && (cardData.inspiration_origin || cardData.inspiration)) || '古典美学设计，望君着美于裳';
        let body = normalizeShareText(raw, 80);
        if (!body) body = '古典美学设计，望君着美于裳';
        if (!body.includes(SITE_SLOGAN)) {
            body = `${SITE_SLOGAN} · ${body}`;
        }
        return {
            title: `${brandName} - 南意秋棠`,
            desc: body,
            timelineTitle: `${brandName} - 南意秋棠 · ${SITE_SLOGAN}`,
            imgUrl: pickShareImage(cardData),
            link: getShareCardPageUrl(brandName)
        };
    }

    /**
     * 统一分享品牌卡片：微信内跳转卡片页；其他环境优先系统分享面板
     */
    async function shareBrandCard(brand, options) {
        const opts = options || {};
        const brandName = brand && (brand.name || brand.brand_name);
        if (!brandName) {
            opts.showToast && opts.showToast('无法识别品牌信息');
            return false;
        }

        const cardData = opts.cardData || brand;
        const preview = buildSharePreview({ ...cardData, brand_name: brandName });
        const cardUrl = preview.link;

        if (typeof opts.beforeShare === 'function') {
            opts.beforeShare(brandName, cardData, preview);
        }

        if (isWeChatBrowser()) {
            if (opts.showToast) {
                opts.showToast('正在打开分享卡片，请点击右上角「…」转发');
            }
            window.location.href = cardUrl;
            return true;
        }

        if (navigator.share) {
            try {
                await navigator.share({
                    title: preview.title,
                    text: preview.desc,
                    url: cardUrl
                });
                return true;
            } catch (error) {
                if (error && error.name === 'AbortError') return false;
            }
        }

        const opened = window.open(cardUrl, '_blank');
        if (!opened) {
            opts.showToast && opts.showToast('请允许弹窗，或在浏览器中开启新窗口');
            return false;
        }
        opts.showToast && opts.showToast('已打开分享卡片，转发后对方将看到卡片预览');
        return true;
    }

    /**
     * 在卡片页内触发分享（不复制裸链接）
     */
    async function shareCardPage(cardData, showToast) {
        const preview = buildSharePreview(cardData || {});
        if (isWeChatBrowser()) {
            showToast && showToast('请点击右上角「…」分享，对方将看到卡片预览');
            return true;
        }
        if (navigator.share) {
            try {
                await navigator.share({
                    title: preview.title,
                    text: preview.desc,
                    url: preview.link
                });
                return true;
            } catch (error) {
                if (error && error.name === 'AbortError') return false;
            }
        }
        showToast && showToast('请使用浏览器或微信分享功能转发卡片页');
        return false;
    }

    window.ShareCardHelper = {
        SITE_SLOGAN,
        isWeChatBrowser,
        getShareCardPageUrl,
        buildSharePreview,
        pickShareImage,
        shareBrandCard,
        shareCardPage
    };
})(window);

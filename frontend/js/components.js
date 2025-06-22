/**
 * Vue组件库 - 南意秋棠
 */

// 品牌卡片组件
const BrandCard = {
    props: ['brand'],
    template: `
        <div class="brand-card" @click="$emit('click', brand)">
            <div class="brand-image-container">
                <img 
                    :src="getDesignImage(brand)" 
                    :alt="brand.name"
                    class="brand-image"
                    @error="handleImageError"
                    loading="lazy"
                >
            </div>
            <div class="brand-info">
                <h3 class="brand-name">{{ brand.name }}</h3>
                <div class="brand-meta">
                    <span v-if="brand.year" class="meta-tag">{{ brand.year }}年</span>
                    <span v-if="brand.material" class="meta-tag">{{ brand.material }}</span>
                    <span v-if="brand.theme_series" class="meta-tag">{{ brand.theme_series }}</span>
                    <span v-if="brand.print_size" class="meta-tag">{{ brand.print_size }}</span>
                </div>
            </div>
        </div>
    `,
    methods: {
        getDesignImage(brand) {
            const designImage = brand.images.find(img => img.image_type === '设计图');
            if (designImage) {
                // 使用前端静态文件路径，正确编码中文字符
                const encodedPath = designImage.relative_path.split('/').map(part => encodeURIComponent(part)).join('/');
                return `/static/images/${encodedPath}`;
            }
            return '/static/images/placeholder.svg';
        },
        handleImageError(event) {
            event.target.src = '/static/images/placeholder.svg';
        }
    },
    emits: ['click']
};

// 筛选标签组件
const FilterTags = {
    props: ['filters', 'activeFilters', 'brandCounts'],
    template: `
        <div class="filter-sections">
            <div v-for="(filterGroup, key) in filters" :key="key" class="filter-section">
                <div class="filter-title">{{ getFilterTitle(key) }}</div>
                <div class="filter-tags-container">
                    <button 
                        v-for="item in filterGroup" 
                        :key="item"
                        @click="$emit('toggle-filter', key, item)"
                        :class="['filter-tag', { active: activeFilters[key] === item }]"
                    >
                        {{ item }}
                        <span v-if="brandCounts[key] && brandCounts[key][item]" class="count">
                            ({{ brandCounts[key][item] }})
                        </span>
                    </button>
                </div>
            </div>
        </div>
    `,
    methods: {
        getFilterTitle(key) {
            const titles = {
                'years': '按年份',
                'materials': '按材质',
                'theme_series': '按主题系列',
                'print_sizes': '按印制尺寸'
            };
            return titles[key] || key;
        }
    },
    emits: ['toggle-filter']
};

// 品牌详情模态框组件
const BrandDetailModal = {
    props: ['brand', 'images', 'visible'],
    template: `
        <div v-if="visible" class="modal-overlay" @click="$emit('close')">
            <div class="modal-content" @click.stop>
                <div class="modal-header">
                    <h2 class="modal-title">{{ brand.name }}</h2>
                    <button @click="$emit('close')" class="close-btn">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <!-- 基本信息 -->
                    <div class="detail-section">
                        <h3 class="section-title">基本信息</h3>
                        <div class="detail-tags">
                            <span v-if="brand.year" class="detail-tag">{{ brand.year }}年发布</span>
                            <span v-if="brand.material" class="detail-tag">{{ brand.material }}</span>
                            <span v-if="brand.theme_series" class="detail-tag">{{ brand.theme_series }}</span>
                            <span v-if="brand.print_size" class="detail-tag">{{ brand.print_size }}</span>
                        </div>
                    </div>

                    <!-- 设计灵感 -->
                    <div v-if="brand.inspiration_origin" class="detail-section">
                        <h3 class="section-title">设计灵感</h3>
                        <div class="inspiration-text">{{ brand.inspiration_origin }}</div>
                    </div>

                    <!-- 设计图片 -->
                    <div class="detail-section">
                        <h3 class="section-title">设计图片</h3>
                        <div class="image-gallery">
                            <div 
                                v-for="image in getDesignImages()" 
                                :key="image.filename"
                                class="gallery-item"
                            >
                                <img 
                                    :src="getImageURL(image)" 
                                    :alt="image.filename"
                                    class="gallery-image"
                                    @error="handleImageError"
                                >
                                <div class="image-type-badge">{{ image.image_type }}</div>
                            </div>
                        </div>
                    </div>

                    <!-- 布料图片 -->
                    <div class="detail-section">
                        <h3 class="section-title">布料图片</h3>
                        <div class="image-gallery">
                            <div 
                                v-for="image in getFabricImages()" 
                                :key="image.filename"
                                class="gallery-item"
                            >
                                <img 
                                    :src="getImageURL(image)" 
                                    :alt="image.filename"
                                    class="gallery-image"
                                    @error="handleImageError"
                                >
                                <div class="image-type-badge">{{ image.image_type }}</div>
                            </div>
                        </div>
                    </div>

                    <!-- 分享按钮 -->
                    <div class="share-actions">
                        <button @click="shareCard" class="share-btn">
                            <i class="fas fa-share-alt"></i>
                            分享卡片
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `,
    methods: {
        getDesignImages() {
            return this.images.filter(img => img.image_type === '设计图');
        },
        getFabricImages() {
            return this.images.filter(img => img.image_type === '布料图');
        },
        getImageURL(image) {
            // 使用前端静态文件路径，正确编码中文字符
            const encodedPath = image.relative_path.split('/').map(part => encodeURIComponent(part)).join('/');
            return `/static/images/${encodedPath}`;
        },
        handleImageError(event) {
            event.target.src = '/static/images/placeholder.svg';
        },
        shareCard() {
            // 生成分享卡片
            if (navigator.share) {
                navigator.share({
                    title: `南意秋棠 - ${this.brand.name}`,
                    text: `查看这个漂亮的传统美学设计：${this.brand.name}`,
                    url: window.location.href
                });
            } else {
                // 复制链接
                navigator.clipboard.writeText(window.location.href).then(() => {
                    alert('链接已复制到剪贴板');
                }).catch(() => {
                    alert('分享功能暂不可用');
                });
            }
        }
    },
    emits: ['close']
};

// 导出组件
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { BrandCard, FilterTags, BrandDetailModal };
} else {
    window.BrandCard = BrandCard;
    window.FilterTags = FilterTags;
    window.BrandDetailModal = BrandDetailModal;
} 
/**
 * 布料卡片
 * 数据来自 GET /api/images 的单个 brand 对象
 */
const fmt = require('../../utils/format');
const api = require('../../utils/api');

Component({
  options: {
    addGlobalClass: true
  },

  properties: {
    brand: {
      type: Object,
      value: null,
      observer(val) {
        this.buildView(val);
      }
    },
    /** 是否展示底部操作行（试穿 / 分享 / 评价） */
    showActions: {
      type: Boolean,
      value: true
    }
  },

  data: {
    view: {
      displayName: '',
      meta: '',
      seriesShort: '',
      cover: '',
      likeCount: 0
    }
  },

  methods: {
    buildView(brand) {
      if (!brand) {
        this.setData({ view: { displayName: '', meta: '', seriesShort: '', cover: '', likeCount: 0 } });
        return;
      }
      this.setData({
        view: {
          displayName: fmt.getDisplayName(brand),
          meta: fmt.getCardMeta(brand),
          seriesShort: fmt.getSeriesShort(brand.theme_series),
          cover: api.pickPreviewImage(brand),
          likeCount: fmt.formatCount(brand.like_count)
        }
      });
    },

    onTapCard() {
      this.triggerEvent('tapcard', { brand: this.data.brand });
    },

    onTapTryOn() {
      this.triggerEvent('tryon', { brand: this.data.brand });
    },

    onTapShare() {
      this.triggerEvent('share', { brand: this.data.brand });
    },

    onTapComment() {
      this.triggerEvent('comment', { brand: this.data.brand });
    }
  }
});

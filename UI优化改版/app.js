/* ==========================================================
   南意秋棠 · interactivity (v2.1)
   - image-priority chain: 概念图 → 设计图 → 布料图 → 成衣图 → 模特图
   - brand-card 自带轮播 + 角标显示当前类型
   - 移动端 2 列卡片（hierarchy 与桌面同源）
   - 3 个底部弹窗（试穿 / 分享 / 评价）
   - 移动端详情页 hero 轮播
   ========================================================== */

(function () {
  'use strict';

  const $  = (s, p) => (p || document).querySelector(s);
  const $$ = (s, p) => Array.from((p || document).querySelectorAll(s));

  /* ============================================================
   * 1. 8 款品牌的元数据 + 图片优先级链
   *    primary = 第一张可用图（concept → design → fabric → garment → model）
   *    carousel = 全集（按同顺序），缺啥自动 skip
   *    feiyu 全部 404 时退回到 assets/feiyu.jpg（model fallback）
   * ============================================================ */
  const PRIORITY = ['concept', 'design', 'fabric', 'garment', 'model'];

  const BRANDS = [
    {
      key: 'feiyu', cn: '翡玉', en: 'FEIYU',
      year: '2025', theme: '画韵春秋', material: '织锦缎',
      likes: '2.1k', isNew: true,
      imageMap: {
        concept: null, design: null, fabric: null, garment: null,
        model:   'assets/feiyu.jpg'
      }
    },
    {
      key: 'zhaoyebai', cn: '照夜白', en: 'ZHAOYEBAI',
      year: '2025', theme: '画韵春秋', material: '银丝乱麻',
      likes: '1.8k', isNew: true,
      imageMap: {
        concept: 'assets/zhaoyebai-concept-01.jpg',
        design:  ['assets/zhaoyebai-design-01.jpg', 'assets/zhaoyebai-design-02.jpg'],
        fabric:  'assets/zhaoyebai-fabric-01.jpg',
        garment: null,
        model:   'assets/zhaoyebai.jpg'
      }
    },
    {
      key: 'yunqi', cn: '云起', en: 'YUNQI',
      year: '2023', theme: '长物志', material: '天丝雪纺',
      likes: '3.4k', isNew: false,
      imageMap: {
        concept: null,
        design:  'assets/yunqi-design-01.jpg',
        fabric:  'assets/yunqi-fabric-01.jpg',
        garment: 'assets/yunqi-garment-01.jpg',
        model:   'assets/yunqi.jpg'
      }
    },
    {
      key: 'lansheng', cn: '澜生', en: 'LANSHENG',
      year: '2025', theme: '执·念', material: '仿醋酸缎',
      likes: '1.2k', isNew: true,
      imageMap: {
        concept: null,
        design:  'assets/lansheng-design-01.jpg',
        fabric:  'assets/lansheng-fabric-01.jpg',
        garment: 'assets/lansheng-garment-01.jpg',
        model:   'assets/lansheng-model-01.jpg'
      }
    },
    {
      key: 'zhaohun', cn: '招魂', en: 'ZHAOHUN',
      year: '2024', theme: '画韵春秋', material: '循环印花料',
      likes: '4.5k', isNew: false,
      imageMap: {
        concept: null,
        design:  'assets/zhaohun-design-01.jpg',
        fabric:  'assets/zhaohun-fabric-01.jpg',
        garment: 'assets/zhaohun-garment-01.jpg',
        model:   'assets/zhaohun-model-01.jpg'
      }
    },
    {
      key: 'wenling', cn: '问灵', en: 'WENLING',
      year: '2025', theme: '画韵春秋', material: '天丝雪纺',
      likes: '986', isNew: false,
      imageMap: {
        concept: null,
        design:  'assets/wenling-design-01.jpg',
        fabric:  'assets/wenling-fabric-01.jpg',
        garment: 'assets/wenling-garment-01.jpg',
        model:   'assets/wenling-model-01.jpg'
      }
    },
    {
      key: 'buyuege', cn: '步月歌', en: 'BUYUEGE',
      year: '2024', theme: '执·念', material: '旗袍定位料',
      likes: '5.6k', isNew: false,
      imageMap: {
        concept: 'assets/buyuege-concept-01.jpg',
        design:  'assets/buyuege-design-01.jpg',
        fabric:  'assets/buyuege-fabric-01.jpg',
        garment: null,
        model:   'assets/buyuege-model-01.jpg'
      }
    },
    {
      key: 'shishitongtang', cn: '柿柿同堂', en: 'SHISHITONGTANG',
      year: '2025', theme: '画韵春秋', material: '银丝乱麻',
      likes: '720', isNew: true,
      imageMap: {
        concept: null,
        design:  'assets/shishitongtang-design-01.jpg',
        fabric:  'assets/shishitongtang-fabric-01.jpg',
        garment: 'assets/shishitongtang-garment-01.jpg',
        model:   'assets/shishitongtang-model-01.jpg'
      }
    }
  ];

  const TYPE_LABEL_CN = {
    concept: '概念图', design: '设计图',
    fabric:  '布料图', garment: '成衣图', model: '模特图'
  };

  /* ---- 把 imageMap 平铺为轮播数组（按优先级序） ---- */
  function carouselOf(brand) {
    const out = [];
    PRIORITY.forEach(type => {
      const v = brand.imageMap[type];
      if (!v) return;
      if (Array.isArray(v)) {
        v.forEach(src => out.push({ type, src }));
      } else {
        out.push({ type, src: v });
      }
    });
    return out;
  }
  function primaryOf(brand) {
    const arr = carouselOf(brand);
    return arr[0] || null;
  }

  /* ============================================================
   * 2. 渲染：桌面 4 列 brand 卡片（首图优先 + 角标 + dots/arrows）
   * ============================================================ */
  function renderBrandGrid() {
    const root = $('#brandGrid');
    if (!root) return;
    root.innerHTML = BRANDS.map((b, idx) => {
      const car = carouselOf(b);
      const primary = primaryOf(b);
      const slides = car.map((it, i) =>
        `<img src="${it.src}" alt="${b.cn} ${TYPE_LABEL_CN[it.type]}" data-type="${it.type}" data-idx="${i}" loading="lazy">`
      ).join('');
      const dots = car.map((_, i) => `<i class="${i===0?'is-active':''}"></i>`).join('');

      return `
        <article class="brand-card" data-brand="${b.key}" data-card-index="${idx}">
          <div class="brand-card__img">
            ${b.isNew ? '<span class="brand-card__ribbon">NEW · 2025</span>' : ''}
            ${primary ? `<span class="brand-card__type">${TYPE_LABEL_CN[primary.type]} 1/${car.length}</span>` : ''}
            <div class="brand-card__track">${slides}</div>
            <button class="brand-card__love" aria-label="收藏">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-4.5-7-10a4 4 0 0 1 7-2 4 4 0 0 1 7 2c0 5.5-7 10-7 10z"/></svg>
            </button>
            <button class="brand-card__arrow prev" aria-label="上一张">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg>
            </button>
            <button class="brand-card__arrow next" aria-label="下一张">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 6 6 6-6 6"/></svg>
            </button>
            <div class="brand-card__dots">${dots}</div>
          </div>
          <div class="brand-card__body">
            <h3 class="brand-card__name">${b.cn} <em>${b.en}</em></h3>
            <div class="brand-card__tags">
              <span class="brand-card__tag">${b.year}</span>
              <span class="brand-card__tag">${b.theme}</span>
              <span class="brand-card__tag">${b.material}</span>
            </div>
            <div class="brand-card__meta">
              <div class="brand-card__stats">
                <span class="brand-card__stat" data-stat-btn="tryon" data-brand="${b.key}">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-7 8-7s8 3 8 7"/></svg>
                  试穿 ${b.likes ? (Math.floor(parseInt(b.likes.replace('k','')) * 50) || 327) : '327'}
                </span>
                <span class="brand-card__stat" data-stat-btn="share" data-brand="${b.key}">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5 15.4 17.5M15.4 6.5 8.6 10.5"/></svg>
                  分享
                </span>
                <span class="brand-card__stat" data-stat-btn="rating" data-brand="${b.key}">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12c0 4-4 8-9 8a10 10 0 0 1-3.5-.6L4 21l1.6-4.5C4.6 15 4 13.6 4 12c0-4 4-8 8-8s9 4 9 8z"/></svg>
                  评价
                </span>
              </div>
              <div class="brand-card__likes">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 21s-7-4.5-7-10a4 4 0 0 1 7-2 4 4 0 0 1 7 2c0 5.5-7 10-7 10z"/></svg>
                ${b.likes}
              </div>
            </div>
          </div>
        </article>
      `;
    }).join('');
  }

  /* ============================================================
   * 3. 渲染：移动端 2 列卡片
   * ============================================================ */
  function renderMobGrid() {
    const root = $('#mobGrid');
    if (!root) return;
    root.innerHTML = BRANDS.map(b => {
      const primary = primaryOf(b);
      const img = primary ? primary.src : `assets/${b.key}.jpg`;
      return `
        <article class="mob-card" data-brand="${b.key}">
          <div class="mob-card__img">
            ${b.isNew ? '<span class="brand-card__ribbon">NEW</span>' : ''}
            <img src="${img}" alt="${b.cn}" loading="lazy">
          </div>
          <div class="mob-card__body">
            <h3 class="mob-card__name">${b.cn}</h3>
            <div class="mob-card__meta">
              <span>${b.year} · ${b.theme}</span>
              <span style="color:var(--c-rose)">♥ ${b.likes}</span>
            </div>
          </div>
        </article>
      `;
    }).join('');
  }

  /* ============================================================
   * 4. Carousel 控制（桌面 brand-card + 移动端详情 hero 共用）
   * ============================================================ */
  function initCarousel(root, opts = {}) {
    const track = $('.brand-card__track, .mob-detail__hero-track', root);
    const slides = $$('img', track || root);
    const dots = $$('.brand-card__dots i, .mob-detail__hero-dots i', root);
    const prev = $('.brand-card__arrow.prev, .mob-detail__hero-arrow.prev', root);
    const next = $('.brand-card__arrow.next, .mob-detail__hero-arrow.next', root);
    const labelEl = $('.brand-card__type, .mob-detail__hero-count', root);
    if (!track || slides.length === 0) return null;

    let idx = 0;
    const total = slides.length;

    const setLabel = () => {
      if (!labelEl) return;
      const t = slides[idx].dataset.type;
      const cn = TYPE_LABEL_CN[t] || '';
      labelEl.textContent = `${cn} ${idx+1}/${total}`;
    };

    const render = () => {
      track.style.transform = `translateX(${-idx * 100}%)`;
      dots.forEach((d, i) => d.classList.toggle('is-active', i === idx));
      setLabel();
    };

    const go = (n) => { idx = (n + total) % total; render(); };

    prev && prev.addEventListener('click', (e) => { e.stopPropagation(); e.preventDefault(); go(idx - 1); });
    next && next.addEventListener('click', (e) => { e.stopPropagation(); e.preventDefault(); go(idx + 1); });
    dots.forEach((d, i) => d.addEventListener('click', (e) => { e.stopPropagation(); e.preventDefault(); go(i); }));

    /* hero 自动轮播（仅 detail 页） */
    let autoId;
    if (opts.auto !== false) {
      autoId = setInterval(() => go(idx + 1), 4500);
      root.addEventListener('mouseenter', () => clearInterval(autoId));
      root.addEventListener('mouseleave', () => { autoId = setInterval(() => go(idx + 1), 4500); });
    }
    setLabel();

    return { go, getIndex: () => idx };
  }

  /* ============================================================
   * 5. 绑定 brand-card 轮播 & 点击进入详情
   * ============================================================ */
  function bindBrandCards() {
    $$('.brand-card').forEach(card => {
      const ctrl = initCarousel(card, { auto: false });
      if (!ctrl) return;

      card.addEventListener('click', (e) => {
        // 收藏 / 箭头 / dots 不触发打开
        if (e.target.closest('.brand-card__love')) return;
        if (e.target.closest('.brand-card__arrow')) return;
        if (e.target.closest('.brand-card__dots')) return;
        if (e.target.closest('.brand-card__stat')) return;
        e.preventDefault();
        open('modal-detail');
      });
    });
    /* 收藏按钮 */
    $$('.brand-card__love').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation(); e.preventDefault();
        btn.classList.toggle('is-loved');
      });
    });
  }

  /* ============================================================
   * 6. Modal 控制（保留：detail / cs）
   * ============================================================ */
  function open(id) {
    const m = document.getElementById(id);
    if (!m) return;
    m.classList.add('is-open');
    document.body.style.overflow = 'hidden';
  }
  function closeModal(m) { m.classList.remove('is-open'); document.body.style.overflow = ''; }
  function closeAllModals() {
    $$('.modal').forEach(closeModal);
  }

  /* ============================================================
   * 7. Bottom Sheet 控制（新增：评价 / 分享 / 试穿）
   * ============================================================ */
  const SHEET_TYPES = ['rating', 'share', 'tryon'];

  function openSheet(type) {
    const id = `sheet-${type}`;
    const sheet = document.getElementById(id);
    const backdrop = $('.sheet-backdrop');
    if (!sheet) return;
    sheet.classList.add('is-open');
    backdrop && backdrop.classList.add('is-open');
    sheet.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }
  function closeSheet(sheet) {
    sheet.classList.remove('is-open');
    sheet.setAttribute('aria-hidden', 'true');
    const anyOpen = SHEET_TYPES.some(t => document.getElementById(`sheet-${t}`).classList.contains('is-open'));
    if (!anyOpen) {
      const backdrop = $('.sheet-backdrop');
      backdrop && backdrop.classList.remove('is-open');
      // body 还要看是否有 modal
      const anyModal = $$('.modal.is-open').length;
      if (!anyModal) document.body.style.overflow = '';
    }
  }
  function closeAllSheets() {
    SHEET_TYPES.forEach(t => {
      const s = document.getElementById(`sheet-${t}`);
      if (s) closeSheet(s);
    });
  }

  /* 点击 stat (试穿/分享/评价) → 打开对应 sheet */
  document.addEventListener('click', (e) => {
    const stat = e.target.closest('[data-stat], [data-stat-btn]');
    if (!stat) return;
    const t = stat.dataset.stat || stat.dataset.statBtn;
    if (!SHEET_TYPES.includes(t)) return;
    e.preventDefault();
    e.stopPropagation();
    openSheet(t);
  });

  /* ========== 旧式 modal 触发（cs / detail） ========== */
  document.addEventListener('click', (e) => {
    const trigger = e.target.closest('[data-open]');
    if (!trigger) return;
    const what = trigger.dataset.open;
    if (what === 'cs')     open('modal-cs');
    if (what === 'detail') open('modal-detail');
  });

  document.addEventListener('click', (e) => {
    const c = e.target.closest('[data-close]');
    if (!c) return;
    e.preventDefault();
    // 判断来源：是 sheet 还是 modal
    const sheet = c.closest('.sheet');
    if (sheet) {
      closeSheet(sheet);
    } else {
      closeAllModals();
      closeAllSheets();
    }
  });

  /* 点 modal 背景关闭 */
  document.addEventListener('click', (e) => {
    if (e.target.classList && e.target.classList.contains('modal')) {
      closeModal(e.target);
    }
    if (e.target.classList && e.target.classList.contains('sheet-backdrop')) {
      closeAllSheets();
    }
  });

  /* ESC */
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    closeAllModals();
    closeAllSheets();
  });

  /* ============================================================
   * 8. 评价星星点击
   * ============================================================ */
  function bindRating() {
    $$('[data-rating-row]').forEach(row => {
      const stars = $$('i', row);
      stars.forEach((s, i) => {
        s.addEventListener('click', () => {
          stars.forEach((x, j) => x.classList.toggle('is-on', j <= i));
        });
      });
    });
  }

  /* ============================================================
   * 9. 试穿尺码 slider
   * ============================================================ */
  const SIZES = ['165 / 88A', '170 / 92A', '175 / 96A', '180 / 100A', '185 / 104A'];
  function bindSize() {
    $$('[data-size-range]').forEach(input => {
      const lbl = $('[data-size-label]', input.closest('.sheet__body') || document);
      const sync = () => { lbl && (lbl.textContent = SIZES[parseInt(input.value, 10)]); };
      input.addEventListener('input', sync);
      sync();
    });
  }

  /* ============================================================
   * 10. 筛选 chip 同组互斥
   * ============================================================ */
  function bindChips() {
    $$('[data-facet], .mob-tabs').forEach(group => {
      const chips = $$('.chip', group);
      chips.forEach(chip => {
        chip.addEventListener('click', () => {
          chips.forEach(c => c.classList.remove('is-active'));
          chip.classList.add('is-active');
        });
      });
    });
  }

  /* ============================================================
   * 11. 分页
   * ============================================================ */
  function bindPagination() {
    $$('.pagination').forEach(group => {
      $$('.pg', group).forEach(pg => {
        pg.addEventListener('click', () => {
          if (pg.textContent.trim() === '…') return;
          $$('.pg', group).forEach(p => p.classList.remove('is-current'));
          pg.classList.add('is-current');
          const grid = $('#brandGrid');
          grid && grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
      });
    });
  }

  /* ============================================================
   * 12. 客服发送（保留 cs modal + 移动端 mob）
   * ============================================================ */
  function sendCsMsg(sendBtn) {
    const host = sendBtn.closest('.modal') || sendBtn.closest('.mob');
    if (!host) return;
    const input = host.querySelector('.cs-input input');
    const body  = host.querySelector('.cs-body');
    const text  = input.value.trim();
    if (!text || !body) return;

    const mine = document.createElement('div');
    mine.className = 'cs-msg cs-msg--mine';
    mine.innerHTML = `<div class="cs-msg__avatar">我</div><div class="cs-msg__bubble"></div>`;
    mine.querySelector('.cs-msg__bubble').textContent = text;
    body.appendChild(mine);

    input.value = '';
    body.scrollTop = body.scrollHeight;

    setTimeout(() => {
      const reply = document.createElement('div');
      reply.className = 'cs-msg';
      const replies = [
        '好的～为您查询中',
        '正在为您筛选款式',
        '请稍等，我来看看',
        '马上为您整理',
        '了解，我推荐几款'
      ];
      const pick = replies[Math.floor(Math.random() * replies.length)];
      reply.innerHTML = `<div class="cs-msg__avatar">棠</div><div class="cs-msg__bubble"></div>`;
      reply.querySelector('.cs-msg__bubble').textContent = pick;
      body.appendChild(reply);
      body.scrollTop = body.scrollHeight;
    }, 600);
  }

  function bindCsInput() {
    $$('.cs-input__send').forEach(btn => {
      btn.addEventListener('click', (e) => { e.preventDefault(); sendCsMsg(btn); });
    });
    $$('.cs-input input').forEach(input => {
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); sendCsMsg(input.nextElementSibling); }
      });
    });
    $$('.cs-chips .chip').forEach(chip => {
      chip.addEventListener('click', (e) => {
        e.preventDefault();
        const host = chip.closest('.modal') || chip.closest('.mob');
        if (!host) return;
        const input = host.querySelector('.cs-input input');
        input && (input.value = '想看一下「' + chip.textContent.trim() + '」', input.focus());
      });
    });
    $$('.cs-quick__item').forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const host = item.closest('.modal') || item.closest('.mob');
        if (!host) return;
        const input = host.querySelector('.cs-input input');
        input && (input.value = item.textContent.trim().replace(/\s+/g, ' '), input.focus());
      });
    });
  }

  /* ============================================================
   * 13. 启动
   * ============================================================ */
  document.addEventListener('DOMContentLoaded', () => {
    renderBrandGrid();
    renderMobGrid();
    bindBrandCards();
    bindChips();
    bindPagination();
    bindCsInput();
    bindRating();
    bindSize();
    // 移动端详情页 hero 轮播
    const hero = document.querySelector('[data-mob-detail-hero]');
    if (hero) initCarousel(hero, { auto: true });
    // 提一下 sheet 也允许 sheet__grab 拖拽模拟（视觉提示）
    $$('.sheet__grab').forEach(g => {
      g.addEventListener('click', () => {
        const sheet = g.closest('.sheet');
        sheet && closeSheet(sheet);
      });
    });
    console.log('%c南意秋棠 v2 · 已加载', 'background:#9E2B25;color:#FCFAF3;padding:4px 12px;font-size:12px;border-radius:14px');
  });
})();

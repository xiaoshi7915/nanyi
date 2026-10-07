/**
 * 文案解析（与 Web 端展示口径保持一致）
 *
 * 设计图详情页的副标题、标签、诗句、简述均由接口原始字段派生：
 *   品牌名   「碧梧(山雪/枫红/玉绿/翡翠)」 → 主标题「碧梧」+ 主图颜色「枫红」→「碧梧 · 枫红」
 *   灵感原文 「【寒影】/ 花纹元素：竹影，月光 / 诗句 / 正文」
 *            → 副标题「HAN YING · 竹影月光」+ 诗句两行 + 正文简述
 */
const { toPinyin } = require('./pinyin');

/** 印制尺寸简称（详情页参数卡用短称，标签仍用全称） */
const PRINT_SHORT_MAP = {
  循环印花料: '印花料',
  旗袍定位料: '定位料',
  单边定位裙料: '定位料'
};

/** 主题系列去掉「系列」后缀（卡片角标用） */
function getSeriesShort(series) {
  return String(series || '').replace(/系列$/, '');
}

/** 印制尺寸简称 */
function getPrintShort(printSize) {
  const s = String(printSize || '');
  return PRINT_SHORT_MAP[s] || s;
}

/**
 * 拆解品牌名
 * 「碧梧(山雪/枫红/玉绿/翡翠)」→ { base: '碧梧', colors: ['山雪','枫红','玉绿','翡翠'] }
 */
function parseBrandName(raw) {
  const name = String(raw || '').trim();
  const m = name.match(/^([^（(]+)[（(]([^）)]+)[）)]$/);
  if (!m) return { base: name, colors: [] };
  return {
    base: m[1].trim(),
    colors: m[2]
      .split(/[\/、,，]/)
      .map(s => s.trim())
      .filter(Boolean)
  };
}

/** 基础名（不含颜色） */
function getBaseName(raw) {
  return parseBrandName(raw).base;
}

/**
 * 卡片 / 详情页展示名
 * 主图带颜色时追加「 · 颜色」，如「碧梧 · 枫红」，无颜色则仅品牌名
 */
function getDisplayName(brand) {
  if (!brand) return '';
  const raw = brand.name || brand.brand_name || brand.base_name || '';
  const { base, colors } = parseBrandName(raw);
  const pv = brand.preview_images || [];
  const color = (pv[0] && pv[0].color) || brand.color || '';
  if (color && (!colors.length || colors.indexOf(color) > -1)) {
    return base + ' · ' + color;
  }
  return base;
}

/**
 * 判断是否为诗句行
 * 特征：以句号结尾，且恰好由两个 4-9 字的分句组成
 * 「独坐幽篁里，弹琴复长啸。」→ true
 * 「一轮明月，穿越千年，皎洁清寂，照彻古今。」→ false（四个分句）
 */
function isVerseLine(line) {
  const t = String(line || '').trim();
  if (!t) return false;
  if (!/[。！？!?]$/.test(t)) return false;
  const body = t.replace(/[。！？!?]$/, '');
  const parts = body
    .split(/[，,]/)
    .map(s => s.trim())
    .filter(Boolean);
  if (parts.length !== 2) return false;
  return parts.every(p => p.length >= 4 && p.length <= 9);
}

/**
 * 解析设计灵感原文
 * @returns {{title:string, elements:string[], verses:string[], paragraphs:string[]}}
 */
function parseInspiration(text) {
  const result = { title: '', elements: [], verses: [], paragraphs: [] };
  const src = String(text || '')
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')
    .trim();
  if (!src) return result;

  const lines = src.split('\n').map(s => s.trim());
  const verseGroups = [];
  let current = [];

  lines.forEach(line => {
    if (!line) {
      if (current.length) {
        verseGroups.push(current);
        current = [];
      }
      return;
    }

    // 标题行：【寒影】
    const titleMatch = line.match(/^【(.+?)】\s*$/);
    if (titleMatch) {
      if (!result.title) result.title = titleMatch[1].trim();
      return;
    }

    // 元素行：花纹元素：竹影，月光
    const elMatch = line.match(/^(花纹元素|纹样元素|元素|意象)\s*[:：]\s*(.+)$/);
    if (elMatch) {
      result.elements = elMatch[2]
        .split(/[，,、\/]/)
        .map(s => s.trim())
        .filter(Boolean);
      return;
    }

    if (isVerseLine(line)) {
      current.push(line);
      return;
    }

    if (current.length) {
      verseGroups.push(current);
      current = [];
    }
    result.paragraphs.push(line);
  });

  if (current.length) verseGroups.push(current);
  // 取第一组诗句，最多两行
  result.verses = (verseGroups[0] || []).slice(0, 2);
  return result;
}

/** 诗句（两行） */
function getVerseLines(inspiration) {
  return parseInspiration(inspiration).verses;
}

/**
 * 灵感简述：取正文首段的前若干句
 * 若后端补充 inspiration_brief 字段，调用方应优先采用
 */
function getBrief(inspiration, maxSentences) {
  const { paragraphs } = parseInspiration(inspiration);
  if (!paragraphs.length) return '';
  const first = paragraphs[0];
  const limit = maxSentences || 2;
  const sentences = first.match(/[^。！？!?]+[。！？!?]?/g) || [first];
  const picked = sentences
    .map(s => s.trim())
    .filter(Boolean)
    .slice(0, limit);
  return picked.join('');
}

/**
 * 详情页副标题：拼音 + 花纹元素
 * 「HAN YING · 竹影月光」
 */
function getSubtitle(brandName, inspiration) {
  const py = toPinyin(getBaseName(brandName));
  const { elements } = parseInspiration(inspiration);
  const el = elements.join('');
  if (py && el) return py + ' · ' + el;
  return py || el || '';
}

/** 详情页标签组：年份 / 材质 / 印制 / 系列 */
function getDetailTags(brand) {
  if (!brand) return [];
  const tags = [];
  if (brand.year) tags.push(String(brand.year));
  if (brand.material) tags.push(brand.material);
  if (brand.print_size && brand.print_size !== 'N/A') tags.push(brand.print_size);
  if (brand.theme_series) tags.push(brand.theme_series);
  return tags;
}

/** 卡片副行：2026 · 厚乱纹麻 · 旗袍定位料 */
function getCardMeta(brand) {
  if (!brand) return '';
  return [brand.year, brand.material, brand.print_size]
    .filter(v => v && v !== 'N/A')
    .join(' · ');
}

/** 格式化点赞数：超过 999 显示 1.2k */
function formatCount(n) {
  const num = Number(n) || 0;
  if (num < 1000) return String(num);
  return (num / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
}

module.exports = {
  PRINT_SHORT_MAP,
  getSeriesShort,
  getPrintShort,
  parseBrandName,
  getBaseName,
  getDisplayName,
  isVerseLine,
  parseInspiration,
  getVerseLines,
  getBrief,
  getSubtitle,
  getDetailTags,
  getCardMeta,
  formatCount,
  toPinyin
};

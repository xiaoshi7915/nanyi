/**
 * 筛选与搜索（与 Web 端本地筛选行为一致）
 * 选项「全部」为不限定条件
 */
const ALL = '全部';

/** 空筛选条件 */
function emptyFilters() {
  return {
    year: ALL,
    series: ALL,
    material: ALL,
    printSize: ALL,
    keyword: ''
  };
}

/** 单项匹配 */
function matchBrand(brand, filters) {
  const f = filters || {};
  if (!brand) return false;

  if (f.year && f.year !== ALL && String(brand.year || '') !== String(f.year)) return false;
  if (f.series && f.series !== ALL && String(brand.theme_series || '') !== f.series) return false;
  if (f.material && f.material !== ALL && String(brand.material || '') !== f.material) return false;
  if (f.printSize && f.printSize !== ALL && String(brand.print_size || '') !== f.printSize) return false;

  const kw = String(f.keyword || '').trim().toLowerCase();
  if (kw) {
    const hay = [brand.name, brand.material, brand.theme_series, brand.print_size, brand.year]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();
    if (hay.indexOf(kw) === -1) return false;
  }
  return true;
}

/** 批量筛选 */
function applyFilters(brands, filters) {
  const list = brands || [];
  return list.filter(b => matchBrand(b, filters));
}

/**
 * 筛选条件摘要文案
 * 「2026 年 · 全部系列 · 全部材质 · 全部尺寸」
 */
function describeFilters(filters) {
  const f = filters || {};
  const year = !f.year || f.year === ALL ? '全部年份' : f.year + ' 年';
  const series = !f.series || f.series === ALL ? '全部系列' : f.series;
  const material = !f.material || f.material === ALL ? '全部材质' : f.material;
  const printSize = !f.printSize || f.printSize === ALL ? '全部尺寸' : f.printSize;
  return [year, series, material, printSize].join(' · ');
}

/** 从品牌列表统计各维度数量 */
function countBy(brands, field) {
  const out = {};
  (brands || []).forEach(b => {
    const key = String(b[field] || '');
    if (!key) return;
    out[key] = (out[key] || 0) + 1;
  });
  return out;
}

/** 按年份倒序排序 */
function sortByYearDesc(brands) {
  return (brands || []).slice().sort((a, b) => {
    const ya = Number(a.year) || 0;
    const yb = Number(b.year) || 0;
    if (yb !== ya) return yb - ya;
    return String(a.name || '').localeCompare(String(b.name || ''), 'zh-Hans-CN');
  });
}

/** 取「猜你也喜欢」：优先同系列同材质，其次同系列，最后同年份 */
function pickRelated(brands, current, count) {
  const n = count || 3;
  const cur = current || {};
  const base = String(cur.name || cur.brand_name || '');
  const pool = (brands || []).filter(b => {
    const name = String(b.name || b.brand_name || '');
    return name && name !== base;
  });

  const score = b => {
    let s = 0;
    if (cur.theme_series && b.theme_series === cur.theme_series) s += 4;
    if (cur.material && b.material === cur.material) s += 2;
    if (cur.print_size && b.print_size === cur.print_size) s += 1;
    if (String(b.year) === String(cur.year)) s += 1;
    return s;
  };

  return pool
    .map(b => ({ b, s: score(b) }))
    .sort((x, y) => {
      if (y.s !== x.s) return y.s - x.s;
      return (Number(y.b.like_count) || 0) - (Number(x.b.like_count) || 0);
    })
    .slice(0, n)
    .map(x => x.b);
}

module.exports = {
  ALL,
  emptyFilters,
  matchBrand,
  applyFilters,
  describeFilters,
  countBy,
  sortByYearDesc,
  pickRelated
};

-- 性能优化索引
-- 执行时间: 2026-01-21

-- 1. 产品表索引（如果不存在）
-- brand_name已有索引，添加组合索引优化查询
CREATE INDEX IF NOT EXISTS idx_product_brand_year ON products(brand_name, year);
CREATE INDEX IF NOT EXISTS idx_product_year_month ON products(year, publish_month);
CREATE INDEX IF NOT EXISTS idx_product_material ON products(material);
CREATE INDEX IF NOT EXISTS idx_product_theme ON products(theme_series);
CREATE INDEX IF NOT EXISTS idx_product_print_size ON products(print_size);

-- 2. 品牌点赞表索引（已存在，但确保存在）
-- idx_brand_name 已存在
-- idx_created_at 已存在

-- 3. 访问日志表索引（已存在）
-- idx_timestamp_ip 已存在
-- idx_path_status 已存在

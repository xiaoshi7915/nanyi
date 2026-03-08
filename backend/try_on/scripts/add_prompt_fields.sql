-- 添加 prompt 和 negative_prompt 字段到 tasks 表
-- 如果字段已存在，会报错但可以忽略

ALTER TABLE tasks 
ADD COLUMN IF NOT EXISTS prompt TEXT COMMENT '自定义提示词',
ADD COLUMN IF NOT EXISTS negative_prompt TEXT COMMENT '负面提示词';


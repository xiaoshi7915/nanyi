#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
静态卡片生成脚本
预生成所有品牌的卡片HTML文件，提升访问速度
"""

import os
import sys
import json
import urllib.parse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.app import create_app
from backend.controllers.product_controller import ProductController
from backend.services.image_service import ImageService
from backend.models import db, init_models
from backend.utils.logger import logger

def generate_static_cards():
    """生成所有品牌的静态卡片HTML"""
    app = create_app()
    
    with app.app_context():
        try:
            # 初始化模型
            Product, Admin, AccessLog = init_models()
            
            # 获取所有品牌
            products = Product.query.all()
            logger.info(f"找到 {len(products)} 个品牌，开始生成静态卡片...")
            
            # 创建静态卡片目录
            static_cards_dir = os.path.join(project_root, 'frontend', 'static', 'cards')
            os.makedirs(static_cards_dir, exist_ok=True)
            
            # 获取前端主机地址（从环境变量或配置）
            frontend_host = os.environ.get('FRONTEND_HOST', 'products.nanyiqiutang.cn')
            request_protocol = 'https'  # 默认使用HTTPS
            
            product_controller = ProductController()
            image_service = ImageService()
            
            # 获取所有图片（用于构建品牌列表）
            all_images = image_service.get_all_images()
            
            # 统计
            success_count = 0
            error_count = 0
            
            # 为每个品牌生成静态HTML
            for product in products:
                try:
                    brand_name = product.brand_name
                    encoded_brand_name = urllib.parse.quote(brand_name, safe='')
                    
                    # 生成卡片数据
                    result = product_controller.generate_share_card(
                        encoded_brand_name,
                        frontend_host,
                        request_protocol
                    )
                    
                    if not result.get('success'):
                        logger.warning(f"品牌 {brand_name} 生成卡片数据失败: {result.get('error')}")
                        error_count += 1
                        continue
                    
                    card_data = result.get('card_data', {})
                    
                    # 读取card.html模板
                    card_template_path = os.path.join(project_root, 'frontend', 'card.html')
                    with open(card_template_path, 'r', encoding='utf-8') as f:
                        template_content = f.read()
                    
                    # 将卡片数据嵌入到HTML中（作为JSON数据）
                    # 在</body>标签前插入数据脚本
                    data_script = f'''
<script>
    // 预加载的卡片数据
    window.preloadedCardData = {json.dumps(card_data, ensure_ascii=False, indent=2)};
</script>
'''
                    
                    # 替换模板中的占位符或插入数据
                    if 'window.preloadedCardData' in template_content:
                        # 如果已有占位符，替换它
                        template_content = template_content.replace(
                            'window.preloadedCardData = null;',
                            f'window.preloadedCardData = {json.dumps(card_data, ensure_ascii=False)};'
                        )
                    else:
                        # 在</body>前插入
                        template_content = template_content.replace(
                            '</body>',
                            data_script + '</body>'
                        )
                    
                    # 更新页面标题和meta标签
                    template_content = template_content.replace(
                        '<title id="pageTitle">南意秋棠 - 传统美学设计</title>',
                        f'<title id="pageTitle">{brand_name} - 南意秋棠</title>'
                    )
                    
                    # 保存静态HTML文件
                    static_file_path = os.path.join(static_cards_dir, f'{encoded_brand_name}.html')
                    with open(static_file_path, 'w', encoding='utf-8') as f:
                        f.write(template_content)
                    
                    success_count += 1
                    
                    if success_count % 10 == 0:
                        logger.info(f"已生成 {success_count} 个静态卡片...")
                        
                except Exception as e:
                    logger.error(f"生成品牌 {product.brand_name} 的静态卡片失败: {e}")
                    error_count += 1
                    continue
            
            logger.info(f"✅ 静态卡片生成完成！成功: {success_count}, 失败: {error_count}")
            
            # 生成索引文件（用于快速查找）
            index_data = {
                'brands': [product.brand_name for product in products],
                'generated_at': str(db.session.execute('SELECT NOW()').scalar())
            }
            
            index_file = os.path.join(static_cards_dir, 'index.json')
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 索引文件已生成: {index_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"生成静态卡片失败: {e}", exc_info=True)
            return False

if __name__ == '__main__':
    success = generate_static_cards()
    sys.exit(0 if success else 1)

from datetime import datetime
import logging
import pymysql
import os

logger = logging.getLogger(__name__)

def get_db_connection():
    """获取数据库连接"""
    # 使用和config.py相同的数据库配置
    host = os.environ.get('DB_HOST', '47.118.250.53')
    port = int(os.environ.get('DB_PORT', 3306))
    user = os.environ.get('DB_USER', 'nanyi')
    password = os.environ.get('DB_PASSWORD', 'admin123456!')
    database = os.environ.get('DB_NAME', 'nanyiqiutang')
    
    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset='utf8mb4',
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )

class BrandLike:
    """布料点赞数据模型"""
    
    @staticmethod
    def create_table():
        """创建点赞相关数据表"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # 创建点赞记录表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS brand_likes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                brand_name VARCHAR(255) NOT NULL COMMENT '品牌名称',
                user_hash VARCHAR(64) NOT NULL COMMENT '用户唯一标识哈希',
                ip_address VARCHAR(45) COMMENT 'IP地址',
                user_agent TEXT COMMENT '用户代理',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '点赞时间',
                UNIQUE KEY unique_user_brand (brand_name, user_hash),
                INDEX idx_brand_name (brand_name),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='布料点赞记录表'
            """)
            
            # 创建点赞统计表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS brand_like_stats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                brand_name VARCHAR(255) NOT NULL UNIQUE COMMENT '品牌名称',
                like_count INT DEFAULT 0 COMMENT '点赞总数',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_brand_name (brand_name),
                INDEX idx_like_count (like_count)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='布料点赞统计表'
            """)
            
            connection.commit()
            logger.info("✅ 点赞数据表创建成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建点赞数据表失败: {e}")
            return False
        finally:
            if 'connection' in locals():
                connection.close()
    
    @staticmethod
    def add_like(brand_name, user_hash, ip_address=None, user_agent=None):
        """添加点赞记录"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # 检查是否已经点赞过
            cursor.execute("""
                SELECT id FROM brand_likes 
                WHERE brand_name = %s AND user_hash = %s
            """, (brand_name, user_hash))
            
            if cursor.fetchone():
                return False, "您已经点赞过了"
            
            # 添加点赞记录
            cursor.execute("""
                INSERT INTO brand_likes (brand_name, user_hash, ip_address, user_agent)
                VALUES (%s, %s, %s, %s)
            """, (brand_name, user_hash, ip_address, user_agent))
            
            # 更新统计
            cursor.execute("""
                INSERT INTO brand_like_stats (brand_name, like_count)
                VALUES (%s, 1)
                ON DUPLICATE KEY UPDATE like_count = like_count + 1
            """, (brand_name,))
            
            connection.commit()
            
            # 获取最新点赞数
            cursor.execute("""
                SELECT like_count FROM brand_like_stats WHERE brand_name = %s
            """, (brand_name,))
            
            result = cursor.fetchone()
            like_count = result['like_count'] if result else 1
            
            return True, like_count
            
        except Exception as e:
            logger.error(f"添加点赞记录失败: {e}")
            return False, str(e)
        finally:
            if 'connection' in locals():
                connection.close()
    
    @staticmethod
    def check_user_liked(brand_name, user_hash):
        """检查用户是否已点赞"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                SELECT id FROM brand_likes 
                WHERE brand_name = %s AND user_hash = %s
            """, (brand_name, user_hash))
            
            return cursor.fetchone() is not None
            
        except Exception as e:
            logger.error(f"检查点赞状态失败: {e}")
            return False
        finally:
            if 'connection' in locals():
                connection.close()
    
    @staticmethod
    def get_like_count(brand_name):
        """获取布料点赞数"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                SELECT like_count FROM brand_like_stats WHERE brand_name = %s
            """, (brand_name,))
            
            result = cursor.fetchone()
            return result['like_count'] if result else 0
            
        except Exception as e:
            logger.error(f"获取点赞数失败: {e}")
            return 0
        finally:
            if 'connection' in locals():
                connection.close()
    
    @staticmethod
    def get_popular_brands(limit=10):
        """获取最受欢迎的布料"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                SELECT brand_name, like_count 
                FROM brand_like_stats 
                ORDER BY like_count DESC 
                LIMIT %s
            """, (limit,))
            
            return cursor.fetchall()
            
        except Exception as e:
            logger.error(f"获取热门布料失败: {e}")
            return []
        finally:
            if 'connection' in locals():
                connection.close() 
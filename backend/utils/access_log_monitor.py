#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
访问日志监控工具
"""

import mysql.connector
import sys
import os
from datetime import datetime, timedelta
from backend.utils.logger import logger


def get_db_config():
    """获取数据库配置（与应用一致：从环境变量读取，禁止硬编码密码）"""
    host = os.environ.get('DB_HOST')
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    database = os.environ.get('DB_NAME')
    missing = [k for k, v in (
        ('DB_HOST', host),
        ('DB_USER', user),
        ('DB_PASSWORD', password),
        ('DB_NAME', database),
    ) if not v]
    if missing:
        raise ValueError(
            f"缺少数据库环境变量: {', '.join(missing)}，请在 .env 中配置"
        )
    return {
        'host': host,
        'port': int(os.environ.get('DB_PORT') or 3306),
        'user': user,
        'password': password,
        'database': database,
        'charset': 'utf8mb4',
    }


def check_access_logs():
    """检查访问日志状态"""
    try:
        conn = mysql.connector.connect(**get_db_config())
        cursor = conn.cursor()

        logger.info("🔍 访问日志监控报告")
        logger.info("=" * 50)

        cursor.execute('SELECT COUNT(*) FROM access_logs')
        total_count = cursor.fetchone()[0]
        logger.info(f"📊 总记录数: {total_count}")

        today = datetime.now().date()
        cursor.execute('SELECT COUNT(*) FROM access_logs WHERE DATE(timestamp) = %s', (today,))
        today_count = cursor.fetchone()[0]
        logger.info(f"📅 今日记录: {today_count}")

        one_hour_ago = datetime.now() - timedelta(hours=1)
        cursor.execute('SELECT COUNT(*) FROM access_logs WHERE timestamp >= %s', (one_hour_ago,))
        hour_count = cursor.fetchone()[0]
        logger.info(f"⏰ 最近1小时: {hour_count}")

        ten_minutes_ago = datetime.now() - timedelta(minutes=10)
        cursor.execute('SELECT COUNT(*) FROM access_logs WHERE timestamp >= %s', (ten_minutes_ago,))
        recent_count = cursor.fetchone()[0]
        logger.info(f"🕐 最近10分钟: {recent_count}")

        logger.info("📋 最新访问记录:")
        cursor.execute(
            'SELECT timestamp, client_ip, method, path, status_code, response_time_ms '
            'FROM access_logs ORDER BY timestamp DESC LIMIT 5'
        )
        records = cursor.fetchall()

        for i, record in enumerate(records, 1):
            timestamp, ip, method, path, status, response_time = record
            response_time_str = f"{response_time:.2f}ms" if response_time else "N/A"
            logger.info(f"  {i}. {timestamp} | {ip} | {method} {path} | {status} | {response_time_str}")

        logger.info("🔥 今日热门API路径:")
        cursor.execute(
            'SELECT path, COUNT(*) as count FROM access_logs '
            'WHERE DATE(timestamp) = %s GROUP BY path ORDER BY count DESC LIMIT 5',
            (today,),
        )
        paths = cursor.fetchall()

        for i, (path, count) in enumerate(paths, 1):
            logger.info(f"  {i}. {path} ({count} 次)")

        logger.info("🌐 今日访问IP统计:")
        cursor.execute(
            'SELECT client_ip, COUNT(*) as count FROM access_logs '
            'WHERE DATE(timestamp) = %s GROUP BY client_ip ORDER BY count DESC LIMIT 5',
            (today,),
        )
        ips = cursor.fetchall()

        for i, (ip, count) in enumerate(ips, 1):
            logger.info(f"  {i}. {ip} ({count} 次)")

        cursor.close()
        conn.close()

        logger.info("✅ 访问日志监控完成")
        return True

    except Exception as e:
        logger.error(f"❌ 监控失败: {e}")
        return False


def test_log_functionality():
    """测试日志功能"""
    import requests
    import time

    logger.info("🧪 测试访问日志功能...")

    try:
        response = requests.get('http://localhost:/api/health', timeout=5)
        logger.info(f"✅ 测试请求发送成功: {response.status_code}")

        time.sleep(2)

        conn = mysql.connector.connect(**get_db_config())
        cursor = conn.cursor()

        cursor.execute(
            'SELECT timestamp, client_ip, method, path, status_code '
            'FROM access_logs WHERE timestamp >= %s ORDER BY timestamp DESC LIMIT 1',
            (datetime.now() - timedelta(minutes=1),),
        )

        record = cursor.fetchone()
        if record:
            logger.info(f"✅ 最新日志记录: {record[0]} | {record[1]} | {record[2]} {record[3]} | {record[4]}")
        else:
            logger.warning("⚠️  没有找到最新的日志记录")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_log_functionality()
    else:
        check_access_logs()

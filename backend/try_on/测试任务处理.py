#!/usr/bin/env python3
"""
测试任务处理脚本
用于诊断任务处理问题
"""
import sys
import os
import asyncio
from datetime import datetime

# 添加项目路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app.services.db_service import db_service
from app.services.image_service import image_service
from sqlalchemy import create_engine, text
from app.config import settings


async def test_task_processing():
    """测试任务处理"""
    print("=" * 60)
    print("任务处理诊断工具")
    print("=" * 60)
    print()
    
    # 1. 检查数据库连接
    print("1. 检查数据库连接...")
    try:
        engine = create_engine(settings.db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("   ✅ 数据库连接正常")
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {e}")
        return
    print()
    
    # 2. 检查数据库中的任务
    print("2. 检查数据库中的任务...")
    try:
        tasks = db_service.list_tasks(limit=10)
        print(f"   找到 {len(tasks)} 个任务")
        for task in tasks[:5]:
            print(f"   - {task['task_id'][:8]}... 状态: {task['status']} 创建: {task['created_at']}")
    except Exception as e:
        print(f"   ❌ 查询任务失败: {e}")
    print()
    
    # 3. 检查特定任务
    task_id = input("请输入要检查的任务ID（或按回车跳过）: ").strip()
    if task_id:
        print(f"\n3. 检查任务 {task_id}...")
        task = db_service.get_task(task_id)
        if task:
            print(f"   状态: {task['status']}")
            print(f"   创建时间: {task['created_at']}")
            print(f"   更新时间: {task['updated_at']}")
            if task['error_message']:
                print(f"   错误信息: {task['error_message']}")
            if task['result_image_url']:
                print(f"   图片URL: {task['result_image_url']}")
            if task['local_path']:
                print(f"   本地路径: {task['local_path']}")
        else:
            print("   ❌ 任务不存在")
        print()
    
    # 4. 检查内存中的任务
    print("4. 检查内存中的任务...")
    print(f"   内存任务数: {len(image_service.tasks)}")
    print(f"   队列大小: {image_service._task_queue.qsize()}")
    print(f"   处理中的任务: {len(image_service._processing_tasks)}")
    print(f"   工作器状态: {'已启动' if image_service._worker_started else '未启动'}")
    print()
    
    # 5. 检查处理中的任务
    if image_service._processing_tasks:
        print("5. 处理中的任务详情:")
        for task_id, task in image_service._processing_tasks.items():
            print(f"   - {task_id[:8]}... 状态: {task.done()}")
    print()
    
    print("=" * 60)
    print("诊断完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_task_processing())


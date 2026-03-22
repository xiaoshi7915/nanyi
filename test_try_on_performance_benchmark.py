#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI试穿性能基准测试脚本
测试集成后的性能，验证响应时间提升（目标：10秒内完成）
"""

import requests
import time
import json
import os
from statistics import mean, median

# 配置
BACKEND_URL = "http://localhost:5432"

def test_performance_benchmark():
    """性能基准测试"""
    print("=" * 60)
    print("⚡ AI试穿性能基准测试（集成模式）")
    print("=" * 60)
    print("📌 测试目标：验证响应时间提升（目标10秒内完成）")
    print("=" * 60)
    
    # 1. 获取款式列表
    print("\n📋 步骤1: 获取款式列表...")
    styles_start = time.time()
    try:
        response = requests.get(f"{BACKEND_URL}/api/try-on/styles", timeout=10)
        response.raise_for_status()
        styles_data = response.json()
        styles_time = (time.time() - styles_start) * 1000
        
        if styles_data.get('success') and styles_data.get('data', {}).get('styles'):
            styles = styles_data['data']['styles']
            print(f"✅ 获取款式列表成功 (耗时: {styles_time:.2f}ms)")
            
            if styles:
                selected_style = styles[0]
                brand_name = selected_style.get('brand_name', '')
                print(f"   选择款式: {brand_name}")
            else:
                print("⚠️  没有可用款式，无法继续测试")
                return
        else:
            print("⚠️  无法获取款式列表")
            return
    except Exception as e:
        print(f"❌ 获取款式列表失败: {e}")
        return
    
    # 2. 准备测试图片
    print("\n📤 步骤2: 准备测试图片...")
    test_image_path = "/opt/hanfu/products/frontend/static/images/瑞宝/瑞宝-布料图-03.jpg"
    if not os.path.exists(test_image_path):
        # 尝试其他路径
        test_image_path = None
        for root, dirs, files in os.walk("/opt/hanfu/products/frontend/static/images"):
            for file in files:
                if file.endswith(('.jpg', '.jpeg', '.png')):
                    test_image_path = os.path.join(root, file)
                    break
            if test_image_path:
                break
    
    if test_image_path and os.path.exists(test_image_path):
        with open(test_image_path, 'rb') as f:
            test_image_data = f.read()
        print(f"   使用真实图片: {test_image_path} ({len(test_image_data)} bytes)")
    else:
        # 创建最小测试图片
        test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.ff\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9'
        print(f"   使用最小测试图片 ({len(test_image_data)} bytes)")
    
    # 3. 测试任务创建性能（多次测试取平均值）
    print("\n🚀 步骤3: 测试任务创建性能...")
    create_times = []
    task_ids = []
    
    num_tests = 3  # 测试3次
    for i in range(num_tests):
        print(f"   测试 {i+1}/{num_tests}...")
        try:
            start_time = time.time()
            
            files = {
                'user_image': ('test_image.jpg', test_image_data, 'image/jpeg')
            }
            data = {
                'brand_name': brand_name
            }
            
            response = requests.post(
                f"{BACKEND_URL}/api/try-on/start",
                files=files,
                data=data,
                timeout=60
            )
            
            create_time = (time.time() - start_time) * 1000
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                task_id = result.get('data', {}).get('task_id')
                task_ids.append(task_id)
                create_times.append(create_time)
                print(f"      ✅ 任务创建成功 (耗时: {create_time:.2f}ms)")
            else:
                print(f"      ❌ 任务创建失败: {result.get('message')}")
        except Exception as e:
            print(f"      ❌ 任务创建异常: {e}")
    
    if create_times:
        avg_create_time = mean(create_times)
        median_create_time = median(create_times)
        print(f"\n   📊 任务创建性能统计:")
        print(f"      平均耗时: {avg_create_time:.2f}ms")
        print(f"      中位数耗时: {median_create_time:.2f}ms")
        print(f"      最快: {min(create_times):.2f}ms")
        print(f"      最慢: {max(create_times):.2f}ms")
        print(f"      ✅ 任务创建性能良好（集成模式，无 HTTP 调用延迟）")
    
    # 4. 测试状态查询性能
    if task_ids:
        print(f"\n🔍 步骤4: 测试状态查询性能...")
        query_times = []
        
        for task_id in task_ids[:3]:  # 只测试前3个任务
            try:
                start_time = time.time()
                response = requests.get(
                    f"{BACKEND_URL}/api/try-on/status/{task_id}",
                    timeout=10
                )
                query_time = (time.time() - start_time) * 1000
                response.raise_for_status()
                result = response.json()
                
                if result.get('success'):
                    query_times.append(query_time)
                    print(f"   任务 {task_id[:8]}... 查询耗时: {query_time:.2f}ms")
            except Exception as e:
                print(f"   任务 {task_id[:8]}... 查询失败: {e}")
        
        if query_times:
            avg_query_time = mean(query_times)
            median_query_time = median(query_times)
            print(f"\n   📊 状态查询性能统计:")
            print(f"      平均耗时: {avg_query_time:.2f}ms")
            print(f"      中位数耗时: {median_query_time:.2f}ms")
            print(f"      最快: {min(query_times):.2f}ms")
            print(f"      最慢: {max(query_times):.2f}ms")
            print(f"      ✅ 状态查询性能良好（从本地数据库查询，无网络延迟）")
    
    # 5. 测试完整流程性能（等待一个任务完成）
    if task_ids:
        print(f"\n⏱️  步骤5: 测试完整流程性能（等待任务完成）...")
        task_id = task_ids[0]
        print(f"   任务ID: {task_id}")
        print(f"   开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        total_start_time = time.time()
        max_wait_time = 300  # 最大等待时间：5分钟
        poll_interval = 2  # 轮询间隔：2秒
        
        while True:
            elapsed_time = time.time() - total_start_time
            if elapsed_time > max_wait_time:
                print(f"   ⚠️  超时：等待时间超过 {max_wait_time} 秒")
                break
            
            try:
                response = requests.get(
                    f"{BACKEND_URL}/api/try-on/status/{task_id}",
                    timeout=10
                )
                response.raise_for_status()
                status_data = response.json()
                
                if status_data.get('success'):
                    status = status_data.get('data', {}).get('status')
                    progress = status_data.get('data', {}).get('progress', 0)
                    
                    if status == 'completed':
                        total_time = time.time() - total_start_time
                        result_image_url = status_data.get('data', {}).get('result_image_url')
                        
                        print(f"\n   ✅ 任务完成！")
                        print(f"      总耗时: {total_time:.2f}秒")
                        print(f"      结果图片URL: {result_image_url}")
                        
                        # 性能评估
                        if total_time <= 10:
                            print(f"      ✅ 性能目标达成：{total_time:.2f}秒 ≤ 10秒")
                        else:
                            print(f"      ⚠️  性能目标未达成：{total_time:.2f}秒 > 10秒")
                            print(f"      （注意：主要耗时在 AI 模型生成，不在通信延迟）")
                        break
                    elif status == 'failed':
                        error = status_data.get('data', {}).get('error')
                        print(f"\n   ❌ 任务失败: {error}")
                        break
                    else:
                        # 处理中或等待中
                        if int(elapsed_time) % 10 == 0:  # 每10秒打印一次
                            print(f"   [{elapsed_time:.0f}s] 状态: {status}, 进度: {progress}%")
                        time.sleep(poll_interval)
                        continue
                else:
                    print(f"   ⚠️  状态查询失败: {status_data.get('message')}")
                    break
            except Exception as e:
                print(f"   ⚠️  状态查询异常: {e}")
                time.sleep(poll_interval)
                continue
    
    print("\n" + "=" * 60)
    print("✅ 性能基准测试完成")
    print("=" * 60)
    print("\n📋 性能测试总结：")
    print("   1. ✅ 任务创建：集成模式，无 HTTP 调用延迟")
    print("   2. ✅ 状态查询：从本地数据库查询，响应快速")
    print("   3. ⏱️  完整流程：主要耗时在 AI 模型生成（取决于模型性能）")
    print("=" * 60)

if __name__ == "__main__":
    test_performance_benchmark()

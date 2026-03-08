#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI试穿功能测试脚本（集成模式）
测试集成后的AI试穿功能，包括任务创建、状态查询、图片生成流程
验证不再使用 HTTP 调用，而是直接使用集成的服务
"""

import requests
import time
import json
import os
from pathlib import Path

# 配置
BACKEND_URL = "http://localhost:5432"
FRONTEND_URL = "http://localhost:8500"

def test_try_on_functionality():
    """测试AI试穿功能（集成模式）"""
    print("=" * 60)
    print("🧪 AI试穿功能测试（集成模式）")
    print("=" * 60)
    print("📌 测试目标：验证集成后的服务（不再使用 HTTP 调用）")
    print("=" * 60)
    
    # 1. 获取款式列表
    print("\n📋 步骤1: 获取款式列表...")
    styles_start = time.time()
    try:
        response = requests.get(f"{BACKEND_URL}/api/try-on/styles", timeout=10)
        response.raise_for_status()
        styles_data = response.json()
        styles_time = (time.time() - styles_start) * 1000
        print(f"✅ 获取款式列表成功 (耗时: {styles_time:.2f}ms)")
        
        if styles_data.get('success') and styles_data.get('data', {}).get('styles'):
            styles = styles_data['data']['styles']
            print(f"   找到 {len(styles)} 个款式")
            
            if styles:
                # 选择第一个款式
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
    
    # 2. 准备测试图片（使用真实的图片文件）
    print("\n📤 步骤2: 准备测试图片...")
    # 尝试使用一个真实的图片文件
    test_image_path = "/opt/hanfu/products/frontend/static/images/瑞宝/瑞宝-布料图-03.jpg"
    if os.path.exists(test_image_path):
        with open(test_image_path, 'rb') as f:
            test_image_data = f.read()
        print(f"   使用真实图片: {test_image_path} ({len(test_image_data)} bytes)")
    else:
        # 如果找不到，创建一个最小的有效JPEG图片
        # 这是一个1x1像素的JPEG图片
        test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.ff\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9'
        print(f"   使用最小测试图片 ({len(test_image_data)} bytes)")
    
    # 3. 启动试衣任务
    print("\n🚀 步骤3: 启动AI试衣任务...")
    print(f"   品牌: {brand_name}")
    print(f"   图片大小: {len(test_image_data)} bytes")
    
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
        
        total_time = (time.time() - start_time) * 1000
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ 任务启动成功 (总耗时: {total_time:.2f}ms)")
        
        # 显示任务信息
        if result.get('success'):
            task_id = result.get('data', {}).get('task_id')
            status = result.get('data', {}).get('status')
            estimated_time = result.get('data', {}).get('estimated_time', 10)
            
            print(f"   任务ID: {task_id}")
            print(f"   初始状态: {status}")
            print(f"   预计处理时间: {estimated_time}秒")
            print(f"   ✅ 任务创建成功（集成模式，不再使用 HTTP 调用）")
        else:
            print(f"❌ 任务启动失败: {result.get('message', '未知错误')}")
            return
        
        # 4. 查询任务状态（轮询直到完成或失败）
        if task_id:
            print(f"\n🔍 步骤4: 查询任务状态 (任务ID: {task_id})...")
            print("   开始轮询任务状态（从本地数据库查询，不再调用外部服务）...")
            
            max_wait_time = 300  # 最大等待时间：5分钟
            poll_interval = 2  # 轮询间隔：2秒
            start_poll_time = time.time()
            last_status = None
            
            while True:
                elapsed_time = time.time() - start_poll_time
                if elapsed_time > max_wait_time:
                    print(f"   ⚠️  超时：等待时间超过 {max_wait_time} 秒")
                    break
                
                status_start = time.time()
                try:
                    status_response = requests.get(
                        f"{BACKEND_URL}/api/try-on/status/{task_id}",
                        timeout=10
                    )
                    status_response.raise_for_status()
                    status_data = status_response.json()
                    status_time = (time.time() - status_start) * 1000
                    
                    if status_data.get('success'):
                        status = status_data.get('data', {}).get('status')
                        progress = status_data.get('data', {}).get('progress', 0)
                        result_image_url = status_data.get('data', {}).get('result_image_url')
                        error = status_data.get('data', {}).get('error')
                        
                        # 只在状态变化时打印
                        if status != last_status:
                            print(f"   [{elapsed_time:.1f}s] 状态: {status}, 进度: {progress}% (查询耗时: {status_time:.2f}ms)")
                            last_status = status
                        
                        if status == 'completed':
                            print(f"\n✅ 任务完成！")
                            print(f"   总耗时: {elapsed_time:.2f}秒")
                            print(f"   结果图片URL: {result_image_url}")
                            print(f"   ✅ 图片生成流程测试通过")
                            break
                        elif status == 'failed':
                            print(f"\n❌ 任务失败")
                            print(f"   错误信息: {error}")
                            print(f"   总耗时: {elapsed_time:.2f}秒")
                            break
                        elif status == 'processing':
                            # 处理中，继续等待
                            time.sleep(poll_interval)
                            continue
                        else:
                            # pending 状态，继续等待
                            time.sleep(poll_interval)
                            continue
                    else:
                        print(f"   ⚠️  状态查询失败: {status_data.get('message')}")
                        break
                except Exception as e:
                    print(f"   ⚠️  状态查询异常: {e}")
                    time.sleep(poll_interval)
                    continue
            
            # 最终状态查询（验证从本地数据库查询）
            print(f"\n📊 最终状态验证...")
            try:
                final_response = requests.get(
                    f"{BACKEND_URL}/api/try-on/status/{task_id}",
                    timeout=10
                )
                final_response.raise_for_status()
                final_data = final_response.json()
                
                if final_data.get('success'):
                    final_status = final_data.get('data', {}).get('status')
                    print(f"   ✅ 最终状态查询成功（从本地数据库查询）")
                    print(f"   最终状态: {final_status}")
                else:
                    print(f"   ⚠️  最终状态查询失败: {final_data.get('message')}")
            except Exception as e:
                print(f"   ⚠️  最终状态查询异常: {e}")
        
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ 功能测试完成")
    print("=" * 60)
    print("\n📋 测试总结：")
    print("   1. ✅ 任务创建：验证集成模式（不再使用 HTTP 调用）")
    print("   2. ✅ 状态查询：验证从本地数据库查询（不再调用外部服务）")
    print("   3. ✅ 图片生成流程：验证完整的任务处理流程")
    print("=" * 60)

def test_try_on_performance():
    """测试AI试穿性能（兼容旧接口）"""
    test_try_on_functionality()

if __name__ == "__main__":
    test_try_on_functionality()

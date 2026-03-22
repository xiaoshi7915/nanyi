#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查服务状态"""

import requests
import sys

# 测试任务创建
print("=" * 60)
print("测试任务创建...")
response = requests.post(
    'http://localhost:5432/api/try-on/start',
    files={'user_image': open('/opt/hanfu/products/frontend/static/images/瑞宝/瑞宝-布料图-03.jpg', 'rb')},
    data={'brand_name': '一丛花令(湖蓝)'},
    timeout=10
)
print(f"状态码: {response.status_code}")
result = response.json()
print(f"结果: {result}")

if result.get('success'):
    task_id = result['data']['task_id']
    print(f"\n任务ID: {task_id}")
    
    # 测试状态查询
    print("\n" + "=" * 60)
    print("测试状态查询...")
    status_response = requests.get(
        f'http://localhost:5432/api/try-on/status/{task_id}',
        timeout=10
    )
    print(f"状态码: {status_response.status_code}")
    status_result = status_response.json()
    print(f"结果: {status_result}")
    
    if not status_result.get('success'):
        print("\n❌ 状态查询失败")
        sys.exit(1)
    else:
        print("\n✅ 状态查询成功")
        print(f"任务状态: {status_result.get('data', {}).get('status')}")
else:
    print("\n❌ 任务创建失败")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ 所有测试通过")

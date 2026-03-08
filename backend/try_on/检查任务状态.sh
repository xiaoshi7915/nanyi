#!/bin/bash
# 检查任务状态的脚本

TASK_ID="$1"

if [ -z "$TASK_ID" ]; then
    echo "用法: $0 <任务ID>"
    echo "示例: $0 700cf750-c48b-4fe0-adf5-36d7bf0e6477"
    exit 1
fi

echo "检查任务: $TASK_ID"
echo ""

cd /opt/try_on/backend
source py312/bin/activate

# 从数据库查询
python3 << EOF
from app.services.db_service import db_service

task = db_service.get_task("$TASK_ID")
if task:
    print("任务信息:")
    print(f"  任务ID: {task['task_id']}")
    print(f"  状态: {task['status']}")
    print(f"  创建时间: {task['created_at']}")
    print(f"  更新时间: {task['updated_at']}")
    if task['error_message']:
        print(f"  错误信息: {task['error_message']}")
    if task['result_image_url']:
        print(f"  图片URL: {task['result_image_url']}")
    if task['local_path']:
        print(f"  本地路径: {task['local_path']}")
        import os
        if os.path.exists(task['local_path']):
            print(f"  本地文件存在: ✅")
        else:
            print(f"  本地文件不存在: ❌")
else:
    print("❌ 任务不存在")
EOF


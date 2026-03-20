# 环境变量配置更新总结

## 更新内容

已更新 `.env` 文件，添加了 Try-On 服务所需的所有环境变量配置。

### 新增配置项

#### 1. Try-On 服务任务配置
```env
TASK_TIMEOUT_SECONDS=300
TASK_MAX_RETRIES=3
MAX_CONCURRENT_TASKS=5
TASK_CLEANUP_INTERVAL_SECONDS=3600
TASK_RETENTION_HOURS=24
WORKER_HEALTH_CHECK_INTERVAL_SECONDS=60
WORKER_RESTART_ON_FAILURE=true
WORKER_MAX_RESTART_ATTEMPTS=10
```

#### 2. Try-On 服务存储配置
```env
STORAGE_LOCAL_PATH=./backend/try_on/storage
STORAGE_UPLOAD_DIR=uploads
STORAGE_FABRIC_DIR=uploads/fabric
STORAGE_REAL_PERSON_DIR=uploads/real_person
STORAGE_GENERATED_DIR=generated
```

#### 3. Try-On 服务限流配置
```env
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_CLEANUP_INTERVAL_SECONDS=3600
RATE_LIMIT_IP_RETENTION_HOURS=24
```

#### 4. Try-On 服务图片配置
```env
MAX_IMAGE_SIZE_MB=10
ALLOWED_IMAGE_FORMATS=jpeg,jpg,png
MAX_IMAGES_PER_REQUEST=5
```

#### 5. Try-On 服务AI模型配置
```env
ARK_MODEL_NAME=doubao-seedream-4-5-251128
# 如需更换 Ark 模型，请修改此项为对应的 doubao-seedream-* 模型名称（重启后端服务生效）
USE_MOCK_AI=false
```

## 已存在的配置

以下配置项已经存在于 `.env` 文件中：

- `ARK_API_KEY` - 火山引擎API密钥
- `ARK_BASE_URL` - 火山引擎API地址
- `ARK_MODEL_NAME` - 模型名称

## 配置说明

所有配置项都有默认值（在 `backend/config/config.py` 中定义），所以即使不设置这些环境变量，服务也能正常运行。但是，为了更好的控制和优化，建议明确配置这些值。

## 应用配置

重启服务后，新的环境变量配置会自动生效：

```bash
systemctl restart nanyi-backend.service
```

## 验证配置

可以通过以下方式验证配置是否生效：

1. 检查服务日志，确认 TryOnImageService 是否成功初始化
2. 测试 API 端点，确认功能正常
3. 检查任务处理是否正常

## 注意事项

- 所有配置项都有默认值，不会因为缺少配置而导致服务无法启动
- 建议根据实际需求调整配置值（如并发任务数、超时时间等）
- 存储路径配置需要确保目录存在且有写权限

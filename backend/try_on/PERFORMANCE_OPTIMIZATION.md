# 性能优化文档

本文档说明已实施的性能优化措施。

## 优化内容

### 1. 异步处理优化

#### 任务队列系统
- **实现位置**: `backend/app/services/image_service.py`
- **优化内容**:
  - 使用 `asyncio.Queue` 实现任务队列，避免任务丢失
  - 使用 `asyncio.Semaphore` 控制最大并发任务数（默认5个）
  - 实现任务处理工作器，从队列中异步处理任务
  - 支持任务并发处理，提高吞吐量

#### 异步文件操作
- **实现位置**: `backend/app/services/storage_service.py`
- **优化内容**:
  - OSS上传使用 `run_in_executor` 在线程池中执行，避免阻塞事件循环
  - 本地文件写入使用线程池，提高并发性能
  - 所有IO操作都使用异步方式

### 2. 错误重试机制

#### 任务处理重试
- **实现位置**: `backend/app/services/image_service.py`
- **优化内容**:
  - 实现 `_process_task_with_retry` 方法，支持自动重试
  - 默认最大重试次数：3次
  - 使用指数退避策略（2^retry_count秒，最多60秒）
  - 智能判断错误是否可重试（网络错误、超时等可重试）

#### OSS上传重试
- **实现位置**: `backend/app/services/storage_service.py`
- **优化内容**:
  - OSS上传失败时自动重试
  - 默认最大重试次数：3次
  - 使用指数退避策略（最多30秒）
  - 识别OSS特定错误码，判断是否可重试

#### AI模型调用重试
- **实现位置**: `backend/app/services/ai_models/seedream.py`
- **优化内容**:
  - API调用超时或网络错误时自动重试
  - 默认最大重试次数：3次
  - 使用指数退避策略

### 3. 日志系统完善

#### 结构化日志
- **实现位置**: `backend/app/utils/logger.py`
- **优化内容**:
  - 使用JSON格式日志，便于日志分析
  - 支持中文日志（`json_ensure_ascii=False`）
  - 包含更多上下文信息（函数名、行号等）

#### 性能日志
- **实现位置**: `backend/app/services/image_service.py`, `backend/app/services/storage_service.py`
- **优化内容**:
  - 记录任务处理各阶段耗时（AI生成、存储上传等）
  - 记录文件大小、重试次数等关键指标
  - 使用结构化日志格式，便于监控和分析

#### 日志级别
- 使用适当的日志级别：
  - `INFO`: 正常操作流程
  - `WARNING`: 可重试的错误
  - `ERROR`: 严重错误
  - `DEBUG`: 调试信息（开发环境）

## 配置参数

### 并发控制

在 `backend/app/config.py` 中可配置：

```python
max_concurrent_tasks: int = 5  # 最大并发任务数
```

### 重试配置

在 `backend/app/config.py` 中可配置：

```python
task_max_retries: int = 3  # 任务最大重试次数
task_timeout_seconds: int = 300  # 任务超时时间（秒）
```

## 性能指标

### 任务处理流程

1. **任务创建**: < 100ms
2. **AI模型生成**: 5-30秒（取决于模型和图片大小）
3. **OSS上传**: 1-5秒（取决于网络和文件大小）
4. **本地备份**: < 500ms

### 并发能力

- 默认支持5个并发任务
- 可通过配置调整 `max_concurrent_tasks`
- 使用信号量控制，避免资源耗尽

## 监控建议

### 关键指标

1. **任务处理时间**: 监控从创建到完成的总时间
2. **重试次数**: 监控任务重试频率，识别系统问题
3. **错误率**: 监控任务失败率
4. **队列长度**: 监控任务队列长度，识别处理瓶颈

### 日志分析

使用结构化日志可以轻松提取性能指标：

```python
# 示例：提取任务处理时间
import json
import re

log_line = '{"asctime": "...", "message": "任务处理完成: task_id=xxx, total_duration=15.23s"}'
# 解析JSON并提取duration
```

## 未来优化方向

1. **任务持久化**: 使用数据库存储任务，避免内存丢失
2. **分布式任务队列**: 使用Redis或RabbitMQ实现分布式任务处理
3. **缓存机制**: 缓存常用图片，减少重复生成
4. **CDN加速**: 使用CDN加速图片访问
5. **监控告警**: 集成Prometheus/Grafana进行监控和告警


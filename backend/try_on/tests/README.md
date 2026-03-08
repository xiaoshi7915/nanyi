# 测试文档

## 测试结构

本项目包含完整的单元测试和集成测试，确保功能正确性和代码质量。

## 测试文件说明

### 单元测试

1. **test_rate_limit_service.py** - 限流服务测试
   - 测试令牌桶算法
   - 测试全局限流和IP限流
   - 测试限流状态查询

2. **test_storage_service.py** - 存储服务测试
   - 测试OSS上传功能
   - 测试本地文件保存
   - 测试文件删除功能
   - 使用Mock避免实际调用OSS

3. **test_validators.py** - 验证工具测试
   - 测试图片格式验证
   - 测试文件大小验证
   - 测试多文件验证

4. **test_image_service.py** - 图片处理服务测试
   - 测试任务创建和管理
   - 测试任务状态查询
   - 测试任务处理流程

### 集成测试

5. **test_api_integration.py** - API集成测试
   - 测试完整的API请求流程
   - 测试错误处理
   - 测试参数验证
   - 使用Mock避免实际调用外部服务

## 运行测试

### 安装测试依赖

```bash
cd backend
pip install -r requirements.txt
```

### 运行所有测试

```bash
pytest tests/
```

### 运行单元测试

```bash
pytest tests/ -m unit
```

### 运行集成测试

```bash
pytest tests/ -m integration
```

### 生成覆盖率报告

```bash
pytest tests/ --cov=app --cov-report=html
```

覆盖率报告将生成在 `htmlcov/index.html`

## 测试配置

测试配置文件：`tests/pytest.ini`

主要配置：
- 异步测试模式：`asyncio_mode = auto`
- 覆盖率报告：自动生成term、html、xml格式
- 日志输出：显示INFO级别日志

## 测试Fixtures

在 `conftest.py` 中定义了以下测试fixtures：

- `test_settings` - 测试用的配置对象
- `client` - FastAPI测试客户端
- `mock_image_data` - 模拟图片数据
- `mock_upload_file` - 模拟上传文件对象
- `mock_oss_bucket` - 模拟OSS Bucket对象
- `mock_ai_model` - 模拟AI模型对象

## 注意事项

1. 测试使用Mock对象，不会实际调用外部服务（OSS、AI模型等）
2. 测试使用临时目录，测试完成后自动清理
3. 某些测试需要异步支持，使用 `pytest-asyncio` 插件
4. 集成测试可能需要更长的执行时间

## 持续集成

建议在CI/CD流程中运行测试：

```yaml
# 示例 GitHub Actions 配置
- name: Run tests
  run: |
    cd backend
    pytest tests/ --cov=app --cov-report=xml
```


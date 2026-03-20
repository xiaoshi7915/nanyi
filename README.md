# 南意秋棠产品展示系统

## 项目简介

南意秋棠是一个传统美学设计产品展示系统，用于展示和管理汉服面料设计产品。

**首页布料卡片**：每张卡片底部提供「试穿」与「分享」；「分享」与品牌详情内「生成布料卡片」相同，均调用 `/api/share/card/{品牌名}` 后打开 `card.html` 分享页。

## 技术栈

- **前端**: Flask (静态文件服务)
- **后端**: Flask + SQLAlchemy + PyMySQL
- **数据库**: MySQL 8.0
- **Web服务器**: Nginx + Gunicorn
- **服务管理**: Systemd
- **Python版本**: 3.12

## 项目结构

```
products/
├── backend/              # 后端代码
│   ├── app.py           # 主应用
│   ├── config/          # 配置
│   ├── models/          # 数据模型
│   ├── routes/          # 路由
│   ├── services/        # 服务层
│   └── utils/           # 工具函数
├── frontend/            # 前端代码
│   ├── static/          # 静态资源
│   ├── js/              # JavaScript
│   ├── server.py        # Flask开发服务器
│   └── wsgi.py          # WSGI入口
├── logs/                # 日志目录
├── systemd/             # Systemd服务文件
│   ├── nanyi-backend.service
│   ├── nanyi-frontend.service
│   └── README.md
├── nginx/               # Nginx配置和脚本
│   ├── README.md
│   └── *.sh
├── deploy.sh            # 部署脚本
├── deploy-nginx.sh      # Nginx部署脚本
├── debug-start.sh       # 调试启动脚本
├── setup-env.sh         # 环境设置脚本
├── requirements.txt     # Python依赖
└── .env                 # 环境变量配置
```

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python3.12 -m venv products_env

# 激活虚拟环境
source products_env/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并配置：

```bash
cp .env.example .env
vi .env
```

必需的环境变量：
- `SECRET_KEY` - Flask密钥
- `DB_HOST` - 数据库主机
- `DB_USER` - 数据库用户
- `DB_PASSWORD` - 数据库密码
- `DB_NAME` - 数据库名称
- `CORS_ORIGINS` - CORS允许的域名（HTTPS）

AI试穿（Try-On / Seedream）环境变量：
- `ARK_API_KEY` - 火山引擎方舟 API Key
- `ARK_BASE_URL` - 火山引擎方舟 Base URL（默认 `https://ark.cn-beijing.volces.com/api/v3`）
- `ARK_MODEL_NAME` - 默认 `doubao-seedream-4-5-251128`；如需更换模型，修改此项为对应的 Ark model 名称并重启后端服务
- `TRY_ON_WATERMARK` - 是否给生成结果加水印（默认 `false`）

**AI 试衣前端交互说明（便于排查体验问题）**：
- 点击「退出」仅关闭弹窗并回到首页浏览，**不会**再打开「试衣结果准备中」空白标签页；后台任务仍通过 SSE/轮询继续追踪。
- 进行中的 `task_id` 会写入浏览器 `localStorage`，再次从首页入口打开试衣时会自动拉回任务并显示生成进度。
- 页面切回前台时的状态补查为**静默**模式，不再连环弹出「任务仍在处理中」类 Toast，避免闪屏感。

可选的环境变量（Redis缓存）：
- `REDIS_HOST` - Redis主机地址（默认：localhost）
- `REDIS_PORT` - Redis端口（默认：6379）
- `REDIS_DB` - Redis数据库编号（默认：0）
- `REDIS_PASSWORD` - Redis密码（可选）

### 3. 数据库迁移

```bash
# 运行数据库迁移（Admin表新字段）
source products_env/bin/activate
python3 -c "
from backend.app import create_app
from backend.models import db
from sqlalchemy import text

app = create_app('development')
with app.app_context():
    result = db.session.execute(text('DESCRIBE admins'))
    columns = [row[0] for row in result]
    
    if 'password_changed_at' not in columns:
        db.session.execute(text('ALTER TABLE admins ADD COLUMN password_changed_at DATETIME'))
    if 'must_change_password' not in columns:
        db.session.execute(text('ALTER TABLE admins ADD COLUMN must_change_password BOOLEAN DEFAULT FALSE'))
    
    db.session.commit()
    print('✅ 数据库迁移完成')
"
```

### 4. 启动服务（使用Systemd）

```bash
# 复制服务文件
sudo cp systemd/nanyi-backend.service /etc/systemd/system/
sudo cp systemd/nanyi-frontend.service /etc/systemd/system/

# 重新加载systemd
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable nanyi-backend.service
sudo systemctl enable nanyi-frontend.service

# 启动服务
sudo systemctl start nanyi-backend.service
sudo systemctl start nanyi-frontend.service

# 查看状态
sudo systemctl status nanyi-backend.service
sudo systemctl status nanyi-frontend.service
```

## 服务管理

### Systemd命令

```bash
# 查看状态
sudo systemctl status nanyi-backend.service
sudo systemctl status nanyi-frontend.service

# 启动/停止/重启
sudo systemctl start nanyi-backend.service
sudo systemctl stop nanyi-backend.service
sudo systemctl restart nanyi-backend.service

# 查看日志
sudo journalctl -u nanyi-backend.service -f
sudo journalctl -u nanyi-frontend.service -f
```

详细说明请参考 `systemd/README.md`

## API文档

### 健康检查
- `GET /health` - 后端健康检查
- `GET /api/health` - API健康检查

### 产品API
- `GET /api/images` - 获取图片列表（支持分页）
- `GET /api/brand/<brand_name>` - 获取品牌详情
- `GET /api/filters` - 获取筛选选项
- `GET /api/products` - 获取产品列表

### 点赞API
- `POST /api/like/card/<brand_name>` - 点赞品牌
- `GET /api/like/card/<brand_name>` - 获取点赞状态

## 安全特性

1. **环境变量配置**: 所有敏感信息从环境变量读取
2. **CORS保护**: 仅允许HTTPS域名（开发环境允许localhost）
3. **密码策略**: 强制密码强度验证
4. **请求限流**: API接口限流保护
5. **输入验证**: 参数类型和范围验证
6. **错误处理**: 统一的错误处理机制

## 性能优化

1. **数据库索引**: 为常用查询字段添加索引
2. **查询优化**: 避免N+1查询问题，使用数据库聚合查询
3. **缓存策略**: 多层缓存（Redis + 内存缓存）
   - Redis缓存：持久化缓存，支持分布式
   - 内存缓存：本地快速缓存，作为Redis的备用
4. **API性能监控**: 自动记录API响应时间，慢查询告警
5. **响应压缩**: Gzip压缩减少传输大小
6. **API版本控制**: 支持 `/api` 和 `/api/v1`

## 日志

- **后端日志**: `/opt/hanfu/products/logs/backend.log`
- **前端日志**: `/opt/hanfu/products/logs/frontend.log`
- **Systemd日志**: `sudo journalctl -u nanyi-backend.service`

## 开发指南

### 代码规范
- 使用Python 3.12
- 遵循PEP 8代码规范
- 所有代码添加中文注释

### 测试
```bash
# 运行测试（待实现）
pytest tests/
```

### 部署
1. 确保环境变量已配置
2. 运行数据库迁移
3. 使用systemd管理服务
4. 配置Nginx反向代理

## 故障排查

### 服务无法启动
1. 检查服务状态: `sudo systemctl status nanyi-backend.service`
2. 查看日志: `sudo journalctl -u nanyi-backend.service -n 50`
3. 检查环境变量: `cat .env`
4. 检查虚拟环境: `source products_env/bin/activate && python3 --version`

### 数据库连接失败
1. 检查数据库配置: `.env` 文件
2. 测试连接: `mysql -h $DB_HOST -u $DB_USER -p`
3. 检查防火墙规则

### 502 Bad Gateway
1. 检查后端服务: `sudo systemctl status nanyi-backend.service`
2. 检查前端服务: `sudo systemctl status nanyi-frontend.service`
3. 检查Nginx配置: `sudo nginx -t`
4. 重启Nginx: `sudo systemctl restart nginx`

## 更新日志

### 2026-01-20
- ✅ 代码审查和优化完成
- ✅ 虚拟环境重建
- ✅ Systemd服务配置
- ✅ 数据库迁移完成
- ✅ 安全性和性能优化

## 许可证

私有项目

## 联系方式

项目维护者: 南意秋棠团队

# 南意秋棠 - 汉服面料展示网站

一个专业的汉服面料展示和管理系统，采用前后端分离架构，支持面料筛选、图片预览、数据管理等功能。

## 🌟 项目特色

- **响应式设计**: 完美适配桌面端和移动端
- **智能筛选**: 支持年份、材质、主题、尺寸多维度筛选
- **图片预览**: 支持图片放大预览和下载功能
- **数据驱动**: 连接MySQL数据库，实时展示面料信息
- **分享功能**: 支持微信、QQ等多平台分享
- **前后端分离**: Flask后端API + 静态前端，易于部署和维护

## 🏗️ 技术架构

### 后端技术栈
- **Python 3.8+**
- **Flask 2.3.3** - Web框架
- **Flask-SQLAlchemy 3.0.5** - ORM数据库操作
- **Flask-CORS 4.0.0** - 跨域支持
- **PyMySQL 1.1.0** - MySQL数据库连接
- **python-dotenv 1.0.0** - 环境变量管理

### 前端技术栈
- **HTML5 + CSS3** - 页面结构和样式
- **JavaScript ES6+** - 交互逻辑
- **Vue.js 3** - 响应式数据绑定
- **响应式布局** - 移动端优先设计

### 数据库
- **MySQL 8.0** - 主数据库
- 包含产品表、分类表等完整数据结构

## 📁 项目结构

```
nanyi/
├── backend/                 # 后端代码
│   ├── app.py              # 主应用入口
│   ├── config/             # 配置文件
│   │   └── config.py       # 数据库和应用配置
│   ├── models/             # 数据模型
│   │   ├── __init__.py
│   │   └── product.py      # 产品模型
│   ├── routes/             # API路由
│   │   ├── __init__.py
│   │   └── api.py          # API接口
│   ├── services/           # 业务逻辑
│   │   ├── __init__.py
│   │   └── product_service.py
│   └── utils/              # 工具函数
│       ├── __init__.py
│       └── db_utils.py
├── frontend/               # 前端代码
│   ├── server.py           # 前端服务器
│   ├── index.html          # 主页面
│   ├── static/             # 静态资源
│   │   ├── css/
│   │   │   └── main.css    # 主样式文件
│   │   ├── js/
│   │   │   ├── main.js     # 主逻辑文件
│   │   │   ├── api.js      # API调用
│   │   │   └── utils.js    # 工具函数
│   │   └── images/         # 图片资源
├── logs/                   # 日志文件
├── .env                    # 环境变量配置（不上传到Git）
├── .env.example            # 环境变量模板
├── .gitignore              # Git忽略文件
├── requirements.txt        # Python依赖
├── start.sh                # 启动脚本
├── stop.sh                 # 停止脚本
└── README.md               # 项目说明
```

## 🚀 快速开始

### 1. 环境准备

确保系统已安装：
- Python 3.8+
- MySQL 8.0+
- Git

### 2. 克隆项目

```bash
git clone https://github.com/xiaoshi7915/nanyi.git
cd nanyi
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，配置数据库等信息
vim .env
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 启动服务

```bash
# 一键启动前后端服务
./start.sh

# 或者分别启动
# 后端服务
cd backend && python app.py

# 前端服务（新终端）
cd frontend && python server.py
```

### 6. 访问应用

- **前端页面**: http://localhost:8500
- **后端API**: http://localhost:5001
- **健康检查**: http://localhost:5001/health

## ⚙️ 配置说明

### 环境变量配置 (.env)

```bash
# 数据库配置
DB_HOST=your_db_host
DB_PORT=3306
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# 应用配置
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your_secret_key

# 服务端口
BACKEND_PORT=5001
FRONTEND_PORT=8500

# 域名配置
DOMAIN=your_domain
BACKEND_URL=http://your_domain:5001
FRONTEND_URL=http://your_domain:8500

# CORS配置
CORS_ORIGINS=http://your_domain:8500,http://localhost:8500
```

## 📊 数据库结构

### products 表
- `id` - 产品ID（主键）
- `name` - 产品名称
- `year` - 年份
- `material` - 材质
- `theme` - 主题
- `size` - 尺寸
- `image_url` - 图片URL
- `description` - 描述
- `created_at` - 创建时间
- `updated_at` - 更新时间

## 🔧 开发指南

### 添加新的API接口

1. 在 `backend/routes/api.py` 中添加路由
2. 在 `backend/services/` 中添加业务逻辑
3. 在前端 `static/js/api.js` 中添加API调用

### 修改前端样式

1. 编辑 `frontend/static/css/main.css`
2. 修改响应式断点和样式规则
3. 测试不同设备的显示效果

### 数据库迁移

```bash
# 进入后端目录
cd backend

# 运行数据库初始化脚本
python -c "from utils.db_utils import init_database; from app import create_app; app = create_app(); init_database(app)"
```

## 🚀 部署指南

### 生产环境部署

1. **服务器准备**
   ```bash
   # 安装必要软件
   yum install python3 python3-pip mysql-server nginx
   
   # 启动MySQL
   systemctl start mysqld
   systemctl enable mysqld
   ```

2. **配置环境变量**
   ```bash
   # 设置生产环境配置
   export FLASK_ENV=production
   export FLASK_DEBUG=False
   ```

3. **使用Gunicorn部署后端**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5001 backend.app:create_app()
   ```

4. **配置Nginx反向代理**
   ```nginx
   server {
       listen 80;
       server_name your_domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8500;
       }
       
       location /api {
           proxy_pass http://127.0.0.1:5001;
       }
   }
   ```

## 🛠️ 常用命令

```bash
# 启动服务
./start.sh

# 停止服务
./stop.sh

# 查看日志
tail -f logs/backend.log
tail -f logs/frontend.log

# 重启服务
./stop.sh && ./start.sh

# 检查服务状态
curl http://localhost:5001/health
curl http://localhost:8500/health
```

## 🐛 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查 `.env` 文件中的数据库配置
   - 确认MySQL服务已启动
   - 验证数据库用户权限

2. **端口被占用**
   ```bash
   # 查看端口占用
   netstat -tlnp | grep :5001
   netstat -tlnp | grep :8500
   
   # 杀死占用进程
   kill -9 <PID>
   ```

3. **前端无法访问后端API**
   - 检查CORS配置
   - 确认防火墙设置
   - 验证后端服务是否正常运行

## 📝 更新日志

### v1.0.0 (2024-01-XX)
- ✨ 初始版本发布
- 🎨 响应式前端界面
- 🔧 Flask后端API
- 💾 MySQL数据库集成
- 📱 移动端适配
- 🔍 多维度筛选功能
- 📤 分享功能

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👥 联系方式

- 项目维护者: [xiaoshi7915](https://github.com/xiaoshi7915)
- 项目地址: [https://github.com/xiaoshi7915/nanyi](https://github.com/xiaoshi7915/nanyi)

---

**南意秋棠** - 传承汉服文化，展示面料之美 ✨ 
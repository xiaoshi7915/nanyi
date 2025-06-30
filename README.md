# 南意秋棠汉服展示网站

<div align="center">

![南意秋棠](https://img.shields.io/badge/南意秋棠-汉服展示-red?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTMuMDkgOC4yNkwyMSA5TDE0IDEyTDEzLjA5IDE1Ljc0TDEyIDIyTDEwLjkxIDE1Ljc0TDMgMTJMMTAgOUwxMC45MSA4LjI2TDEyIDJaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4K)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green?style=for-the-badge&logo=flask)
![Vue.js](https://img.shields.io/badge/Vue.js-3.x-green?style=for-the-badge&logo=vue.js)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?style=for-the-badge&logo=mysql)

**传承经典 美美与共 - 古典美学设计，望君着美于裳**

🌸 专业的汉服面料设计与展示平台 🌸

</div>

## 📖 项目简介

南意秋棠汉服展示网站是一个专业的汉服设计展示平台，致力于传承和发扬中华传统服饰文化。网站展示了各种精美的汉服设计，包括不同材质、主题系列和印花工艺的产品。

### ✨ 主要特色

- 🎨 **精美设计展示** - 高质量汉服设计图片展示
- 🔍 **智能筛选系统** - 按年份、材质、主题等多维度筛选
- 💖 **互动点赞功能** - 用户可为喜爱的设计点赞
- 📱 **响应式设计** - 完美适配移动端和桌面端
- 🚀 **高性能加载** - 优化的图片加载和缓存策略
- 🎪 **分享功能** - 精美的设计分享卡片
- 🌐 **社交平台集成** - 一键跳转淘宝、小红书、微店、微信

## 🏗️ 技术架构

### 前端技术栈
- **Vue.js 3.x** - 现代化前端框架
- **HTML5/CSS3** - 响应式布局
- **JavaScript ES6+** - 交互逻辑
- **Axios** - HTTP请求库

### 后端技术栈
- **Python 3.8+** - 编程语言
- **Flask 2.3.3** - Web应用框架
- **Flask-SQLAlchemy 3.1.1** - ORM数据库操作
- **PyMySQL** - MySQL数据库连接
- **Flask-CORS** - 跨域资源共享

### 数据存储
- **MySQL 8.0** - 关系型数据库
- **本地文件系统** - 图片资源存储
- **内存缓存** - 提升响应速度

### 部署环境
- **CentOS/Linux** - 服务器操作系统
- **Nginx** - 反向代理和静态资源服务
- **Python虚拟环境** - 依赖隔离

## 🚀 快速开始

### 环境要求

- Python 3.8+
- MySQL 8.0+
- Git
- Linux/MacOS/Windows

### 一键部署

```bash
# 克隆项目
git clone <repository-url>
cd products

# 运行一键部署脚本
chmod +x deploy.sh
./deploy.sh

# 或者分步骤部署
./deploy.sh install  # 仅安装环境
./deploy.sh start     # 仅启动服务
./deploy.sh verify    # 验证部署状态
```

### 手动部署

#### 1. 环境设置

```bash
# 创建虚拟环境
python3 -m venv products_env
source products_env/bin/activate

# 或使用快速设置脚本
chmod +x setup-env.sh
./setup-env.sh
```

#### 2. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 或使用当前版本依赖
pip install -r requirements-current.txt
```

#### 3. 配置环境变量

创建 `.env` 文件：

```env
# 服务配置
FLASK_ENV=development
DEBUG=True
BACKEND_PORT=5001
FRONTEND_PORT=8500
HOST=0.0.0.0

# 数据库配置
DB_HOST=your_db_host
DB_PORT=3306
DB_NAME=nanyiqiutang
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# 安全配置
SECRET_KEY=your_secret_key_here
```

#### 4. 初始化数据库

```bash
# 激活虚拟环境
source products_env/bin/activate

# 初始化数据库
cd backend
python app.py
```

#### 5. 启动服务

```bash
# 使用管理脚本
./manage.sh start

# 或手动启动
# 后端服务
cd backend && python app.py &

# 前端服务  
cd frontend && python server.py &
```

## 📁 项目结构

```
products/
├── backend/                 # 后端代码
│   ├── app.py              # Flask应用入口
│   ├── config/             # 配置文件
│   ├── models/             # 数据模型
│   ├── routes/             # API路由
│   ├── services/           # 业务逻辑服务
│   └── utils/              # 工具函数
├── frontend/               # 前端代码
│   ├── index.html          # 主页面
│   ├── css/                # 样式文件
│   ├── js/                 # JavaScript文件
│   ├── static/             # 静态资源
│   └── server.py           # 前端服务器
├── nginx/                  # Nginx配置
├── logs/                   # 日志文件
├── requirements.txt        # Python依赖(主要)
├── requirements-current.txt # 当前环境依赖(完整)
├── deploy.sh               # 一键部署脚本
├── setup-env.sh            # 环境设置脚本
├── manage.sh               # 服务管理脚本
└── README.md               # 项目说明
```

## 🛠️ 开发指南

### 开发环境设置

```bash
# 激活开发环境
source products_env/bin/activate

# 启动开发服务器
./manage.sh start

# 查看日志
tail -f logs/app.log
```

### API接口文档

#### 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/images` | GET | 获取图片列表(支持分页) |
| `/api/filters` | GET | 获取筛选选项 |
| `/api/brand/<name>` | GET | 获取品牌详情 |
| `/api/like/card/<name>` | POST | 品牌点赞 |
| `/api/share/card/<name>` | GET | 生成分享卡片 |
| `/health` | GET | 健康检查 |

#### 请求示例

```javascript
// 获取图片列表
fetch('/api/images?page=1&per_page=12')
  .then(response => response.json())
  .then(data => console.log(data));

// 品牌点赞
fetch('/api/like/card/一丛花令', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'}
})
.then(response => response.json())
.then(data => console.log(data));
```

### 数据库设计

#### 主要数据表

- **products** - 产品信息表
- **brand_likes** - 品牌点赞表  
- **access_logs** - 访问日志表
- **admins** - 管理员表

### 前端组件

- **ProductCard** - 产品卡片组件
- **FilterPanel** - 筛选面板组件
- **LikeButton** - 点赞按钮组件
- **ShareCard** - 分享卡片组件
- **SocialIcons** - 社交平台图标组件

### 社交平台集成

网站头部集成了四个主要社交平台入口，按以下顺序排列：

#### 🛒 淘宝店铺
- **图标**: taobao.png
- **链接**: https://m.tb.cn/h.hVSffucqrHuJeRZ
- **功能**: 直接跳转到南意秋棠淘宝店铺
- **适配**: 移动端和桌面端均可访问

#### 📱 小红书
- **图标**: xiaohongshu.jpg  
- **链接**: https://www.xiaohongshu.com/user/profile/60195c9800000000010082c4
- **功能**: 跳转到南意秋棠小红书主页
- **内容**: 汉服设计灵感和穿搭分享

#### 🏪 微店
- **图标**: weidian.jpg
- **链接**: https://weidian.com/?userid=1330457134
- **功能**: 访问南意秋棠微店
- **特色**: 移动端购物体验优化

#### 💬 微信客服
- **图标**: wechat.png
- **功能**: 智能客服系统
- **服务**: 
  - 小南客服: LPumpkin0217
  - 染白客服: moonysy511
- **特色**: 一键复制微信号，快速联系客服

## 🔧 服务管理

### 服务控制命令

```bash
# 启动所有服务
./manage.sh start

# 停止所有服务
./manage.sh stop

# 重启所有服务
./manage.sh restart

# 查看服务状态
./manage.sh status

# 查看日志
./manage.sh logs
```

### 访问地址

- **前端页面**: http://localhost:8500
- **后端API**: http://localhost:5001  
- **健康检查**: http://localhost:5001/health
- **域名访问**: http://products.nanyiqiutang.cn

## 📊 性能优化

### 缓存策略
- API响应缓存(Redis/内存)
- 图片资源CDN加速
- 数据库查询优化
- 前端资源压缩

### 监控指标
- 响应时间监控
- 数据库性能监控
- 服务器资源监控
- 用户访问统计

## 🐛 故障排除

### 常见问题

#### 1. 数据库连接失败
```bash
# 检查数据库配置
cat .env | grep DB_

# 测试数据库连接
mysql -h your_db_host -u your_db_user -p
```

#### 2. 服务启动失败
```bash
# 检查端口占用
netstat -tlnp | grep -E ":(5001|8500)"

# 查看错误日志
tail -f logs/app.log
```

#### 3. 图片无法显示
```bash
# 检查图片目录权限
ls -la frontend/static/images/

# 检查Nginx配置
nginx -t
```

## 📦 依赖管理

### 更新依赖

```bash
# 激活虚拟环境
source products_env/bin/activate

# 生成当前依赖清单
pip freeze > requirements-current.txt

# 安装新依赖
pip install package_name
pip freeze > requirements-current.txt
```

### 依赖文件说明

- `requirements.txt` - 主要依赖，手动维护
- `requirements-current.txt` - 完整依赖快照，自动生成
- `requirements-lock.txt` - 锁定版本依赖

## 🚀 部署到生产环境

### 生产环境配置

```bash
# 修改环境变量
export FLASK_ENV=production
export DEBUG=False

# 使用生产级WSGI服务器
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 backend.app:app
```

### Nginx配置

```nginx
server {
    listen 80;
    server_name products.nanyiqiutang.cn;
    
    location / {
        proxy_pass http://127.0.0.1:8500;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📝 更新日志

### v2.1.0 (2025-06-26)
- ✅ 新增社交平台图标集成
- ✅ 替换原有微店和智能客服图标为实际logo
- ✅ 新增淘宝和小红书平台入口
- ✅ 优化图标显示效果和响应式适配
- ✅ 保持原有微信客服功能不变

### v2.0.0 (2025-06-23)
- ✅ 修复Flask-SQLAlchemy 3.x兼容性问题
- ✅ 完善虚拟环境管理
- ✅ 添加一键部署脚本
- ✅ 优化图片加载性能
- ✅ 完善项目文档

### v1.5.0
- ✅ 添加品牌点赞功能
- ✅ 实现分享卡片功能
- ✅ 优化移动端适配

### v1.0.0
- ✅ 基础功能实现
- ✅ 图片展示系统
- ✅ 筛选功能

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目！

### 开发流程

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👥 联系我们

- **项目负责人**: 南意秋棠团队
- **技术支持**: 请通过 GitHub Issues 联系
- **网站**: http://products.nanyiqiutang.cn

---

<div align="center">

**南意秋棠 - 传承经典，美美与共** 🌸

Made with ❤️ by 南意秋棠团队

</div>
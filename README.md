# 南意秋棠汉服产品展示系统

一个专业的汉服产品展示网站，支持品牌分类、图片展示和产品搜索功能。

## 🚀 快速启动

### 环境要求
- Python 3.7+
- MySQL 5.7+
- 系统：Linux/macOS/Windows

### 安装和运行
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置数据库
# 编辑 .env 文件，设置数据库连接信息
cp .env.example .env

# 3. 启动服务
./start_services_fixed.sh

# 4. 停止服务
./stop_services.sh
```

## 📱 访问地址

### 前端网站
- **IP访问**: http://121.36.205.70:8500
- **域名访问**: http://chenxiaoshivivid.com.cn:8500

### 后端API
- **IP访问**: http://121.36.205.70:5001
- **域名访问**: http://chenxiaoshivivid.com.cn:5001

### 主要API接口
- `GET /api/images` - 获取所有图片数据
- `GET /api/brands` - 获取品牌列表
- `GET /api/share/card/<brand_name>` - 生成布料分享卡片数据
- `GET /api/cache/stats` - 缓存统计
- `GET /api/logs/access/stats` - 访问日志统计

## 🎨 功能特性

### 前端功能
- 📸 **图片展示** - 支持布料图、设计图、成衣图等多种类型
- 🏷️ **品牌分类** - 按品牌组织产品展示
- 🔍 **搜索功能** - 支持品牌名称、布料材质、主题搜索
- 📱 **响应式设计** - 适配桌面和移动设备
- 🖼️ **图片预览** - 点击放大查看高清图片
- 📋 **布料卡片分享** - 生成精美卡片，支持微信朋友圈分享
  - 包含布料名、设计灵感、产品图片
  - 长按保存图片或分享
  - 支持复制链接分享

### 后端功能
- 🗄️ **数据库管理** - MySQL存储产品和图片信息
- 🚀 **缓存优化** - Redis缓存提高响应速度
- 📊 **访问统计** - 记录和分析用户访问数据
- 🔒 **CORS支持** - 跨域访问配置
- 📝 **日志记录** - 详细的访问和错误日志

## 🖼️ 图片存储系统

### 当前配置：本地图片存储
系统当前使用本地图片存储，图片文件存放在 `frontend/static/images/` 目录下。

### 图片源切换
```bash
# 查看当前图片源状态
./switch-image-source.sh status

# 切换到本地图片源（当前使用）
./switch-image-source.sh local

# 切换到OSS图片源（需要配置跨域）
./switch-image-source.sh oss
```

### OSS图片存储（可选）
如需使用阿里云OSS存储：

1. **配置OSS跨域访问**
   ```bash
   ./configure-oss-cors.sh  # 查看配置指导
   ```

2. **测试OSS访问**
   ```bash
   ./test-oss-access.sh
   ```

3. **切换到OSS**
   ```bash
   ./switch-image-source.sh oss
   ```

## 🔧 管理工具

### 服务管理
```bash
./start_services_fixed.sh    # 启动所有服务
./stop_services.sh          # 停止所有服务
./service-manager.sh        # 服务管理菜单
```

### 系统监控
```bash
# 查看服务状态
ps aux | grep -E "(app.py|server.py)"

# 查看端口占用
netstat -tlnp | grep -E "(5001|8500)"

# 查看日志
tail -f logs/backend.log     # 后端日志
tail -f logs/frontend.log    # 前端日志
tail -f logs/access.log      # 访问日志
```

## 🗂️ 项目结构

```
products/
├── backend/                 # 后端Flask应用
│   ├── app.py              # 主应用文件
│   ├── config/             # 配置文件
│   ├── models/             # 数据模型
│   ├── routes/             # 路由定义
│   ├── services/           # 业务逻辑
│   └── utils/              # 工具函数
├── frontend/               # 前端静态文件
│   ├── index.html          # 主页面
│   ├── css/                # 样式文件
│   ├── js/                 # JavaScript文件
│   └── static/             # 静态资源
├── logs/                   # 日志文件
├── .env                    # 环境配置
└── requirements.txt        # Python依赖
```

## 🔧 常见问题解决

### 1. 服务启动失败
```bash
# 检查端口占用
netstat -tlnp | grep -E "(5001|8500)"

# 强制停止服务
./stop_services.sh

# 重新启动
./start_services_fixed.sh
```

### 2. 图片加载失败
```bash
# 检查当前图片源
./switch-image-source.sh status

# 切换到本地图片源
./switch-image-source.sh local

# 如果使用OSS，检查跨域配置
./configure-oss-cors.sh
```

### 3. 域名访问问题
如果域名无法访问：
1. **清除浏览器缓存** - Ctrl+Shift+Delete
2. **使用无痕模式** - Ctrl+Shift+N
3. **使用IP访问** - http://121.36.205.70:8500
4. **检查网络环境** - 尝试手机热点

### 4. 数据库连接问题
```bash
# 检查数据库配置
cat .env | grep DB_

# 测试数据库连接
mysql -h localhost -u nanyi -p nanyiqiutang
```

## 📊 系统状态

### 当前配置
- ✅ **前端服务**: 运行在8500端口
- ✅ **后端服务**: 运行在5001端口  
- ✅ **数据库**: MySQL连接正常
- ✅ **图片存储**: 本地存储模式
- ✅ **域名访问**: 支持IP和域名访问

### 性能特性
- 🚀 **缓存优化**: Redis缓存提升响应速度
- 📱 **响应式设计**: 移动端友好
- 🔍 **搜索功能**: 快速产品查找
- 📊 **访问统计**: 用户行为分析

## 🎯 技术栈

- **前端**: HTML5, CSS3, JavaScript, Vue.js
- **后端**: Python Flask, SQLAlchemy
- **数据库**: MySQL
- **缓存**: Redis
- **Web服务器**: Python内置服务器
- **图片存储**: 本地存储 + 阿里云OSS（可选）

## 📞 支持

如遇到问题：
1. 查看日志文件定位错误
2. 运行相关诊断脚本
3. 检查服务和端口状态
4. 确认网络连接正常

---

**南意秋棠汉服展示系统** - 专业、美观、高效的汉服产品展示平台 
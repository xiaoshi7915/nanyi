# 南意秋棠项目依赖管理指南

## 🚨 依赖冲突问题

其他项目的以下依赖包可能会破坏当前项目环境：

### ⚠️ 危险的依赖组合
```
APScheduler>=3.10.0          # 任务调度器，可能与Flask冲突
python-magic>=0.4.27         # 文件类型检测，可能影响Pillow
PyYAML>=6.0                  # YAML解析器，可能影响配置加载
colorlog>=6.7.0              # 彩色日志，可能影响Flask日志
simplejson>=3.19.0           # JSON处理，可能与Flask内置JSON冲突
gunicorn                     # WSGI服务器，与开发服务器冲突
```

### 🔧 版本冲突说明

1. **Flask-SQLAlchemy版本冲突**
   - 其他项目要求: `>=3.0.0`
   - 当前项目锁定: `==3.1.1`
   - 冲突原因: 版本范围可能导致意外升级

2. **SQLAlchemy版本冲突**
   - 其他项目要求: `>=2.0.0`
   - 当前项目锁定: `==2.0.23`
   - 冲突原因: 新版本可能有API变化

## 🛡️ 预防措施

### 1. 使用锁定版本文件
```bash
# 安装精确版本
pip install -r requirements-lock.txt
```

### 2. 环境隔离
```bash
# 为每个项目创建独立虚拟环境
python -m venv project_specific_env
source project_specific_env/bin/activate
```

### 3. 定期检查
```bash
# 检查是否有意外安装的包
pip list | grep -E "(APScheduler|python-magic|PyYAML|colorlog|simplejson|gunicorn)"
```

## 🚑 紧急修复

### 方法1: 使用恢复脚本
```bash
./restore-env.sh
```

### 方法2: 手动修复
```bash
# 1. 激活虚拟环境
source products_env/bin/activate

# 2. 卸载冲突包
pip uninstall -y APScheduler python-magic PyYAML colorlog simplejson gunicorn

# 3. 重新安装锁定版本
pip install -r requirements-lock.txt --force-reinstall

# 4. 重启服务
pkill -f "python.*app.py"
pkill -f "python.*server.py"
cd backend && python app.py &
cd ../frontend && python server.py &
```

## 📋 验证清单

修复后请验证以下内容：

- [ ] Flask版本: 2.3.3
- [ ] Flask-SQLAlchemy版本: 3.1.1  
- [ ] SQLAlchemy版本: 2.0.23
- [ ] 后端服务: http://localhost:5001/health
- [ ] 前端服务: http://localhost:8500
- [ ] 筛选API: 返回真实数据而非默认数据
- [ ] 图片显示: 正常加载
- [ ] 数据库连接: 无SQLAlchemy错误

## 🔄 日常维护

### 安装新依赖时的注意事项
1. 先在测试环境验证
2. 检查版本兼容性
3. 更新requirements-lock.txt
4. 测试所有功能

### 备份当前工作环境
```bash
pip freeze > backup-$(date +%Y%m%d).txt
```

## 📞 故障排除

如果遇到以下错误：

### SQLAlchemy错误
```
The current Flask app is not registered with this 'SQLAlchemy' instance
```
**解决方案**: 运行 `./restore-env.sh`

### 模块导入错误
```
ImportError: cannot import name 'app_ctx' from 'flask.globals'
```
**解决方案**: Flask版本不匹配，重新安装锁定版本

### 端口占用错误
```
Address already in use
```
**解决方案**: `pkill -f "python.*app.py"` 然后重启 
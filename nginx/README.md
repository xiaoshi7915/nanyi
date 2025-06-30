# Nginx域名配置指南

## 🎯 目标
配置nginx反向代理，让以下域名都可以访问您的汉服产品展示网站：
- `products.nanyiqiutang.cn`
- `products.chenxiaoshivivid.com.cn`

## 🚀 快速部署

### 一键部署
```bash
sudo ./deploy-config.sh
```

### 测试验证
```bash
./test-domains.sh
```

## 📋 配置说明

### 文件结构
```
nginx/
├── products-sites.conf     # 主配置文件
├── deploy-config.sh       # 部署脚本
├── test-domains.sh        # 测试脚本
└── README.md             # 说明文档
```

### 代理配置
- **前端页面**: `/*` → `127.0.0.1:8500`
- **API接口**: `/api/*` → `127.0.0.1:5001`
- **静态资源**: 30天缓存优化

### 域名重定向
- `nanyiqiutang.cn` → `products.nanyiqiutang.cn`
- `chenxiaoshivivid.com.cn` → `products.chenxiaoshivivid.com.cn`

## 🔧 手动部署步骤

### 1. 复制配置文件
```bash
sudo cp products-sites.conf /etc/nginx/conf.d/
```

### 2. 测试配置语法
```bash
sudo nginx -t
```

### 3. 重新加载nginx
```bash
sudo systemctl reload nginx
```

### 4. 验证访问
```bash
curl -I http://products.nanyiqiutang.cn
curl -I http://products.chenxiaoshivivid.com.cn
```

## 📊 监控和日志

### 查看访问日志
```bash
tail -f /var/log/nginx/products.nanyiqiutang.cn.access.log
tail -f /var/log/nginx/products.chenxiaoshivivid.com.cn.access.log
```

### 查看错误日志
```bash
tail -f /var/log/nginx/products.nanyiqiutang.cn.error.log
tail -f /var/log/nginx/products.chenxiaoshivivid.com.cn.error.log
```

### 健康检查
```bash
curl http://products.nanyiqiutang.cn/nginx-health
```

## 🛠️ 故障排查

### 常见问题

1. **502 Bad Gateway**
   - 检查后端服务: `curl http://127.0.0.1:8500`
   - 检查进程状态: `ps aux | grep -E "(app.py|server.py)"`

2. **404 Not Found**
   - 检查nginx配置: `nginx -t`
   - 检查配置加载: `systemctl status nginx`

3. **域名无法访问**
   - 检查DNS解析: `nslookup products.nanyiqiutang.cn`
   - 检查防火墙: `systemctl status firewalld`

### 调试命令
```bash
# 检查nginx进程
ps aux | grep nginx

# 检查端口监听
netstat -tlnp | grep :80

# 检查配置文件
nginx -T | grep -A 10 -B 10 products

# 重启nginx
sudo systemctl restart nginx
```

## 🔒 安全配置

当前配置包含的安全特性：
- ✅ 隐藏nginx版本信息
- ✅ 限制文件上传大小(50M)
- ✅ CORS跨域控制
- ✅ 静态资源缓存优化
- ✅ 连接超时控制

## 📈 性能优化

配置中的性能优化：
- ✅ upstream keepalive连接池
- ✅ proxy buffering缓冲优化
- ✅ 静态文件长期缓存
- ✅ gzip压缩(如果启用)

## 🚨 注意事项

1. **备份原配置**: 部署前会自动备份现有配置
2. **测试优先**: 配置语法错误会自动回滚
3. **日志监控**: 建议定期查看error日志
4. **服务依赖**: 确保前后端服务(8500/5001)正常运行

## 📞 支持

如果遇到问题：
1. 运行测试脚本: `./test-domains.sh`
2. 查看错误日志
3. 检查服务状态
4. 参考故障排查章节 
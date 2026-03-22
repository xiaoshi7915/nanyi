# Systemd 服务管理

## 服务文件

- `nanyi-backend.service` - 后端服务
- `nanyi-frontend.service` - 前端服务

## 后端降权与目录权限（使用 `nanyi` 用户前必做）

`nanyi-backend.service` 以 **`User=nanyi`** 运行，且 `ProtectSystem=strict` 下仅 **`ReadWritePaths`** 中的路径可写（当前为 `logs` 与试衣本地存储）。

```bash
# 系统用户（无登录 shell）
sudo useradd -r -M -s /sbin/nologin nanyi 2>/dev/null || true

sudo mkdir -p /opt/hanfu/products/logs /opt/hanfu/products/backend/try_on/storage

# 可写目录归 nanyi
sudo chown -R nanyi:nanyi /opt/hanfu/products/logs /opt/hanfu/products/backend/try_on/storage

# 代码与虚拟环境需可读、可进入目录（按你当前部署属主选择其一）：
# 方案 A：整仓对其它用户开放读与目录执行
sudo chmod -R a+rX /opt/hanfu/products
# 方案 B：将项目组设为 nanyi 并组读
# sudo chgrp -R nanyi /opt/hanfu/products && sudo chmod -R g+rX /opt/hanfu/products
```

若 `.env` 中 **`STORAGE_LOCAL_PATH`** 指向其它目录，请在 `nanyi-backend.service` 里为该路径增加一行 `ReadWritePaths=`，并同样 `chown nanyi:nanyi`。

## 安装步骤

### 1. 复制服务文件
```bash
sudo cp /opt/hanfu/products/systemd/nanyi-backend.service /etc/systemd/system/
sudo cp /opt/hanfu/products/systemd/nanyi-frontend.service /etc/systemd/system/
```

### 2. 重新加载systemd配置
```bash
sudo systemctl daemon-reload
```

### 3. 启用服务（开机自启）
```bash
sudo systemctl enable nanyi-backend.service
sudo systemctl enable nanyi-frontend.service
```

### 4. 启动服务
```bash
sudo systemctl start nanyi-backend.service
sudo systemctl start nanyi-frontend.service
```

## 常用命令

### 查看服务状态
```bash
# 查看单个服务状态
sudo systemctl status nanyi-backend.service
sudo systemctl status nanyi-frontend.service

# 查看所有服务状态
sudo systemctl status nanyi-backend.service nanyi-frontend.service
```

### 启动/停止/重启服务
```bash
# 启动
sudo systemctl start nanyi-backend.service
sudo systemctl start nanyi-frontend.service

# 停止
sudo systemctl stop nanyi-backend.service
sudo systemctl stop nanyi-frontend.service

# 重启
sudo systemctl restart nanyi-backend.service
sudo systemctl restart nanyi-frontend.service
```

### 查看日志
```bash
# 查看服务日志
sudo journalctl -u nanyi-backend.service -f
sudo journalctl -u nanyi-frontend.service -f

# 查看最近的日志
sudo journalctl -u nanyi-backend.service -n 50
sudo journalctl -u nanyi-frontend.service -n 50

# 查看应用日志
tail -f /opt/hanfu/products/logs/backend.log
tail -f /opt/hanfu/products/logs/frontend.log
```

### 禁用/启用服务
```bash
# 禁用开机自启
sudo systemctl disable nanyi-backend.service
sudo systemctl disable nanyi-frontend.service

# 启用开机自启
sudo systemctl enable nanyi-backend.service
sudo systemctl enable nanyi-frontend.service
```

## 服务配置说明

### 后端服务 (nanyi-backend.service)
- **类型**: notify (gunicorn 支持 systemd 通知)
- **运行用户**: `nanyi`（非 root）
- **工作目录**: /opt/hanfu/products
- **端口**: 5432
- **Worker**: 2，`worker-class=gthread`，`threads=8`（利于 SSE 长连接与其它请求并发）
- **keep-alive**: 75（长连接更友好）
- **可写路径**: 仅 `logs/` 与 `backend/try_on/storage/`（见服务单元文件中 `ReadWritePaths`）
- **自动重启**: 是（10 秒后）
- **日志**: 
  - systemd: `journalctl -u nanyi-backend.service`
  - 应用: `/opt/hanfu/products/logs/backend.log`

### 前端服务 (nanyi-frontend.service)
- **类型**: simple (Flask开发服务器)
- **工作目录**: /opt/hanfu/products/frontend
- **端口**: 8500
- **自动重启**: 是（10秒后）
- **日志**: 
  - systemd日志: `journalctl -u nanyi-frontend.service`
  - 应用日志: `/opt/hanfu/products/logs/frontend.log`

## 故障排查

### 服务无法启动
1. 检查服务状态: `sudo systemctl status nanyi-backend.service`
2. 查看日志: `sudo journalctl -u nanyi-backend.service -n 50`
3. 检查虚拟环境: `ls -la /opt/hanfu/products/products_env/bin/`
4. 检查端口占用: `netstat -tlnp | grep -E "8500|5432"`

### 服务频繁重启
1. 查看日志找出错误原因
2. 检查资源限制（内存、文件描述符）
3. 检查依赖服务（数据库、网络）

### 修改服务配置后
```bash
# 修改服务文件后需要重新加载
sudo systemctl daemon-reload
sudo systemctl restart nanyi-backend.service
```

## 优势

1. **自动重启**: 服务崩溃后自动重启
2. **开机自启**: 系统重启后自动启动服务
3. **日志管理**: 统一的日志管理
4. **资源控制**: 可以设置资源限制
5. **依赖管理**: 可以设置服务依赖关系
6. **状态监控**: 方便监控服务状态

## 注意事项

1. 服务文件中的路径必须是绝对路径
2. 确保虚拟环境路径正确
3. 确保日志目录有写权限
4. 修改服务文件后需要重新加载: `sudo systemctl daemon-reload`

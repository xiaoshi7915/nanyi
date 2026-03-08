# 存储路径更新总结

## 更新内容

已将 Try-On 服务生成的照片存储路径从前端文件夹改为前端文件夹，便于前端直接访问。

## 配置变更

### .env 文件更新

**修改前**:
```env
STORAGE_LOCAL_PATH=./backend/try_on/storage
```

**修改后**:
```env
STORAGE_LOCAL_PATH=./frontend/static/images
```

## 存储目录结构

生成的照片现在保存在：
```
frontend/static/images/generated/
```

前端可以通过以下 URL 访问：
```
/static/images/generated/文件名.jpg
```

## 代码变更

### 1. 路径转换逻辑

在 `backend/services/try_on_image_service.py` 中添加了路径转换逻辑：
- 检查保存的本地路径是否在前端文件夹下
- 如果是，将绝对路径转换为前端可访问的相对 URL
- 格式：`/static/images/generated/文件名.jpg`

### 2. URL 优先级

- **优先使用本地路径**：如果图片保存在前端文件夹下，使用本地 URL
- **回退到 OSS URL**：如果不在前端文件夹下或本地保存失败，使用 OSS URL

## 目录创建

已创建必要的目录：
```bash
mkdir -p frontend/static/images/generated
```

## 优势

1. **前端直接访问**：生成的照片可以直接通过 `/static/images/generated/` 访问
2. **无需额外代理**：不需要通过后端 API 代理图片
3. **统一管理**：所有图片都在 `frontend/static/images/` 目录下
4. **便于清理**：可以轻松删除 `backend/try_on` 文件夹

## 注意事项

1. **文件权限**：确保应用有权限在 `frontend/static/images/generated/` 目录下创建文件
2. **目录清理**：定期清理旧的照片文件，避免占用过多磁盘空间
3. **备份策略**：如果需要备份，可以配置定期备份 `frontend/static/images/generated/` 目录

## 验证

重启服务后，新生成的照片将保存在：
- 本地路径：`frontend/static/images/generated/文件名.jpg`
- 访问 URL：`/static/images/generated/文件名.jpg`

可以通过以下方式验证：
1. 创建一个试衣任务
2. 等待任务完成
3. 检查 `frontend/static/images/generated/` 目录是否有新文件
4. 检查返回的 `result_image_url` 是否为 `/static/images/generated/...` 格式

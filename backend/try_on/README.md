# DEPRECATED — 遗留试衣子树

**本目录为历史独立 FastAPI/试衣服务骨架，已不再作为线上入口。**

## 以谁为准

- **主站 Flask 集成**（`backend/routes/try_on.py`、`backend/services/try_on_*`、`backend/controllers/try_on_controller.py`）是当前唯一正式路径。
- 对外 API：`/api/try-on/*`（由主应用 gunicorn / `nanyi-backend` 提供）。

## 为何保留

- 内含早期模型适配、Mock、限流与部分单测，可供对照或迁移参考。
- **请勿**再单独部署本树，也勿假定其配置/路由与主站一致。

## 后续

归档或精简删除可在单独清理阶段进行；本阶段仅标明废弃，避免误用。

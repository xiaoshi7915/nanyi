#!/bin/bash
# 发布前 bump 缓存版本号（同步 app-version.js 与 index.html 中的 ?v=）
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="${1:-$(date +%Y%m%d)-1}"
APP_VERSION_FILE="$ROOT/frontend/js/app-version.js"
INDEX_FILE="$ROOT/frontend/index.html"

if [ ! -f "$APP_VERSION_FILE" ]; then
  echo "找不到 $APP_VERSION_FILE"
  exit 1
fi

sed -i "s/var APP_RELEASE_VERSION = '[^']*'/var APP_RELEASE_VERSION = '${VERSION}'/" "$APP_VERSION_FILE"
sed -i "s/?v=[0-9][0-9]*/?v=${VERSION}/g" "$INDEX_FILE"

echo "已更新发布版本号为: ${VERSION}"
echo "  - $APP_VERSION_FILE"
echo "  - $INDEX_FILE (?v= 参数)"
echo ""
echo "请重启前端服务并让用户刷新页面（或等待 Service Worker 自动更新）。"

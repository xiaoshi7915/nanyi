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

python3 - "$APP_VERSION_FILE" "$INDEX_FILE" "$VERSION" <<'PY'
import re, sys
app_file, index_file, version = sys.argv[1], sys.argv[2], sys.argv[3]
app = open(app_file, encoding='utf-8').read()
app = re.sub(r"var APP_RELEASE_VERSION = '[^']*'", f"var APP_RELEASE_VERSION = '{version}'", app)
open(app_file, 'w', encoding='utf-8').write(app)
idx = open(index_file, encoding='utf-8').read()
idx, n = re.subn(r'\?v=[^"\'\s>&]+', f'?v={version}', idx)
open(index_file, 'w', encoding='utf-8').write(idx)
print(f'normalized {n} ?v= params')
PY

echo "已更新发布版本号为: ${VERSION}"
echo "  - $APP_VERSION_FILE"
echo "  - $INDEX_FILE (?v= 参数)"
echo ""
echo "请重启前端服务并让用户刷新页面（或等待 Service Worker 自动更新）。"

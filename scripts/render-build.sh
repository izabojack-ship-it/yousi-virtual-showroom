#!/usr/bin/env bash
# Render build script — 安裝依賴、收集靜態檔、套用資料庫遷移、選擇性建立示範資料
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate --no-input

# 首次部署可設 SEED_ON_DEPLOY=true 建立示範展間內容（重複執行安全）
if [ "${SEED_ON_DEPLOY:-false}" = "true" ]; then
  echo "Seeding demo showroom data..."
  python manage.py seed_showroom || echo "seed_showroom skipped/failed (non-fatal)"
fi

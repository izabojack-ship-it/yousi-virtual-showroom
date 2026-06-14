# 優思國際 — 雲端虛擬展間系統

基於 **Python + Django** 架構的企業雲端虛擬展間平台，對應優思國際自行車零件 Virtual Showroom 方案規劃。

## 功能特色

| 模組 | 說明 |
|------|------|
| 展間站點 | 企業識別色彩、Logo、社群連結、多語系 |
| 分區導覽 | 形象區、設備展示區、加工展示區 |
| 熱點導覽 | 平面圖可點擊熱點，跳轉產品詳情 |
| 360 全景 | 支援上傳全景圖或嵌入外部 360 導覽 |
| 產品詳情 | 一頁式介紹：3D、PopReal AR、影片、型錄 PDF |
| 動態展示 | 設備加工動態說明標記 |
| 形象區 | 企業海報、社群一鍵連結 |
| 線上諮詢 | 表單送出，後台管理 |
| 會員系統 | 經銷商/客戶註冊登入，查看諮詢紀錄 |
| 數據分析 | 自動追蹤瀏覽，後台分析儀表板 |
| ERP 串接 | 從 ERP API 同步產品資料 |
| 多語系 | 繁中 / 英文 / 日文切換 |
| REST API | 供 AR / 3D 外部系統串接 |

## 快速啟動

```powershell
cd C:\yousi-virtual-showroom

# 建立虛擬環境（建議）
python -m venv venv
.\venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 複製環境設定
copy .env.example .env

# 資料庫遷移
python manage.py makemigrations showroom
python manage.py migrate

# 建立示範資料（含 Logo、海報、產品圖、AR/3D/360 連結）
python manage.py seed_showroom

# 建立管理員（若 seed 未建立）
python manage.py createsuperuser

# 啟動開發伺服器（port 9000）
python manage.py runserver 9000
# 或直接執行 start.bat / start.ps1
```

瀏覽器開啟：
- 展間首頁：http://127.0.0.1:9000/
- 後台管理：http://127.0.0.1:9000/admin/
- 分析儀表板：http://127.0.0.1:9000/admin/analytics/
- 會員登入：http://127.0.0.1:9000/member/login/

示範管理員帳號（seed 建立）：`admin` / `admin123`

## 後台管理（/admin/）

登入後可管理：

### 品牌與內容
- **展間站點**：品牌色（主色/強調色）、Logo、社群連結、多語系設定
- **展間分區**：上傳**平面導覽圖**、360 全景圖、嵌入外部 360 導覽連結
- **導覽熱點**：在平面圖上設定 X/Y 座標（0–100%）連結產品
- **產品設備**：上傳**實際產品圖片**、文案、規格，填入 **PopReal AR**、**3D 模型**、**360 導覽**嵌入連結
- **形象海報**：上傳企業識別**海報**
- **線上諮詢**：查看與處理客戶詢問

### 會員與分析
- **展間會員**：查看註冊會員資料
- **分析事件**：瀏覽追蹤紀錄（頁面、產品、諮詢、登入等）
- **分析儀表板**：`/admin/analytics/` — 事件統計、熱門產品/頁面、諮詢列表

### ERP 串接
- **ERP 連線**：設定 API 網址、認證、欄位對應
- 後台選取連線 → 動作「立即同步產品」
- 或執行：`python manage.py sync_erp`
- 示範 API：`GET /api/erp/demo-products/`（開發測試用）

## 會員系統

| 路徑 | 說明 |
|------|------|
| `/member/register/` | 註冊（帳號、Email、公司、電話） |
| `/member/login/` | 登入 |
| `/member/` | 會員中心（諮詢紀錄） |
| `/member/logout/` | 登出 |

## API 端點

| 路徑 | 說明 |
|------|------|
| `GET /api/site/` | 展間設定 |
| `GET /api/zones/` | 分區列表 |
| `GET /api/zones/<slug>/` | 分區詳情 |
| `GET /api/products/` | 產品列表 |
| `GET /api/products/<slug>/` | 產品詳情 |
| `GET /api/hotspots/<zone_slug>/` | 熱點座標 |
| `GET /api/erp/demo-products/` | ERP 示範產品（測試同步用） |

## 公開網址瀏覽（正式部署）

> 本系統是 **Django 動態網站**（含後台、會員、資料庫、分析），不是靜態網頁，
> 因此不適用「把前端丟 Vercel 當靜態站」的做法。要有「固定網址、秒開、24 小時開著」
> 的公開體驗，建議用 **Django 友善的 PaaS（Render / Railway）+ Cloudinary 圖片 CDN**。

### 架構（路線 A：免費且資料不過期）

| 層 | 採用 | 免費方案重點 |
|----|------|------|
| 網站（前後端） | **Render** 免費 Web 服務 | 固定 HTTPS 網址；閒置 15 分鐘休眠，喚醒約 1 分鐘 |
| 資料庫 | **Neon** 免費 Postgres | 由 `DATABASE_URL` 接入；**不會 30 天過期**（閒置自動休眠、有請求即喚醒） |
| 圖片 | **Cloudinary** 免費 | 全球 CDN，交付時自動 webp/avif + 壓縮 + 縮放；每月 25 credits |
| 靜態檔(CSS/JS) | WhiteNoise（內建） | 隨網站打包、自動壓縮快取 |

> 為什麼資料庫用 Neon 而非 Render 內建？Render 免費 Postgres **30 天後會過期並刪除資料**；
> Neon 免費 Postgres 不會過期，因此這套組合可長期免費使用。

### A. 圖片 CDN：Cloudinary（圖片優化的關鍵）

整合已完成，採「設金鑰即啟用、未設金鑰自動退回本機」的安全設計：

1. 註冊 [Cloudinary](https://cloudinary.com)（免費方案足夠展示用）。
2. 在 Dashboard 首頁複製 **API Environment variable**，格式：
   `cloudinary://<api_key>:<api_secret>@<cloud_name>`
3. 設成環境變數 `CLOUDINARY_URL`（本機 `.env` 或 PaaS 後台）。
4. （建議）在 Cloudinary → **Settings → Optimization**，把
   **Format = Auto (f_auto)**、**Quality = Auto (q_auto)** 打開 —
   之後所有交付的圖片都會自動轉 webp/avif 並壓縮，達成「秒開」。

設好之後，後台上傳的圖片會自動存到 Cloudinary 並走 CDN，程式碼無需改動
（所有 `ImageField` 的 `.url` 會自動指向 Cloudinary）。

> 注意：PaaS 的檔案系統「不持久」，所以正式上線**務必**設定 Cloudinary
> 來存放上傳圖片，否則重啟後媒體會遺失。

#### 上傳前先壓圖（省 CDN 流量、再加速）

```powershell
# 將 media/ 內所有圖片轉 webp 並縮到 1920px（1080p 級）
python manage.py optimize_media --max-width 1920 --quality 82
# 確認無誤後可加 --replace 清除原始大檔
```

### B. 免費資料庫：Neon Postgres

1. 註冊 [Neon](https://neon.tech)（免費,免信用卡）。
2. 建立一個 Project（區域選離你近的,如 `AWS ap-southeast-1 Singapore`）。
3. 在 Dashboard 的 **Connection string** 複製連線字串,格式類似：
   `postgresql://user:pass@ep-xxx.ap-southeast-1.aws.neon.tech/dbname?sslmode=require`
4. 這串等一下填到 Render 的 `DATABASE_URL`（下一步）。

> Neon 免費方案不會過期;閒置會自動休眠,有請求時自動喚醒（首次喚醒約數秒）。

### C. 公開網址：Render（一鍵 Blueprint）

專案已附 `render.yaml`,會自動建立免費 Web 服務（資料庫用上面的 Neon）：

1. 把專案推上 GitHub（見下方「推送到 GitHub」）。
2. 登入 [Render](https://render.com) → **New → Blueprint** → 選此 repo。
3. Render 讀取 `render.yaml`,建立網站並自動產生 `SECRET_KEY`。
4. 在 Web 服務的 **Environment** 手動填入兩個金鑰：
   - `DATABASE_URL` ← 步驟 B 的 Neon 連線字串
   - `CLOUDINARY_URL` ← Cloudinary 圖片 CDN 金鑰
5. 部署完成後即得固定網址：`https://yousi-virtual-showroom.onrender.com`
   - 首頁 `/`、產線導覽 `/zone/<slug>/`、VR `/vr/<slug>/`、後台 `/admin/`
   - 首次部署會自動建立示範資料（`admin` / `admin123`,**請立即改密碼**）
   - 確認資料建好後,可把 Render 環境變數 `SEED_ON_DEPLOY` 改成 `false`

> Railway 亦可：建立專案 → 設定相同環境變數
> （`DATABASE_URL`、`SECRET_KEY`、`ALLOWED_HOSTS`、`CLOUDINARY_URL`、`BEHIND_PROXY=True`）,
> Start command：`gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`。

### 推送到 GitHub

```powershell
git init
git add .
git commit -m "Initial commit: 優思虛擬展間"
git branch -M main
git remote add origin https://github.com/<你的帳號>/yousi-virtual-showroom.git
git push -u origin main
```

### D. 快速公開預覽（Cloudflare Tunnel，純本機免費）

無需 VPS，在本機執行後將產生的網址分享給他人（電腦需開著、網址每次會變）：

```powershell
.\deploy\preview.ps1
```

輸出範例：`https://xxxx.trycloudflare.com`  
產線導覽：`/zone/plant1-production/` · VR：`/vr/plant1-production/`

### E. Docker 部署（VPS / 雲端主機）

```powershell
copy .env.production.example .env.production
# 編輯 .env.production 填入網域與 SECRET_KEY
docker compose up -d --build
```

### F. 傳統部署步驟

```powershell
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:9000
```

3. 使用 Nginx 反向代理，媒體檔案建議使用 S3 / Azure Blob
4. 定期執行 `python manage.py sync_erp`（可設 cron）

## 目錄結構

```
C:\yousi-virtual-showroom\
├── config/              # Django 專案設定
├── showroom/            # 展間核心 App
│   ├── models.py        # 資料模型
│   ├── views.py         # 頁面視圖
│   ├── member_views.py  # 會員登入/註冊
│   ├── api.py           # REST API
│   ├── analytics.py     # 數據分析
│   ├── erp_sync.py      # ERP 同步
│   ├── middleware.py    # 瀏覽追蹤
│   ├── admin.py         # 後台管理
│   └── management/      # seed_showroom、sync_erp
├── templates/           # 前端模板
├── static/              # CSS / JS
├── media/               # 上傳檔案
├── requirements.txt
├── .env.example
└── README.md
```

## 技術架構

- Python 3.10+
- Django 5.x
- SQLite（開發）/ PostgreSQL（正式）
- WhiteNoise 靜態檔案
- Gunicorn（正式環境）
- 響應式前端（支援手機瀏覽）

## 授權

內部專案 — 優思國際虛擬展間方案

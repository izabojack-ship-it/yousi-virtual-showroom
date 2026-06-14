"""
優思國際 — 雲端虛擬展間系統設定
"""
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-yousi-showroom-dev-key-change-in-production")
DEBUG = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

# 預覽 tunnel / 反向代理（Cloudflare Tunnel、Nginx 等）
if os.getenv("BEHIND_PROXY", "False").lower() in ("1", "true", "yes"):
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# 無 Nginx 時由 Django 直接提供 media（預覽部署用）
SERVE_MEDIA = os.getenv("SERVE_MEDIA", "False").lower() in ("1", "true", "yes")

# Cloudflare Tunnel 等臨時公開預覽（允許 *.trycloudflare.com 的 CSRF origin）
PREVIEW_MODE = os.getenv("PREVIEW_MODE", "False").lower() in ("1", "true", "yes")
PREVIEW_PASSWORD = os.getenv("PREVIEW_PASSWORD", "")
# 預覽模式下禁止訪客寫入資料（表單、會員、後台等）
PREVIEW_READONLY = os.getenv(
    "PREVIEW_READONLY",
    "True" if PREVIEW_MODE else "False",
).lower() in ("1", "true", "yes")

# Cloudinary 媒體 CDN：設定 CLOUDINARY_URL 環境變數即自動啟用，
# 未設定時自動退回本機 FileSystemStorage（開發/離線可用）。
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL", "").strip()
USE_CLOUDINARY = bool(CLOUDINARY_URL)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "showroom",
]

if USE_CLOUDINARY:
    # cloudinary_storage 必須在 staticfiles 之後即可（僅用於 media）
    INSTALLED_APPS += ["cloudinary_storage", "cloudinary"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "showroom.middleware.ShowroomCsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "showroom.middleware.PreviewGateMiddleware",
    "showroom.middleware.PreviewReadOnlyMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "showroom.middleware.AnalyticsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "showroom.context_processors.showroom_globals",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DB_ENGINE = os.getenv("DB_ENGINE", "sqlite")
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if DATABASE_URL:
    # PaaS（Render / Railway 等）以單一 DATABASE_URL 提供 Postgres 連線字串
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=os.getenv("DB_SSL_REQUIRE", "True").lower() in ("1", "true", "yes"),
        )
    }
elif DB_ENGINE == "postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "yousi_showroom"),
            "USER": os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "zh-hant")
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Taipei")
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("zh-hant", "繁體中文"),
    ("en", "English"),
    ("ja", "日本語"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# 預設媒體存於本機檔案系統；設定 CLOUDINARY_URL 後改走 Cloudinary CDN
_DEFAULT_MEDIA_BACKEND = "django.core.files.storage.FileSystemStorage"
if USE_CLOUDINARY:
    _DEFAULT_MEDIA_BACKEND = "cloudinary_storage.storage.MediaCloudinaryStorage"
    # cloudinary SDK 會自動讀取 CLOUDINARY_URL 環境變數；強制 https 交付
    CLOUDINARY_STORAGE = {"SECURE": True}

STORAGES = {
    "default": {
        "BACKEND": _DEFAULT_MEDIA_BACKEND,
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOW_ALL_ORIGINS = DEBUG

LOGIN_URL = "/member/login/"
LOGIN_REDIRECT_URL = "/member/"
LOGOUT_REDIRECT_URL = "/"

# 展間預設品牌色 — 休閒運動風（Leisure Sports）黃/白/藍策略
# 藍色主調襯托背景，黃色強調關鍵零組件高反差對比（可被 ShowroomSite 覆寫）
SHOWROOM_DEFAULT_PRIMARY = "#1E4A8C"
SHOWROOM_DEFAULT_ACCENT = "#FFD100"
SHOWROOM_DEFAULT_SURFACE = "#FFFFFF"

# 正式環境安全設定
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "True").lower() in ("1", "true", "yes")
    CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "True").lower() in ("1", "true", "yes")
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False").lower() in ("1", "true", "yes")
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = [
        o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()
    ]

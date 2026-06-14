"""設定公開預覽安全：隨機後台密碼 + 預覽通行碼（寫入 deploy/preview-credentials.local.txt）"""
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

CREDS_FILE = ROOT / "deploy" / "preview-credentials.local.txt"


def _load_existing():
    if not CREDS_FILE.exists():
        return {}
    data = {}
    for line in CREDS_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, val = line.split("=", 1)
            data[key.strip()] = val.strip()
    return data


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from django.contrib.auth import get_user_model

    existing = _load_existing()
    admin_password = existing.get("ADMIN_PASSWORD") or secrets.token_urlsafe(16)
    preview_password = existing.get("PREVIEW_PASSWORD") or secrets.token_urlsafe(9)

    User = get_user_model()
    admin = User.objects.filter(username="admin").first()
    if admin:
        admin.set_password(admin_password)
        admin.save(update_fields=["password"])
        admin_status = "已更新 admin 密碼"
    else:
        admin_status = "找不到 admin 帳號（請先執行 seed_zitai 或 createsuperuser）"

    CREDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CREDS_FILE.write_text(
        "\n".join(
            [
                "# 本機預覽憑證 — 請勿提交 git，勿公開分享",
                f"ADMIN_PASSWORD={admin_password}",
                f"PREVIEW_PASSWORD={preview_password}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(admin_status)
    print(f"憑證已寫入：{CREDS_FILE.relative_to(ROOT)}")
    print("")
    print("=== 請妥善保存（私下傳給客戶即可）===")
    print(f"預覽通行碼（訪客）：{preview_password}")
    print(f"後台 admin 密碼：    {admin_password}")
    print("後台網址：/admin/")


if __name__ == "__main__":
    main()

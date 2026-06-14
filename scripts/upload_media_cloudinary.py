"""Upload local media/ files to Cloudinary (public_id = media/<relpath>)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import cloudinary
import cloudinary.uploader

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
MEDIA_ROOT = BASE / "media"
PREFIX = "media"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # Cloudinary free tier per-file limit

IMAGE_EXTS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".ico",
    ".heic", ".heif", ".jpc", ".jp2", ".j2k", ".wdp", ".jxr", ".hdp",
}
VIDEO_EXTS = {".mp4", ".webm", ".flv", ".mov", ".ogv", ".avi", ".wmv", ".mkv", ".3gp"}


def resource_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in VIDEO_EXTS:
        return "video"
    return "raw"


def public_id_for(rel: str) -> str:
    """Match django-cloudinary-storage: public_id without file extension."""
    base = f"{PREFIX}/{rel}"
    filename = rel.rsplit("/", 1)[-1]
    if "." in filename:
        return base.rsplit(".", 1)[0]
    return base


def upload_file(path: Path) -> str:
    rel = path.relative_to(MEDIA_ROOT).as_posix()
    public_id = public_id_for(rel)
    rtype = resource_type(path)
    result = cloudinary.uploader.upload(
        str(path),
        public_id=public_id,
        resource_type=rtype,
        overwrite=True,
        invalidate=True,
        tags=["media"],
    )
    return result.get("public_id", public_id)


def upload_alias(db_name: str) -> None:
    """Upload same file under the exact DB path (e.g. cache-buster ?v=)."""
    base_name = db_name.split("?")[0]
    src = MEDIA_ROOT / base_name
    if not src.is_file():
        return
    public_id = public_id_for(base_name)
    rtype = resource_type(src)
    cloudinary.uploader.upload(
        str(src),
        public_id=public_id,
        resource_type=rtype,
        overwrite=True,
        invalidate=True,
        tags=["media"],
    )


def collect_db_aliases() -> set[str]:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from django.apps import apps
    from django.db.models import FileField, ImageField

    names: set[str] = set()
    for model in apps.get_app_config("showroom").get_models():
        for field in model._meta.get_fields():
            if not isinstance(field, (FileField, ImageField)):
                continue
            for obj in model.objects.all():
                f = getattr(obj, field.name)
                if f and f.name and "?" in f.name:
                    names.add(f.name)
    return names


def main() -> int:
    if not os.environ.get("CLOUDINARY_URL"):
        print("Set CLOUDINARY_URL first.", file=sys.stderr)
        return 1
    if not MEDIA_ROOT.is_dir():
        print("media/ folder not found.", file=sys.stderr)
        return 1

    cloudinary.config()
    files = sorted(p for p in MEDIA_ROOT.rglob("*") if p.is_file())
    total = len(files)
    print(f"Uploading {total} files from {MEDIA_ROOT} ...")

    ok = 0
    fail = 0
    for i, path in enumerate(files, 1):
        try:
            if path.stat().st_size > MAX_UPLOAD_BYTES:
                print(f"  SKIP large file ({path.stat().st_size // 1024 // 1024}MB): {path.relative_to(MEDIA_ROOT)}")
                continue
            upload_file(path)
            ok += 1
            if i % 20 == 0 or i == total:
                print(f"  [{i}/{total}] ok={ok} fail={fail}")
        except Exception as exc:
            fail += 1
            print(f"  FAIL {path.relative_to(MEDIA_ROOT)}: {exc}", file=sys.stderr)

    aliases = collect_db_aliases()
    if aliases:
        print(f"Uploading {len(aliases)} cache-buster aliases ...")
        for name in sorted(aliases):
            try:
                upload_alias(name)
            except Exception as exc:
                print(f"  ALIAS FAIL {name}: {exc}", file=sys.stderr)

    print(f"Done. uploaded={ok} failed={fail} aliases={len(aliases)}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

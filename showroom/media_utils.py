"""產生示範用佔位圖片"""
import io
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from .image_enhance import enhance_showroom_photo
from .ai_cleanup import cleanup_factory_photo


def _get_font(size=24):
    for name in ("msyh.ttc", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_placeholder(text, width, height, bg="#1a4d8c", fg="#ffffff", sub=""):
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)
    font = _get_font(28)
    subfont = _get_font(16)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((width - tw) / 2, (height - th) / 2 - 10), text, fill=fg, font=font)
    if sub:
        sb = draw.textbbox((0, 0), sub, font=subfont)
        sw = sb[2] - sb[0]
        draw.text(((width - sw) / 2, (height + th) / 2), sub, fill="#e8a317", font=subfont)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return ContentFile(buf.getvalue())


def save_placeholder_image(instance, field_name, text, width, height, subpath, sub=""):
    media_root = Path(settings.MEDIA_ROOT)
    media_root.mkdir(parents=True, exist_ok=True)
    cf = make_placeholder(text, width, height, sub=sub)
    filename = f"{subpath}.png"
    getattr(instance, field_name).save(filename, cf, save=True)


def save_standalone_placeholder(text, width, height, subpath, sub="", bg="#1E4A8C"):
    """寫入獨立媒體檔（供 JSON 資產庫等用途），回傳 /media/ 相對 URL"""
    media_root = Path(settings.MEDIA_ROOT)
    rel = f"{subpath}.png"
    dest = media_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    cf = make_placeholder(text, width, height, bg=bg, sub=sub)
    dest.write_bytes(cf.read())
    return f"/media/{Path(rel).as_posix()}"


def _register_heif():
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass


def convert_image_to_jpg(
    src: Path,
    dest: Path,
    max_width: int = 3840,
    *,
    enhance: bool = False,
    enhance_preset: str = "tech_clean",
    remove_clutter: bool = False,
    cleanup_strength: float = 0.38,
) -> bool:
    """將 HEIC/JPG/PNG 轉為 JPEG，可選去雜物與科技美顏強化"""
    if not src.is_file():
        return False
    _register_heif()
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(src) as img:
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            w, h = img.size
            if w > max_width:
                ratio = max_width / w
                img = img.resize((max_width, int(h * ratio)), Image.Resampling.LANCZOS)
            if remove_clutter:
                img, _ = cleanup_factory_photo(img, strength=cleanup_strength)
            if enhance:
                img = enhance_showroom_photo(img, preset=enhance_preset)
            img.save(dest, format="JPEG", quality=95, optimize=True, subsampling=0)
        return True
    except Exception:
        return False


def enhance_image_file(
    src: Path,
    dest: Path | None = None,
    preset: str = "tech_clean",
    max_width: int = 3840,
    *,
    remove_clutter: bool = False,
    cleanup_strength: float = 0.38,
) -> bool:
    """對既有 JPG 套用去雜物與科技美顏（可覆写原檔）"""
    if not src.is_file():
        return False
    out = dest or src
    _register_heif()
    try:
        with Image.open(src) as img:
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            w, h = img.size
            if w > max_width:
                ratio = max_width / w
                img = img.resize((max_width, int(h * ratio)), Image.Resampling.LANCZOS)
            if remove_clutter:
                img, _ = cleanup_factory_photo(img, strength=cleanup_strength)
            img = enhance_showroom_photo(img, preset=preset)
            out.parent.mkdir(parents=True, exist_ok=True)
            img.save(out, format="JPEG", quality=91, optimize=True)
        return True
    except Exception:
        return False


def import_folder_gallery(
    folder: Path,
    media_subdir: str,
    *,
    max_width: int = 3840,
    enhance: bool = False,
    enhance_preset: str = "tech_clean",
    remove_clutter: bool = False,
    cleanup_strength: float = 0.38,
) -> list[str]:
    """
    將資料夾內 HEIC/JPG/PNG 轉為 JPEG 並存入 media/，回傳 /media/ URL 列表。
    enhance=True 時套用科技美顏；remove_clutter=True 時先 AI 去雜物。
    """
    if not folder.is_dir():
        return []
    media_root = Path(settings.MEDIA_ROOT)
    out_dir = media_root / media_subdir
    urls = []
    exts = {".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp"}
    files = sorted(
        [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in exts],
        key=lambda p: p.name.lower(),
    )
    for src in files:
        dest_name = f"{src.stem}.jpg"
        dest = out_dir / dest_name
        if convert_image_to_jpg(
            src, dest, max_width=max_width,
            enhance=enhance, enhance_preset=enhance_preset,
            remove_clutter=remove_clutter, cleanup_strength=cleanup_strength,
        ):
            urls.append(f"/media/{media_subdir}/{dest_name}".replace("\\", "/"))
    return urls


def save_image_from_path(
    instance,
    field_name: str,
    src: Path,
    media_subdir: str,
    *,
    enhance: bool = False,
    enhance_preset: str = "tech_clean",
) -> bool:
    """從本機路徑轉檔並寫入模型 ImageField"""
    if not src.is_file():
        return False
    media_root = Path(settings.MEDIA_ROOT)
    dest = media_root / media_subdir / f"{src.stem}.jpg"
    if not convert_image_to_jpg(
        src, dest, enhance=enhance, enhance_preset=enhance_preset,
    ):
        return False
    with dest.open("rb") as fh:
        getattr(instance, field_name).save(dest.name, ContentFile(fh.read()), save=False)
    return True


def save_audio_from_path(instance, field_name: str, src: Path, media_subdir: str) -> bool:
    """複製音檔至 media 並寫入 FileField"""
    if not src.is_file():
        return False
    media_root = Path(settings.MEDIA_ROOT)
    dest_dir = media_root / media_subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    dest.write_bytes(src.read_bytes())
    with dest.open("rb") as fh:
        getattr(instance, field_name).save(src.name, ContentFile(fh.read()), save=False)
    return True


def resolve_media_url(url: str) -> str:
    """將 /media/ 相對路徑轉為可公開存取的 URL（Cloudinary 或站點根網址）。"""
    if not url:
        return url
    if url.startswith(("http://", "https://")):
        return url.split("?", 1)[0] if getattr(settings, "USE_CLOUDINARY", False) else url

    rel = url.replace("/media/", "", 1).split("?", 1)[0].lstrip("/")
    if getattr(settings, "USE_CLOUDINARY", False):
        import cloudinary
        from cloudinary import CloudinaryImage

        cloudinary.config(force_version=False)
        return CloudinaryImage(f"media/{rel}").build_url(secure=True)

    base = (getattr(settings, "SHOWROOM_PUBLIC_BASE_URL", "") or "").rstrip("/")
    if base:
        return f"{base}/media/{rel}"
    return f"/media/{rel}"


def resolve_file_field_url(file_field) -> str:
    """FileField/ImageField → 公開 URL（Cloudinary 時走 CDN）。"""
    if not file_field:
        return ""
    name = file_field.name or ""
    if getattr(settings, "USE_CLOUDINARY", False) and name:
        ext = Path(name.split("?", 1)[0]).suffix.lower()
        raw_exts = {".pdf", ".step", ".stp", ".m4a", ".mp3", ".wav", ".igs", ".glb", ".gltf"}
        if ext in raw_exts:
            import cloudinary
            from cloudinary import CloudinaryResource

            cloudinary.config(force_version=False)
            rel = name.split("?", 1)[0].lstrip("/")
            return CloudinaryResource(
                f"media/{rel}",
                default_resource_type="raw",
            ).build_url(secure=True)
    try:
        return file_field.url
    except Exception:
        return resolve_media_url(f"/media/{name}")

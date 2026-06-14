"""
將圖片批次轉為 .webp 並縮小至瀏覽器顯示尺寸，降低上傳/CDN 流量。

雖然 Cloudinary 交付時會自動 f_auto/q_auto，但先把「原檔」壓小可省下
Cloudinary 儲存與頻寬額度，也讓本機/Tunnel 模式直接受惠。

用法範例：
  python manage.py optimize_media                      # 處理 media/ 整個資料夾
  python manage.py optimize_media --dir media/products # 指定子資料夾
  python manage.py optimize_media --max-width 1920 --quality 82
  python manage.py optimize_media --replace            # 轉檔後刪除原始 jpg/png
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from PIL import Image

try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except ImportError:
    pass

SOURCE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".bmp", ".tiff"}


class Command(BaseCommand):
    help = "批次將圖片轉為 webp 並縮小至顯示尺寸（圖片優化）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dir",
            default=None,
            help="要處理的資料夾（預設為 MEDIA_ROOT）",
        )
        parser.add_argument(
            "--max-width",
            type=int,
            default=1920,
            help="最大寬度（px），超過則等比縮小。預設 1920（1080p 級）",
        )
        parser.add_argument(
            "--quality",
            type=int,
            default=82,
            help="webp 品質 0–100，預設 82（肉眼幾乎無損、檔案大幅縮小）",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="成功轉檔後刪除原始 jpg/png 等檔案",
        )

    def handle(self, *args, **opts):
        base = Path(opts["dir"]) if opts["dir"] else Path(settings.MEDIA_ROOT)
        if not base.is_absolute():
            base = Path(settings.BASE_DIR) / base
        if not base.is_dir():
            self.stderr.write(self.style.ERROR(f"找不到資料夾：{base}"))
            return

        max_width = opts["max_width"]
        quality = opts["quality"]
        replace = opts["replace"]

        files = [
            p for p in base.rglob("*")
            if p.is_file() and p.suffix.lower() in SOURCE_EXTS
        ]
        if not files:
            self.stdout.write(self.style.WARNING(f"{base} 內沒有可處理的圖片。"))
            return

        saved_before = 0
        saved_after = 0
        converted = 0

        for src in files:
            dest = src.with_suffix(".webp")
            if dest.exists() and dest != src:
                continue
            try:
                with Image.open(src) as img:
                    if img.mode in ("P", "CMYK"):
                        img = img.convert("RGB")
                    elif img.mode == "LA":
                        img = img.convert("RGBA")
                    w, h = img.size
                    if w > max_width:
                        ratio = max_width / w
                        img = img.resize((max_width, int(h * ratio)), Image.Resampling.LANCZOS)
                    has_alpha = img.mode in ("RGBA", "LA")
                    img.save(
                        dest,
                        format="WEBP",
                        quality=quality,
                        method=6,
                        lossless=False,
                        exact=has_alpha,
                    )
                before = src.stat().st_size
                after = dest.stat().st_size
                saved_before += before
                saved_after += after
                converted += 1
                pct = (1 - after / before) * 100 if before else 0
                self.stdout.write(
                    f"  {src.relative_to(base)} → {dest.name}  "
                    f"({before // 1024}KB → {after // 1024}KB, -{pct:.0f}%)"
                )
                if replace and dest != src:
                    src.unlink()
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(self.style.ERROR(f"  跳過 {src.name}：{exc}"))

        mb_before = saved_before / 1024 / 1024
        mb_after = saved_after / 1024 / 1024
        total_pct = (1 - saved_after / saved_before) * 100 if saved_before else 0
        self.stdout.write(
            self.style.SUCCESS(
                f"\n完成：轉換 {converted} 張圖片，"
                f"{mb_before:.1f}MB → {mb_after:.1f}MB（省下 {total_pct:.0f}%）"
            )
        )
        if not replace:
            self.stdout.write(
                "提示：原始檔保留中。確認 webp 無誤後，可加 --replace 重跑以清除原檔。"
            )

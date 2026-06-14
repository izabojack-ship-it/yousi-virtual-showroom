"""
鋁台展間 — 對已匯入環景照片套用去雜物 + 科技美顏

執行：
  python manage.py enhance_zitai_photos
  python manage.py enhance_zitai_photos --from-source
  python manage.py enhance_zitai_photos --no-remove-clutter   # 僅美顏不去雜物

DEMO（只處理少數照片）：
  python manage.py enhance_zitai_photos --zone plant1-coating --remove-clutter
  python manage.py enhance_zitai_photos --zone plant1-production --limit 3
  python manage.py enhance_zitai_photos --files media/zitai/zones/plant1-coating/IMG_7729.jpg
"""
from pathlib import Path
import re
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from showroom.ai_cleanup import get_cleanup_provider
from showroom.media_utils import convert_image_to_jpg, enhance_image_file, import_folder_gallery
from showroom.models import FactoryPlant, ShowroomSite, Zone
from showroom.zitai_catalog import DEFAULT_SOURCE, SITE_SLUG, ZONE_FOLDER_KEYS

from showroom.management.commands.seed_zitai import find_file, find_folder





class Command(BaseCommand):

    help = "鋁台環景照片：AI 去雜物 + 科技美顏（鮮豔明亮整齊）"



    def add_arguments(self, parser):

        parser.add_argument(

            "--preset",

            choices=["tech_clean", "tech_strong", "tech_cyber", "tech_refined", "tech_industrial", "tech_vivid", "tech_pristine", "tech_showroom", "tech_matterport", "tech_matterport_pro", "tech_bright_white"],

            default="tech_matterport_pro",

            help="tech_matterport_pro=強化 Matterport 冷色 HDR＋金屬質感（推薦）",

        )

        parser.add_argument(

            "--from-source",

            action="store_true",

            help="從原始 HEIC 資料夾重新轉檔並美顏（品質最佳）",

        )

        parser.add_argument(

            "--source",

            type=str,

            default=str(DEFAULT_SOURCE),

            help="原始資料目錄",

        )

        parser.add_argument(

            "--remove-clutter",

            action="store_true",

            default=True,

            help="AI 去雜物（電風扇、垃圾袋、走道雜物等），預設開啟",

        )

        parser.add_argument(

            "--no-remove-clutter",

            action="store_false",

            dest="remove_clutter",

            help="關閉去雜物，僅套用色彩美顏",

        )

        parser.add_argument(
            "--cleanup-strength",
            type=float,
            default=0.38,
            help="AI 去雜物強度 0.2–0.6（愈低愈保留原圖，預設 0.38）",
        )
        parser.add_argument(
            "--zone",
            action="append",
            dest="zones",
            metavar="SLUG",
            help="只處理指定分區（可重複），例如 --zone plant1-coating",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="配合 --zone：每分區最多處理 N 張（0=該分區全部）",
        )
        parser.add_argument(
            "--files",
            nargs="+",
            metavar="PATH",
            help="只處理指定檔案，例如 media/zitai/zones/plant1-coating/IMG_7729.jpg",
        )



    def handle(self, *args, **options):

        preset = options["preset"]

        remove_clutter = options["remove_clutter"]

        cleanup_strength = options["cleanup_strength"]

        site = ShowroomSite.objects.filter(slug=SITE_SLUG).first()

        if not site:

            self.stdout.write(self.style.ERROR("找不到鋁台展間，請先執行 seed_zitai"))

            return



        if remove_clutter:

            provider = get_cleanup_provider()

            self.stdout.write(f"去雜物模式：{provider}")

            if provider == "local_soften":

                self.stdout.write(self.style.WARNING(

                    "未設定 REPLICATE_API_TOKEN 或 IMAGE_PROCESSOR_URL，"

                    "將使用本機保守柔化（無法真正移除物件）。\n"

                    "建議在 .env 加入 REPLICATE_API_TOKEN 以啟用 AI 去雜物。"

                ))



        count = 0
        cache_ver = int(time.time())
        zones = options.get("zones") or []
        files = options.get("files")
        limit = options.get("limit") or 0
        target_paths = self._collect_target_paths(site, zones, limit, files)

        if target_paths is not None and options["from_source"] and not zones:
            self.stdout.write(self.style.ERROR(
                "--from-source 不支援 --files / --limit；可搭配 --zone 從 HEIC 原圖重匯。"
            ))
            return

        if options["from_source"]:
            source = Path(options["source"])
            if not source.is_dir():
                self.stdout.write(self.style.ERROR(f"找不到：{source}"))
                return
            if zones:
                count += self._reimport_zones_from_source(
                    site, source, zones, preset, cache_ver,
                    remove_clutter, cleanup_strength, limit=limit,
                )
                self._bust_zone_gallery_cache(site, cache_ver, zone_slugs=zones)
            else:
                count += self._reimport_from_source(
                    site, source, preset, cache_ver, remove_clutter, cleanup_strength,
                )
        else:
            if target_paths is not None and not target_paths:
                self.stdout.write(self.style.ERROR("找不到要處理的照片，請檢查 --zone 或 --files"))
                return
            count += self._enhance_existing_media(
                preset, remove_clutter, cleanup_strength, target_paths=target_paths,
            )
            self._bust_zone_gallery_cache(site, cache_ver, zone_slugs=zones or None)

        clutter_note = " + 去雜物" if remove_clutter else ""
        scope = ""
        if zones:
            scope = f" · 分區 {', '.join(zones)}"
        elif files:
            scope = f" · {len(files)} 個檔案"
        if limit and zones:
            scope += f" · 每區最多 {limit} 張"

        self.stdout.write(self.style.SUCCESS(
            f"完成！已處理 {count} 張環景照片（{preset}{clutter_note}{scope}）"
        ))
        if zones:
            self.stdout.write(f"  http://127.0.0.1:9000/zone/{zones[0]}/")
        else:
            self.stdout.write("  http://127.0.0.1:9000/zone/plant1-production/")



    def _media_url_to_path(self, url: str) -> Path | None:
        base = re.sub(r"\?v=\d+", "", url).split("?", 1)[0]
        if not base.startswith("/media/"):
            return None
        path = Path(settings.MEDIA_ROOT) / base.replace("/media/", "", 1)
        return path if path.is_file() else None

    def _resolve_file_arg(self, raw: str) -> Path | None:
        p = Path(raw)
        if p.is_file():
            return p
        media_root = Path(settings.MEDIA_ROOT)
        for candidate in (
            media_root / raw,
            media_root / raw.replace("/media/", "", 1),
            Path(raw.lstrip("/")),
        ):
            if candidate.is_file():
                return candidate
        return None

    def _collect_target_paths(self, site, zones, limit, files):
        if files:
            paths = []
            for raw in files:
                p = self._resolve_file_arg(raw)
                if p:
                    paths.append(p)
                else:
                    self.stdout.write(self.style.WARNING(f"找不到檔案：{raw}"))
            return paths

        if zones:
            paths = []
            qs = Zone.objects.filter(site=site, slug__in=zones)
            found = set(qs.values_list("slug", flat=True))
            missing = [z for z in zones if z not in found]
            for slug in missing:
                self.stdout.write(self.style.WARNING(f"找不到分區：{slug}"))
            for zone in qs.order_by("sort_order"):
                gallery = zone.photo_gallery or []
                if limit:
                    gallery = gallery[:limit]
                for url in gallery:
                    p = self._media_url_to_path(url)
                    if p:
                        paths.append(p)
                    else:
                        self.stdout.write(self.style.WARNING(f"找不到媒體：{url}"))
            return paths

        return None

    def _enhance_existing_media(
        self,
        preset: str,
        remove_clutter: bool,
        cleanup_strength: float,
        target_paths=None,
    ) -> int:
        kwargs = dict(
            preset=preset,
            remove_clutter=remove_clutter,
            cleanup_strength=cleanup_strength,
        )
        count = 0

        if target_paths is not None:
            seen = set()
            for jpg in target_paths:
                key = jpg.resolve()
                if key in seen:
                    continue
                seen.add(key)
                self.stdout.write(f"  → {jpg.name}")
                if enhance_image_file(jpg, **kwargs):
                    count += 1
            return count

        root = Path(settings.MEDIA_ROOT) / "zitai"
        if not root.is_dir():
            self.stdout.write(self.style.WARNING("找不到 media/zitai/，改用 from-source"))
            return 0

        for jpg in root.rglob("*.jpg"):
            if enhance_image_file(jpg, **kwargs):
                count += 1

        zones_dir = Path(settings.MEDIA_ROOT) / "zones"
        if zones_dir.is_dir():
            for jpg in zones_dir.rglob("*.jpg"):
                if "zitai" in str(jpg).lower() or jpg.parent.name.startswith("plant"):
                    if enhance_image_file(jpg, **kwargs):
                        count += 1

        branding = Path(settings.MEDIA_ROOT) / "branding" / "zitai"
        if branding.is_dir():
            for jpg in branding.glob("*.jpg"):
                if enhance_image_file(jpg, **kwargs):
                    count += 1

        return count

    def _bust_zone_gallery_cache(self, site, ver: int, zone_slugs=None):
        qs = Zone.objects.filter(site=site)
        if zone_slugs:
            qs = qs.filter(slug__in=zone_slugs)
        for zone in qs:
            if not zone.photo_gallery:
                continue
            updated = []
            for u in zone.photo_gallery:
                base = re.sub(r"\?v=\d+", "", u).split("?", 1)[0]
                updated.append(f"{base}?v={ver}")
            zone.photo_gallery = updated
            zone.save(update_fields=["photo_gallery"])

    def _reimport_zones_from_source(
        self,
        site,
        source: Path,
        zone_slugs: list,
        preset: str,
        cache_ver: int,
        remove_clutter: bool,
        cleanup_strength: float,
        limit: int = 0,
    ) -> int:
        slug_map = {slug: keyword for slug, keyword, _title in ZONE_FOLDER_KEYS}
        gallery_kw = dict(
            enhance=True,
            enhance_preset=preset,
            remove_clutter=remove_clutter,
            cleanup_strength=cleanup_strength,
        )
        count = 0
        for slug in zone_slugs:
            keyword = slug_map.get(slug)
            if not keyword:
                self.stdout.write(self.style.WARNING(f"未知分區 slug：{slug}"))
                continue
            folder = find_folder(source, keyword)
            if not folder:
                self.stdout.write(self.style.WARNING(f"找不到原始資料夾（{keyword}）：{slug}"))
                continue
            self.stdout.write(self.style.NOTICE(f"從 HEIC 原圖重匯：{folder.name} → {slug}"))
            urls = import_folder_gallery(folder, f"zitai/zones/{slug}", **gallery_kw)
            if limit:
                urls = urls[:limit]
            count += len(urls)
            zone = Zone.objects.filter(site=site, slug=slug).first()
            if zone and urls:
                zone.photo_gallery = [f"{u}?v={cache_ver}" for u in urls]
                rel = urls[0].replace("/media/", "").split("?")[0]
                zone.cover_image.name = rel
                zone.save()
        return count

    def _reimport_from_source(

        self, site, source: Path, preset: str, cache_ver: int,

        remove_clutter: bool, cleanup_strength: float,

    ) -> int:

        count = 0

        gallery_kw = dict(

            enhance=True,

            enhance_preset=preset,

            remove_clutter=remove_clutter,

            cleanup_strength=cleanup_strength,

        )

        convert_kw = dict(

            enhance=True,

            enhance_preset=preset,

            remove_clutter=remove_clutter,

            cleanup_strength=cleanup_strength,

        )



        lobby = find_folder(source, "大門")

        if lobby:

            urls = import_folder_gallery(lobby, "zitai/plant1/lobby", **gallery_kw)

            count += len(urls)

            plant1 = FactoryPlant.objects.filter(site=site, slug="plant1").first()

            if plant1 and urls:

                plant1.asset_gallery = urls[:6]

                if urls:

                    plant1.cover_image.name = urls[0].replace("/media/", "")

                plant1.save()



        for slug, keyword, _title in ZONE_FOLDER_KEYS:

            folder = find_folder(source, keyword)

            if not folder:

                continue

            urls = import_folder_gallery(folder, f"zitai/zones/{slug}", **gallery_kw)

            count += len(urls)

            zone = Zone.objects.filter(site=site, slug=slug).first()

            if zone and urls:

                zone.photo_gallery = [f"{u}?v={cache_ver}" for u in urls]

                zone.cover_image.name = urls[0].replace("/media/", "")

                zone.save()



        ent = find_file(source, "二廠大門")

        if ent:

            from django.conf import settings

            dest = Path(settings.MEDIA_ROOT) / "zitai" / "zones" / "plant2-entrance" / f"{ent.stem}.jpg"

            if convert_image_to_jpg(ent, dest, **convert_kw):

                count += 1

                zone = Zone.objects.filter(site=site, slug="plant2-entrance").first()

                if zone:

                    url = f"/media/zitai/zones/plant2-entrance/{ent.stem}.jpg?v={cache_ver}"

                    zone.photo_gallery = [url]

                    zone.cover_image.name = f"zitai/zones/plant2-entrance/{ent.stem}.jpg"

                    zone.save()



        from showroom.models import Product

        for p in Product.objects.filter(site=site).select_related("zone"):

            if p.zone and p.zone.photo_gallery:

                p.cover_image.name = p.zone.photo_gallery[0].replace("/media/", "")

                p.save(update_fields=["cover_image"])



        return count


"""
鋁台精機廠 — 沉浸式 AR 展間建置

執行：
  python manage.py seed_zitai
  python manage.py seed_zitai --default
  python manage.py seed_zitai --source "D:\\path\\to\\drive-download-..."

資料來源預設：D:\\川海\\廠商資料\\輔導中\\鋁台\\drive-download-20260613T004405Z-3-001
"""
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from showroom.media_utils import (
    import_folder_gallery,
    save_audio_from_path,
    save_image_from_path,
    save_placeholder_image,
)
from showroom.models import (
    FactoryPlant,
    GuideStep,
    Hotspot,
    Product,
    ProductCategory,
    ShowroomLevel,
    ShowroomSite,
    Zone,
)
from showroom.zitai_catalog import (
    DEFAULT_SOURCE,
    PRODUCTS,
    SITE_SLUG,
    ZONE_FOLDER_KEYS,
    ZONE_SUMMARIES,
)


def find_folder(root: Path, keyword: str) -> Path | None:
    if not root.is_dir():
        return None
    for p in root.iterdir():
        if p.is_dir() and keyword in p.name:
            return p
    return None


def find_file(root: Path, keyword: str, extensions=(".heic", ".HEIC", ".jpg", ".m4a", ".mp3")) -> Path | None:
    if not root.is_dir():
        return None
    for p in root.iterdir():
        if p.is_file() and keyword in p.name and p.suffix.lower() in {e.lower() for e in extensions}:
            return p
    return None


class Command(BaseCommand):
    help = "建立鋁台精機廠 AR 虛擬展間（匯入現場 HEIC 照片與語音導覽）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=str,
            default=str(DEFAULT_SOURCE),
            help="Google Drive 下載資料根目錄",
        )
        parser.add_argument(
            "--default",
            action="store_true",
            help="設為網站預設展間（首頁顯示鋁台）",
        )

    def handle(self, *args, **options):
        source = Path(options["source"])
        if not source.is_dir():
            self.stdout.write(self.style.ERROR(f"找不到資料目錄：{source}"))
            return

        site, _ = ShowroomSite.objects.get_or_create(
            slug=SITE_SLUG,
            defaults={"name": "鋁台精機廠", "is_active": True},
        )
        site.name = "鋁台精機廠"
        site.tagline = "ZITAI · 冷室壓鑄機專業製造 · 沉浸式 AR 工廠導覽"
        site.description = (
            "鋁台精機廠創立於 1981 年，以 ZITAI 品牌專業生產冷室壓鑄機及週邊設備，"
            "行銷全世界。本展間串聯一廠、二廠現場實景照片與語音導覽，"
            "供海外客戶遠端驗廠與展會 AR 體驗。"
        )
        site.primary_color = "#0D3B66"
        site.accent_color = "#F4A261"
        site.website_url = "https://www.zitai.com/zh-tw"
        site.contact_email = "zitai@zitai.com"
        site.contact_phone = "04-2561-1858"
        site.share_title = "鋁台精機 ZITAI — AR 虛擬工廠導覽"
        site.share_description = "一廠・二廠現場實景 · 冷室壓鑄機 · 語音導覽"
        site.inquiry_enabled = True
        site.is_active = True
        if options["default"]:
            ShowroomSite.objects.exclude(slug=SITE_SLUG).update(is_default=False)
            site.is_default = True
        site.save()

        save_placeholder_image(
            site, "logo", "ZITAI", 320, 120, "branding/zitai-logo", "鋁台精機",
        )
        lobby_folder = find_folder(source, "大門")
        if lobby_folder:
            imgs = list(lobby_folder.glob("*.HEIC")) + list(lobby_folder.glob("*.heic"))
            if imgs:
                save_image_from_path(site, "hero_image", imgs[0], "branding/zitai", enhance=True)
        if not site.hero_image:
            save_placeholder_image(
                site, "hero_image", "ZITAI 工廠導覽", 1200, 480,
                "branding/zitai-hero", "Cold Chamber Die Casting",
            )

        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@demo.local", "admin123")

        GuideStep.objects.filter(site=site).delete()
        guides = [
            ("認識鋁台 ZITAI", "Level 1 品牌大廳：1981 年創立，冷室壓鑄機專業製造，行銷全球。"),
            ("一廠・二廠實景", "Level 2 選擇一廠（溪頭路）或二廠（和睦路），播放環境語音導覽。"),
            ("產線現場照片廊", "各分區提供現場實拍照片，可左右滑動瀏覽生產動線。"),
            ("壓鑄機產品", "ZDC 系列 100T~420T 冷室壓鑄機，一頁式規格與 3D 互動。"),
            ("AR 展會體驗", "展會現場可透過 AR 將機台模型疊加於實景（PopReal 示範）。"),
            ("線上諮詢", "填寫表單索取型錄或預約實地參訪神岡一廠、二廠。"),
        ]
        for i, (title, content) in enumerate(guides):
            GuideStep.objects.create(site=site, title_zh=title, content_zh=content, sort_order=i)

        ShowroomLevel.objects.filter(site=site).delete()
        lvl1 = ShowroomLevel.objects.create(
            site=site, level_number=1, level_type="lobby", slug="brand-lobby",
            name_zh="品牌迎賓大廳", name_en="Brand Lobby",
            summary_zh="鋁台精機企業識別、公司簡介與 ZITAI 品牌故事。",
            sort_order=0,
        )
        lvl2 = ShowroomLevel.objects.create(
            site=site, level_number=2, level_type="factory_hub", slug="dual-plant",
            name_zh="一廠・二廠樞紐", name_en="Plant 1 & Plant 2 Hub",
            summary_zh="台中市神岡區一廠（溪頭路172號）與二廠（和睦路801號）實地導覽入口。",
            sort_order=1,
        )
        lvl3 = ShowroomLevel.objects.create(
            site=site, level_number=3, level_type="process_deep", slug="factory-tour",
            name_zh="製造現場導覽", name_en="Factory Floor Tour",
            summary_zh="生產線、噴塗、品管、組裝、成品庫存等分區實景照片與解說。",
            sort_order=2,
        )

        FactoryPlant.objects.filter(site=site).delete()
        plant1 = FactoryPlant.objects.create(
            site=site, level=lvl2, plant_type="taiwan", slug="plant1",
            name_zh="一廠（溪頭路172號）", name_en="Plant 1 — Xitou Rd.",
            description_zh="429 台中市神岡區新庄里溪頭路172號 · 04-2561-1858",
            sort_order=0,
        )
        plant2 = FactoryPlant.objects.create(
            site=site, level=lvl2, plant_type="taiwan", slug="plant2",
            name_zh="二廠（和睦路801號）", name_en="Plant 2 — Hemei Rd.",
            description_zh="429 台中市神岡區新庄里和睦路801號 · 04-2561-1885",
            sort_order=1,
        )

        audio1 = find_file(source, "1廠環境")
        audio2 = find_file(source, "2廠環境")
        if audio1:
            save_audio_from_path(plant1, "audio_guide", audio1, "plants/audio/plant1")
            plant1.save()
        if audio2:
            save_audio_from_path(plant2, "audio_guide", audio2, "plants/audio/plant2")
            plant2.save()

        if lobby_folder:
            urls = import_folder_gallery(lobby_folder, "zitai/plant1/lobby", enhance=True)
            if urls:
                plant1.cover_image.name = urls[0].replace("/media/", "")
                plant1.asset_gallery = urls[:6]
                plant1.save()

        plant2_entrance = find_file(source, "二廠大門")
        if plant2_entrance:
            save_image_from_path(plant2, "cover_image", plant2_entrance, "zitai/plant2", enhance=True)
            plant2.save()

        Zone.objects.filter(site=site).delete()
        zone_map = {}
        sort = 0
        for slug, keyword, title in ZONE_FOLDER_KEYS:
            folder = find_folder(source, keyword)
            zone = Zone.objects.create(
                site=site, slug=slug, name=title, zone_type="process",
                title_zh=title, title_en=title,
                summary_zh=ZONE_SUMMARIES.get(slug, ""),
                sort_order=sort,
            )
            sort += 1
            if folder:
                gallery = import_folder_gallery(folder, f"zitai/zones/{slug}", enhance=True)
                zone.photo_gallery = gallery
                if gallery:
                    zone.cover_image.name = gallery[0].replace("/media/", "")
                zone.save()
            zone_map[slug] = zone

        plant2_ent_zone = Zone.objects.create(
            site=site, slug="plant2-entrance", name="二廠大門口",
            zone_type="brand", title_zh="二廠大門口", title_en="Plant 2 Entrance",
            summary_zh=ZONE_SUMMARIES["plant2-entrance"],
            sort_order=sort,
        )
        if plant2_entrance:
            save_image_from_path(plant2_ent_zone, "cover_image", plant2_entrance, "zitai/zones/plant2-entrance", enhance=True)
            plant2_ent_zone.photo_gallery = [f"/media/{plant2_ent_zone.cover_image.name}"]
            plant2_ent_zone.save()
        zone_map["plant2-entrance"] = plant2_ent_zone

        ProductCategory.objects.filter(site=site).delete()
        cat = ProductCategory.objects.create(
            site=site, slug="cold-chamber", name_zh="冷室壓鑄機", name_en="Cold Chamber",
        )

        Product.objects.filter(site=site).delete()
        product_objs = {}
        for i, pdata in enumerate(PRODUCTS):
            zone = zone_map.get(pdata["zone"])
            p = Product.objects.create(
                site=site, category=cat, zone=zone, showroom_level=lvl3,
                factory_plant=plant1 if "plant1" in pdata["zone"] else plant2,
                slug=pdata["slug"], model_no=pdata["model_no"],
                name_zh=pdata["name_zh"], name_en=pdata["name_en"],
                tagline_zh=pdata["tagline_zh"], summary_zh=pdata["summary_zh"],
                description_zh=(
                    f"{pdata['summary_zh']}\n\n"
                    "品質始於設計及匠心獨運的展現 — Quality through better design with an expert workforce.\n"
                    "詳細規格請參考官網產品介紹或索取線上型錄。"
                ),
                is_featured=True, is_active=True, sort_order=i,
                model_3d_url="https://modelviewer.dev/shared-assets/models/Astronaut.glb",
                ar_popreal_url="https://popreal.app/ar/demo",
            )
            z = zone_map.get(pdata["zone"])
            if z and z.photo_gallery:
                p.cover_image.name = z.photo_gallery[0].replace("/media/", "")
                p.save()
            product_objs[pdata["slug"]] = p

        Hotspot.objects.filter(zone__site=site).delete()
        prod_zone = zone_map.get("plant1-production")
        if prod_zone:
            positions = [
                ("ZDC-100TPS", "zdc-100tps", 25, 35),
                ("ZDC-180TPSA", "zdc-180tpsa", 55, 40),
                ("生產動線", "plant1-inventory", 75, 60, "zone"),
            ]
            for i, item in enumerate(positions):
                label, target, x, y = item[0], item[1], item[2], item[3]
                htype = item[4] if len(item) > 4 else "product"
                Hotspot.objects.create(
                    zone=prod_zone, label_zh=label, hotspot_type=htype,
                    pos_x=x, pos_y=y, sort_order=i,
                    product=product_objs.get(target) if htype == "product" else None,
                    target_zone=zone_map.get(target) if htype == "zone" else None,
                )

        self.stdout.write(self.style.SUCCESS(f"鋁台展間建置完成：{site.name}（slug={SITE_SLUG}）"))
        total_photos = sum(len(z.photo_gallery or []) for z in Zone.objects.filter(site=site))
        self.stdout.write(f"  已匯入現場照片 {total_photos} 張")
        self.stdout.write(f"  語音導覽：一廠={'有' if plant1.audio_guide else '無'} · 二廠={'有' if plant2.audio_guide else '無'}")
        self.stdout.write("")
        self.stdout.write("預覽網址：")
        self.stdout.write("  http://127.0.0.1:9000/s/zitai/")
        self.stdout.write("  http://127.0.0.1:9000/s/zitai/tour/")
        if not options["default"]:
            self.stdout.write("設為首頁：python manage.py seed_zitai --default")

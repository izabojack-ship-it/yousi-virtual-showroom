"""
鋁台展間 — 同步產品 CAD 檔（STEP / IGS）至 Django 媒體庫

範例：
  python manage.py sync_zitai_cad --product zdc-1250t --step "C:\\Users\\user\\Downloads\\ZDC-1250T冷室壓鑄機.STEP"
"""
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from showroom.models import FactoryPlant, Product, ProductCategory, ShowroomLevel, ShowroomSite, Zone
from showroom.zitai_catalog import PRODUCTS, SITE_SLUG


def _catalog_entry(slug: str) -> dict | None:
    for item in PRODUCTS:
        if item["slug"] == slug:
            return item
    return None


class Command(BaseCommand):
    help = "同步鋁台產品 CAD 原始檔（STEP / IGS）至展間系統"

    def add_arguments(self, parser):
        parser.add_argument("--product", required=True, help="產品 slug，例如 zdc-1250t")
        parser.add_argument("--step", type=str, default="", help="STEP / STP 檔案路徑")
        parser.add_argument("--igs", type=str, default="", help="IGS / IGES 檔案路徑")
        parser.add_argument("--gltf", type=str, default="", help="GLB / GLTF 檔案路徑（Web 3D 預覽）")
        parser.add_argument("--create", action="store_true", help="若產品不存在則依 catalog 建立")

    def handle(self, *args, **options):
        slug = options["product"]
        site = ShowroomSite.objects.filter(slug=SITE_SLUG).first()
        if not site:
            self.stdout.write(self.style.ERROR("找不到鋁台展間，請先執行 seed_zitai"))
            return

        product = Product.objects.filter(site=site, slug=slug).first()
        if not product:
            if not options["create"]:
                self.stdout.write(self.style.ERROR(f"找不到產品 {slug}，請加 --create 或先 seed_zitai"))
                return
            product = self._create_product(site, slug)
            if not product:
                return

        changed = []
        if options["step"]:
            if self._assign_file(product, "step_file", Path(options["step"])):
                changed.append("step_file")
        if options["igs"]:
            if self._assign_file(product, "igs_file", Path(options["igs"])):
                changed.append("igs_file")
        if options["gltf"]:
            if self._assign_file(product, "gltf_file", Path(options["gltf"])):
                changed.append("gltf_file")
                product.model_3d_url = ""

        if changed:
            product.save()
            self.stdout.write(self.style.SUCCESS(f"已更新 {product.model_no}：{', '.join(changed)}"))
        else:
            self.stdout.write(self.style.WARNING("未指定有效檔案或檔案不存在"))

        if product.step_file:
            self.stdout.write(f"  STEP：{product.step_file.url}")
        if product.gltf_file:
            self.stdout.write(f"  GLB：{product.gltf_file.url}")
        self.stdout.write(f"  產品頁：http://127.0.0.1:9000/product/{product.slug}/")

    def _create_product(self, site, slug: str) -> Product | None:
        entry = _catalog_entry(slug)
        if not entry:
            self.stdout.write(self.style.ERROR(f"catalog 中找不到 {slug}"))
            return None

        cat = ProductCategory.objects.filter(site=site, slug="cold-chamber").first()
        zone = Zone.objects.filter(site=site, slug=entry["zone"]).first()
        lvl3 = ShowroomLevel.objects.filter(site=site, slug="deep-process").first()
        plant_slug = "plant2" if "plant2" in entry["zone"] else "plant1"
        plant = FactoryPlant.objects.filter(site=site, slug=plant_slug).first()

        sort_order = Product.objects.filter(site=site).count()
        product = Product.objects.create(
            site=site,
            category=cat,
            zone=zone,
            showroom_level=lvl3,
            factory_plant=plant,
            slug=entry["slug"],
            model_no=entry["model_no"],
            name_zh=entry["name_zh"],
            name_en=entry.get("name_en", ""),
            tagline_zh=entry.get("tagline_zh", ""),
            summary_zh=entry.get("summary_zh", ""),
            description_zh=(
                f"{entry['summary_zh']}\n\n"
                "品質始於設計及匠心獨運的展現 — Quality through better design with an expert workforce.\n"
                "詳細規格請參考官網產品介紹或索取線上型錄。"
            ),
            default_color_hex="#8B9299",
            color_options=["#8B9299", "#CC0000", "#2D2D2D", "#E8E8E8"],
            specs={"鎖模力": "1250 噸", "型式": "冷室壓鑄機", "CAD": "STEP 3D 模型已上傳"},
            is_featured=True,
            is_active=True,
            sort_order=sort_order,
        )
        if zone and zone.photo_gallery:
            product.cover_image.name = zone.photo_gallery[0].replace("/media/", "")
            product.save(update_fields=["cover_image"])
        self.stdout.write(self.style.SUCCESS(f"已建立產品 {product.model_no}"))
        return product

    def _assign_file(self, product, field_name: str, src: Path) -> bool:
        if not src.is_file():
            self.stdout.write(self.style.ERROR(f"找不到檔案：{src}"))
            return False
        field = getattr(product, field_name)
        if field.name:
            try:
                field.delete(save=False)
            except Exception:
                pass
        dest_name = f"{product.slug}{src.suffix.lower()}"
        with src.open("rb") as fh:
            field.save(dest_name, File(fh), save=False)
        size_mb = src.stat().st_size / (1024 * 1024)
        self.stdout.write(f"  已複製 {src.name} ({size_mb:.1f} MB)")
        return True

"""
展間資料 intake — 從 media/intake/ 讀取客戶上傳檔案並匯入 Django 模型

流程：
1. python manage.py setup_intake      → 建立資料夾與 planning.yaml 範本
2. 將檔案放入 media/intake/ 對應路徑
3. python manage.py seed_showroom     → 若尚未有展間骨架（首次）
4. python manage.py import_intake     → 匯入真實資料並清除外部 360 占位
5. 開啟 /plan/ 查看規劃成果與完成度
"""
from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from django.conf import settings
from django.core.files import File

from .models import (
    BrandPoster,
    FactoryPlant,
    Product,
    ProductMedia,
    ShowroomLevel,
    ShowroomSite,
    Zone,
)

INTAKE_DIR_NAME = "intake"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXT = {".mp4", ".webm", ".mov"}
MODEL_EXT = {".glb", ".gltf"}
DOC_EXT = {".pdf", ".igs", ".iges", ".stp", ".step"}


def get_intake_root() -> Path:
    return Path(settings.MEDIA_ROOT) / INTAKE_DIR_NAME


def get_planning_yaml_path() -> Path:
    return get_intake_root() / "planning.yaml"


def load_planning_config() -> dict:
    path = get_planning_yaml_path()
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_intake_path(relative: str) -> Path:
    """將 planning.yaml 內相對路徑解析為 intake 根目錄下的絕對路徑"""
    return get_intake_root() / relative.replace("\\", "/")


def file_exists(relative: str) -> bool:
    if not relative:
        return False
    p = resolve_intake_path(relative)
    return p.is_file()


def assign_file_field(instance, field_name: str, relative: str) -> bool:
    """若 intake 檔案存在，寫入模型 FileField / ImageField"""
    if not relative:
        return False
    src = resolve_intake_path(relative)
    if not src.is_file():
        return False
    field = getattr(instance, field_name)
    if field.name:
        try:
            field.delete(save=False)
        except Exception:
            pass
    with src.open("rb") as fh:
        field.save(src.name, File(fh), save=False)
    return True


def get_site(config: dict) -> ShowroomSite:
    slug = config.get("site_slug", "yousi")
    site = ShowroomSite.objects.filter(slug=slug, is_active=True).first()
    if site:
        return site
    site = ShowroomSite.objects.filter(is_default=True, is_active=True).first()
    if site:
        return site
    return ShowroomSite.objects.filter(is_active=True).first()


def import_from_intake(dry_run: bool = False, use_local_360_only: bool = True) -> dict:
    """
    依 planning.yaml 匯入資料。
    use_local_360_only=True 時，上傳本機 360 後會清空 panorama_embed_url（避免第三方雲端）。
    """
    config = load_planning_config()
    if not config:
        return {"ok": False, "error": "找不到 media/intake/planning.yaml，請先執行 setup_intake"}

    site = get_site(config)
    if not site:
        return {"ok": False, "error": "找不到展間站點，請先執行 seed_showroom"}

    stats = {"site": 0, "levels": 0, "plants": 0, "zones": 0, "products": 0, "posters": 0, "skipped": []}

    site_cfg = config.get("site") or {}
    if assign_file_field(site, "logo", site_cfg.get("logo", "")):
        stats["site"] += 1
    if assign_file_field(site, "hero_image", site_cfg.get("hero_image", "")):
        stats["site"] += 1
    if not dry_run and stats["site"]:
        site.save()

    for slug, lvl_cfg in (config.get("levels") or {}).items():
        level = ShowroomLevel.objects.filter(site=site, slug=slug).first()
        if not level:
            stats["skipped"].append(f"level:{slug}")
            continue
        changed = False
        if assign_file_field(level, "floor_plan_image", lvl_cfg.get("floor_plan", "")):
            changed = True
        if assign_file_field(level, "panorama_image", lvl_cfg.get("panorama_360", "")):
            changed = True
            if use_local_360_only:
                level.panorama_embed_url = ""
        if changed:
            stats["levels"] += 1
            if not dry_run:
                level.save()

    for slug, plant_cfg in (config.get("plants") or {}).items():
        plant = FactoryPlant.objects.filter(site=site, slug=slug).first()
        if not plant:
            stats["skipped"].append(f"plant:{slug}")
            continue
        changed = False
        if assign_file_field(plant, "cover_image", plant_cfg.get("cover", "")):
            changed = True
        if assign_file_field(plant, "panorama_image", plant_cfg.get("panorama_360", "")):
            changed = True
            if use_local_360_only:
                plant.panorama_embed_url = ""
        gallery = plant_cfg.get("gallery") or []
        urls = []
        for rel in gallery:
            if file_exists(rel):
                dest_rel = f"plants/gallery/{Path(rel).name}"
                dest = Path(settings.MEDIA_ROOT) / dest_rel
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(resolve_intake_path(rel), dest)
                urls.append(f"/media/{dest_rel.replace(chr(92), '/')}")
        if urls:
            plant.asset_gallery = urls
            changed = True
        if changed:
            stats["plants"] += 1
            if not dry_run:
                plant.save()

    for slug, zone_cfg in (config.get("zones") or {}).items():
        zone = Zone.objects.filter(site=site, slug=slug).first()
        if not zone:
            stats["skipped"].append(f"zone:{slug}")
            continue
        changed = False
        if assign_file_field(zone, "cover_image", zone_cfg.get("cover", "")):
            changed = True
        if assign_file_field(zone, "floor_plan_image", zone_cfg.get("floor_plan", "")):
            changed = True
        if assign_file_field(zone, "panorama_image", zone_cfg.get("panorama_360", "")):
            changed = True
            if use_local_360_only:
                zone.panorama_embed_url = ""
        if changed:
            stats["zones"] += 1
            if not dry_run:
                zone.save()

    for rel in config.get("posters") or []:
        if not file_exists(rel):
            continue
        title = Path(rel).stem
        poster = BrandPoster(site=site, title_zh=title, sort_order=stats["posters"])
        if not dry_run:
            poster.save()
            assign_file_field(poster, "image", rel)
            poster.save()
        stats["posters"] += 1

    products_cfg = config.get("products") or {}
    for slug, prod_cfg in products_cfg.items():
        product = Product.objects.filter(site=site, slug=slug).first()
        if not product:
            stats["skipped"].append(f"product:{slug}")
            continue
        base = prod_cfg.get("folder", f"05_products/{slug}")
        if not base.endswith("/"):
            base = base + "/"

        def prod_file(key: str) -> str:
            name = prod_cfg.get(key, "")
            if not name:
                return ""
            if "/" in name:
                return name
            return base + name

        changed = False
        for field, key in [
            ("cover_image", "cover"),
            ("frame_position_image", "frame_position"),
            ("gltf_file", "gltf"),
            ("step_file", "step"),
            ("igs_file", "igs"),
            ("catalog_pdf", "catalog"),
        ]:
            if assign_file_field(product, field, prod_file(key)):
                changed = True

        video_rel = prod_file("video")
        if file_exists(video_rel) and not dry_run:
            ProductMedia.objects.filter(product=product, media_type="video").delete()
            media = ProductMedia(product=product, media_type="video", title="產品影片", sort_order=0)
            media.save()
            assign_file_field(media, "file", video_rel)
            media.save()
            changed = True
        elif file_exists(video_rel):
            changed = True

        gallery = prod_cfg.get("gallery") or []
        if gallery and not dry_run:
            ProductMedia.objects.filter(product=product, media_type="image").delete()
            for i, g in enumerate(gallery):
                rel = g if "/" in g else base + g
                if not file_exists(rel):
                    continue
                media = ProductMedia(product=product, media_type="image", title=Path(g).stem, sort_order=i)
                media.save()
                assign_file_field(media, "image", rel)
                media.save()
            changed = True

        if changed:
            stats["products"] += 1
            if not dry_run:
                product.save()

    stats["ok"] = True
    stats["site_name"] = site.name
    return stats


def build_intake_status() -> dict:
    """掃描 intake 資料夾與 planning.yaml，產生規劃完成度報告"""
    config = load_planning_config()
    intake_root = get_intake_root()
    sections = []

    def check_items(label: str, items: list) -> dict:
        done = sum(1 for _, rel in items if file_exists(rel))
        return {
            "label": label,
            "done": done,
            "total": len(items),
            "items": [
                {
                    "name": name,
                    "path": rel,
                    "ready": file_exists(rel),
                    "abs": str(resolve_intake_path(rel)) if rel else "",
                }
                for name, rel in items
            ],
        }

    site_cfg = config.get("site") or {}
    sections.append(check_items("品牌與主視覺", [
        ("Logo", site_cfg.get("logo", "01_brand/logo.png")),
        ("首頁主視覺", site_cfg.get("hero_image", "01_brand/hero.jpg")),
    ]))

    level_items = []
    for slug, cfg in (config.get("levels") or {}).items():
        level_items.append((f"Level {slug} 平面圖", cfg.get("floor_plan", "")))
        level_items.append((f"Level {slug} 360°", cfg.get("panorama_360", "")))
    if level_items:
        sections.append(check_items("空間層級 Level 1~3", level_items))

    zone_items = []
    for slug, cfg in (config.get("zones") or {}).items():
        zone_items.append((f"{slug} 平面圖", cfg.get("floor_plan", "")))
        zone_items.append((f"{slug} 360°", cfg.get("panorama_360", "")))
    if zone_items:
        sections.append(check_items("車間分區", zone_items))

    product_items = []
    for slug, cfg in (config.get("products") or {}).items():
        base = cfg.get("folder", f"05_products/{slug}/")
        product_items.append((f"{slug} 封面", base + cfg.get("cover", "cover.jpg")))
        product_items.append((f"{slug} GLB", base + cfg.get("gltf", "model.glb")))
        if cfg.get("panorama_360") or cfg.get("frame_position"):
            product_items.append((f"{slug} 定位圖", base + cfg.get("frame_position", "frame.png")))
    if product_items:
        sections.append(check_items("關鍵零組件 / 機台", product_items))

    total_files = sum(s["total"] for s in sections)
    ready_files = sum(s["done"] for s in sections)

    return {
        "intake_root": str(intake_root),
        "planning_exists": get_planning_yaml_path().is_file(),
        "intake_exists": intake_root.is_dir(),
        "sections": sections,
        "ready_files": ready_files,
        "total_files": total_files,
        "percent": round(100 * ready_files / total_files, 1) if total_files else 0,
        "config": config,
    }

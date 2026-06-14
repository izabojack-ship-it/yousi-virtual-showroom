"""
鋁台 89 張照片 — 完整 Industry 4.0 Pipeline

Stages:
  1. INGEST    — 讀取原始 HEIC / 既有 JPG
  2. ENHANCE   — Pillow 科技美顏 (tech_clean / tech_strong)
  3. AI_TECHIFY — 可選：呼叫 Node image-processor (Replicate / Cloudinary / mock)
  4. PUBLISH   — 寫入 media/zitai/pipeline/{zone}/
  5. INDEX     — 更新 Zone.photo_gallery + pipeline_meta
  6. SYNC      — 同步產品封面、廠區資產
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from django.conf import settings

from showroom.media_utils import convert_image_to_jpg, import_folder_gallery
from showroom.models import FactoryPlant, Product, ShowroomSite, Zone
from showroom.zitai_catalog import DEFAULT_SOURCE, SITE_SLUG, ZONE_FOLDER_KEYS

logger = logging.getLogger(__name__)

PIPELINE_VERSION = 2


@dataclass
class PipelineStageResult:
    stage: str
    ok: bool
    count: int = 0
    message: str = ""


@dataclass
class ZitaiPipelineReport:
    site_slug: str = SITE_SLUG
    total_photos: int = 0
    zones_updated: int = 0
    stages: list[PipelineStageResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    duration_sec: float = 0.0

    def to_dict(self) -> dict:
        return {
            "site_slug": self.site_slug,
            "total_photos": self.total_photos,
            "zones_updated": self.zones_updated,
            "duration_sec": round(self.duration_sec, 2),
            "stages": [{"stage": s.stage, "ok": s.ok, "count": s.count, "message": s.message} for s in self.stages],
            "errors": self.errors,
            "pipeline_version": PIPELINE_VERSION,
        }


def _public_media_url(relative_path: str, cache_ver: int | None = None) -> str:
    """組成可供前端 / 外部 AI 使用的絕對 URL"""
    base = os.getenv("SHOWROOM_PUBLIC_BASE_URL", "http://127.0.0.1:9000").rstrip("/")
    rel = relative_path.replace("\\", "/").lstrip("/")
    url = f"{base}/media/{rel}"
    if cache_ver:
        url = f"{url}?v={cache_ver}"
    return url


def _call_external_ai(public_url: str, provider: str = "mock") -> str | None:
    """
    呼叫 smart-industrial-showroom Node 服務 (IMAGE_PROCESSOR_URL)。
    未設定時跳過，沿用 Pillow 結果。
    """
    processor = os.getenv("IMAGE_PROCESSOR_URL", "").rstrip("/")
    if not processor:
        return None
    payload = json.dumps({"imageUrl": public_url, "provider": provider}).encode("utf-8")
    req = urllib.request.Request(
        f"{processor}/api/v1/process/url",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
            if data.get("success") and data.get("enhancedImageUrl"):
                return data["enhancedImageUrl"]
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("External AI processor failed: %s", exc)
    return None


class ZitaiPipelineService:
    def __init__(
        self,
        source_dir: Path | None = None,
        *,
        enhance_preset: str = "tech_clean",
        use_external_ai: bool | None = None,
        ai_provider: str = "mock",
    ):
        self.source_dir = source_dir or DEFAULT_SOURCE
        self.enhance_preset = enhance_preset
        self.use_external_ai = (
            use_external_ai
            if use_external_ai is not None
            else bool(os.getenv("IMAGE_PROCESSOR_URL"))
        )
        self.ai_provider = os.getenv("IMAGE_PROCESSOR_PROVIDER", ai_provider)
        self.cache_ver = int(time.time())

    def run(self, site: ShowroomSite | None = None) -> ZitaiPipelineReport:
        t0 = time.time()
        report = ZitaiPipelineReport()

        site = site or ShowroomSite.objects.filter(slug=SITE_SLUG, is_active=True).first()
        if not site:
            report.errors.append("找不到鋁台展間 (slug=zitai)，請先執行 seed_zitai")
            return report

        if not self.source_dir.is_dir():
            report.errors.append(f"找不到原始資料目錄：{self.source_dir}")
            return report

        from showroom.management.commands.seed_zitai import find_file, find_folder

        # --- Stage 1+2+4+5: 分區批次匯入 ---
        ingest_count = 0
        for slug, keyword, _title in ZONE_FOLDER_KEYS:
            folder = find_folder(self.source_dir, keyword)
            if not folder:
                report.errors.append(f"略過分區 {slug}：找不到資料夾關鍵字 {keyword}")
                continue
            media_subdir = f"zitai/pipeline/{slug}"
            urls = import_folder_gallery(
                folder,
                media_subdir,
                enhance=True,
                enhance_preset=self.enhance_preset,
            )
            if not urls:
                continue

            # --- Stage 3: 可選外部 AI（每分區取代表圖 1 張以節省 API）---
            ai_applied = 0
            if self.use_external_ai and urls:
                rel = urls[0].replace("/media/", "").split("?")[0]
                public = _public_media_url(rel)
                ai_url = _call_external_ai(public, self.ai_provider)
                if ai_url:
                    ai_applied = 1

            ingest_count += len(urls)
            zone = Zone.objects.filter(site=site, slug=slug).first()
            if zone:
                gallery = [f"{u.split('?')[0]}?v={self.cache_ver}" for u in urls]
                zone.photo_gallery = gallery
                if gallery:
                    zone.cover_image.name = gallery[0].replace("/media/", "").split("?")[0]
                zone.pipeline_meta = {
                    "version": PIPELINE_VERSION,
                    "stage": "complete",
                    "photo_count": len(gallery),
                    "enhance_preset": self.enhance_preset,
                    "ai_provider": self.ai_provider if ai_applied else "pillow_local",
                    "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "source_dir": str(self.source_dir),
                }
                zone.save()
                report.zones_updated += 1

        report.stages.append(PipelineStageResult("INGEST+ENHANCE+PUBLISH", True, ingest_count, "HEIC→JPG 科技美顏"))

        # 二廠大門
        ent = find_file(self.source_dir, "二廠大門")
        if ent:
            dest_rel = f"zitai/pipeline/plant2-entrance/{ent.stem}.jpg"
            dest = Path(settings.MEDIA_ROOT) / dest_rel
            if convert_image_to_jpg(ent, dest, enhance=True, enhance_preset=self.enhance_preset):
                ingest_count += 1
                zone = Zone.objects.filter(site=site, slug="plant2-entrance").first()
                if zone:
                    url = _public_media_url(dest_rel, self.cache_ver)
                    zone.photo_gallery = [url]
                    zone.cover_image.name = dest_rel
                    zone.pipeline_meta = {
                        "version": PIPELINE_VERSION,
                        "stage": "complete",
                        "photo_count": 1,
                        "enhance_preset": self.enhance_preset,
                        "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }
                    zone.save()
                    report.zones_updated += 1

        # 一廠大門 lobby → plant1 資產
        lobby = find_folder(self.source_dir, "大門")
        if lobby:
            lobby_urls = import_folder_gallery(
                lobby, "zitai/pipeline/plant1-lobby", enhance=True, enhance_preset=self.enhance_preset,
            )
            ingest_count += len(lobby_urls)
            plant1 = FactoryPlant.objects.filter(site=site, slug="plant1").first()
            if plant1 and lobby_urls:
                plant1.asset_gallery = [f"{u.split('?')[0]}?v={self.cache_ver}" for u in lobby_urls[:6]]
                if lobby_urls:
                    plant1.cover_image.name = lobby_urls[0].replace("/media/", "").split("?")[0]
                plant1.save()

        report.total_photos = ingest_count
        report.stages.append(PipelineStageResult(
            "AI_TECHIFY",
            True,
            1 if self.use_external_ai else 0,
            f"provider={self.ai_provider}" if self.use_external_ai else "skipped (Pillow only)",
        ))

        # --- Stage 6: SYNC 產品封面 ---
        sync = 0
        for p in Product.objects.filter(site=site).select_related("zone"):
            if p.zone and p.zone.photo_gallery:
                rel = p.zone.photo_gallery[0].replace("/media/", "").split("?")[0]
                p.cover_image.name = rel
                p.save(update_fields=["cover_image"])
                sync += 1
        report.stages.append(PipelineStageResult("SYNC_PRODUCTS", True, sync))

        report.duration_sec = time.time() - t0
        return report


def get_pipeline_status(site: ShowroomSite) -> dict:
    zones = Zone.objects.filter(site=site, is_active=True).order_by("sort_order")
    items = []
    total_photos = 0
    complete = 0
    for z in zones:
        meta = z.pipeline_meta or {}
        count = len(z.photo_gallery or [])
        total_photos += count
        stage = meta.get("stage", "pending" if count else "empty")
        if stage == "complete" and count:
            complete += 1
        items.append({
            "slug": z.slug,
            "title": z.title_zh,
            "photo_count": count,
            "stage": stage,
            "enhance_preset": meta.get("enhance_preset"),
            "processed_at": meta.get("processed_at"),
            "preview_url": z.photo_gallery[0] if z.photo_gallery else None,
            "zone_url": f"/zone/{z.slug}/",
        })
    return {
        "site": site.name,
        "site_slug": site.slug,
        "total_zones": zones.count(),
        "complete_zones": complete,
        "total_photos": total_photos,
        "pipeline_version": PIPELINE_VERSION,
        "zones": items,
    }

"""REST API — 供 AR / 3D / 外部系統串接"""
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from pathlib import Path

from .models import Hotspot, Product, ShowroomSite, Zone


def _get_default_site(slug=None):
    if slug:
        return get_object_or_404(ShowroomSite, slug=slug, is_active=True)
    site = ShowroomSite.objects.filter(is_default=True, is_active=True).first()
    return site or get_object_or_404(ShowroomSite, is_active=True)


def _serialize_site(site):
    return {
        "id": site.id,
        "name": site.name,
        "slug": site.slug,
        "tagline": site.tagline,
        "description": site.description,
        "primary_color": site.primary_color,
        "accent_color": site.accent_color,
        "website_url": site.website_url,
        "social": {
            "facebook": site.facebook_url,
            "instagram": site.instagram_url,
            "linkedin": site.linkedin_url,
            "youtube": site.youtube_url,
            "line": site.line_url,
        },
        "contact": {
            "email": site.contact_email,
            "phone": site.contact_phone,
        },
    }


def _serialize_product(p):
    return {
        "id": p.id,
        "slug": p.slug,
        "name_zh": p.name_zh,
        "name_en": p.name_en,
        "model_no": p.model_no,
        "summary_zh": p.summary_zh,
        "features_zh": p.features_zh,
        "specs": p.specs,
        "cover_image": p.cover_image.url if p.cover_image else None,
        "hero_video_url": p.hero_video_url,
        "gltf_url": p.gltf_source_url() or None,
        "cad_url": p.cad_source_url() or None,
        "step_file": p.step_file.url if p.step_file else None,
        "igs_file": p.igs_file.url if p.igs_file else None,
        "model_3d_url": p.model_3d_url,
        "ar_popreal_url": p.ar_popreal_url,
        "catalog_pdf": p.catalog_pdf.url if p.catalog_pdf else None,
        "official_url": p.official_url,
        "has_animation": p.has_animation,
        "zone_slug": p.zone.slug if p.zone else None,
    }


def api_site(request, site_slug=None):
    site = _get_default_site(site_slug)
    return JsonResponse({"success": True, "site": _serialize_site(site)})


def api_zones(request):
    site = _get_default_site(request.GET.get("site"))
    zones = site.zones.filter(is_active=True)
    data = [{
        "slug": z.slug,
        "name": z.name,
        "zone_type": z.zone_type,
        "title_zh": z.title_zh,
        "summary_zh": z.summary_zh,
        "panorama_embed_url": z.panorama_embed_url,
        "cover_image": z.cover_image.url if z.cover_image else None,
    } for z in zones]
    return JsonResponse({"success": True, "zones": data})


def api_zone_detail(request, zone_slug):
    site = _get_default_site(request.GET.get("site"))
    zone = get_object_or_404(Zone, site=site, slug=zone_slug, is_active=True)
    return JsonResponse({
        "success": True,
        "zone": {
            "slug": zone.slug,
            "title_zh": zone.title_zh,
            "summary_zh": zone.summary_zh,
            "floor_plan_image": zone.floor_plan_image.url if zone.floor_plan_image else None,
            "panorama_image": zone.panorama_image.url if zone.panorama_image else None,
            "panorama_embed_url": zone.panorama_embed_url,
        },
    })


def api_products(request):
    site = _get_default_site(request.GET.get("site"))
    qs = site.products.filter(is_active=True)
    zone = request.GET.get("zone")
    if zone:
        qs = qs.filter(zone__slug=zone)
    return JsonResponse({
        "success": True,
        "products": [_serialize_product(p) for p in qs],
    })


def api_product_detail(request, product_slug):
    site = _get_default_site(request.GET.get("site"))
    product = get_object_or_404(Product, site=site, slug=product_slug, is_active=True)
    media = [{
        "type": m.media_type,
        "title": m.title,
        "image": m.image.url if m.image else None,
        "video_url": m.video_url,
    } for m in product.media_items.all()]
    data = _serialize_product(product)
    data["media"] = media
    data["description_zh"] = product.description_zh
    return JsonResponse({"success": True, "product": data})


def api_hotspots(request, zone_slug):
    site = _get_default_site(request.GET.get("site"))
    zone = get_object_or_404(Zone, site=site, slug=zone_slug, is_active=True)
    hotspots = zone.hotspots.filter(is_active=True).select_related("product")
    data = [{
        "id": h.id,
        "label_zh": h.label_zh,
        "type": h.hotspot_type,
        "pos_x": h.pos_x,
        "pos_y": h.pos_y,
        "product_slug": h.product.slug if h.product else None,
        "target_zone_slug": h.target_zone.slug if h.target_zone else None,
        "external_url": h.external_url,
        "tooltip_zh": h.tooltip_zh,
    } for h in hotspots]
    return JsonResponse({"success": True, "hotspots": data})


def api_erp_demo_products(request):
    """示範 ERP 產品 API — 供 sync_erp 測試"""
    return JsonResponse({
        "products": [
            {
                "name": "ERP 匯入 — 自動送料機",
                "model_no": "YS-AF-01",
                "summary": "由 ERP 同步匯入的示範產品",
                "description": "此資料由 ERP API 同步而來，可在後台啟用 ErpConnection 後執行同步。",
            },
            {
                "name": "ERP 匯入 — 品質檢測站",
                "model_no": "YS-QC-02",
                "summary": "視覺檢測 + 尺寸量測一體化",
            },
        ]
    })


def api_analytics_summary(request):
    from .analytics import get_dashboard_stats
    days = int(request.GET.get("days", 7))
    return JsonResponse({"success": True, "stats": get_dashboard_stats(days=days)})


def api_pipeline_status(request, site_slug=None):
    """鋁台 / 展間 pipeline 完成度"""
    from .pipeline.digital_twins import get_digital_twins
    from .pipeline.zitai_pipeline import get_pipeline_status

    site = _get_default_site(site_slug or request.GET.get("site"))
    status = get_pipeline_status(site)
    return JsonResponse({"success": True, "pipeline": status})


def api_zone_pipeline(request, zone_slug, site_slug=None):
    """分區 pipeline 資料：環景圖集 + Digital Twin 錨點"""
    from .pipeline.digital_twins import get_digital_twins

    site = _get_default_site(site_slug or request.GET.get("site"))
    zone = get_object_or_404(Zone, site=site, slug=zone_slug, is_active=True)
    return JsonResponse({
        "success": True,
        "zone": {
            "slug": zone.slug,
            "title_zh": zone.title_zh,
            "summary_zh": zone.summary_zh,
            "photo_gallery": zone.photo_gallery or [],
            "pipeline_meta": zone.pipeline_meta or {},
            "digital_twins": get_digital_twins(zone.slug),
            "audio_guide": zone.audio_guide.url if zone.audio_guide else None,
        },
    })


def api_cad_convert_status(request):
    """檢查 STEP 轉檔工具是否可用（同 PAS /ai/api/modelviewer/convert-status）"""
    from .cad_converter import detect_tool, is_converter_available

    tool = detect_tool()
    return JsonResponse({
        "success": True,
        "available": is_converter_available(),
        "tool": tool[0] if tool else None,
    })


def api_cad_convert_product(request, product_slug):
    """將產品 STEP/IGES 轉為 GLB/OBJ 供 Three.js 載入（同 PAS convert API）"""
    from .cad_converter import convert_step_file

    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    quality = request.GET.get("quality", "low")
    if quality not in ("low", "medium", "high"):
        quality = "low"

    cad_path = None
    if product.step_file:
        cad_path = Path(product.step_file.path)
    elif product.igs_file:
        cad_path = Path(product.igs_file.path)

    if not cad_path or not cad_path.is_file():
        return JsonResponse({"success": False, "rtnmsg": "找不到 CAD 原始檔"}, status=404)

    result = convert_step_file(cad_path, quality=quality)
    if not result.success:
        return JsonResponse({
            "success": False,
            "rtnmsg": result.error,
            "installHint": result.install_hint,
        }, status=400)

    content_types = {
        "glb": "model/gltf-binary",
        "obj": "text/plain; charset=utf-8",
        "stl": "application/octet-stream",
    }
    response = HttpResponse(
        result.data,
        content_type=content_types.get(result.output_format, "application/octet-stream"),
    )
    response["X-3D-Format"] = result.output_format
    response["Content-Disposition"] = f'inline; filename="{result.output_name}"'
    return response

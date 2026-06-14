from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import translation
from django.views.decorators.http import require_http_methods, require_POST

from .analytics import track_event
from .factory_tour_catalog import DEFAULT_FACTORY_PANORAMA, REAL_FACTORY_CASES
from .site_tours import get_tour_steps
from .models import (
    BrandPoster,
    FactoryPlant,
    GuideStep,
    Inquiry,
    Product,
    ShowroomLevel,
    ShowroomSite,
    Zone,
)


def _get_site(slug=None):
    if slug:
        return get_object_or_404(ShowroomSite, slug=slug, is_active=True)
    site = ShowroomSite.objects.filter(is_default=True, is_active=True).first()
    if site:
        return site
    return get_object_or_404(ShowroomSite, is_active=True)


def _lang_field(obj, base, lang):
    suffix = {"en": "_en", "ja": "_ja"}.get(lang, "_zh")
    return getattr(obj, f"{base}{suffix}", "") or getattr(obj, f"{base}_zh", "")


def set_language(request):
    lang = request.GET.get("lang", "zh-hant")
    if lang not in ("zh-hant", "en", "ja"):
        lang = "zh-hant"
    translation.activate(lang)
    request.session["django_language"] = lang
    response = redirect(request.GET.get("next", "/"))
    response.set_cookie("django_language", lang)
    return response


def home(request, site_slug=None):
    """展間主頁面：傳遞 Level 1~3 空間拓撲、廠區節點與產品列表"""
    site = _get_site(site_slug)
    lang = translation.get_language() or "zh-hant"
    levels = (
        site.levels.filter(is_active=True)
        .prefetch_related("plants", "products")
        .order_by("sort_order", "level_number")
    )
    plants = site.plants.filter(is_active=True).select_related("level")
    zones = site.zones.filter(is_active=True)
    featured = site.products.filter(is_active=True, is_featured=True)[:10]
    all_products = site.products.filter(is_active=True).select_related(
        "showroom_level", "factory_plant", "zone"
    )
    posters = site.posters.filter(is_active=True)[:8]
    guides = site.guide_steps.all()[:5]
    current_level = levels.first()
    return render(request, "showroom/home.html", {
        "site": site,
        "levels": levels,
        "plants": plants,
        "zones": zones,
        "featured_products": featured,
        "all_products": all_products,
        "posters": posters,
        "guides": guides,
        "current_level": current_level,
        "lang": lang,
    })


def _zone_vr_context(site, zone, lang):
    digital_twins = []
    street_tour = {}
    if zone.photo_gallery:
        from .street_tour import build_street_tour
        street_tour = build_street_tour(zone, site, vr=True)
        if site.slug == "zitai":
            from .pipeline.digital_twins import get_digital_twins
            digital_twins = get_digital_twins(zone.slug)
    return {
        "digital_twins": digital_twins,
        "street_tour": street_tour,
    }


def zone_detail(request, zone_slug, site_slug=None):
    site = _get_site(site_slug)
    zone = get_object_or_404(Zone, site=site, slug=zone_slug, is_active=True)
    lang = translation.get_language() or "zh-hant"
    hotspots = zone.hotspots.filter(is_active=True).select_related("product", "target_zone")
    products = zone.products.filter(is_active=True)
    current_level = site.levels.filter(is_active=True, level_type="process_deep").first()
    track_event(request, "zone_view", path=request.path, zone=zone)

    vr_ctx = _zone_vr_context(site, zone, lang)

    return render(request, "showroom/zone.html", {
        "site": site,
        "zone": zone,
        "hotspots": hotspots,
        "products": products,
        "current_level": current_level,
        "digital_twins": vr_ctx["digital_twins"],
        "street_tour": vr_ctx["street_tour"],
        "pipeline_meta": zone.pipeline_meta or {},
        "lang": lang,
    })


def vr_zone_tour(request, zone_slug, site_slug=None):
    """VR 展覽館 — 全螢幕沉浸導覽（類似 VR展覽館）"""
    site = _get_site(site_slug)
    zone = get_object_or_404(Zone, site=site, slug=zone_slug, is_active=True)
    if not zone.photo_gallery:
        return redirect("zone", zone_slug=zone_slug) if not site_slug else redirect("site_zone", site_slug=site.slug, zone_slug=zone_slug)
    lang = translation.get_language() or "zh-hant"
    vr_ctx = _zone_vr_context(site, zone, lang)
    track_event(request, "page_view", path=request.path, zone=zone, meta={"mode": "vr_hall"})
    return render(request, "showroom/vr_tour.html", {
        "site": site,
        "zone": zone,
        "street_tour": vr_ctx["street_tour"],
        "digital_twins": vr_ctx["digital_twins"],
        "lang": lang,
    })


def vr_hall(request, site_slug=None):
    """VR 展覽館入口 — 導向第一個有照片的分區"""
    site = _get_site(site_slug)
    zone = site.zones.filter(is_active=True).exclude(photo_gallery=[]).order_by("sort_order").first()
    if not zone:
        zone = site.zones.filter(is_active=True).order_by("sort_order").first()
    if zone and zone.photo_gallery:
        if site_slug:
            return redirect("site_vr_zone", site_slug=site.slug, zone_slug=zone.slug)
        return redirect("vr_zone", zone_slug=zone.slug)
    return redirect("home")


def ar_tour(request, site_slug=None):
    """AR 沉浸式導覽示範頁 — 一次體驗全部展間功能"""
    site = _get_site(site_slug)
    lang = translation.get_language() or "zh-hant"
    levels = site.levels.filter(is_active=True).prefetch_related("plants").order_by("level_number")
    plants = site.plants.filter(is_active=True).select_related("level")
    zones = site.zones.filter(is_active=True).prefetch_related("hotspots")
    products = site.products.filter(is_active=True).select_related("zone", "showroom_level")[:10]
    flagship = site.products.filter(is_active=True, is_featured=True).first()
    demo_360_url = DEFAULT_FACTORY_PANORAMA
    tw_plant = plants.filter(plant_type="taiwan").first()
    if tw_plant and tw_plant.panorama_embed_url:
        demo_360_url = tw_plant.panorama_embed_url
    elif zones.first() and zones.first().panorama_embed_url:
        demo_360_url = zones.first().panorama_embed_url
    current_level = levels.filter(level_number=1).first()
    track_event(request, "page_view", path=request.path, meta={"tour": "ar_demo"})
    demo_steps = get_tour_steps(site, lang)
    return render(request, "showroom/tour.html", {
        "site": site,
        "levels": levels,
        "plants": plants,
        "zones": zones,
        "products": products,
        "flagship": flagship,
        "demo_360_url": demo_360_url,
        "current_level": current_level,
        "demo_steps": demo_steps,
        "lang": lang,
    })


def factory_cases(request, site_slug=None):
    """真實工廠 360° 案例展示頁（Matterport 公開 Showcase）"""
    site = _get_site(site_slug)
    lang = translation.get_language() or "zh-hant"
    cases = REAL_FACTORY_CASES
    featured = cases[0] if cases else None
    zones = site.zones.filter(is_active=True).select_related("site")
    track_event(request, "page_view", path=request.path, meta={"page": "factory_cases"})
    return render(request, "showroom/factory_cases.html", {
        "site": site,
        "cases": cases,
        "featured_case": featured,
        "zones": zones,
        "lang": lang,
    })


def product_detail(request, product_slug, site_slug=None):
    """一頁式設備詳細介紹（PopRealAR + Three.js 3D 互動）"""
    site = _get_site(site_slug)
    product = get_object_or_404(
        Product.objects.select_related("showroom_level", "factory_plant", "zone"),
        site=site, slug=product_slug, is_active=True,
    )
    lang = translation.get_language() or "zh-hant"
    media_items = product.media_items.all()
    related = site.products.filter(is_active=True).exclude(pk=product.pk)[:4]
    if product.zone_id:
        related = site.products.filter(is_active=True, zone=product.zone).exclude(pk=product.pk)[:4]
    popreal_config = product.popreal_config()
    track_event(request, "product_view", path=request.path, product=product)
    return render(request, "showroom/detail.html", {
        "site": site,
        "product": product,
        "media_items": media_items,
        "related_products": related,
        "popreal_config": popreal_config,
        "popreal_config_json": json.dumps(popreal_config, ensure_ascii=False),
        "product_name": _lang_field(product, "name", lang),
        "product_tagline": _lang_field(product, "tagline", lang),
        "product_summary": _lang_field(product, "summary", lang),
        "product_description": _lang_field(product, "description", lang),
        "product_features": getattr(product, f"features_{lang.replace('zh-hant', 'zh')}", None) or product.features_zh,
        "current_level": product.showroom_level,
        "lang": lang,
    })


def brand_zone(request, site_slug=None):
    site = _get_site(site_slug)
    lang = translation.get_language() or "zh-hant"
    posters = site.posters.filter(is_active=True)
    guides = site.guide_steps.all()
    return render(request, "showroom/brand.html", {
        "site": site,
        "posters": posters,
        "guides": guides,
        "lang": lang,
    })


def product_list(request, site_slug=None):
    site = _get_site(site_slug)
    lang = translation.get_language() or "zh-hant"
    category_slug = request.GET.get("category", "")
    qs = site.products.filter(is_active=True).select_related("category", "zone")
    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    categories = site.categories.all()
    return render(request, "showroom/products.html", {
        "site": site,
        "products": qs,
        "categories": categories,
        "current_category": category_slug,
        "lang": lang,
    })


@require_POST
def submit_inquiry(request, site_slug=None):
    site = _get_site(site_slug)
    if not site.inquiry_enabled:
        return JsonResponse({"success": False, "error": "諮詢功能未開啟"}, status=403)

    try:
        data = json.loads(request.body) if request.content_type == "application/json" else request.POST
    except json.JSONDecodeError:
        data = request.POST

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()
    if not name or not email or not message:
        return JsonResponse({"success": False, "error": "請填寫姓名、Email 與諮詢內容"}, status=400)

    product = None
    product_slug = (data.get("product_slug") or "").strip()
    if product_slug:
        product = Product.objects.filter(site=site, slug=product_slug).first()

    ip = request.META.get("REMOTE_ADDR")
    inquiry = Inquiry.objects.create(
        site=site,
        product=product,
        name=name,
        company=(data.get("company") or "").strip(),
        email=email,
        phone=(data.get("phone") or "").strip(),
        message=message,
        ip_address=ip,
    )
    track_event(request, "inquiry", path="/inquiry/", product=product, meta={"inquiry_id": inquiry.id})
    return JsonResponse({"success": True, "message": "感謝您的諮詢，我們將盡快與您聯繫！"})


def share_page(request, product_slug=None, site_slug=None):
    """社群分享預覽頁"""
    site = _get_site(site_slug)
    product = None
    if product_slug:
        product = Product.objects.filter(site=site, slug=product_slug, is_active=True).first()
    return render(request, "showroom/share.html", {"site": site, "product": product})


def preview_access(request):
    """公開預覽通行碼驗證（PREVIEW_MODE）"""
    next_url = request.GET.get("next") or request.POST.get("next") or "/"
    if not next_url.startswith("/"):
        next_url = "/"

    if request.session.get("preview_authenticated"):
        return redirect(next_url)

    error = ""
    if request.method == "POST":
        password = request.POST.get("password", "")
        if password and password == getattr(settings, "PREVIEW_PASSWORD", ""):
            request.session["preview_authenticated"] = True
            return redirect(next_url)
        error = "通行碼不正確，請再試一次。"

    return render(request, "showroom/preview_access.html", {
        "error": error,
        "next_url": next_url,
    })


def planning_preview(request, site_slug=None):
    """資料上傳規劃儀表板 — 顯示 intake 完成度與展間預覽連結"""
    from .intake import build_intake_status

    site = _get_site(site_slug)
    status = build_intake_status()
    levels = site.levels.filter(is_active=True).order_by("sort_order", "level_number")
    zones = site.zones.filter(is_active=True).order_by("sort_order")
    products = site.products.filter(is_active=True).order_by("sort_order", "name_zh")
    plants = site.plants.filter(is_active=True).order_by("sort_order")
    return render(request, "showroom/planning.html", {
        "site": site,
        "status": status,
        "levels": levels,
        "zones": zones,
        "products": products,
        "plants": plants,
    })

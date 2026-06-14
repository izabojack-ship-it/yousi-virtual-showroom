"""分析事件工具"""
from .models import AnalyticsEvent, ShowroomSite


def _get_site():
    return ShowroomSite.objects.filter(is_default=True, is_active=True).first()


def track_event(request, event_type, *, path="", product=None, zone=None, meta=None):
    try:
        AnalyticsEvent.objects.create(
            site=_get_site(),
            event_type=event_type,
            path=path or request.path,
            product=product,
            zone=zone,
            user=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:300],
            referer=(request.META.get("HTTP_REFERER") or "")[:300],
            meta=meta or {},
        )
    except Exception:
        pass


def get_dashboard_stats(days=30):
    from django.db.models import Count
    from django.db.models.functions import TruncDate
    from django.utils import timezone
    from datetime import timedelta

    since = timezone.now() - timedelta(days=days)
    qs = AnalyticsEvent.objects.filter(created_at__gte=since)

    by_type = list(qs.values("event_type").annotate(count=Count("id")).order_by("-count"))
    daily = list(
        qs.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    top_products = list(
        qs.filter(event_type="product_view", product__isnull=False)
        .values("product__name_zh", "product__slug")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    top_pages = list(
        qs.filter(event_type="page_view")
        .values("path")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    inquiry_count = qs.filter(event_type="inquiry").count()
    login_count = qs.filter(event_type="login").count()

    return {
        "days": days,
        "total_events": qs.count(),
        "by_type": by_type,
        "daily": daily,
        "top_products": top_products,
        "top_pages": top_pages,
        "inquiry_count": inquiry_count,
        "login_count": login_count,
    }

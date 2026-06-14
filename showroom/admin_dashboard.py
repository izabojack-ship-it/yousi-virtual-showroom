from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from .analytics import get_dashboard_stats
from .models import ErpConnection, ErpSyncLog, Inquiry, MemberProfile


@staff_member_required
def analytics_dashboard(request):
    days = int(request.GET.get("days", 30))
    stats = get_dashboard_stats(days=days)
    recent_inquiries = Inquiry.objects.order_by("-created_at")[:10]
    members_count = MemberProfile.objects.count()
    erp_logs = ErpSyncLog.objects.select_related("connection").order_by("-created_at")[:5]
    erp = ErpConnection.objects.filter(is_active=True).first()
    return render(request, "admin/analytics_dashboard.html", {
        "stats": stats,
        "recent_inquiries": recent_inquiries,
        "members_count": members_count,
        "erp_logs": erp_logs,
        "erp": erp,
        "days": days,
    })

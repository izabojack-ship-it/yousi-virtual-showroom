from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from showroom.admin_dashboard import analytics_dashboard

urlpatterns = [
    path("admin/analytics/", analytics_dashboard, name="admin_analytics"),
    path("admin/", admin.site.urls),
    path("api/", include("showroom.api_urls")),
    path("", include("showroom.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
elif getattr(settings, "SERVE_MEDIA", False):
    # Django 5 的 static() 在非 DEBUG 時為 no-op，預覽部署需明確掛載 media
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]

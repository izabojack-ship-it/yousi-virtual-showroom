"""瀏覽追蹤中介層"""
from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware

from .analytics import track_event


class ShowroomCsrfViewMiddleware(CsrfViewMiddleware):
    """正式環境 CSRF；PREVIEW_MODE 時允許 Cloudflare Tunnel 子網域。"""

    def _origin_verified(self, request):
        if getattr(settings, "PREVIEW_MODE", False):
            origin = request.META.get("HTTP_ORIGIN", "")
            if origin.endswith(".trycloudflare.com"):
                return True
        return super()._origin_verified(request)


class PreviewGateMiddleware:
    """PREVIEW_MODE + PREVIEW_PASSWORD 時，訪客須先通過預覽通行碼。"""

    OPEN_PREFIXES = ("/preview-access/", "/static/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "PREVIEW_MODE", False):
            return self.get_response(request)
        if not getattr(settings, "PREVIEW_PASSWORD", ""):
            return self.get_response(request)

        path = request.path
        if path.startswith("/admin/"):
            return self.get_response(request)
        if any(path.startswith(prefix) for prefix in self.OPEN_PREFIXES):
            return self.get_response(request)
        if request.session.get("preview_authenticated"):
            return self.get_response(request)

        from django.shortcuts import redirect
        from urllib.parse import quote

        return redirect(f"/preview-access/?next={quote(request.get_full_path(), safe='/')}")


class PreviewReadOnlyMiddleware:
    """PREVIEW_READONLY 時禁止外部寫入與後台存取。"""

    ALLOW_POST_PREFIXES = ("/preview-access/",)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "PREVIEW_READONLY", False):
            return self.get_response(request)

        path = request.path
        if path.startswith("/admin/"):
            from django.http import HttpResponseNotFound

            return HttpResponseNotFound("預覽模式不提供後台管理。")

        if request.method not in ("GET", "HEAD", "OPTIONS"):
            if not any(path.startswith(prefix) for prefix in self.ALLOW_POST_PREFIXES):
                from django.http import HttpResponseForbidden, JsonResponse

                if path.startswith("/api/") or "application/json" in (
                    request.content_type or ""
                ):
                    return JsonResponse(
                        {"success": False, "error": "預覽模式僅供瀏覽，無法提交或修改資料。"},
                        status=403,
                    )
                return HttpResponseForbidden("預覽模式僅供瀏覽，無法提交或修改資料。")

        return self.get_response(request)


class AnalyticsMiddleware:
    SKIP_PREFIXES = ("/admin/", "/static/", "/media/", "/api/analytics")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        path = request.path
        if request.method == "GET" and not any(path.startswith(p) for p in self.SKIP_PREFIXES):
            if response.status_code == 200:
                track_event(
                    request,
                    "page_view",
                    path=path,
                    meta={"query": request.META.get("QUERY_STRING", "")},
                )
        return response

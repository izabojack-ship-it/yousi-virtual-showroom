from .models import ShowroomSite
from .preview_utils import is_preview_readonly


def showroom_globals(request):
    site = (
        ShowroomSite.objects.filter(is_default=True, is_active=True)
        .prefetch_related("levels")
        .first()
    )
    if not site:
        site = ShowroomSite.objects.filter(is_active=True).prefetch_related("levels").first()
    lang = getattr(request, "LANGUAGE_CODE", "zh-hant") or "zh-hant"
    return {
        "showroom_site": site,
        "site": site,
        "current_lang": lang,
        "preview_readonly": is_preview_readonly(),
    }

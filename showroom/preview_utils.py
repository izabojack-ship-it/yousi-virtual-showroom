"""公開預覽模式工具"""
from django.conf import settings


def is_preview_readonly():
    return getattr(settings, "PREVIEW_MODE", False) and getattr(
        settings, "PREVIEW_READONLY", True
    )

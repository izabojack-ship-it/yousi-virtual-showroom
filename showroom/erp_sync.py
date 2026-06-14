"""ERP 產品同步"""
import json
import urllib.error
import urllib.request
from django.utils import timezone
from django.utils.text import slugify

from .models import ErpConnection, ErpSyncLog, Product, ProductCategory


DEFAULT_MAPPING = {
    "name_zh": "name",
    "model_no": "model_no",
    "summary_zh": "summary",
    "description_zh": "description",
    "official_url": "url",
    "features_zh": "features",
    "specs": "specs",
}


def _fetch_products(connection: ErpConnection) -> list:
    url = connection.api_base_url.rstrip("/") + "/" + connection.products_endpoint.lstrip("/")
    headers = {"Accept": "application/json", "User-Agent": "YousiShowroom/1.0"}
    if connection.api_key:
        headers[connection.auth_header] = f"{connection.auth_prefix} {connection.api_key}".strip()
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if isinstance(data, dict):
        return data.get("products") or data.get("items") or data.get("data") or []
    return data


def _map_fields(erp_item: dict, mapping: dict) -> dict:
    out = {}
    m = {**DEFAULT_MAPPING, **(mapping or {})}
    for local_field, erp_field in m.items():
        val = erp_item.get(erp_field)
        if val is not None and val != "":
            out[local_field] = val
    return out


def sync_products(connection: ErpConnection, *, dry_run=False) -> ErpSyncLog:
    site = connection.site
    created = updated = skipped = 0
    messages = []

    try:
        items = _fetch_products(connection)
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
        log = ErpSyncLog.objects.create(
            connection=connection, status="error", message=str(e)
        )
        connection.last_sync_at = timezone.now()
        connection.last_sync_status = "error"
        connection.last_sync_message = str(e)
        connection.save(update_fields=["last_sync_at", "last_sync_status", "last_sync_message", "updated_at"])
        return log

    default_cat, _ = ProductCategory.objects.get_or_create(
        site=site, slug="erp-import", defaults={"name_zh": "ERP 匯入"}
    )

    for item in items:
        mapped = _map_fields(item, connection.field_mapping)
        name = mapped.get("name_zh") or item.get("name") or item.get("item_name")
        if not name:
            skipped += 1
            continue
        model_no = mapped.get("model_no") or item.get("code") or item.get("item_no") or ""
        slug_base = slugify(model_no or name) or "product"
        slug = slug_base[:90]

        existing = Product.objects.filter(site=site, slug=slug).first()
        if not existing and model_no:
            existing = Product.objects.filter(site=site, model_no=model_no).first()

        if dry_run:
            created += 0 if existing else 1
            updated += 1 if existing else 0
            continue

        if existing:
            for k, v in mapped.items():
                setattr(existing, k, v)
            existing.is_active = True
            existing.save()
            updated += 1
        else:
            n = 1
            final_slug = slug
            while Product.objects.filter(site=site, slug=final_slug).exists():
                final_slug = f"{slug}-{n}"
                n += 1
            Product.objects.create(
                site=site,
                category=default_cat,
                slug=final_slug,
                name_zh=name,
                model_no=model_no,
                summary_zh=mapped.get("summary_zh", ""),
                description_zh=mapped.get("description_zh", ""),
                features_zh=mapped.get("features_zh") or [],
                specs=mapped.get("specs") or {},
                official_url=mapped.get("official_url", ""),
                is_active=True,
            )
            created += 1

    msg = f"同步完成：新增 {created}、更新 {updated}、略過 {skipped}"
    log = ErpSyncLog.objects.create(
        connection=connection,
        status="ok",
        created_count=created,
        updated_count=updated,
        skipped_count=skipped,
        message=msg,
    )
    connection.last_sync_at = timezone.now()
    connection.last_sync_status = "ok"
    connection.last_sync_message = msg
    connection.save(update_fields=["last_sync_at", "last_sync_status", "last_sync_message", "updated_at"])
    return log

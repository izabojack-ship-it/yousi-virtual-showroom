"""Remove ?v= cache-buster suffixes from file field names (Cloudinary incompatible)."""
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.apps import apps
from django.db.models import FileField, ImageField

updated = 0
for model in apps.get_app_config("showroom").get_models():
    for field in model._meta.get_fields():
        if not isinstance(field, (FileField, ImageField)):
            continue
        for obj in model.objects.all():
            f = getattr(obj, field.name)
            if not f or not f.name or "?" not in f.name:
                continue
            clean = f.name.split("?", 1)[0]
            setattr(obj, field.name, clean)
            obj.save(update_fields=[field.name])
            updated += 1
            print(f"{model.__name__}.{field.name} pk={obj.pk}: {clean}")

print(f"Updated {updated} field(s).")

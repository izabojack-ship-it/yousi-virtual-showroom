import os
import re
import sys
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from showroom.models import ShowroomSite, Zone

site = ShowroomSite.objects.get(slug="zitai")
zone = Zone.objects.get(slug="plant1-production", site=site)
print("gallery count", len(zone.photo_gallery or []))
if zone.photo_gallery:
    for u in zone.photo_gallery[:3]:
        if u.startswith("http"):
            code = requests.head(u, timeout=20).status_code
            print(" gallery", code, u[-80:])

html = urllib.request.urlopen(
    "https://yousi-virtual-showroom.onrender.com/zone/plant1-production/",
    timeout=90,
).read().decode("utf-8", "ignore")
cloud = re.findall(r"https://res\.cloudinary\.com[^\"'\s>]+", html)
print("cloudinary in zone html", len(cloud))
for u in cloud[:8]:
    print(" ", requests.head(u, timeout=20).status_code, u[-75:])

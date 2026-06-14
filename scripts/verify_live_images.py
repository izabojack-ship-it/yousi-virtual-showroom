import re
import urllib.request

import requests

pages = [
    "https://yousi-virtual-showroom.onrender.com/",
    "https://yousi-virtual-showroom.onrender.com/zone/plant1-production/",
    "https://yousi-virtual-showroom.onrender.com/vr/plant1-production/",
]
for page in pages:
    html = urllib.request.urlopen(page, timeout=90).read().decode("utf-8", "ignore")
    cloud = re.findall(r'(?:src|href|data-src)="(https://res\.cloudinary\.com[^"]+)"', html)
    ok = bad = 0
    for u in cloud:
        r = requests.head(u, timeout=30, allow_redirects=True)
        if r.status_code == 200:
            ok += 1
        else:
            bad += 1
    print(page.split(".com")[-1], "imgs", len(cloud), "ok", ok, "bad", bad)

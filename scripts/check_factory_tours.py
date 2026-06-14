"""Verify factory-related Matterport tours and print titles."""
import re
import urllib.request

CANDIDATES = [
    ("SxQL3iGyoDo", "unknown"),
    ("Zh14WDtkjdC", "matterport-doc-example"),
    ("zMEBqKJrX5N", "CU-Boulder-COSINC-lab"),
    ("4mqC2aD5XVu", "Fleetwood-2024-Factory-Show"),
    ("Y3mrZUbxzfv", "Meijer-warehouse-retail"),
    ("8Q6cw6yWM6y", "factory-barndominium"),
    ("Qy4ShA63M1a", "office"),
    ("JGPnGQ6hosj", "luxury-home"),
]

for mid, label in CANDIDATES:
    url = f"https://my.matterport.com/show/?m={mid}&play=1&qs=1&help=2"
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as r:
            status = r.status
    except Exception:
        print(f"FAIL {mid} ({label})")
        continue
    html = urllib.request.urlopen(url.replace("&play=1", ""), timeout=15).read().decode("utf-8", "ignore")
    title = re.search(r'property="og:title" content="([^"]+)"', html)
    print(f"OK {mid} ({label})")
    if title:
        print(f"   {title.group(1)[:120]}")

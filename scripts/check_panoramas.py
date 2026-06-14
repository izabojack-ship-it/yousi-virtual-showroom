"""Check embeddable factory 360 tour URLs."""
import re
import urllib.request

MATTERPORT_IDS = [
    "JGPnGQ6hosj", "Zk2KYD3JNvp", "GbPanTZARDF", "W7S4Y8k8fek", "VmWJqRfy5xE",
    "Fxm1Qv5mEBo", "9CdGqW5h8dB", "L5FZUqJ9NEB", "S7cGdT9EY5w", "1Q1cGk4B9X8",
    "x8ZVTNoHXEk", "T6uJVqJ9NEB", "oP7KqG8YJdB", "HMxL3G7Jek9", "Zh14WDtnEkP",
]

IMAGE_URLS = [
    ("warehouse", "https://pannellum.org/images/city.jpg"),
    ("alma", "https://pannellum.org/images/alma.jpg"),
    ("bma", "https://pannellum.org/images/bma-1.jpg"),
]

print("=== Matterport ===")
for mid in MATTERPORT_IDS:
    url = f"https://my.matterport.com/show/?m={mid}&play=1&qs=1"
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as r:
            print("OK", mid, url)
    except Exception as e:
        print("FAIL", mid)

print("\n=== Images ===")
for name, url in IMAGE_URLS:
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as r:
            print("OK", name, r.headers.get("Content-Length"), url)
    except Exception as e:
        print("FAIL", name, e)

mid = "JGPnGQ6hosj"
html = urllib.request.urlopen(f"https://my.matterport.com/show/?m={mid}", timeout=15).read().decode("utf-8", "ignore")
for key in ("og:title", "og:description"):
    m = re.search(rf'property="{key}" content="([^"]+)"', html)
    if m:
        print(key, ":", m.group(1)[:200])

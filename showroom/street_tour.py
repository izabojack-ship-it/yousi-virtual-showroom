"""
街景式導覽 — 由照片廊建立場景節點、地面箭頭與分區路標

模擬 Google Street View：同一分區內沿動線「步行」切換視角，
分區邊界顯示路標指向相鄰車間。
"""
from __future__ import annotations

from showroom.models import ShowroomSite, Zone

# 分區間路標（相鄰車間導覽動線）
ZONE_EXIT_SIGNS: dict[str, list[dict]] = {
    "plant1-lobby": [
        {"slug": "plant1-production", "label": "生產線動線", "yaw": 15},
        {"slug": "plant1-training", "label": "教育訓練室", "yaw": -55},
    ],
    "plant1-production": [
        {"slug": "plant1-coating", "label": "噴塗區", "yaw": 35},
        {"slug": "plant1-qc", "label": "品管室", "yaw": -25},
        {"slug": "plant1-inventory", "label": "成品庫存", "yaw": 70},
        {"slug": "plant1-lobby", "label": "← 返回大門", "yaw": 165},
    ],
    "plant1-coating": [
        {"slug": "plant1-production", "label": "← 生產線", "yaw": -140},
        {"slug": "plant1-qc", "label": "品管室", "yaw": 20},
    ],
    "plant1-qc": [
        {"slug": "plant1-production", "label": "← 生產線", "yaw": 160},
        {"slug": "plant1-inventory", "label": "成品庫存", "yaw": 40},
    ],
    "plant1-inventory": [
        {"slug": "plant1-production", "label": "← 生產線", "yaw": -150},
        {"slug": "plant2-production", "label": "二廠生產線 →", "yaw": 10},
    ],
    "plant1-assembly-2f": [
        {"slug": "plant1-production", "label": "← 一樓生產線", "yaw": -170},
        {"slug": "plant1-training", "label": "教育訓練室", "yaw": 30},
    ],
    "plant1-training": [
        {"slug": "plant1-lobby", "label": "← 大門入口", "yaw": -160},
        {"slug": "plant1-assembly-2f", "label": "組裝區", "yaw": 25},
    ],
    "plant2-entrance": [
        {"slug": "plant2-production", "label": "進入生產線 →", "yaw": 5},
        {"slug": "plant1-inventory", "label": "← 一廠成品區", "yaw": -175},
    ],
    "plant2-production": [
        {"slug": "plant2-entrance", "label": "← 二廠大門", "yaw": 175},
        {"slug": "plant1-production", "label": "← 一廠生產線", "yaw": -120},
    ],
}

# 各分區場景節點預設路標名稱（依序對應照片）
ZONE_SCENE_LABELS: dict[str, list[str]] = {
    "plant1-lobby": ["大門入口", "接待區", "會議室", "文管室"],
    "plant1-production": ["產線入口", "壓鑄機組裝區", "主產線通道", "設備待機區", "動線轉角"],
    "plant1-qc": ["品管入口", "量測站", "檢驗台面"],
    "plant2-production": ["二廠產線入口", "主力機型區", "組裝平台"],
}


def _scene_label(zone_slug: str, index: int, total: int) -> str:
    presets = ZONE_SCENE_LABELS.get(zone_slug, [])
    if index < len(presets):
        return presets[index]
    if index == 0:
        return "起點"
    if index == total - 1:
        return "終點"
    return f"視角 {index + 1}"


def build_street_tour(zone: Zone, site: ShowroomSite, *, vr: bool = False) -> dict:
    """組裝街景導覽 JSON（供前端 showroom-streetview.js 使用）"""
    gallery = zone.photo_gallery or []
    total = len(gallery)
    scenes = []

    for i, url in enumerate(gallery):
        links = []
        if i > 0:
            links.append({
                "type": "walk",
                "target": i - 1,
                "label": _scene_label(zone.slug, i - 1, total),
                "yaw": 180,
                "sign": "← 返回",
            })
        if i < total - 1:
            links.append({
                "type": "walk",
                "target": i + 1,
                "label": _scene_label(zone.slug, i + 1, total),
                "yaw": 0,
                "sign": "沿動線前進 →",
            })
        scenes.append({
            "id": i,
            "url": url,
            "label": _scene_label(zone.slug, i, total),
            "links": links,
        })

    exits = []
    for ex in ZONE_EXIT_SIGNS.get(zone.slug, []):
        target = Zone.objects.filter(site=site, slug=ex["slug"], is_active=True).first()
        if not target:
            continue
        if vr:
            zone_url = f"/vr/{target.slug}/"
        else:
            zone_url = f"/zone/{target.slug}/"
        exits.append({
            "zoneSlug": target.slug,
            "zoneTitle": target.title_zh,
            "label": ex["label"],
            "yaw": ex["yaw"],
            "url": zone_url,
        })

    return {
        "mode": "streetview",
        "zoneSlug": zone.slug,
        "zoneTitle": zone.title_zh,
        "sceneCount": total,
        "scenes": scenes,
        "exits": exits,
    }

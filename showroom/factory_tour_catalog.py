"""
公開可嵌入的真實工廠 / 產線 / 倉儲 Matterport 360° 案例目錄

注意：以下為第三方公開 Showcase，僅供 demo 與驗廠 UI 流程展示。
正式上線請替換為貴司 qwhouse720 或自架 Matterport 場景。
"""

MATTERPORT_BASE = "https://my.matterport.com/show/"

# Matterport 嵌入參數：自動播放、簡化說明、隱藏部分品牌元素
MATTERPORT_PARAMS = "play=1&qs=1&help=2&nt=1"


def matterport_embed(model_id: str) -> str:
    return f"{MATTERPORT_BASE}?m={model_id}&{MATTERPORT_PARAMS}"


# 精選真實工廠 / 工業場景（已驗證可 HTTP 200 嵌入）
REAL_FACTORY_CASES = [
    {
        "id": "hyundai-steel",
        "model_id": "6Wrc8Eu65py",
        "title_zh": "Hyundai Steel STS 仁川廠",
        "title_en": "Hyundai Steel STS Plant in Incheon",
        "summary_zh": "韓國現代鋼鐵 STS 產線 3D 實境，冷色工業質感、乾淨 HDR 光影，為科技導覽視覺參考標竿。",
        "scene_type": "steel_plant",
        "embed_url": matterport_embed("6Wrc8Eu65py"),
        "recommended_zones": ["cnc-machining", "surface-treatment", "assembly-qc"],
    },
    {
        "id": "factory-show",
        "model_id": "4mqC2aD5XVu",
        "title_zh": "Fleetwood 2024 工廠展（Factory Show）",
        "title_en": "Fleetwood Riverside 2024 Factory Show",
        "summary_zh": "真實製造業工廠展場 3D 實境，適合模擬「走進產線大廳」的驗廠體驗。",
        "scene_type": "factory_show",
        "embed_url": matterport_embed("4mqC2aD5XVu"),
        "recommended_zones": ["assembly-qc", "injection-workshop", "cnc-machining"],
    },
    {
        "id": "cosinc-lab",
        "model_id": "zMEBqKJrX5N",
        "title_zh": "COSINC 精密設備實驗室（CU Boulder）",
        "title_en": "COSINC XPS and LEIS Facilities",
        "summary_zh": "含精密儀器、設備機台的室內工業空間，適合模擬 CNC / 檢測車間。",
        "scene_type": "equipment_lab",
        "embed_url": matterport_embed("zMEBqKJrX5N"),
        "recommended_zones": ["cnc-workshop", "cnc-machining", "assembly-qc"],
    },
    {
        "id": "warehouse",
        "model_id": "Y3mrZUbxzfv",
        "title_zh": "Meijer 大型倉儲 / 物流空間",
        "title_en": "Meijer-Sized Retail Warehouse",
        "summary_zh": "大尺度倉儲動線與貨架空間，適合模擬原料倉、物流區。",
        "scene_type": "warehouse",
        "embed_url": matterport_embed("Y3mrZUbxzfv"),
        "recommended_zones": ["raw-material", "sawing"],
    },
    {
        "id": "construction-industrial",
        "model_id": "SxQL3iGyoDo",
        "title_zh": "工地 / 工業建置現場",
        "title_en": "Construction Site 3D Tour",
        "summary_zh": "工業建置現場 360°，適合模擬擴廠、越南廠建置進度展示。",
        "scene_type": "construction",
        "embed_url": matterport_embed("SxQL3iGyoDo"),
        "recommended_zones": ["surface-treatment", "deburring", "factory_hub"],
    },
]

CASE_BY_ID = {c["id"]: c for c in REAL_FACTORY_CASES}
CASE_BY_MODEL = {c["model_id"]: c for c in REAL_FACTORY_CASES}

# 分區 slug → 推薦案例（用於 seed 自動配置）
ZONE_PANORAMA_MAP = {
    "cnc-machining": "cosinc-lab",
    "cnc-workshop": "cosinc-lab",
    "injection-workshop": "factory-show",
    "assembly": "factory-show",
    "assembly-qc": "factory-show",
    "sawing": "warehouse",
    "raw-material": "warehouse",
    "deburring": "construction-industrial",
    "surface-treatment": "construction-industrial",
}

DEFAULT_FACTORY_PANORAMA = matterport_embed("4mqC2aD5XVu")


def panorama_for_zone(zone_slug: str) -> str:
    case_id = ZONE_PANORAMA_MAP.get(zone_slug, "factory-show")
    case = CASE_BY_ID.get(case_id)
    return case["embed_url"] if case else DEFAULT_FACTORY_PANORAMA

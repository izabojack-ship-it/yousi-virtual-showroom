"""鋁台精機廠 — 展間站點設定與分區對照"""
from pathlib import Path

SITE_SLUG = "zitai"

DEFAULT_SOURCE = Path(
    r"d:\川海\廠商資料\輔導中\鋁台\drive-download-20260613T004405Z-3-001"
)

# 資料夾關鍵字 → 分區 slug（以實際目錄名稱子字串比對）
ZONE_FOLDER_KEYS = [
    ("plant1-lobby", "大門", "一廠大門・入口・會議室・文管室"),
    ("plant1-production", "一廠一樓生產線", "一廠一樓生產線動線"),
    ("plant1-coating", "噴塗", "一廠一樓噴塗區"),
    ("plant1-qc", "品管", "一廠一樓品管室"),
    ("plant1-inventory", "成品", "一廠一樓成品庫存區"),
    ("plant1-assembly-2f", "組裝", "一廠二樓零件組裝區"),
    ("plant1-training", "教育", "一廠二樓教育訓練室"),
    ("plant2-production", "二廠一樓", "二廠一樓生產線"),
]

ZONE_SUMMARIES = {
    "plant1-lobby": (
        "一廠迎賓動線：大門入口、會議室與文管室，展現鋁台精機企業形象與接待空間。"
    ),
    "plant1-production": (
        "冷室壓鑄機組裝與生產動線，可見 ZITAI 壓鑄設備製造現場與產線配置。"
    ),
    "plant1-coating": (
        "噴塗與表面處理區域，機台塗裝與外觀品質作業一線實景。"
    ),
    "plant1-qc": (
        "品質管理室，量測、檢驗與品保流程展示。"
    ),
    "plant1-inventory": (
        "成品庫存區，已完工壓鑄機與週邊設備待出貨實景。"
    ),
    "plant1-assembly-2f": (
        "二樓零件組裝區，液壓、電控與機構零件整合作業現場。"
    ),
    "plant1-training": (
        "教育訓練室，員工技能培訓與客戶技術交流空間。"
    ),
    "plant2-entrance": (
        "二廠大門口，和睦路801號廠區入口實景。"
    ),
    "plant2-production": (
        "二廠一樓生產線，擴充產能之製造現場與設備展示。"
    ),
}

PRODUCTS = [
    {
        "slug": "zdc-100tps",
        "model_no": "ZDC-100TPS",
        "name_zh": "100T 冷室壓鑄機",
        "name_en": "100T Cold Chamber Die Casting Machine",
        "tagline_zh": "精密中小型鑄件生產",
        "summary_zh": "100 噸冷室壓鑄機，適用鋁、鋅合金精密鑄件，操作穩定、占地精省。",
        "zone": "plant1-production",
    },
    {
        "slug": "zdc-180tpsa",
        "model_no": "ZDC-180TPSA",
        "name_zh": "180T 冷室壓鑄機",
        "name_en": "180T Cold Chamber Die Casting Machine",
        "tagline_zh": "高效能中型壓鑄解決方案",
        "summary_zh": "180 噸 TPSA 系列，強化鎖模力與射出性能，適合汽機車與通訊零件。",
        "zone": "plant1-production",
    },
    {
        "slug": "zdc-250tpsa",
        "model_no": "ZDC-250TPSA",
        "name_zh": "250T 冷室壓鑄機",
        "name_en": "250T Cold Chamber Die Casting Machine",
        "tagline_zh": "量產級壓鑄主力機型",
        "summary_zh": "250 噸級冷室壓鑄機，兼顧產能與精度，廣泛應用於工業零組件。",
        "zone": "plant2-production",
    },
    {
        "slug": "zdc-420tpsa",
        "model_no": "ZDC-420TPSA",
        "name_zh": "420T 冷室壓鑄機",
        "name_en": "420T Cold Chamber Die Casting Machine",
        "tagline_zh": "大型鑄件重載機型",
        "summary_zh": "420 噸大型冷室壓鑄機，滿足大型結構件與高鎖模力需求。",
        "zone": "plant2-production",
    },
    {
        "slug": "zdc-1250t",
        "model_no": "ZDC-1250T",
        "name_zh": "1250T 冷室壓鑄機",
        "name_en": "1250T Cold Chamber Die Casting Machine",
        "tagline_zh": "超大型重載壓鑄旗艦機型",
        "summary_zh": "1250 噸冷室壓鑄機，適用大型結構件、高鎖模力量產與重載工業應用。",
        "zone": "plant2-production",
    },
]

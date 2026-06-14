"""Digital twin AR anchor definitions per 鋁台 zone."""

ZONE_DIGITAL_TWINS = {
    "plant1-lobby": [
        {
            "id": "dt-lobby",
            "position": [0, 1.3, -4],
            "title": "鋁台精機廠",
            "subtitle": "ZITAI · EST. 1981",
            "rows": [
                {"label": "一廠", "value": "溪頭路172號", "status": "neutral"},
                {"label": "二廠", "value": "和睦路801號", "status": "neutral"},
                {"label": "連線", "value": "ONLINE", "status": "running"},
            ],
            "accent": "#00ffff",
        },
        {
            "id": "dt-lobby-env",
            "position": [-2.2, 1.1, -3.2],
            "title": "迎賓區環境",
            "subtitle": "IoT · LOBBY",
            "rows": [
                {"label": "Temp", "value": "23°C", "status": "neutral"},
                {"label": "Air", "value": "Clean", "status": "running"},
                {"label": "訪客", "value": "Ready", "status": "running"},
            ],
            "accent": "#39ff14",
        },
    ],
    "plant1-production": [
        {
            "id": "dt-cnc-01",
            "position": [2, 1, -3],
            "title": "冷室壓鑄機 #01",
            "subtitle": "ZITAI · DIGITAL TWIN",
            "rows": [
                {"label": "Status", "value": "RUNNING", "status": "running"},
                {"label": "OEE", "value": "92.5%", "status": "running"},
                {"label": "鎖模力", "value": "180T", "status": "neutral"},
            ],
            "accent": "#39ff14",
        },
        {
            "id": "dt-env-a",
            "position": [-2, 1.5, -4],
            "title": "產線環境感測",
            "subtitle": "IoT · ZONE-PROD-1F",
            "rows": [
                {"label": "Temp", "value": "24°C", "status": "neutral"},
                {"label": "Humidity", "value": "52%", "status": "neutral"},
                {"label": "PM2.5", "value": "Safe", "status": "running"},
            ],
            "accent": "#00ffff",
        },
        {
            "id": "dt-cycle",
            "position": [0.5, 0.8, -2.6],
            "title": "射出週期監控",
            "subtitle": "MES · LIVE",
            "rows": [
                {"label": "Cycle", "value": "38s", "status": "running"},
                {"label": "Yield", "value": "98.7%", "status": "running"},
                {"label": "Alarm", "value": "None", "status": "neutral"},
            ],
            "accent": "#00ffff",
        },
    ],
    "plant1-coating": [
        {
            "id": "dt-coating",
            "position": [1.8, 1.2, -3.2],
            "title": "噴塗作業站",
            "subtitle": "SURFACE · QC",
            "rows": [
                {"label": "Status", "value": "ACTIVE", "status": "running"},
                {"label": "塗層", "value": "Epoxy", "status": "neutral"},
                {"label": "溫度", "value": "26°C", "status": "neutral"},
            ],
            "accent": "#00ffff",
        },
    ],
    "plant1-qc": [
        {
            "id": "dt-qc",
            "position": [1.5, 1.2, -3.5],
            "title": "品管檢測站",
            "subtitle": "QC · LIVE",
            "rows": [
                {"label": "Status", "value": "INSPECTING", "status": "running"},
                {"label": "良率", "value": "99.2%", "status": "running"},
                {"label": "批次", "value": "ZDC-250", "status": "neutral"},
            ],
            "accent": "#00ffff",
        },
    ],
    "plant1-inventory": [
        {
            "id": "dt-inv",
            "position": [0, 1.4, -3.8],
            "title": "成品庫存區",
            "subtitle": "WMS · TRACKING",
            "rows": [
                {"label": "在庫", "value": "12 台", "status": "running"},
                {"label": "待出貨", "value": "3 台", "status": "neutral"},
                {"label": "GPS", "value": "Locked", "status": "running"},
            ],
            "accent": "#39ff14",
        },
    ],
    "plant1-assembly-2f": [
        {
            "id": "dt-asm",
            "position": [-1.5, 1.3, -3.4],
            "title": "零件組裝線",
            "subtitle": "2F · ASSEMBLY",
            "rows": [
                {"label": "Status", "value": "ACTIVE", "status": "running"},
                {"label": "工位", "value": "4/4", "status": "running"},
                {"label": "進度", "value": "78%", "status": "neutral"},
            ],
            "accent": "#00ffff",
        },
    ],
    "plant1-training": [
        {
            "id": "dt-train",
            "position": [1.2, 1.2, -3.6],
            "title": "教育訓練室",
            "subtitle": "TRAINING · VR",
            "rows": [
                {"label": "課程", "value": "壓鑄基礎", "status": "neutral"},
                {"label": "席位", "value": "Available", "status": "running"},
                {"label": "連線", "value": "ONLINE", "status": "running"},
            ],
            "accent": "#00ffff",
        },
    ],
    "plant2-entrance": [
        {
            "id": "dt-p2-gate",
            "position": [0, 1.3, -4],
            "title": "二廠大門",
            "subtitle": "PLANT-2 · GATE",
            "rows": [
                {"label": "地址", "value": "和睦路801號", "status": "neutral"},
                {"label": "狀態", "value": "OPEN", "status": "running"},
                {"label": "產線", "value": "Ready", "status": "running"},
            ],
            "accent": "#39ff14",
        },
    ],
    "plant2-production": [
        {
            "id": "dt-press-1250",
            "position": [0, 1.2, -3.2],
            "title": "ZDC-1250T",
            "subtitle": "1250T 冷室壓鑄機",
            "rows": [
                {"label": "Status", "value": "READY", "status": "running"},
                {"label": "Clamping", "value": "1250T", "status": "neutral"},
                {"label": "CAD", "value": "STEP", "status": "running"},
            ],
            "accent": "#CC0000",
        },
        {
            "id": "dt-press-420",
            "position": [2.2, 1, -3],
            "title": "ZDC-420TPSA",
            "subtitle": "二廠主力機型",
            "rows": [
                {"label": "Status", "value": "RUNNING", "status": "running"},
                {"label": "OEE", "value": "89.1%", "status": "running"},
                {"label": "Cycle", "value": "42s", "status": "neutral"},
            ],
            "accent": "#39ff14",
        },
        {
            "id": "dt-p2-env",
            "position": [-2, 1.4, -3.8],
            "title": "二廠產線感測",
            "subtitle": "IoT · PLANT-2",
            "rows": [
                {"label": "Temp", "value": "25°C", "status": "neutral"},
                {"label": "Power", "value": "Stable", "status": "running"},
                {"label": "Load", "value": "86%", "status": "running"},
            ],
            "accent": "#00ffff",
        },
    ],
}

DEFAULT_TWINS = [
    {
        "id": "dt-generic-env",
        "position": [-1.5, 1.4, -3.5],
        "title": "環境遙測",
        "subtitle": "FACTORY IoT",
        "rows": [
            {"label": "Temp", "value": "24°C", "status": "neutral"},
            {"label": "Humidity", "value": "52%", "status": "neutral"},
            {"label": "PM2.5", "value": "Safe", "status": "running"},
        ],
        "accent": "#00ffff",
    },
]


def get_digital_twins(zone_slug: str) -> list:
    return ZONE_DIGITAL_TWINS.get(zone_slug, DEFAULT_TWINS)

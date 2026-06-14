"""各展間站點的 AR 導覽步驟設定"""


def _prefix(site_slug: str | None, path: str) -> str:
    if site_slug:
        return f"/s/{site_slug}{path}"
    return path


def get_tour_steps(site, lang: str = "zh-hant") -> list:
    slug = site.slug if site else None

    if slug == "zitai":
        return [
            {
                "num": 1,
                "title": "品牌迎賓大廳",
                "desc": "認識鋁台精機：1981 年創立，ZITAI 冷室壓鑄機行銷全球",
                "url": _prefix(slug, "/brand/"),
                "cta": "進入形象區",
            },
            {
                "num": 2,
                "title": "一廠・二廠樞紐",
                "desc": "神岡一廠、二廠環境語音導覽，溪頭路與和睦路雙廠區",
                "url": _prefix(slug, "/"),
                "cta": "首頁選廠區",
            },
            {
                "num": 3,
                "title": "生產線現場",
                "desc": "一廠一樓生產線動線實拍，點熱點查看壓鑄機型號",
                "url": _prefix(slug, "/zone/plant1-production/"),
                "cta": "進入生產線",
            },
            {
                "num": 4,
                "title": "噴塗・品管・組裝",
                "desc": "噴塗區、品管室、二樓組裝與成品庫存完整製程動線",
                "url": _prefix(slug, "/zone/plant1-coating/"),
                "cta": "製程分區",
            },
            {
                "num": 5,
                "title": "二廠生產線",
                "desc": "二廠一樓生產線與 250T、420T 主力機型展示",
                "url": _prefix(slug, "/zone/plant2-production/"),
                "cta": "進入二廠",
            },
            {
                "num": 6,
                "title": "諮詢與官網",
                "desc": "線上諮詢、索取型錄，或前往 zitai.com 產品規格",
                "url": "#more-features",
                "cta": "本頁下方",
            },
        ]

    if slug == "smart-factory":
        return [
            {
                "num": 1,
                "title": "品牌迎賓大廳" if lang == "zh-hant" else "Brand Lobby",
                "desc": "Level 1 企業識別、海報、操作指引",
                "url": _prefix(slug, "/brand/"),
                "cta": "進入形象區",
            },
            {
                "num": 2,
                "title": "360° 產線導覽",
                "desc": "五大車間 360° 環景實境",
                "url": _prefix(slug, "/zone/cnc-workshop/"),
                "cta": "CNC 車間",
            },
            {
                "num": 3,
                "title": "平面熱點",
                "desc": "點選平面圖熱點跳轉機台",
                "url": _prefix(slug, "/zone/assembly-qc/"),
                "cta": "組裝品管",
            },
            {
                "num": 4,
                "title": "3D 數位孿生",
                "desc": "機台 3D 互動與參數模擬",
                "url": _prefix(slug, "/product/cnc-5axis/"),
                "cta": "五軸加工中心",
            },
            {
                "num": 5,
                "title": "PopReal AR",
                "desc": "展會 AR 疊加體驗",
                "url": _prefix(slug, "/product/cnc-5axis/"),
                "cta": "體驗 AR",
            },
            {
                "num": 6,
                "title": "分享與諮詢",
                "desc": "社群分享、線上諮詢",
                "url": "#more-features",
                "cta": "本頁下方",
            },
        ]

    # 預設 yousi / 通用
    return [
        {
            "num": 1,
            "title": "品牌迎賓大廳" if lang == "zh-hant" else ("Brand Lobby" if lang == "en" else "ロビー"),
            "desc": "Level 1 企業識別、海報、操作指引" if lang == "zh-hant" else "Corporate identity & guides",
            "url": _prefix(slug, "/brand/"),
            "cta": "進入形象區" if lang == "zh-hant" else "Enter",
        },
        {
            "num": 2,
            "title": "360° 廠區導覽" if lang == "zh-hant" else ("360° Factory" if lang == "en" else "360°工場"),
            "desc": "Level 2 台灣廠實地 360° + 越南廠數位資產" if lang == "zh-hant" else "Taiwan 360° & Vietnam digital",
            "url": _prefix(slug, "/zone/cnc-machining/"),
            "cta": "進入 CNC 分區" if lang == "zh-hant" else "Enter zone",
        },
        {
            "num": 3,
            "title": "平面熱點導覽" if lang == "zh-hant" else ("Hotspot Map" if lang == "en" else "ホットスポット"),
            "desc": "點選平面圖黃色脈衝熱點跳轉產品" if lang == "zh-hant" else "Click pulsing hotspots on floor plan",
            "url": _prefix(slug, "/zone/assembly/"),
            "cta": "組裝線熱點" if lang == "zh-hant" else "Assembly zone",
        },
        {
            "num": 4,
            "title": "PopRealAR 3D 互動" if lang == "zh-hant" else ("PopRealAR 3D" if lang == "en" else "PopRealAR 3D"),
            "desc": "滑桿微調尺寸/角度、切換零件顏色" if lang == "zh-hant" else "Scale, angles, color simulation",
            "url": _prefix(slug, "/product/hydraulic-stem/"),
            "cta": "液壓滑角示範" if lang == "zh-hant" else "Hydraulic stem",
        },
        {
            "num": 5,
            "title": "PopReal AR 相機" if lang == "zh-hant" else ("PopReal AR" if lang == "en" else "PopReal AR"),
            "desc": "產品頁「體驗 AR」按鈕（示範連結）" if lang == "zh-hant" else "Experience AR button on product page",
            "url": _prefix(slug, "/product/hydraulic-stem/"),
            "cta": "體驗 AR" if lang == "zh-hant" else "Try AR",
        },
        {
            "num": 6,
            "title": "分享與諮詢" if lang == "zh-hant" else ("Share & Inquiry" if lang == "en" else "共有・問合せ"),
            "desc": "一鍵分享 LINE/FB、線上諮詢表單" if lang == "zh-hant" else "Social share & inquiry form",
            "url": "#more-features",
            "cta": "本頁下方" if lang == "zh-hant" else "Buttons below",
        },
    ]

"""
智慧製造工廠虛擬導覽 — 示範案例（以產線 / 設備 / 360° 廠區為主）

與 seed_showroom（零組件展間）不同，本案例模擬：
- 台灣主廠 + 越南二廠 360° 實境導覽
- CNC / 射出 / 表面處理 / 組裝 / 品管 五大車間分區
- 10 台關鍵設備（機台）一頁式介紹 + 3D / AR

執行：
  python manage.py seed_factory_demo           # 建立案例，保留原零組件展間為預設
  python manage.py seed_factory_demo --default # 建立並切換為首頁預設展間
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from showroom.factory_tour_catalog import CASE_BY_ID, DEFAULT_FACTORY_PANORAMA, panorama_for_zone
from showroom.media_utils import save_placeholder_image, save_standalone_placeholder
from showroom.models import (
    BrandPoster,
    FactoryPlant,
    GuideStep,
    Hotspot,
    Product,
    ProductCategory,
    ProductMedia,
    ShowroomLevel,
    ShowroomSite,
    Zone,
)

# 真實工廠 Matterport 360° 案例（見 factory_tour_catalog.py）
DEMO_360_MAIN = DEFAULT_FACTORY_PANORAMA
DEMO_360_WORKSHOP = CASE_BY_ID["cosinc-lab"]["embed_url"]
DEMO_AR_URL = "https://popreal.app/ar/demo"
DEMO_3D_URL = "https://modelviewer.dev/shared-assets/models/Astronaut.glb"

SITE_SLUG = "smart-factory"


class Command(BaseCommand):
    help = "建立智慧工廠虛擬導覽示範（產線 / 機台 / 360° 廠區）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--default",
            action="store_true",
            help="將此工廠案例設為網站預設展間（首頁 /tour/ 將顯示工廠版）",
        )

    def handle(self, *args, **options):
        site, _ = ShowroomSite.objects.get_or_create(
            slug=SITE_SLUG,
            defaults={
                "name": "金享智慧製造 · 虛擬工廠",
                "tagline": "Smart Factory Virtual Tour — 360° 產線實境 · 設備數位孿生",
                "description": (
                    "以台灣主廠為核心，串聯 CNC 智能制造、射出成型、表面處理、"
                    "自動組裝與品質檢驗五大車間，搭配 360° 環景與機台 3D 互動，"
                    "供海外客戶遠端驗廠與展會現場導覽。"
                ),
                "primary_color": "#1B4332",
                "accent_color": "#F4A261",
                "website_url": "https://www.yousi.com.tw",
                "contact_email": "factory-demo@yousi-showroom.local",
                "contact_phone": "+886-4-0000-0000",
                "share_title": "金享智慧製造 — 虛擬工廠導覽",
                "share_description": "360° 產線實境 · 10 台關鍵設備 · 台灣廠 + 越南廠",
                "inquiry_enabled": True,
                "is_default": False,
                "is_active": True,
            },
        )
        site.name = "金享智慧製造 · 虛擬工廠"
        site.tagline = "Smart Factory Virtual Tour — 360° 產線實境 · 設備數位孿生"
        site.primary_color = "#1B4332"
        site.accent_color = "#F4A261"
        site.is_active = True
        if options["default"]:
            ShowroomSite.objects.exclude(slug=SITE_SLUG).update(is_default=False)
            site.is_default = True
        site.save()

        save_placeholder_image(
            site, "logo", "智慧工廠", 320, 120, "branding/factory-logo", "SMART FACTORY TOUR",
        )
        save_placeholder_image(
            site, "hero_image", "虛擬工廠導覽", 1200, 480, "branding/factory-hero", "360° Production Line",
        )
        self.stdout.write(self.style.SUCCESS(f"工廠展間：{site.name}（slug={SITE_SLUG}）"))

        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@demo.local", "admin123")

        GuideStep.objects.filter(site=site).delete()
        guides = [
            ("360° 驗廠導覽", "從首頁進入各車間分區，上方為 360° 產線環景，可全螢幕環顧現場。"),
            ("平面圖跳轉機台", "車間平面圖上的熱點對應各台設備，點選進入機台詳情與 3D 模型。"),
            ("台灣廠 vs 越南廠", "Level 2 可切換台灣主廠（實地 360°）與越南二廠（數位展間）。"),
            ("設備 3D 數位孿生", "機台詳情頁可旋轉 3D 模型，模擬行程、轉速等參數（示範滑桿）。"),
            ("AR 現場疊加", "「體驗 AR」可於展會現場將機台模型疊加於實景（PopReal 示範連結）。"),
            ("遠端諮詢", "客戶可線上諮詢排程實地參訪或索取設備型錄。"),
        ]
        for i, (title, content) in enumerate(guides):
            GuideStep.objects.create(site=site, title_zh=title, content_zh=content, sort_order=i)

        # 五大車間分區（工廠動線）
        zones_data = [
            ("raw-material", "原料倉儲區", "process", "原料倉儲與 AGV 物流",
             "鋁擠型原料入庫、條碼管理、AGV 自動配送至各產線。"),
            ("cnc-workshop", "CNC 智能制造車間", "equipment", "CNC 智能制造車間",
             "五軸加工中心、走心式車床，24hr 無人化精密加工。"),
            ("injection-workshop", "射出成型車間", "equipment", "射出成型車間",
             "200T 射出機、模具溫控、自動取件，適用結構件與包覆件。"),
            ("surface-treatment", "表面處理區", "process", "表面處理區",
             "陽極染色、去毛刺機械手臂、清洗與乾燥一體線。"),
            ("assembly-qc", "組裝與品管線", "equipment", "自動組裝與品質檢驗",
             "自動鎖付組裝線、三次元 CMM、視覺 AOI 全檢。"),
        ]
        Zone.objects.filter(site=site).delete()
        zone_map = {}
        for i, (slug, name, ztype, title, summary) in enumerate(zones_data):
            pano = panorama_for_zone(slug)
            z = Zone.objects.create(
                site=site, slug=slug, name=name, zone_type=ztype,
                title_zh=title, title_en=title, summary_zh=summary, sort_order=i,
                panorama_embed_url=pano,
            )
            save_placeholder_image(z, "cover_image", name[:6], 640, 360, f"factory/zones/{slug}-cover")
            save_placeholder_image(z, "floor_plan_image", f"{title} 平面", 900, 506, f"factory/zones/{slug}-floor")
            zone_map[slug] = z

        BrandPoster.objects.filter(site=site).delete()
        for i, title in enumerate(["ISO 9001 品質認證", "智慧製造產線概況", "ESG 永續製造"]):
            poster = BrandPoster(site=site, title_zh=title, sort_order=i)
            poster.save()
            save_placeholder_image(poster, "image", title, 600, 400, f"factory/posters/{i}")

        ShowroomLevel.objects.filter(site=site).delete()
        level_lobby = ShowroomLevel.objects.create(
            site=site, level_number=1, level_type="lobby", slug="factory-lobby",
            name_zh="企業迎賓與製程概覽", name_en="Welcome & Process Overview",
            summary_zh="認識金享製造能力、品質體系與全球佈局，開始虛擬驗廠。",
            panorama_embed_url=DEMO_360_MAIN, sort_order=0,
        )
        save_placeholder_image(level_lobby, "cover_image", "迎賓大廳", 800, 450, "factory/levels/lobby")
        save_placeholder_image(level_lobby, "floor_plan_image", "L1 工廠總配置", 900, 506, "factory/levels/lobby-floor")

        level_factory = ShowroomLevel.objects.create(
            site=site, level_number=2, level_type="factory_hub", slug="dual-factory",
            name_zh="雙廠區樞紐", name_en="Taiwan & Vietnam Plants",
            summary_zh="台灣台中主廠（實地 360°）＋越南海防二廠（數位重構展間）。",
            panorama_embed_url=DEMO_360_MAIN, sort_order=1,
        )
        save_placeholder_image(level_factory, "cover_image", "雙廠區", 800, 450, "factory/levels/factory")
        save_placeholder_image(level_factory, "floor_plan_image", "L2 雙廠配置", 900, 506, "factory/levels/factory-floor")

        level_equip = ShowroomLevel.objects.create(
            site=site, level_number=3, level_type="process_deep", slug="equipment-deep",
            name_zh="關鍵設備深度展示", name_en="Key Equipment Showcase",
            summary_zh="10 台代表性機台：CNC、射出、表面處理、組裝檢測與智慧物流。",
            sort_order=2,
        )
        save_placeholder_image(level_equip, "cover_image", "設備展區", 800, 450, "factory/levels/equip")
        save_placeholder_image(level_equip, "floor_plan_image", "L3 設備配置", 900, 506, "factory/levels/equip-floor")

        FactoryPlant.objects.filter(site=site).delete()
        plant_tw = FactoryPlant.objects.create(
            site=site, level=level_factory, plant_type="taiwan", slug="taichung-main",
            name_zh="台中主廠（台灣）", name_en="Taichung Main Plant",
            description_zh="佔地 8,000㎡，CNC / 射出 / 陽極一貫化產線，實地 360° 環景導覽。",
            panorama_embed_url=DEMO_360_MAIN, sort_order=0,
        )
        save_placeholder_image(plant_tw, "cover_image", "台中主廠", 640, 360, "factory/plants/taiwan")

        vn_assets = [
            save_standalone_placeholder("越南廠 概況", 640, 360, "factory/vietnam/overview", "Haiphong Plant"),
            save_standalone_placeholder("越南 組裝線", 640, 360, "factory/vietnam/assembly", "Assembly"),
            save_standalone_placeholder("越南 倉儲", 640, 360, "factory/vietnam/warehouse", "Warehouse"),
        ]
        plant_vn = FactoryPlant.objects.create(
            site=site, level=level_factory, plant_type="vietnam", slug="haiphong-plant",
            name_zh="海防二廠（越南）", name_en="Haiphong Plant 2",
            description_zh="2022 投產，組裝與包裝為主，PPT / 空拍圖數位重構展間。",
            asset_gallery=vn_assets, sort_order=1,
        )
        save_placeholder_image(plant_vn, "cover_image", "海防二廠", 640, 360, "factory/plants/vietnam")

        ProductCategory.objects.filter(site=site).delete()
        cat_cnc = ProductCategory.objects.create(site=site, slug="cnc", name_zh="CNC 加工設備", sort_order=0)
        cat_injection = ProductCategory.objects.create(site=site, slug="injection", name_zh="射出成型設備", sort_order=1)
        cat_surface = ProductCategory.objects.create(site=site, slug="surface", name_zh="表面處理設備", sort_order=2)
        cat_assembly = ProductCategory.objects.create(site=site, slug="assembly-qc", name_zh="組裝檢測設備", sort_order=3)
        cat_logistics = ProductCategory.objects.create(site=site, slug="logistics", name_zh="智慧物流", sort_order=4)

        COLORS = ["#F4A261", "#1B4332", "#E9ECEF", "#2D6A4F"]
        equipment_data = [
            {"slug": "5-axis-cnc", "zone": "cnc-workshop", "cat": cat_cnc, "plant": plant_tw,
             "model": "VF-5/50", "name": "五軸 CNC 加工中心",
             "tagline": "複合曲面一次成型，精度 ±0.005mm",
             "summary": "立式五軸加工中心，適用鋁合金結構件、把立、座管精密加工。",
             "features": ["五軸同動", "24,000 rpm 主軸", "自動換刀 30 把", "MES 稼動監控"],
             "specs": {"工作台": "1270×508 mm", "主軸轉速": "24,000 rpm", "定位精度": "±0.005 mm"},
             "scale": (0.85, 1.15, 1.0), "joint": (0, 360, 0)},
            {"slug": "swiss-lathe", "zone": "cnc-workshop", "cat": cat_cnc, "plant": plant_tw,
             "model": "SR-32J", "name": "走心式 CNC 車床",
             "tagline": "長徑比零件一次完成，少工序",
             "summary": "走心式自動車床，專精細長軸類、油壓滑角內部零件。",
             "features": ["7 軸控制", "背向動力刀塔", "棒材自動送料", "Cpk ≥ 1.67"],
             "specs": {"最大加工徑": "32 mm", "主軸轉速": "8,000 rpm", "刀塔": "12 站"},
             "diameter": (20.0, 32.0, 25.0)},
            {"slug": "injection-200t", "zone": "injection-workshop", "cat": cat_injection, "plant": plant_tw,
             "model": "IM-200T", "name": "200T 射出成型機",
             "tagline": "結構件穩定射出，週期時間優化",
             "summary": "200 噸伺服節能射出機，搭配模溫機與機械手臂取件。",
             "features": ["伺服節能", "模內監控", "機械手臂取件", "多腔模具"],
             "specs": {"鎖模力": "200 T", "射出量": "350 cm³", "週期": "28–45 s"},
             "scale": (0.9, 1.1, 1.0)},
            {"slug": "deburr-robot", "zone": "surface-treatment", "cat": cat_surface, "plant": plant_tw,
             "model": "DBR-6AX", "name": "六軸去毛刺機械手臂",
             "tagline": "複雜內角自動去毛刺，一致性高",
             "summary": "六軸機械手臂搭配浮動銼刀，取代人工去毛刺。",
             "features": ["六軸柔性路徑", "力控浮動銼刀", "粉塵收集", "視覺定位"],
             "specs": {"臂展": "1,420 mm", "負載": "6 kg", "重複精度": "±0.02 mm"},
             "joint": (0, 180, 90)},
            {"slug": "auto-saw", "zone": "raw-material", "cat": cat_cnc, "plant": plant_tw,
             "model": "ASW-450", "name": "自動鋸切定尺機",
             "tagline": "鋁擠型自動裁切，公差 ±0.1mm",
             "summary": "自動送料 + 圓鋸裁切，對接 CNC 產線原料需求。",
             "features": ["自動定尺", "短料回收", "條碼追溯", "與 AGV 對接"],
             "specs": {"最大裁切寬": "450 mm", "定尺長度": "50–6,000 mm", "精度": "±0.1 mm"}},
            {"slug": "anodizing-line", "zone": "surface-treatment", "cat": cat_surface, "plant": plant_tw,
             "model": "ANO-LINE3", "name": "陽極處理自動線",
             "tagline": "多色陽極，批次追溯",
             "summary": "吊掛式陽極染色線，黃/藍/黑多色，符合休閒運動風配色需求。",
             "features": ["多色染色", "膜厚監控", "RoHS 合規", "水循環過濾"],
             "specs": {"槽數": "12 槽", "日產能": "8,000 pcs", "膜厚": "10–25 μm"},
             "color_note": True},
            {"slug": "cmm-inspector", "zone": "assembly-qc", "cat": cat_assembly, "plant": plant_tw,
             "model": "CMM-777", "name": "三次元量測儀",
             "tagline": "關鍵尺寸全檢，SPC 統計管制",
             "summary": "橋式 CMM，量測報告自動產出，對接 ERP 品質模組。",
             "features": ["自動報告", "SPC 連線", "溫控實驗室", "GR&R 驗證"],
             "specs": {"量測範圍": "700×700×600 mm", "精度": "1.9+L/300 μm", "探針": "TP20"},
             "diameter": (0, 100, 50)},
            {"slug": "auto-assembly", "zone": "assembly-qc", "cat": cat_assembly, "plant": plant_vn,
             "model": "ASM-L04", "name": "自動組裝產線",
             "tagline": "四工站自動鎖付，人機協作",
             "summary": "輸送帶 + 自動鎖螺絲 + 扭力監控，適用把立組立。",
             "features": ["扭力監控", "條碼綁定", "NG 自動分流", "OEE 看板"],
             "specs": {"工站數": "4", "UPH": "120 pcs", "扭力範圍": "2–8 N·m"},
             "scale": (0.8, 1.2, 1.0)},
            {"slug": "vision-aoi", "zone": "assembly-qc", "cat": cat_assembly, "plant": plant_vn,
             "model": "AOI-V3", "name": "視覺 AOI 檢測站",
             "tagline": "外觀缺陷 AI 辨識，零漏檢",
             "summary": "工業相機 + 深度學習，檢測刮傷、色差、毛邊。",
             "features": ["AI 缺陷分類", "360° 環光", "即時 NG 標記", "模型可再訓練"],
             "specs": {"相機": "5 MP × 4", "檢測時間": "< 1.2 s", "誤判率": "< 0.3%"}},
            {"slug": "agv-fleet", "zone": "raw-material", "cat": cat_logistics, "plant": plant_vn,
             "model": "AGV-M100", "name": "AGV 智慧物流車隊",
             "tagline": "產線間自動搬運，減少 WIP 等待",
             "summary": "磁條 / SLAM 雙模導航，串接 WMS 與產線叫料。",
             "features": ["SLAM 導航", "自動充電", "WMS 對接", "多車調度"],
             "specs": {"載重": "100 kg", "速度": "1.2 m/s", "續航": "8 hr"},
             "elevation": (-10, 10, 0)},
        ]

        Product.objects.filter(site=site).delete()
        product_map = {}
        for i, ed in enumerate(equipment_data):
            dia = ed.get("diameter", (0, 0, 0))
            joint = ed.get("joint", (0, 0, 0))
            elev = ed.get("elevation", (0, 0, 0))
            scale = ed.get("scale", (0.8, 1.2, 1.0))
            p = Product.objects.create(
                site=site, zone=zone_map[ed["zone"]], category=ed["cat"],
                showroom_level=level_equip, factory_plant=ed.get("plant"),
                slug=ed["slug"], name_zh=ed["name"], model_no=ed["model"],
                tagline_zh=ed["tagline"], summary_zh=ed["summary"],
                description_zh=(
                    f"{ed['summary']}\n\n"
                    "本機台為虛擬工廠示範案例，展示 360° 驗廠 + 設備 3D 互動流程。"
                    "正式上線請替換為貴司實機照片、GLB 與 qwhouse720 場景連結。"
                ),
                features_zh=ed["features"], specs=ed["specs"],
                ar_popreal_url=DEMO_AR_URL, model_3d_url=DEMO_3D_URL,
                default_color_hex="#F4A261" if ed.get("color_note") else "#2D6A4F",
                color_options=COLORS,
                scale_min=scale[0], scale_max=scale[1], scale_default=scale[2],
                diameter_min=dia[0], diameter_max=dia[1], diameter_default=dia[2],
                joint_angle_min=joint[0], joint_angle_max=joint[1], joint_angle_default=joint[2],
                elevation_angle_min=elev[0], elevation_angle_max=elev[1], elevation_angle_default=elev[2],
                ai_translation_key=f"equipment.{ed['slug']}",
                training_notes_zh=f"{ed['name']} 操作訓練：安全規範、日常點檢、異常排除（AI 問答接口預留）。",
                is_featured=True, sort_order=i, is_active=True,
            )
            save_placeholder_image(p, "cover_image", ed["model"], 480, 320, f"factory/equip/{ed['slug']}")
            save_placeholder_image(
                p, "frame_position_image", f"{ed['name']}配置", 600, 400,
                f"factory/equip/{ed['slug']}-layout",
            )
            product_map[ed["slug"]] = p

        flagship = product_map.get("5-axis-cnc")
        if flagship:
            for j, label in enumerate(["機台正面", "加工實況", "控制面板"]):
                media = ProductMedia(product=flagship, media_type="image", title=label, sort_order=j)
                media.save()
                save_placeholder_image(media, "image", label, 400, 400, f"factory/equip/{flagship.slug}-m{j}")

        Hotspot.objects.filter(zone__site=site).delete()
        hotspot_layout = {
            "raw-material": [
                ("auto-saw", 35, 45, "自動鋸切機"),
                ("agv-fleet", 68, 55, "AGV 物流"),
            ],
            "cnc-workshop": [
                ("5-axis-cnc", 30, 40, "五軸 CNC"),
                ("swiss-lathe", 62, 52, "走心車床"),
            ],
            "injection-workshop": [("injection-200t", 50, 48, "200T 射出機")],
            "surface-treatment": [
                ("deburr-robot", 38, 42, "去毛刺手臂"),
                ("anodizing-line", 65, 58, "陽極處理線"),
            ],
            "assembly-qc": [
                ("auto-assembly", 28, 38, "組裝產線"),
                ("cmm-inspector", 52, 45, "三次元量測"),
                ("vision-aoi", 72, 55, "視覺 AOI"),
            ],
        }
        for zone_slug, items in hotspot_layout.items():
            z = zone_map[zone_slug]
            for i, (prod_slug, x, y, label) in enumerate(items):
                Hotspot.objects.create(
                    zone=z, label_zh=label, hotspot_type="product",
                    pos_x=x, pos_y=y, product=product_map[prod_slug],
                    tooltip_zh=f"查看 {label}", sort_order=i, is_active=True,
                )

        self.stdout.write(self.style.SUCCESS(
            f"完成！車間 {len(zone_map)}｜機台 {len(product_map)}｜熱點 {sum(len(v) for v in hotspot_layout.values())}"
        ))
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("=== 工廠案例網址 ==="))
        base = f"http://127.0.0.1:9000/s/{SITE_SLUG}"
        self.stdout.write(f"工廠首頁：     {base}/")
        self.stdout.write(f"AR 導覽：     {base}/tour/")
        self.stdout.write(f"CNC 車間：    {base}/zone/cnc-workshop/")
        self.stdout.write(f"五軸 CNC 3D： {base}/product/5-axis-cnc/")
        if options["default"]:
            self.stdout.write(f"（已設為預設，亦可從 http://127.0.0.1:9000/ 進入）")
        else:
            self.stdout.write(f"零組件案例：  http://127.0.0.1:9000/  （原 yousi 展間仍為預設）")
            self.stdout.write("切換預設：     python manage.py seed_factory_demo --default")

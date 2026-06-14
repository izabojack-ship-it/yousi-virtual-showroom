"""
建立優思國際示範展間初始資料（含圖片、AR/3D/360 連結）
執行：python manage.py seed_showroom
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from showroom.factory_tour_catalog import DEFAULT_FACTORY_PANORAMA, panorama_for_zone
from showroom.media_utils import save_placeholder_image, save_standalone_placeholder
from showroom.models import (
    BrandPoster,
    ErpConnection,
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

# 真實工廠 Matterport 360°（見 showroom/factory_tour_catalog.py）
DEMO_360_URL = DEFAULT_FACTORY_PANORAMA
DEMO_AR_URL = "https://popreal.app/ar/demo"
DEMO_3D_URL = "https://modelviewer.dev/shared-assets/models/Astronaut.glb"
DEMO_VIDEO = "https://www.youtube.com/embed/dQw4w9WgXcQ"


class Command(BaseCommand):
    help = "建立優思國際雲端展間完整模擬示範資料"

    def handle(self, *args, **options):
        site, _ = ShowroomSite.objects.get_or_create(
            slug="yousi",
            defaults={
                "name": "優思國際 × 金享",
                "tagline": "自行車關鍵零組件沉浸式雲端虛擬展間 — Leisure Sports Virtual Showroom",
                "description": (
                    "優思國際 × 金享專注自行車關鍵零組件，透過雲端虛擬展間提供 Level 1~3 沉浸式導覽，"
                    "結合 360°、PopReal AR、Three.js 3D 數位孿生與型錄，讓海外展會客戶如臨現場。"
                ),
                "primary_color": "#1E4A8C",
                "accent_color": "#FFD100",
                "website_url": "https://www.yousi.com.tw",
                "facebook_url": "https://www.facebook.com/",
                "instagram_url": "https://www.instagram.com/",
                "linkedin_url": "https://www.linkedin.com/",
                "youtube_url": "https://www.youtube.com/",
                "line_url": "https://line.me/",
                "contact_email": "demo@yousi-showroom.local",
                "contact_phone": "+886-2-0000-0000",
                "share_title": "優思國際 × 金享 — 雲端虛擬展間",
                "share_description": "10 項關鍵零組件 1:1 數位孿生 · PopRealAR 即時互動 · 手機端零延遲",
                "inquiry_enabled": True,
                "is_default": True,
                "is_active": True,
            },
        )
        site.name = "優思國際 × 金享"
        site.primary_color = "#1E4A8C"
        site.accent_color = "#FFD100"
        site.inquiry_enabled = True
        site.is_default = True
        site.is_active = True
        site.save()
        save_placeholder_image(site, "logo", "優思×金享", 320, 120, "branding/yousi-logo", "YOUSI × JINXIANG")
        save_placeholder_image(site, "hero_image", "AR 沉浸式展間", 1200, 480, "branding/yousi-hero", "Leisure Sports Showroom")
        self.stdout.write(self.style.SUCCESS(f"展間：{site.name}（Logo / 主視覺已產生）"))

        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@demo.local", "admin123")
            self.stdout.write(self.style.SUCCESS("示範管理員：admin / admin123"))

        guides = [
            ("開始 AR 導覽", "首頁或 /tour/ 點選「開始 AR 沉浸式導覽」，依 6 步驟體驗全部功能。"),
            ("360° 空間", "進入分區後上方為 360° 嵌入，可拖曳或全螢幕瀏覽廠區實景。"),
            ("平面熱點", "平面導覽圖上黃色脈衝點為熱點，點選直達產品 PopRealAR 頁面。"),
            ("PopRealAR 3D", "產品頁可拖曳旋轉 3D 模型，滑桿微調尺寸、角度、顏色。"),
            ("體驗 AR", "產品頁「體驗 AR」開啟 PopReal 相機 AR（示範連結）。"),
            ("語系 / 分享 / 諮詢", "右上角切換中/EN/日；產品頁一鍵分享；任意頁可線上諮詢。"),
        ]
        GuideStep.objects.filter(site=site).delete()
        for i, (title, content) in enumerate(guides):
            GuideStep.objects.create(site=site, title_zh=title, content_zh=content, sort_order=i)

        zones_data = [
            ("cnc-machining", "CNC 加工中心區", "equipment", "CNC 加工中心展示區", "高精度 CNC 加工設備，適用自行車零件精密加工。"),
            ("sawing", "鋸切加工區", "process", "鋸切加工展示區", "鋁型材鋸切、定尺裁切等加工單元展示。"),
            ("deburring", "去毛刺區", "process", "去毛刺展示區", "自動去毛刺、表面處理設備。"),
            ("assembly", "組裝線區", "equipment", "組裝展示區", "自行車零件組裝與檢測設備。"),
        ]
        Zone.objects.filter(site=site).delete()
        zone_map = {}
        for i, (slug, name, ztype, title, summary) in enumerate(zones_data):
            z = Zone.objects.create(
                site=site, slug=slug, name=name, zone_type=ztype,
                title_zh=title, title_en=title, summary_zh=summary, sort_order=i,
                panorama_embed_url=panorama_for_zone(slug),
            )
            save_placeholder_image(z, "cover_image", title[:8], 640, 360, f"zones/{slug}-cover")
            save_placeholder_image(z, "floor_plan_image", f"{title} 平面圖", 900, 506, f"zones/{slug}-floor")
            zone_map[slug] = z

        BrandPoster.objects.filter(site=site).delete()
        for i, title in enumerate(["企業形象海報 A", "企業形象海報 B", "品牌識別展示"]):
            poster = BrandPoster(site=site, title_zh=title, sort_order=i)
            poster.save()
            save_placeholder_image(poster, "image", title, 600, 400, f"posters/poster-{i}")

        ShowroomLevel.objects.filter(site=site).delete()
        level_lobby = ShowroomLevel.objects.create(
            site=site, level_number=1, level_type="lobby", slug="brand-lobby",
            name_zh="品牌迎賓大廳", name_en="Brand Welcome Lobby", name_ja="ブランドロビー",
            summary_zh="優思國際 × 金享品牌識別與迎賓導覽，展開沉浸式雲端展間旅程。",
            summary_en="Brand welcome lobby — start your immersive tour.",
            panorama_embed_url=DEMO_360_URL,
            sort_order=0, ai_translation_key="level.lobby",
        )
        save_placeholder_image(level_lobby, "cover_image", "迎賓大廳", 800, 450, "levels/lobby-cover")
        save_placeholder_image(level_lobby, "floor_plan_image", "L1 全景地圖", 900, 506, "levels/lobby-floor")

        level_factory = ShowroomLevel.objects.create(
            site=site, level_number=2, level_type="factory_hub", slug="dual-plant-hub",
            name_zh="雙廠區樞紐", name_en="Dual-Plant Hub", name_ja="双工場ハブ",
            summary_zh="台灣廠實地取景與越南廠數位重構，呈現跨國製造實力。",
            summary_en="Taiwan on-site 360° and Vietnam digital reconstruction.",
            panorama_embed_url=DEMO_360_URL,
            sort_order=1, ai_translation_key="level.factory",
        )
        save_placeholder_image(level_factory, "cover_image", "雙廠區", 800, 450, "levels/factory-cover")
        save_placeholder_image(level_factory, "floor_plan_image", "L2 全景地圖", 900, 506, "levels/factory-floor")

        level_process = ShowroomLevel.objects.create(
            site=site, level_number=3, level_type="process_deep", slug="deep-process",
            name_zh="深度製程展區", name_en="Deep Process Zone", name_ja="深度工程ゾーン",
            summary_zh="管理、研發、製造、機台展示 — 完整呈現關鍵零組件製程能力。",
            summary_en="Management, R&D, manufacturing and machine showcase.",
            sort_order=2, ai_translation_key="level.process",
        )
        save_placeholder_image(level_process, "cover_image", "製程展區", 800, 450, "levels/process-cover")
        save_placeholder_image(level_process, "floor_plan_image", "L3 全景地圖", 900, 506, "levels/process-floor")

        FactoryPlant.objects.filter(site=site).delete()
        plant_tw = FactoryPlant.objects.create(
            site=site, level=level_factory, plant_type="taiwan", slug="taiwan-plant",
            name_zh="台灣廠", name_en="Taiwan Plant", name_ja="台湾工場",
            description_zh="台灣廠實地 360° 取景，展示 CNC、射出、組裝等核心產線。",
            description_en="On-site 360° tour of Taiwan manufacturing lines.",
            panorama_embed_url=DEMO_360_URL, sort_order=0, ai_translation_key="plant.taiwan",
        )
        save_placeholder_image(plant_tw, "cover_image", "台灣廠", 640, 360, "plants/taiwan-cover")

        vn_gallery = [
            save_standalone_placeholder("越南廠 PPT-1", 640, 360, "plants/vietnam/ppt-1", "Digital Rebuild"),
            save_standalone_placeholder("越南廠 PPT-2", 640, 360, "plants/vietnam/ppt-2", "Assembly Line"),
            save_standalone_placeholder("越南廠 產線", 640, 360, "plants/vietnam/line-1", "Vietnam Plant"),
        ]
        plant_vn = FactoryPlant.objects.create(
            site=site, level=level_factory, plant_type="vietnam", slug="vietnam-plant",
            name_zh="越南廠", name_en="Vietnam Plant", name_ja="ベトナム工場",
            description_zh="越南廠數位重構展間，PPT 與現場圖片資產示範（asset_gallery）。",
            description_en="Digitally reconstructed Vietnam plant with PPT and photo assets.",
            asset_gallery=vn_gallery,
            sort_order=1, ai_translation_key="plant.vietnam",
        )
        save_placeholder_image(plant_vn, "cover_image", "越南廠", 640, 360, "plants/vietnam-cover")

        ProductCategory.objects.filter(site=site).delete()
        cat_stem = ProductCategory.objects.create(site=site, slug="stem", name_zh="車把系統", sort_order=0)
        cat_headset = ProductCategory.objects.create(site=site, slug="headset", name_zh="頭碗系統", sort_order=1)
        cat_seatpost = ProductCategory.objects.create(site=site, slug="seatpost", name_zh="座管系統", sort_order=2)
        cat_injection = ProductCategory.objects.create(site=site, slug="injection", name_zh="射出系統件", sort_order=3)

        POPREAL_COLORS = ["#FFD100", "#1E4A8C", "#FFFFFF", "#2D2D2D"]
        products_data = [
            {"slug": "hydraulic-stem", "zone": "cnc-machining", "level": level_process, "plant": plant_tw,
             "cat": cat_stem, "name": "液壓滑角", "model": "JX-HS-100",
             "tagline": "精密液壓調角，騎乘姿態即時適應", "summary": "液壓滑角把立，支援多角度微調與高剛性結合。",
             "features": ["液壓阻尼調角", "7075 鋁合金鍛造", "±6° 角度微調", "PopRealAR 即時模擬"],
             "specs": {"角度範圍": "±6°", "把立長度": "90–120 mm", "重量": "168 g"},
             "video": DEMO_VIDEO,
             "diameter": (25.4, 31.8, 28.6), "angle_cut": (-6, 6, 0), "joint": (0, 90, 45)},
            {"slug": "injection-cover", "zone": "assembly", "level": level_process, "plant": plant_vn,
             "cat": cat_injection, "name": "射出系統件", "model": "JX-INJ-200",
             "tagline": "高精度射出成型，表面質感一致", "summary": "自行車關鍵射出包覆件，適用把立蓋、座管夾等。",
             "features": ["模具一體射出", "耐 UV 表面處理", "多色共射成型", "尺寸公差 ±0.05 mm"],
             "specs": {"材質": "PA66+GF30", "耐溫": "-20~80°C", "表面硬度": "2H"}},
            {"slug": "threadless-headset", "zone": "cnc-machining", "level": level_process, "plant": plant_tw,
             "cat": cat_headset, "name": "無牙頭碗", "model": "JX-TH-44",
             "tagline": "培林預壓精準，轉向順暢無異音", "summary": "內藏式無牙頭碗組，適用公路與登山車。",
             "features": ["密封培林", "陽極多色", "車架定位精準", "免工具預壓調整"],
             "specs": {"碗組規格": "1-1/8\"", "培林類型": "密封式", "重量": "92 g"},
             "diameter": (28.6, 34.0, 30.0)},
            {"slug": "aero-seatpost", "zone": "sawing", "level": level_process, "plant": plant_tw,
             "cat": cat_seatpost, "name": "空力座管", "model": "JX-SP-A350",
             "tagline": "空力截面降低風阻，夾持穩固", "summary": "空力座管搭配雙軌夾持，適用競賽級車架。",
             "features": ["空力翼面截面", "雙軌夾持", "後傾角可調", "碳纖維外觀塗裝"],
             "specs": {"直徑": "27.2 / 30.9 / 31.6 mm", "長度": "300–400 mm", "重量": "215 g"},
             "elevation": (-5, 15, 5)},
            {"slug": "quill-stem", "zone": "cnc-machining", "level": level_process, "plant": plant_tw,
             "cat": cat_stem, "name": "鵝頸把立", "model": "JX-QS-80",
             "tagline": "經典鵝頸造型，城市車首選", "summary": "鵝頸把立提供舒適騎姿，陽極多色可選。",
             "features": ["鍛造鋁合金", "多段角度", "陽極多色", "車架相對定位精準"],
             "specs": {"把立長度": "80–110 mm", "仰角": "0° / +6° / +17°", "重量": "145 g"},
             "joint": (0, 17, 6)},
            {"slug": "expander-plug", "zone": "assembly", "level": level_process, "plant": plant_vn,
             "cat": cat_stem, "name": "膨脹塞", "model": "JX-EP-28",
             "tagline": "碳纖維車把安全鎖固", "summary": "碳纖維前叉專用膨脹塞，分散夾持應力。",
             "features": ["應力分散設計", "鈦合金螺栓", "扭矩標示", "多規格適配"],
             "specs": {"適用內徑": "22.2–25.4 mm", "扭矩": "5–8 N·m", "重量": "38 g"}},
            {"slug": "seat-clamp", "zone": "deburring", "level": level_process, "plant": plant_tw,
             "cat": cat_seatpost, "name": "座管夾", "model": "JX-SC-34",
             "tagline": "單螺栓快速鎖固", "summary": "輕量座管夾，陽極黃色高辨識度。",
             "features": ["單螺栓設計", "陽極黃色標準色", "夾持力均勻", "螺紋防鬆"],
             "specs": {"夾持直徑": "34.9 mm", "重量": "28 g", "扭矩": "4–6 N·m"},
             "diameter": (30.9, 34.9, 34.9)},
            {"slug": "top-cap", "zone": "assembly", "level": level_process, "plant": plant_vn,
             "cat": cat_headset, "name": "上蓋", "model": "JX-TC-11",
             "tagline": "頭碗上蓋精密配合", "summary": "頭碗上蓋與把立蓋一體成型配合件。",
             "features": ["CNC 精密加工", "陽極多色", "Logo 雷雕", "防水密封"],
             "specs": {"規格": "1-1/8\"", "材質": "6061-T6", "重量": "12 g"}},
            {"slug": "spacer-set", "zone": "cnc-machining", "level": level_process, "plant": plant_tw,
             "cat": cat_headset, "name": "墊圈組", "model": "JX-WS-SET",
             "tagline": "把立高度精準墊高", "summary": "陽極墊圈組，多厚度組合調整把立高度。",
             "features": ["多厚度組合", "陽極同色", "倒角去毛刺", "堆疊定位精準"],
             "specs": {"厚度": "3/5/10/15 mm", "內徑": "28.6 mm", "重量": "48 g/set"}},
            {"slug": "bar-end-plug", "zone": "deburring", "level": level_process, "plant": plant_vn,
             "cat": cat_injection, "name": "把塞", "model": "JX-BEP-22",
             "tagline": "安全把塞，防止穿刺", "summary": "射出成型把塞，符合 EN 安全規範。",
             "features": ["射出一体成型", "高韌性材質", "多色可選", "快拆設計"],
             "specs": {"適用內徑": "17–22 mm", "材質": "TPR", "重量": "8 g/pair"}},
        ]

        Product.objects.filter(site=site).delete()
        product_map = {}
        for i, pd in enumerate(products_data):
            dia = pd.get("diameter", (0, 0, 0))
            ac = pd.get("angle_cut", (0, 0, 0))
            joint = pd.get("joint", (0, 0, 0))
            elev = pd.get("elevation", (0, 0, 0))
            p = Product.objects.create(
                site=site, zone=zone_map[pd["zone"]], category=pd["cat"],
                showroom_level=pd.get("level"), factory_plant=pd.get("plant"),
                slug=pd["slug"], name_zh=pd["name"], model_no=pd["model"],
                name_en=pd["name"], tagline_zh=pd["tagline"], summary_zh=pd["summary"],
                description_zh=f"{pd['summary']}\n\n本零組件為優思國際 × 金享精選展示，歡迎透過 PopRealAR 即時模擬或線上諮詢了解更多。",
                features_zh=pd["features"], specs=pd["specs"],
                has_animation=pd.get("has_animation", False),
                animation_note_zh=pd.get("animation_note", ""),
                ar_popreal_url=DEMO_AR_URL,
                model_3d_url=DEMO_3D_URL,
                hero_video_url=pd.get("video", ""),
                official_url="https://www.yousi.com.tw",
                default_color_hex="#FFD100",
                color_options=POPREAL_COLORS,
                scale_min=0.8, scale_max=1.2, scale_default=1.0,
                diameter_min=dia[0], diameter_max=dia[1], diameter_default=dia[2],
                angle_cut_min=ac[0], angle_cut_max=ac[1], angle_cut_default=ac[2],
                joint_angle_min=joint[0], joint_angle_max=joint[1], joint_angle_default=joint[2],
                elevation_angle_min=elev[0], elevation_angle_max=elev[1], elevation_angle_default=elev[2],
                ai_translation_key=f"product.{pd['slug']}",
                training_notes_zh=f"{pd['name']} 教育訓練：安裝扭矩、車架定位與品質檢驗要點（預留 AI 問答接口）。",
                is_featured=True, sort_order=i, is_active=True,
            )
            save_placeholder_image(p, "cover_image", pd["model"], 480, 320, f"products/{pd['slug']}")
            save_placeholder_image(p, "frame_position_image", f"{pd['name']}定位", 600, 400, f"products/{pd['slug']}-frame")
            product_map[pd["slug"]] = p

        flagship = product_map.get("hydraulic-stem")
        if flagship:
            for j, label in enumerate(["側視圖", "細節圖", "包裝圖"]):
                media = ProductMedia(product=flagship, media_type="image", title=label, sort_order=j)
                media.save()
                save_placeholder_image(media, "image", label, 400, 400, f"products/{flagship.slug}-media-{j}")

        Hotspot.objects.filter(zone__site=site).delete()
        hotspot_layout = {
            "cnc-machining": [
                ("hydraulic-stem", 28, 38, "液壓滑角"),
                ("threadless-headset", 62, 48, "無牙頭碗"),
                ("quill-stem", 45, 68, "鵝頸把立"),
                ("spacer-set", 72, 28, "墊圈組"),
            ],
            "sawing": [("aero-seatpost", 48, 52, "空力座管")],
            "deburring": [
                ("seat-clamp", 32, 42, "座管夾"),
                ("bar-end-plug", 68, 55, "把塞"),
            ],
            "assembly": [
                ("injection-cover", 40, 45, "射出系統件"),
                ("expander-plug", 58, 62, "膨脹塞"),
                ("top-cap", 75, 35, "上蓋"),
            ],
        }
        for zone_slug, items in hotspot_layout.items():
            z = zone_map[zone_slug]
            for i, (prod_slug, x, y, label) in enumerate(items):
                Hotspot.objects.create(
                    zone=z, label_zh=label, hotspot_type="product",
                    pos_x=x, pos_y=y, product=product_map[prod_slug],
                    tooltip_zh=f"點選查看 {label}", sort_order=i, is_active=True,
                )

        ErpConnection.objects.update_or_create(
            site=site,
            defaults={
                "name": "優思 ERP",
                "api_base_url": "http://127.0.0.1:9000",
                "products_endpoint": "/api/erp/demo-products/",
                "is_active": False,
                "field_mapping": {
                    "name_zh": "name",
                    "model_no": "model_no",
                    "summary_zh": "summary",
                    "description_zh": "description",
                },
            },
        )

        self.stdout.write(self.style.SUCCESS(
            f"完成！Level 3｜廠區 2｜分區 {len(zone_map)}｜零組件 {len(product_map)}｜熱點 10+｜全功能模擬就緒"
        ))
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("=== 立即體驗（請先 runserver 9000）==="))
        self.stdout.write("AR 導覽總入口：http://127.0.0.1:9000/tour/")
        self.stdout.write("展間首頁：     http://127.0.0.1:9000/")
        self.stdout.write("360+熱點：     http://127.0.0.1:9000/zone/cnc-machining/")
        self.stdout.write("PopRealAR 3D： http://127.0.0.1:9000/product/hydraulic-stem/")
        self.stdout.write("後台管理：     http://127.0.0.1:9000/admin/  (admin / admin123)")

"""
建立 media/intake/ 資料上傳目錄與 planning.yaml 規劃範本

執行：python manage.py setup_intake
"""
from pathlib import Path

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand

DEFAULT_PLANNING = {
    "site_slug": "yousi",
    "site": {
        "logo": "01_brand/logo.png",
        "hero_image": "01_brand/hero.jpg",
    },
    "levels": {
        "brand-lobby": {
            "floor_plan": "02_floor_plans/L1_lobby.png",
            "panorama_360": "03_panorama_360/L1_lobby.jpg",
        },
        "dual-plant-hub": {
            "floor_plan": "02_floor_plans/L2_dual_factory.png",
        },
        "deep-process": {
            "floor_plan": "02_floor_plans/L3_process.png",
        },
    },
    "plants": {
        "taiwan-plant": {
            "cover": "03_panorama_360/taiwan_cover.jpg",
            "panorama_360": "03_panorama_360/taiwan_main.jpg",
        },
        "vietnam-plant": {
            "cover": "06_vietnam/cover.jpg",
            "gallery": [
                "06_vietnam/slide_01.png",
                "06_vietnam/slide_02.png",
                "06_vietnam/slide_03.png",
            ],
        },
    },
    "zones": {
        "cnc-machining": {
            "floor_plan": "02_floor_plans/zone_cnc.png",
            "panorama_360": "03_panorama_360/zone_cnc.jpg",
        },
        "sawing": {
            "floor_plan": "02_floor_plans/zone_sawing.png",
            "panorama_360": "03_panorama_360/zone_sawing.jpg",
        },
        "deburring": {
            "floor_plan": "02_floor_plans/zone_deburring.png",
            "panorama_360": "03_panorama_360/zone_deburring.jpg",
        },
        "assembly": {
            "floor_plan": "02_floor_plans/zone_assembly.png",
            "panorama_360": "03_panorama_360/zone_assembly.jpg",
        },
    },
    "posters": [
        "01_brand/poster_01.jpg",
        "01_brand/poster_02.jpg",
    ],
    "products": {
        "hydraulic-stem": {
            "folder": "05_products/hydraulic-stem/",
            "cover": "cover.jpg",
            "frame_position": "frame.png",
            "gltf": "model.glb",
            "igs": "source.igs",
            "catalog": "catalog.pdf",
            "video": "intro.mp4",
            "gallery": ["detail_01.jpg", "detail_02.jpg"],
        },
        "injection-cover": {"folder": "05_products/injection-cover/", "cover": "cover.jpg", "gltf": "model.glb"},
        "threadless-headset": {"folder": "05_products/threadless-headset/", "cover": "cover.jpg", "gltf": "model.glb"},
        "aero-seatpost": {"folder": "05_products/aero-seatpost/", "cover": "cover.jpg", "gltf": "model.glb"},
        "quill-stem": {"folder": "05_products/quill-stem/", "cover": "cover.jpg", "gltf": "model.glb"},
        "expander-plug": {"folder": "05_products/expander-plug/", "cover": "cover.jpg", "gltf": "model.glb"},
        "seat-clamp": {"folder": "05_products/seat-clamp/", "cover": "cover.jpg", "gltf": "model.glb"},
        "top-cap": {"folder": "05_products/top-cap/", "cover": "cover.jpg", "gltf": "model.glb"},
        "spacer-set": {"folder": "05_products/spacer-set/", "cover": "cover.jpg", "gltf": "model.glb"},
        "bar-end-plug": {"folder": "05_products/bar-end-plug/", "cover": "cover.jpg", "gltf": "model.glb"},
    },
}

FOLDERS = [
    "01_brand",
    "02_floor_plans",
    "03_panorama_360",
    "04_videos",
    "06_vietnam",
    "05_products/hydraulic-stem",
    "05_products/injection-cover",
    "05_products/threadless-headset",
    "05_products/aero-seatpost",
    "05_products/quill-stem",
    "05_products/expander-plug",
    "05_products/seat-clamp",
    "05_products/top-cap",
    "05_products/spacer-set",
    "05_products/bar-end-plug",
]

README = """優思國際 × 金享 — 展間資料上傳區（Intake）
==========================================

【使用步驟】
1. 將檔案依下方資料夾放入（檔名可對照 planning.yaml）
2. 執行：python manage.py import_intake
3. 瀏覽器開啟：http://127.0.0.1:9000/plan/  查看完成度與成果

【資料夾說明】
01_brand/          Logo、主視覺、海報
02_floor_plans/    各層級 / 分區平面配置圖（PNG）
03_panorama_360/   360° 環景（JPG，比例 2:1，如 8192×4096）
04_videos/         通用影片（可選）
05_products/       各產品子資料夾（cover、model.glb、intro.mp4…）
06_vietnam/        越南廠 PPT 截圖

【360° 格式】
- 等距柱狀投影（Equirectangular），寬:高 = 2:1
- 上傳後會使用本機環景播放，不經第三方雲端

【保密】
- 檔案僅存於本機 media/intake/ 與 media/，不會自動上傳外部平台
- 正式部署方式（內網 / 雲端）待您看成果後再決定

詳細對照請編輯：planning.yaml
"""


class Command(BaseCommand):
    help = "建立 media/intake/ 上傳目錄與 planning.yaml 規劃範本"

    def handle(self, *args, **options):
        intake_root = Path(settings.MEDIA_ROOT) / "intake"
        intake_root.mkdir(parents=True, exist_ok=True)

        for folder in FOLDERS:
            (intake_root / folder).mkdir(parents=True, exist_ok=True)

        readme_path = intake_root / "README.txt"
        readme_path.write_text(README, encoding="utf-8")

        planning_path = intake_root / "planning.yaml"
        if not planning_path.is_file():
            with planning_path.open("w", encoding="utf-8") as f:
                yaml.dump(
                    DEFAULT_PLANNING,
                    f,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                )
            self.stdout.write(self.style.SUCCESS(f"已建立 {planning_path}"))
        else:
            self.stdout.write(f"保留既有 {planning_path}")

        self.stdout.write(self.style.SUCCESS(f"Intake 根目錄：{intake_root.resolve()}"))
        self.stdout.write("")
        self.stdout.write("請將真實檔案放入上述資料夾，然後執行：")
        self.stdout.write("  python manage.py import_intake")
        self.stdout.write("  開啟 http://127.0.0.1:9000/plan/")

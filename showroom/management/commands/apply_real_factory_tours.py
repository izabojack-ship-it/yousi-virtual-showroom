"""
將所有展間分區 / 廠區 / 層級的 360° 連結更新為真實工廠 Matterport 案例

執行：python manage.py apply_real_factory_tours
"""
from django.core.management.base import BaseCommand

from showroom.factory_tour_catalog import (
    CASE_BY_ID,
    DEFAULT_FACTORY_PANORAMA,
    ZONE_PANORAMA_MAP,
    panorama_for_zone,
)
from showroom.models import FactoryPlant, ShowroomLevel, ShowroomSite, Zone


class Command(BaseCommand):
    help = "更新 360° 嵌入連結為真實工廠 Matterport 案例（取代 qwhouse720 占位）"

    def handle(self, *args, **options):
        updated = 0
        for site in ShowroomSite.objects.filter(is_active=True):
            for zone in Zone.objects.filter(site=site):
                url = panorama_for_zone(zone.slug)
                if zone.panorama_embed_url != url:
                    zone.panorama_embed_url = url
                    zone.save(update_fields=["panorama_embed_url", "updated_at"])
                    updated += 1
                    case_id = ZONE_PANORAMA_MAP.get(zone.slug, "factory-show")
                    self.stdout.write(f"  分區 {zone.slug} → {CASE_BY_ID[case_id]['title_zh']}")

            for plant in FactoryPlant.objects.filter(site=site):
                url = DEFAULT_FACTORY_PANORAMA if plant.plant_type == "taiwan" else CASE_BY_ID["construction-industrial"]["embed_url"]
                if plant.panorama_embed_url != url:
                    plant.panorama_embed_url = url
                    plant.save(update_fields=["panorama_embed_url", "updated_at"])
                    updated += 1
                    self.stdout.write(f"  廠區 {plant.slug} → Matterport 已更新")

            for level in ShowroomLevel.objects.filter(site=site):
                if level.level_type == "factory_hub":
                    url = DEFAULT_FACTORY_PANORAMA
                elif level.level_type == "process_deep":
                    url = CASE_BY_ID["cosinc-lab"]["embed_url"]
                else:
                    url = DEFAULT_FACTORY_PANORAMA
                if level.panorama_embed_url != url:
                    level.panorama_embed_url = url
                    level.save(update_fields=["panorama_embed_url", "updated_at"])
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"完成，共更新 {updated} 筆 360° 連結"))
        self.stdout.write("")
        self.stdout.write("真實工廠案例總覽：http://127.0.0.1:9000/demo/factory-cases/")
        self.stdout.write("CNC 分區（設備實驗室）：http://127.0.0.1:9000/zone/cnc-machining/")
        self.stdout.write("組裝分區（工廠展）：    http://127.0.0.1:9000/zone/assembly/")

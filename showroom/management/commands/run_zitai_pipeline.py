"""
鋁台 89 張 — 完整 Industry 4.0 Pipeline

執行：
  python manage.py run_zitai_pipeline
  python manage.py run_zitai_pipeline --preset tech_strong
  python manage.py run_zitai_pipeline --source "D:\\path\\to\\photos"
  python manage.py run_zitai_pipeline --with-ai   # 需 IMAGE_PROCESSOR_URL
"""
from pathlib import Path

from django.core.management.base import BaseCommand

from showroom.pipeline.zitai_pipeline import ZitaiPipelineService
from showroom.zitai_catalog import DEFAULT_SOURCE, SITE_SLUG


class Command(BaseCommand):
    help = "鋁台完整 pipeline：HEIC 匯入 → 科技美顏 → 可選 AI → 環景 AR 索引"

    def add_arguments(self, parser):
        parser.add_argument("--source", type=str, default=str(DEFAULT_SOURCE))
        parser.add_argument(
            "--preset",
            choices=["tech_clean", "tech_strong"],
            default="tech_clean",
        )
        parser.add_argument(
            "--with-ai",
            action="store_true",
            help="呼叫 Node image-processor（需設定 IMAGE_PROCESSOR_URL）",
        )

    def handle(self, *args, **options):
        service = ZitaiPipelineService(
            source_dir=Path(options["source"]),
            enhance_preset=options["preset"],
            use_external_ai=options["with_ai"] or None,
        )
        report = service.run()

        if report.errors:
            for e in report.errors:
                self.stdout.write(self.style.WARNING(e))

        self.stdout.write(self.style.SUCCESS(
            f"Pipeline 完成 · {report.total_photos} 張 · {report.zones_updated} 分區 · {report.duration_sec:.1f}s"
        ))
        for stage in report.stages:
            self.stdout.write(f"  [{stage.stage}] {stage.count} — {stage.message}")

        self.stdout.write("")
        self.stdout.write("Pipeline 儀表板：http://127.0.0.1:9000/pipeline/")
        self.stdout.write("生產線環景：    http://127.0.0.1:9000/zone/plant1-production/")

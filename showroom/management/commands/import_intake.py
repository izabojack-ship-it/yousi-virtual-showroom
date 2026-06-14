"""
從 media/intake/ 匯入真實展間資料到資料庫

執行：python manage.py import_intake
預覽：python manage.py import_intake --dry-run
"""
from django.core.management.base import BaseCommand

from showroom.intake import import_from_intake


class Command(BaseCommand):
    help = "匯入 media/intake/ 內真實工廠資料至展間（本機 360°，清除外部占位連結）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="只檢查可匯入項目，不寫入資料庫",
        )
        parser.add_argument(
            "--keep-external-360",
            action="store_true",
            help="保留 panorama_embed_url（預設上傳本機 360 後會清空外部連結）",
        )

    def handle(self, *args, **options):
        result = import_from_intake(
            dry_run=options["dry_run"],
            use_local_360_only=not options["keep_external_360"],
        )
        if not result.get("ok"):
            self.stdout.write(self.style.ERROR(result.get("error", "匯入失敗")))
            return

        prefix = "[預覽] " if options["dry_run"] else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}展間「{result['site_name']}」匯入完成"
        ))
        self.stdout.write(
            f"  品牌 {result['site']} · 層級 {result['levels']} · "
            f"廠區 {result['plants']} · 分區 {result['zones']} · "
            f"產品 {result['products']} · 海報 {result['posters']}"
        )
        if result.get("skipped"):
            self.stdout.write(self.style.WARNING(f"  略過（找不到模型）: {', '.join(result['skipped'][:8])}"))
        self.stdout.write("")
        self.stdout.write("成果預覽：http://127.0.0.1:9000/plan/")
        self.stdout.write("展間首頁：http://127.0.0.1:9000/")

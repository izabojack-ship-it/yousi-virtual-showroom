from django.core.management.base import BaseCommand
from showroom.erp_sync import sync_products
from showroom.models import ErpConnection


class Command(BaseCommand):
    help = "從 ERP API 同步產品資料"

    def add_arguments(self, parser):
        parser.add_argument("--site", default="yousi", help="展間 slug")
        parser.add_argument("--dry-run", action="store_true", help="僅預覽不寫入")

    def handle(self, *args, **options):
        conn = ErpConnection.objects.filter(site__slug=options["site"], is_active=True).first()
        if not conn:
            self.stderr.write("找不到啟用中的 ERP 連線，請至後台設定")
            return
        log = sync_products(conn, dry_run=options["dry_run"])
        self.stdout.write(self.style.SUCCESS(log.message))

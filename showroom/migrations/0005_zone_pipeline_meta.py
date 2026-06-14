from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("showroom", "0004_zone_gallery_plant_audio"),
    ]

    operations = [
        migrations.AddField(
            model_name="zone",
            name="pipeline_meta",
            field=models.JSONField(blank=True, default=dict, verbose_name="Pipeline 狀態"),
        ),
    ]

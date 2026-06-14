from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("showroom", "0003_showroom_level_factory_plant_3d"),
    ]

    operations = [
        migrations.AddField(
            model_name="zone",
            name="audio_guide",
            field=models.FileField(
                blank=True, null=True, upload_to="zones/audio/", verbose_name="語音導覽"
            ),
        ),
        migrations.AddField(
            model_name="zone",
            name="photo_gallery",
            field=models.JSONField(blank=True, default=list, verbose_name="現場照片廊"),
        ),
        migrations.AddField(
            model_name="factoryplant",
            name="audio_guide",
            field=models.FileField(
                blank=True, null=True, upload_to="plants/audio/", verbose_name="環境語音導覽"
            ),
        ),
    ]

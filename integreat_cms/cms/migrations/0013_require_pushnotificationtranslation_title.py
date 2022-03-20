# Generated by Django 3.2.12 on 2022-03-19 12:55

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Migration file to make the title field of push notification translations required
    """

    dependencies = [
        ("cms", "0012_mediafile_file_size"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pushnotificationtranslation",
            name="title",
            field=models.CharField(max_length=250, verbose_name="title"),
        ),
    ]

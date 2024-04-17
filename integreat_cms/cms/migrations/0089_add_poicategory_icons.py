# Generated by Django 4.2.10 on 2024-03-20 17:37

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Migration file to add new POI category icons (mental health and shelter)
    """

    dependencies = [
        ("cms", "0088_rename_mt_related_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="poicategory",
            name="icon",
            field=models.CharField(
                blank=True,
                choices=[
                    ("advice", "Advice"),
                    ("culture", "Culture"),
                    ("daily_routine", "Daily routine"),
                    ("education", "Education"),
                    ("finance", "Finance"),
                    ("gastronomy", "Gastronomy"),
                    ("health", "Health"),
                    ("house", "House"),
                    ("leisure", "Leisure"),
                    ("media", "Media"),
                    ("medical_aid", "Medical aid"),
                    ("meeting_point", "Meeting point"),
                    ("mental_health", "Mental Health"),
                    ("mobility", "Mobility"),
                    ("office", "Office"),
                    ("other", "Other"),
                    ("other_help", "Other help"),
                    ("service", "Service"),
                    ("shelter", "Shelter"),
                    ("shopping", "Shopping"),
                    ("structure", "Structure"),
                ],
                help_text="Select an icon for this category",
                max_length=256,
                null=True,
                verbose_name="icon",
            ),
        ),
    ]

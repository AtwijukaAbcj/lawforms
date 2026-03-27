from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0003_netfamilypropertystatement_draft"),
    ]

    operations = [
        migrations.AddField(
            model_name="comparisonnetfamilyproperty",
            name="draft",
            field=models.JSONField(blank=True, null=True),
        ),
    ]

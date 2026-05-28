from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forms', '0015_casefile_comparisonnetfamilyproperty_case_file_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='casefile',
            name='owner',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='case_files',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]

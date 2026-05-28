from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forms', '0027_divorceorder_persons_in_court_alter_divorceorder_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicationdivorce8a',
            name='cruelty_victim_name',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
    ]

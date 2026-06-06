# Generated manually to add DivorceOrderA25A model table

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('forms', '0030_alter_form13cfinaltotals_eq_app_pos_applicant_pays_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DivorceOrderA25A',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('court_name', models.CharField(blank=True, max_length=255, null=True)),
                ('court_file_number', models.CharField(blank=True, max_length=100, null=True)),
                ('court_office_address', models.CharField(blank=True, max_length=255, null=True)),
                ('judge_name', models.CharField(blank=True, max_length=255, null=True)),
                ('judge_title', models.CharField(blank=True, max_length=255, null=True)),
                ('applicant_name', models.CharField(blank=True, max_length=255, null=True)),
                ('applicant_address', models.TextField(blank=True, null=True)),
                ('applicant_lawyer_name', models.CharField(blank=True, max_length=255, null=True)),
                ('applicant_lawyer_address', models.TextField(blank=True, null=True)),
                ('respondent_name', models.CharField(blank=True, max_length=255, null=True)),
                ('respondent_address', models.TextField(blank=True, null=True)),
                ('respondent_lawyer_name', models.CharField(blank=True, max_length=255, null=True)),
                ('respondent_lawyer_address', models.TextField(blank=True, null=True)),
                ('application_of_name', models.CharField(blank=True, max_length=255, null=True)),
                ('persons_in_court', models.TextField(blank=True, null=True)),
                ('evidence_submissions', models.TextField(blank=True, null=True)),
                ('marriage_place', models.CharField(blank=True, max_length=255, null=True)),
                ('marriage_date', models.DateField(blank=True, null=True)),
                ('divorce_effective_days', models.PositiveIntegerField(blank=True, null=True, default=31)),
                ('other_relief_details', models.TextField(blank=True, null=True)),
                ('date_of_order', models.DateField(blank=True, null=True)),
                ('date_of_signature', models.DateField(blank=True, null=True)),
                ('judge_or_clerk_signature', models.CharField(blank=True, max_length=255, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('case_file', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='divorce_order_a25as', to='forms.casefile')),
            ],
            options={
                'ordering': ['-updated_at', '-created_at'],
            },
        ),
    ]

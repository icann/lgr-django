# Generated by Django 3.1.7 on 2021-08-24 17:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import lgr_models.models.lgr
import lgr_models.models.report


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='IANAIdnTable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=lgr_models.models.lgr.get_upload_path)),
                ('name', models.CharField(max_length=128)),
                ('url', models.URLField()),
                ('date', models.DateField()),
                ('lang_script', models.CharField(max_length=16)),
                ('version', models.DecimalField(decimal_places=1, max_digits=2)),
            ],
            options={
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='IdnReviewIcannReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=lgr_models.models.report.get_upload_path)),
                ('report_id', models.CharField(max_length=256)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
# Generated by Django 3.1.7 on 2022-07-07 20:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import lgr_models.models.lgr


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('lgr_models', '0008_report_owner_nullable'),
    ]

    operations = [
        migrations.CreateModel(
            name='IDNARepertoire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=lgr_models.models.lgr.get_upload_path)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('active', models.BooleanField(default=False)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
    ]

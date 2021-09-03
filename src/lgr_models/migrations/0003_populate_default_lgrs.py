# Generated by Django 3.1.7 on 2021-08-23 16:43
import os
import re

from django.db import migrations
from django.conf import settings
from django.core.files import File

from lgr_models.models.lgr import RzLgr


def initial_data(apps, schema_editor):
    OldRzLgr: RzLgr = apps.get_model("lgr_models", "RzLgr")
    resouces_path = os.path.join(settings.BASE_DIR, 'resources')
    default_root_zones = os.path.join(resouces_path, 'idn_ref', 'root-zone')
    db_alias = schema_editor.connection.alias

    for lgr in os.listdir(default_root_zones):
        if os.path.isfile(os.path.join(default_root_zones, lgr)):
            with open(os.path.join(default_root_zones, lgr), 'rb') as f:
                fname = os.path.splitext(lgr)[0]
                name = re.sub(r'lgr-([1-9]+)-.*', r'RZ-LGR \1', fname)
                if not OldRzLgr.objects.filter(name=name).exists():
                    OldRzLgr.objects.using(db_alias).create(name=name,
                                                            file=File(f, name=lgr))

    for lgr in RzLgr.objects.all():
        lgr.save()


class Migration(migrations.Migration):
    dependencies = [
        ('lgr_models', '0002_populate_reference_lgrs'),
    ]

    operations = [
        migrations.RunPython(initial_data)
    ]
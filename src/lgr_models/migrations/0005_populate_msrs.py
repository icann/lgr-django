# -*- coding: utf-8 -*-
import os

from django.conf import settings
from django.core.files import File
from django.db import migrations


def msr_filename_to_name(msr):
    msr = os.path.splitext(msr)[0]
    if msr.startswith('idna'):
        return msr.replace('_', ' ').upper()
    if msr.startswith('msr'):
        return ' '.join(msr.split('-', 2)[:2]).upper()
    return msr


def initial_data(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    OldMSR = apps.get_model("lgr_models", "MSR")
    db_alias = schema_editor.connection.alias

    resouces_path = os.path.join(settings.BASE_DIR, 'resources')
    msr = os.path.join(resouces_path, 'idn_ref', 'msr')

    for lgr in os.listdir(msr):
        with open(os.path.join(msr, lgr), 'r') as f:
            OldMSR.objects.using(db_alias).create(name=msr_filename_to_name(lgr),
                                                  file=File(f, name=lgr))


class Migration(migrations.Migration):
    dependencies = [
        ('lgr_models', '0004_msr'),
    ]

    operations = [
        migrations.RunPython(initial_data)
    ]

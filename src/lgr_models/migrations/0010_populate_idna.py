import os

from django.conf import settings
from django.core.files import File
from django.db import migrations


def idna_filename_to_name(idna):
    idna = os.path.splitext(idna)[0]
    return idna


def initial_data(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    OldMSR = apps.get_model("lgr_models", "MSR")
    OldIDNA = apps.get_model("lgr_models", "IDNARepertoire")
    db_alias = schema_editor.connection.alias

    idnas = OldMSR.objects.using(db_alias).filter(name__contains='IDNA')

    resouces_path = os.path.join(settings.BASE_DIR, 'resources')
    idna = os.path.join(resouces_path, 'idn_ref', 'idna')

    for lgr in os.listdir(idna):
        with open(os.path.join(idna, lgr), 'r') as f:
            OldIDNA.objects.using(db_alias).create(name=idna_filename_to_name(lgr),
                                                   file=File(f, name=lgr))
    first = OldIDNA.objects.first()
    first.active = True
    first.save(update_fields=['active'])

    idnas.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('lgr_models', '0009_idna'),
    ]

    operations = [
        migrations.RunPython(initial_data)
    ]

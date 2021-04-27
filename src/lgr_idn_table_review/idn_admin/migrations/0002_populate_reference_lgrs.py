# -*- coding: utf-8 -*-
import os

from django.conf import settings
from django.core.files import File
from django.db import migrations

from lgr_idn_table_review.idn_admin.models import RefLgr, RzLgrMember

SECOND_LEVEL_LANG = {
    'lgr-second-level-arabic-language-13jan21-en.xml': 'ar-Arab',
    'lgr-second-level-arabic-script-22apr21-en.xml': 'und-Arab',
    'lgr-second-level-belarusian-17dec16-en.xml': 'bel-Cyrl',
    'lgr-second-level-bengali-script-15dec20-en.xml': 'und-Beng',
    'lgr-second-level-bosnian-cyrillic-30aug16-en.xml': 'bos-Cyrl',
    'lgr-second-level-bosnian-latin-30aug16-en.xml': 'bos-Latn',
    'lgr-second-level-bulgarian-30aug16-en.xml': 'bul-Cyrl',
    'lgr-second-level-chinese-language-15dec20-en.xml': 'zh-Hani',
    'lgr-second-level-danish-30aug16-en.xml': 'dan-Latn',
    'lgr-second-level-devanagari-script-15dec20-en.xml': 'und-Deva',
    'lgr-second-level-english-30aug16-en.xml': 'eng-Latn',
    'lgr-second-level-ethiopic-script-15dec20-en.xml': 'und-Ethi',
    'lgr-second-level-finnish-30aug16-en.xml': 'fin-Latn',
    'lgr-second-level-french-30aug16-en.xml': 'fra-Latn',
    'lgr-second-level-georgian-script-15dec20-en.xml': 'und-Geor',
    'lgr-second-level-german-30aug16-en.xml': 'deu-Latn',
    'lgr-second-level-gujarati-script-15dec20-en.xml': 'und-Gujr',
    'lgr-second-level-gurmukhi-script-15dec20-en.xml': 'und-Guru',
    'lgr-second-level-hebrew-language-22apr21-en.xml': 'he-Hebr',
    'lgr-second-level-hebrew-script-22apr21-en.xml': 'und-Hebr',
    'lgr-second-level-hindi-language-15dec20-en.xml': 'hi-Deva',
    'lgr-second-level-hungarian-30aug16-en.xml': 'hun-Latn',
    'lgr-second-level-icelandic-30aug16-en.xml': 'isl-Latn',
    'lgr-second-level-italian-30aug16-en.xml': 'ita-Latn',
    'lgr-second-level-kannada-script-15dec20-en.xml': 'und-Knda',
    'lgr-second-level-khmer-script-15dec20-en.xml': 'und-Khmr',
    'lgr-second-level-korean-30aug16-en.xml': 'kor-Hang',
    'lgr-second-level-lao-script-15dec20-en.xml': 'und-Laoo',
    'lgr-second-level-latvian-30aug16-en.xml': 'lav-Latn',
    'lgr-second-level-lithuanian-30aug16-en.xml': 'lit-Latn',
    'lgr-second-level-macedonian-30aug16-en.xml': 'mkd-Cyrl',
    'lgr-second-level-malayalam-script-15dec20-en.xml': 'und-Mlym',
    'lgr-second-level-montenegrin-30aug16-en.xml': 'mxx-Cyrl',
    'lgr-second-level-norwegian-30aug16-en.xml': 'nor-Latn',
    'lgr-second-level-oriya-script-15dec20-en.xml': 'und-Orya',
    'lgr-second-level-polish-30aug16-en.xml': 'pol-Latn',
    'lgr-second-level-portuguese-30aug16-en.xml': 'por-Latn',
    'lgr-second-level-russian-30aug16-en.xml': 'rus-Cyrl',
    'lgr-second-level-serbian-30aug16-en.xml': 'srp-Cyrl',
    'lgr-second-level-sinhala-script-22apr21-en.xml': 'und-Sinh',
    'lgr-second-level-spanish-30aug16-en.xml': 'spa-Latn',
    'lgr-second-level-swedish-30aug16-en.xml': 'swe-Latn',
    'lgr-second-level-tamil-script-15dec20-en.xml': 'und-Taml',
    'lgr-second-level-telugu-script-15dec20-en.xml': 'und-Telu',
    'lgr-second-level-thai-language-15dec20-en.xml': 'th-Thai',
    'lgr-second-level-ukrainian-17dec16-en.xml': 'ukr-Cyrl'
}


def initial_data(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    OldRefLgr = apps.get_model("idn_admin", "RefLgr")
    OldRzLgr = apps.get_model("idn_admin", "RzLgr")
    OldRzLgrMember = apps.get_model("idn_admin", "RzLgrMember")
    db_alias = schema_editor.connection.alias

    resouces_path = os.path.join(settings.BASE_DIR, 'resources')
    second_level = os.path.join(resouces_path, 'idn_ref', 'second-level-reference-lgr')
    root_zone_members = os.path.join(resouces_path, 'idn_ref', 'root-zone', 'lgr-4')
    root_zone = os.path.join(resouces_path, 'lgr')

    for lgr in os.listdir(second_level):
        with open(os.path.join(second_level, lgr), 'r') as f:
            OldRefLgr.objects.using(db_alias).create(name=os.path.splitext(lgr)[0],
                                                     language_script=SECOND_LEVEL_LANG[lgr],
                                                     file=File(f, name=lgr))

    with open(os.path.join(root_zone, 'lgr-4-common-05nov20-en.xml'), 'r') as f:
        rz_lgr = OldRzLgr.objects.using(db_alias).create(name="RZ-LGR 4",
                                                         file=File(f, name='lgr-4-common-05nov20-en.xml'))

    for lgr in os.listdir(root_zone_members):
        with open(os.path.join(root_zone_members, lgr), 'rb') as f:
            OldRzLgrMember.objects.using(db_alias).create(name=os.path.splitext(lgr)[0],
                                                          rz_lgr=rz_lgr,
                                                          file=File(f, name=lgr))

    # call save on objects with real model to populate script and language fields
    for lgr in RefLgr.objects.all():
        lgr.save()
    for lgr in RzLgrMember.objects.all():
        lgr.save()


class Migration(migrations.Migration):
    dependencies = [
        ('idn_admin', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(initial_data)
    ]

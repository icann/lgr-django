# -*- coding: utf-8 -*-
import os

from django.conf import settings
from django.core.files import File
from django.db import migrations

from lgr.utils import tag_to_language_script

SECOND_LEVEL_LANG = {
    'lgr-second-level-arabic-language-31may22-en.xml': 'ar',
    'lgr-second-level-arabic-script-31may22-en.xml': 'und-Arab',
    'lgr-second-level-armenian-script-31may22-en.xml': 'und-Armn',
    'lgr-second-level-belarusian-language-31may22-en.xml': 'be',
    'lgr-second-level-bengali-script-31may22-en.xml': 'und-Beng',
    'lgr-second-level-bosnian-cyrillic-language-31may22-en.xml': 'bs-Cyrl',
    'lgr-second-level-bosnian-latin-language-31may22-en.xml': 'bs-Latn',
    'lgr-second-level-bulgarian-language-31may22-en.xml': 'bg',
    'lgr-second-level-chinese-language-31may22-en.xml': 'zh-Hani',
    'lgr-second-level-cyrillic-script-31may22-en.xml': 'und-Cyrl',
    'lgr-second-level-danish-language-31may22-en.xml': 'da',
    'lgr-second-level-devanagari-script-31may22-en.xml': 'und-Deva',
    'lgr-second-level-english-language-31may22-en.xml': 'en',
    'lgr-second-level-ethiopic-script-31may22-en.xml': 'und-Ethi',
    'lgr-second-level-finnish-language-31may22-en.xml': 'fi',
    'lgr-second-level-french-language-31may22-en.xml': 'fr',
    'lgr-second-level-georgian-script-31may22-en.xml': 'und-Geor',
    'lgr-second-level-german-language-31may22-en.xml': 'de',
    'lgr-second-level-greek-script-31may22-en.xml': 'und-Grek',
    'lgr-second-level-gujarati-script-31may22-en.xml': 'und-Gujr',
    'lgr-second-level-gurmukhi-script-31may22-en.xml': 'und-Guru',
    'lgr-second-level-hebrew-language-31may22-en.xml': 'he',
    'lgr-second-level-hebrew-script-31may22-en.xml': 'und-Hebr',
    'lgr-second-level-hindi-language-31may22-en.xml': 'hi',
    'lgr-second-level-hungarian-language-31may22-en.xml': 'hu',
    'lgr-second-level-icelandic-language-31may22-en.xml': 'is',
    'lgr-second-level-italian-language-31may22-en.xml': 'it',
    'lgr-second-level-japanese-script-31may22-en.xml': 'und-Jpan',
    'lgr-second-level-kannada-script-31may22-en.xml': 'und-Knda',
    'lgr-second-level-khmer-script-31may22-en.xml': 'und-Khmr',
    'lgr-second-level-korean-hangul-language-31may22-en.xml': 'ko-Hang',
    'lgr-second-level-korean-script-31may22-en.xml': 'und-Kore',
    'lgr-second-level-lao-script-31may22-en.xml': 'und-Laoo',
    'lgr-second-level-latin-script-31may22-en.xml': 'und-Latn',
    'lgr-second-level-latvian-language-31may22-en.xml': 'lv',
    'lgr-second-level-lithuanian-language-31may22-en.xml': 'lt',
    'lgr-second-level-macedonian-language-31may22-en.xml': 'mk',
    'lgr-second-level-malayalam-script-31may22-en.xml': 'und-Mlym',
    'lgr-second-level-montenegrin-cyrillic-language-31may22-en.xml': 'cnr-Cyrl',
    'lgr-second-level-myanmar-script-31may22-en.xml': 'und-Mymr',
    'lgr-second-level-norwegian-language-31may22-en.xml': 'no',
    'lgr-second-level-oriya-script-31may22-en.xml': 'und-Orya',
    'lgr-second-level-polish-language-31may22-en.xml': 'pl',
    'lgr-second-level-portuguese-language-31may22-en.xml': 'pt',
    'lgr-second-level-russian-language-31may22-en.xml': 'ru',
    'lgr-second-level-serbian-cyrillic-language-31may22-en.xml': 'sr-Cyrl',
    'lgr-second-level-sinhala-script-31may22-en.xml': 'und-Sinh',
    'lgr-second-level-spanish-language-31may22-en.xml': 'es',
    'lgr-second-level-swedish-language-31may22-en.xml': 'sv',
    'lgr-second-level-tamil-script-31may22-en.xml': 'und-Taml',
    'lgr-second-level-telugu-script-31may22-en.xml': 'und-Telu',
    'lgr-second-level-thai-language-31may22-en.xml': 'th',
    'lgr-second-level-ukrainian-language-31may22-en.xml': 'uk'
}


def initial_data(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    OldRefLgr = apps.get_model("lgr_models", "RefLgr")
    db_alias = schema_editor.connection.alias

    resouces_path = os.path.join(settings.BASE_DIR, 'resources')
    second_level = os.path.join(resouces_path, 'idn_ref', 'second-level-reference-lgr')
    for lgr in os.listdir(second_level):
        if lgr == 'lgr-second-level-common-31may22-en.xml':
            continue
        with open(os.path.join(second_level, lgr), 'r') as f:
            language, script = tag_to_language_script(SECOND_LEVEL_LANG[lgr])
            OldRefLgr.objects.using(db_alias).create(name=os.path.splitext(lgr)[0],
                                                     language_script=SECOND_LEVEL_LANG[lgr],
                                                     file=File(f, name=lgr),
                                                     language=language,
                                                     script=script)


class Migration(migrations.Migration):
    dependencies = [
        ('lgr_models', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(initial_data)
    ]

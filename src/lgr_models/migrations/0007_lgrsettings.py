# Generated by Django 3.1.7 on 2022-06-02 20:02
import django.core.validators
from django.db import migrations, models

from lgr_models.models.settings import LGRSettings


def init_settings(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    OldSettings: LGRSettings = apps.get_model("lgr_models", "LGRSettings")
    db_alias = schema_editor.connection.alias

    OldSettings.objects.using(db_alias).create(variant_calculation_limit=100, variant_calculation_max=10000)


class Migration(migrations.Migration):
    dependencies = [
        ('lgr_models', '0006_add_active_field_in_rz_lgr_and_msr'),
    ]

    operations = [
        migrations.CreateModel(
            name='LGRSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variant_calculation_limit',
                 models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(2)])),
                ('variant_calculation_max',
                 models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(3)])),
            ],
        ),
        migrations.RunPython(init_settings)
    ]
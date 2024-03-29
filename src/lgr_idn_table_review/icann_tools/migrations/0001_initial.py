# Generated by Django 3.1.7 on 2022-05-27 03:35

from django.db import migrations, models
import django.db.models.deletion
import lgr_models.models.lgr


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('lgr_models', '0006_add_active_field_in_rz_lgr_and_msr'),
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
                ('lgrreport_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lgr_models.lgrreport')),
            ],
            bases=('lgr_models.lgrreport',),
        ),
    ]

# Generated by Django 3.1.14 on 2023-07-03 20:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lgr_models', '0013_auto_20230607_0412'),
    ]

    operations = [
        migrations.RenameField(
            model_name='reflgrmember',
            old_name='ref_lgr',
            new_name='common',
        ),
        migrations.RenameField(
            model_name='rzlgrmember',
            old_name='rz_lgr',
            new_name='common',
        ),
        migrations.AlterField(
            model_name='reflgrmember',
            name='name',
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name='rzlgrmember',
            name='name',
            field=models.CharField(max_length=128),
        ),
        migrations.AlterUniqueTogether(
            name='reflgrmember',
            unique_together={('name', 'common')},
        ),
        migrations.AlterUniqueTogether(
            name='rzlgrmember',
            unique_together={('name', 'common')},
        ),
    ]

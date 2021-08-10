# Generated by Django 3.1.7 on 2021-08-10 13:01

from django.db import migrations, models


def update_roles(apps, schema_editor):
    OldUser = apps.get_model('lgr_auth', 'lgruser')
    OldUser.objects.filter(role=1).update(role='Admin')
    OldUser.objects.filter(role=2).update(role='ICANN')


class Migration(migrations.Migration):

    dependencies = [
        ('lgr_auth', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lgruser',
            name='role',
            field=models.CharField(choices=[('User', 'User'), ('ICANN', 'ICANN'), ('Admin', 'Admin')], default='User',
                                   max_length=16),
        ),
        migrations.RunPython(update_roles)
    ]
# Generated by Django 5.2.1 on 2025-05-29 02:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Products', '0009_user'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='User',
            new_name='Gestionnaire',
        ),
    ]

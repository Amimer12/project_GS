# Generated by Django 5.2.1 on 2025-05-26 23:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Products', '0002_alter_variant_quantite'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variant',
            name='quantite',
            field=models.IntegerField(),
        ),
    ]

# Generated by Django 5.2.1 on 2025-06-06 20:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Orders', '0001_initial'),
        ('Products', '0011_remove_boutique_liste_produits_produit_id_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='commande',
            options={'ordering': ['-id_commande']},
        ),
        migrations.AddIndex(
            model_name='commande',
            index=models.Index(fields=['-id_commande'], name='Orders_comm_id_comm_4597f6_idx'),
        ),
        migrations.AddIndex(
            model_name='commande',
            index=models.Index(fields=['date_commande'], name='Orders_comm_date_co_dec884_idx'),
        ),
        migrations.AddIndex(
            model_name='commande',
            index=models.Index(fields=['etat_commande'], name='Orders_comm_etat_co_ff77ab_idx'),
        ),
        migrations.AddIndex(
            model_name='commande',
            index=models.Index(fields=['produit_commandé'], name='Orders_comm_produit_006477_idx'),
        ),
        migrations.AddIndex(
            model_name='sheet',
            index=models.Index(fields=['created_at'], name='Orders_shee_created_03edb1_idx'),
        ),
    ]

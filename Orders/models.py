from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from Products.models import Variant, Produit, Couleur, Taille
from django.core.exceptions import ValidationError
from decimal import Decimal
import re

# utils.py or models.py if preferred
from django import forms
from Orders.google_sheets import get_sheets_service
from datetime import datetime

def append_commande_to_sheet(commande):
    try:
        sheet_obj = Sheet.objects.first()
        if not sheet_obj or not sheet_obj.sheet_id:
            print("[✘] No sheet configured")
            return

        service = get_sheets_service()
        sheet = service.spreadsheets()
        
        # Use the correct related name 'produits' instead of 'produitcommande_set'
        produits = commande.produits.all()

        if produits.exists():
            produit_strs = []
            skus = []
            boutique_name = produits[0].produit.boutique.nom_boutique if produits[0].produit and produits[0].produit.boutique else "N/A"

            for pc in produits:
                variant = pc.get_variant()
                produit_strs.append(
                    f"{pc.produit.nom_produit}-{pc.couleur.nom_couleur}-{pc.taille.nom_taille} (x{pc.quantite})"
                )
                skus.append(variant.SKU if variant and variant.SKU else "N/A")

            produits_text = ", ".join(produit_strs)
            skus_text = ", ".join(skus)
        else:
            produits_text = "No products"
            skus_text = "N/A"
            boutique_name = "N/A"

        values = [[
            str(commande.id_commande),
            commande.date_commande.strftime('%d/%m/%Y'),
            skus_text,
            boutique_name,
            produits_text,
            commande.etat_commande,
            commande.nom_client,
            commande.numero_client,
            f"{float(commande.prix_total)} DZD",
            commande.type_livraison,
            commande.Adresse_livraison or '',
            commande.wilaya,
            commande.commune or '',
            commande.Bureau_Yalidine or '',
            commande.Bureau_ZR or ''
        ]]

        # Insert new row at position 2
        sheet.batchUpdate(
            spreadsheetId=sheet_obj.sheet_id,
            body={"requests": [{
                "insertDimension": {
                    "range": {
                        "sheetId": 0,
                        "dimension": "ROWS",
                        "startIndex": 1,
                        "endIndex": 2
                    },
                    "inheritFromBefore": False
                }
            }]}
        ).execute()

        # Write the row
        sheet.values().update(
            spreadsheetId=sheet_obj.sheet_id,
            range="A2:O2",
            valueInputOption="USER_ENTERED",
            body={'values': values}
        ).execute()

        print(f"[✔] Added commande {commande.id_commande} to sheet")
    except Exception as e:
        print(f"[✘] Erreur ajout Google Sheet: {e}")
        import traceback
        traceback.print_exc()


def update_commande_on_sheet(commande):
    try:
        sheet_obj = Sheet.objects.first()
        if not sheet_obj or not sheet_obj.sheet_id:
            print("[✘] No sheet configured")
            return

        service = get_sheets_service()
        sheet = service.spreadsheets()
        
        # Use the correct related name 'produits' instead of 'produitcommande_set'
        produits = commande.produits.all()

        if produits.exists():
            produit_strs = []
            skus = []
            boutique_name = produits[0].produit.boutique.nom_boutique if produits[0].produit and produits[0].produit.boutique else "N/A"
            for pc in produits:
                variant = pc.get_variant()
                produit_strs.append(
                    f"{pc.produit.nom_produit}-{pc.couleur.nom_couleur}-{pc.taille.nom_taille} (x{pc.quantite})"
                )
                skus.append(variant.SKU if variant and variant.SKU else "N/A")

            produits_text = ", ".join(produit_strs)
            skus_text = ", ".join(skus)
        else:
            produits_text = "No products"
            skus_text = "N/A"
            boutique_name = "N/A"

        updated_row = [
            str(commande.id_commande),
            commande.date_commande.strftime('%d/%m/%Y'),
            skus_text,
            boutique_name,
            produits_text,
            commande.etat_commande,
            commande.nom_client,
            commande.numero_client,
            f"{float(commande.prix_total)} DZD",
            commande.type_livraison,
            commande.Adresse_livraison or '',
            commande.wilaya,
            commande.commune or '',
            commande.Bureau_Yalidine or '',
            commande.Bureau_ZR or ''
        ]

        # Get all data to find the row to update
        data = sheet.values().get(
            spreadsheetId=sheet_obj.sheet_id,
            range="A2:A"
        ).execute()
        rows = data.get('values', [])

        row_found = False
        for idx, row in enumerate(rows, start=2):
            if row and str(commande.id_commande) == str(row[0]):
                sheet.values().update(
                    spreadsheetId=sheet_obj.sheet_id,
                    range=f"A{idx}:O{idx}",
                    valueInputOption="USER_ENTERED",
                    body={'values': [updated_row]}
                ).execute()
                print(f"[✔] Updated commande {commande.id_commande} in sheet")
                row_found = True
                break
        
        if not row_found:
            print(f"[!] Commande {commande.id_commande} not found in sheet, adding new row")
            append_commande_to_sheet(commande)
            
    except Exception as e:
        print(f"[✘] Erreur update Google Sheet: {e}")
        import traceback
        traceback.print_exc()

def initialize_sheet_headers(sheet_id):
    """Initialize sheet with new column order"""
    try:
        service = get_sheets_service()
        sheet = service.spreadsheets()

        # Step 1: Clear existing content
        sheet.values().clear(
            spreadsheetId=sheet_id,
            range="A:Z"
        ).execute()

        # Step 2: Add headers with correct order (15 columns)
        headers = [[
            "ID", "Date", "SKU", "Boutique", "Produit",
            "État", "Nom client", "Téléphone", "Prix total",
            "Type livraison", "Adresse", "Wilaya", "Commune",
            "Bureau Yalidine", "Bureau ZR"
        ]]

        body = {'values': headers}

        sheet.values().update(
            spreadsheetId=sheet_id,
            range="A1:O1",  # Changed from P1 to O1 (15 columns)
            valueInputOption="RAW",
            body=body
        ).execute()

        # Step 3: Format the header row (bold + colored background)
        requests = [{
            "repeatCell": {
                "range": {
                    "sheetId": 0,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 15  # 15 columns (A-O)
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": 0.2,
                            "green": 0.6,
                            "blue": 0.86
                        },
                        "textFormat": {
                            "bold": True,
                            "foregroundColor": {
                                "red": 1.0,
                                "green": 1.0,
                                "blue": 1.0
                            }
                        }
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat)"
            }
        }]

        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": requests}
        ).execute()
        
        print("[✔] Sheet headers initialized successfully")
    except Exception as e:
        print("Erreur lors de l'initialisation des en-têtes:", e)
        import traceback
        traceback.print_exc()


def export_all_commandes_to_sheet(sheet_id):
    try:
        from Orders.models import Commande
        service = get_sheets_service()
        sheet = service.spreadsheets()

        # Use select_related and prefetch_related for better performance
        commandes = Commande.objects.select_related().prefetch_related(
            'produits__produit__boutique',
            'produits__couleur',
            'produits__taille'
        ).order_by('-id_commande')

        if not commandes.exists():
            print("[!] No commandes found to export")
            return

        rows = []
        for cmd in commandes:
            # Use the correct related name 'produits'
            produits = cmd.produits.all()
            if produits.exists():
                produit_strs = []
                skus = []
                boutique_name = produits[0].produit.boutique.nom_boutique if produits[0].produit and produits[0].produit.boutique else "N/A"
                for pc in produits:
                    variant = pc.get_variant()
                    produit_strs.append(
                        f"{pc.produit.nom_produit}-{pc.couleur.nom_couleur}-{pc.taille.nom_taille} (x{pc.quantite})"
                    )
                    skus.append(variant.SKU if variant and variant.SKU else "N/A")

                produits_text = ", ".join(produit_strs)
                skus_text = ", ".join(skus)
            else:
                produits_text = "No products"
                skus_text = "N/A"
                boutique_name = "N/A"

            rows.append([
                str(cmd.id_commande),
                cmd.date_commande.strftime('%d/%m/%Y'),
                skus_text,
                boutique_name,
                produits_text,
                cmd.etat_commande,
                cmd.nom_client,
                cmd.numero_client,
                f"{float(cmd.prix_total)} DZD",
                cmd.type_livraison,
                cmd.Adresse_livraison or '',
                cmd.wilaya,
                cmd.commune or '',
                cmd.Bureau_Yalidine or '',
                cmd.Bureau_ZR or ''
            ])

        # Clear existing data (except headers)
        sheet.values().clear(
            spreadsheetId=sheet_id,
            range="A2:Z1000"
        ).execute()

        # Write all rows at once
        if rows:
            sheet.values().update(
                spreadsheetId=sheet_id,
                range="A2:O",
                valueInputOption="USER_ENTERED",
                body={'values': rows}
            ).execute()

        print(f"[✔] Exported {len(rows)} commandes")
    except Exception as e:
        print(f"[✘] Erreur export Google Sheet: {e}")
        import traceback
        traceback.print_exc()


WILAYA_CHOICES = [
    ('Adrar', 'Adrar'), ('Chlef', 'Chlef'), ('Laghouat', 'Laghouat'), ('Oum El Bouaghi', 'Oum El Bouaghi'),
    ('Batna', 'Batna'), ('Bejaia', 'Bejaia'), ('Biskra', 'Biskra'), ('Bechar', 'Bechar'),
    ('Blida', 'Blida'), ('Bouira', 'Bouira'), ('Tamanrasset', 'Tamanrasset'), ('Tebessa', 'Tebessa'),
    ('Tlemcen', 'Tlemcen'), ('Tiaret', 'Tiaret'), ('Tizi Ouzou', 'Tizi Ouzou'), ('Alger', 'Alger'),
    ('Djelfa', 'Djelfa'), ('Jijel', 'Jijel'), ('Setif', 'Setif'), ('Saida', 'Saida'),
    ('Skikda', 'Skikda'), ('Sidi Bel Abbes', 'Sidi Bel Abbes'), ('Annaba', 'Annaba'), ('Guelma', 'Guelma'),
    ('Constantine', 'Constantine'), ('Medea', 'Medea'), ('Mostaganem', 'Mostaganem'), ('Msila', 'Msila'),
    ('Mascara', 'Mascara'), ('Ouargla', 'Ouargla'), ('Oran', 'Oran'), ('El Bayadh', 'El Bayadh'),
    ('Illizi', 'Illizi'), ('Bordj Bou Arreridj', 'Bordj Bou Arreridj'), ('Boumerdes', 'Boumerdes'),
    ('El Tarf', 'El Tarf'), ('Tindouf', 'Tindouf'), ('Tissemsilt', 'Tissemsilt'), ('El Oued', 'El Oued'),
    ('Khenchela', 'Khenchela'), ('Souk Ahras', 'Souk Ahras'), ('Tipaza', 'Tipaza'), ('Mila', 'Mila'),
    ('Ain Defla', 'Ain Defla'), ('Naama', 'Naama'), ('Ain Temouchent', 'Ain Temouchent'), ('Ghardaia', 'Ghardaia'),
    ('Relizane', 'Relizane'), ('Timimoun', 'Timimoun'), ('Bordj Badji Mokhtar', 'Bordj Badji Mokhtar'),
    ('Ouled Djellal', 'Ouled Djellal'), ('Beni Abbes', 'Beni Abbes'), ('In Salah', 'In Salah'),
    ('In Guezzam', 'In Guezzam'), ('Touggourt', 'Touggourt'), ('Djanet', 'Djanet'), ('El M\'Ghair', 'El M\'Ghair'),
    ('El Menia', 'El Menia')
]


class Commande(models.Model):
    id_commande = models.AutoField(primary_key=True)
    date_commande = models.DateField(default=now)
    etat_commande = models.CharField(
        max_length=30,
        choices=[
            ("En attente", _("En attente")),
            ("Livrée", _("Livrée")),
            ("Retour", _("Retour")),
        ],
        default="En attente",
    )
    nom_client = models.CharField(max_length=100)
    numero_client = models.CharField(max_length=15)
    prix_total = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    type_livraison = models.CharField(
        max_length=30,
        choices=[
            ("Bureau", _("Bureau")),
            ("Domicile", _("Domicile")),
        ],
        default="Bureau",
    )
    Adresse_livraison = models.CharField(max_length=255, blank=True, null=True)
    wilaya = models.CharField(max_length=100, choices=WILAYA_CHOICES, default='Alger')
    commune = models.CharField(max_length=255, blank=True, null=True)
    Bureau_Yalidine = models.CharField(max_length=255, blank=True, null=True, default=None)
    Bureau_ZR = models.CharField(max_length=255, blank=True, null=True, default=None)

    class Meta:
        indexes = [models.Index(fields=['-id_commande'])]
        ordering = ['-id_commande']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Add delay to ensure related objects are saved
        if is_new:
            # Use Django's transaction.on_commit to ensure the transaction is complete
            from django.db import transaction
            transaction.on_commit(lambda: append_commande_to_sheet(self))
        else:
            from django.db import transaction
            transaction.on_commit(lambda: update_commande_on_sheet(self))


class ProduitCommande(models.Model):
    commande = models.ForeignKey("Commande", on_delete=models.CASCADE, related_name="produits")
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    couleur = models.ForeignKey(Couleur, on_delete=models.CASCADE)
    taille = models.ForeignKey(Taille, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()

    class Meta:
        unique_together = ('commande', 'produit', 'couleur', 'taille')

    def get_variant(self):
        try:
            return Variant.objects.get(
                produit=self.produit,
                couleur=self.couleur,
                taille=self.taille
            )
        except Variant.DoesNotExist:
            return None


class Sheet(models.Model):
    name = models.CharField(max_length=100, help_text="A name or label for the sheet")
    sheet_url = models.URLField(help_text="The full Google Sheets URL")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Add index for better performance
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def clean(self):
        # Ensure only one Sheet instance exists
        if not self.pk and Sheet.objects.exists():
            raise ValidationError("Seulement une Sheet est autorisée.")

    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        # Initialize sheet when created
        if is_new and self.sheet_id:
            from django.db import transaction
            transaction.on_commit(lambda: self._initialize_and_export())

    def _initialize_and_export(self):
        """Helper method to initialize and export data"""
        try:
            initialize_sheet_headers(self.sheet_id)
            export_all_commandes_to_sheet(self.sheet_id)
        except Exception as e:
            print(f"Error initializing sheet: {e}")

    def delete(self, *args, **kwargs):
        raise ValidationError("La suppression de Sheet n'est pas autorisée.")

    @property
    def sheet_id(self):
        import re
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", self.sheet_url)
        return match.group(1) if match else None

    def __str__(self):
        return self.name
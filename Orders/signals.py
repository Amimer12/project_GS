from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Commande,ProduitCommande
from Orders.google_sheets import get_sheets_service
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

@receiver(pre_delete, sender=Commande)
def handle_commande_delete(sender, instance, **kwargs):
    """
    Handle commande deletion - called BEFORE the commande is actually deleted
    """
    commande_id = instance.id_commande
    try:
        success = delete_commande_from_sheet(commande_id)
        if success:
            print(f"✓ Removed commande {commande_id} from Google Sheet")
        else:
            print(f"⚠ Could not remove commande {commande_id} from Google Sheet")
    except Exception as e:
        print(f"✗ Error removing commande {commande_id} from Google Sheet: {e}")

@receiver(pre_delete, sender=ProduitCommande)
def restore_stock_on_delete(sender, instance, **kwargs):
    variant = instance.get_variant()
    if variant:
        variant.quantite += instance.quantite
        variant.save()

    commande_id = instance.commande.id_commande if instance.commande else None
    print(f"Restored stock for produit {variant} after deleting ligne of commande {commande_id}")
    
    try:
        success = delete_commande_from_sheet(commande_id)
        if success:
            print(f"✓ Removed commande {commande_id} from Google Sheet")
        else:
            print(f"⚠ Could not remove commande {commande_id} from Google Sheet")
    except Exception as e:
        print(f"✗ Error removing commande {commande_id} from Google Sheet: {e}")


import threading
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver

_local = threading.local()

def get_old_quantities():
    if not hasattr(_local, 'old_quantities'):
        _local.old_quantities = {}
    return _local.old_quantities

@receiver(pre_save, sender=ProduitCommande)
def cache_old_quantity(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = ProduitCommande.objects.get(pk=instance.pk)
            get_old_quantities()[instance.pk] = old_instance.quantite
        except ProduitCommande.DoesNotExist:
            pass

@receiver(post_save, sender=ProduitCommande)
def update_variant_stock(sender, instance, created, **kwargs):
    variant = instance.get_variant()
    if not variant:
        return

    if created:
        variant.quantite -= instance.quantite
    else:
        old_q = get_old_quantities().pop(instance.pk, 0)
        delta = instance.quantite - old_q
        variant.quantite -= delta

    variant.save()



# utils.py (move your Google Sheets functions here)
def delete_commande_from_sheet(commande_id):
    """
    Delete a commande from Google Sheet by ID
    """
    try:
        from .models import Sheet  # Import here to avoid circular imports
        
        sheet_obj = Sheet.objects.first()
        if not sheet_obj:
            print("No sheet configured.")
            return False

        sheet_id = sheet_obj.sheet_id
        if not sheet_id:
            print("Sheet ID missing.")
            return False

        service = get_sheets_service()
        sheet = service.spreadsheets()

        # Fetch all rows from column A (where IDs are stored)
        result = sheet.values().get(
            spreadsheetId=sheet_id,
            range="A:A"
        ).execute()

        values = result.get('values', [])
        if not values:
            print("No data found in the sheet.")
            return False

        row_to_delete = None
        print(f"Looking for commande ID: {commande_id}")
        
        # Start from row 2 (index 1) since row 1 is the header
        for idx, row in enumerate(values):
            if idx == 0:  # Skip header row
                continue
                
            if row and len(row) > 0:
                cell_value = str(row[0]).strip()
                
                if cell_value == str(commande_id):
                    row_to_delete = idx + 1  # +1 because sheets are 1-indexed
                    print(f"✓ Found commande ID {commande_id} at row {row_to_delete}")
                    break

        if row_to_delete:
            # Delete the row - this automatically shifts all rows below up
            delete_request = {
                "requests": [{
                    "deleteDimension": {
                        "range": {
                            "sheetId": 0,
                            "dimension": "ROWS",
                            "startIndex": row_to_delete - 1,  # Convert to 0-based index
                            "endIndex": row_to_delete
                        }
                    }
                }]
            }
            
            response = sheet.batchUpdate(spreadsheetId=sheet_id, body=delete_request).execute()
            print(f"✓ Successfully deleted commande ID {commande_id} from Google Sheet")
            print(f"All rows below have automatically shifted up")
            return True
        else:
            print(f"✗ Commande ID {commande_id} not found in Google Sheet")
            return False

    except Exception as e:
        print(f"Error while deleting from Google Sheet: {e}")
        import traceback
        traceback.print_exc()
        return False

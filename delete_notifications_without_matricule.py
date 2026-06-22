#!/usr/bin/env python
"""
Script pour supprimer toutes les notifications qui n'ont PAS de target_matricule.
Cela nettoie les anciennes notifications générales (sans matricule cible).

Exécuter avec: python manage.py shell < delete_notifications_without_matricule.py
OU directement: python delete_notifications_without_matricule.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'estim_campus_api.settings')
django.setup()

from campus.models import Notification

print("=" * 60)
print("SCRIPT: Suppression des notifications sans target_matricule")
print("=" * 60)

# Compter les notifications à supprimer
notifications_to_delete = Notification.objects.filter(
    target_matricule__isnull=True
) | Notification.objects.filter(target_matricule='')

count = notifications_to_delete.count()
print(f"\nTrouvé {count} notifications SANS target_matricule")

if count > 0:
    print("\nDétails des notifications à supprimer:")
    for notif in notifications_to_delete[:10]:  # Afficher les 10 premières
        print(f"  - ID: {notif.id}, Type: {notif.notification_type}, Titre: {notif.title}")
    if count > 10:
        print(f"  ... et {count - 10} autres")
    
    print("\n" + "=" * 60)
    response = input("Voulez-vous VRAIMENT supprimer ces notifications? (oui/non): ")
    
    if response.lower() == 'oui':
        deleted_count, _ = notifications_to_delete.delete()
        print(f"\n✓ {deleted_count} notifications supprimées avec succès!")
    else:
        print("\nAnnulé. Aucune notification supprimée.")
else:
    print("\nAucune notification sans target_matricule trouvée. Rien à supprimer.")

print("\n" + "=" * 60)

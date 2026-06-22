#!/usr/bin/env python3
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'estim_campus_api.settings')
django.setup()

from django.db.models import Q
from campus.models import Notification

print("=" * 70)
print(" NETTOYAGE DES NOTIFICATIONS SANS TARGET_MATRICULE ")
print("=" * 70)

# Compter avant suppression
count_before = Notification.objects.filter(
    Q(target_matricule__isnull=True) | Q(target_matricule='')
).count()

print(f"\nNotifications SANS target_matricule (avant suppression): {count_before}")

# Supprimer
deleted = Notification.objects.filter(
    Q(target_matricule__isnull=True) | Q(target_matricule='')
).delete()

print(f"Notifications supprimées: {deleted[0]}")

# Compter après
count_after = Notification.objects.filter(
    Q(target_matricule__isnull=True) | Q(target_matricule='')
).count()

print(f"Notifications SANS target_matricule (après suppression): {count_after}")

# Vérifier les notifications restantes
remaining = Notification.objects.all().count()
print(f"\nTotal notifications restantes dans la base: {remaining}")

if remaining > 0:
    print("\nNotifications RESTANTES (avec target_matricule):")
    for n in Notification.objects.all().order_by('-created_at')[:10]:
        print(f"  ID: {n.id}, Type: {n.notification_type}, Matricule: {n.target_matricule}, Titre: {n.title[:50]}")

print("\n" + "=" * 70)
print(" Nettoyage terminé !")
print("=" * 70)

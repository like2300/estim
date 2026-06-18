import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'estim_campus_api.settings')
django.setup()

from campus.models import CalendrierAcademique, SiteWeb

def populate():
    print("Populating extra data...")

    # Fake data for CalendrierAcademique
    events = [
        {
            "title": "Rentrée Académique 2025-2026",
            "description": "Ouverture officielle de l'année académique pour tous les cycles.",
            "date_debut": date(2025, 10, 1),
            "is_important": True
        },
        {
            "title": "Session de Rattrapage (S1)",
            "description": "Période de rattrapage pour les étudiants ayant échoué aux examens du premier semestre.",
            "date_debut": date(2025, 3, 15),
            "date_fin": date(2025, 3, 22),
            "is_important": False
        },
        {
            "title": "Semaine Culturelle",
            "description": "Activités sportives, culturelles et conférences.",
            "date_debut": date(2025, 5, 10),
            "date_fin": date(2025, 5, 17),
            "is_important": False
        },
        {
            "title": "Examens de Fin d'Année (Session Normale)",
            "description": "Examens finaux pour tous les niveaux.",
            "date_debut": date(2025, 7, 1),
            "date_fin": date(2025, 7, 15),
            "is_important": True
        }
    ]

    for event in events:
        CalendrierAcademique.objects.get_or_create(
            title=event["title"],
            defaults={
                "description": event["description"],
                "date_debut": event["date_debut"],
                "date_fin": event.get("date_fin"),
                "is_important": event["is_important"]
            }
        )

    # SiteWeb data
    sites = [
        {
            "title": "Facebook ESTIM",
            "url": "https://www.facebook.com/estim.congo",
            "icon_name": "facebook"
        },
        {
            "title": "Portail Inscription",
            "url": "https://estim-campus.alwaysdata.net/inscription/",
            "icon_name": "how_to_reg"
        },
        {
            "title": "Site Officiel ESTIM",
            "url": "https://www.estim-congo.com",
            "icon_name": "language"
        }
    ]

    for site in sites:
        SiteWeb.objects.get_or_create(
            title=site["title"],
            defaults={
                "url": site["url"],
                "icon_name": site["icon_name"]
            }
        )

    print("Populating extra data finished!")

if __name__ == "__main__":
    populate()

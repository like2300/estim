import os
import django
import pandas as pd
import random
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'estim_campus_api.settings')
django.setup()

from campus.models import (
    Cours, Etablissement, Niveau, Filiere, 
    Resultat, SessionExamen
)

def populate():
    # 1. Create Etablissement
    etab, _ = Etablissement.objects.get_or_create(nom="ESTM Brazzaville")
    
    # 2. Process Excel for Timetable (Cours)
    excel_path = '_brazzaville.xlsx'
    try:
        # Based on my previous peek, skipping 2 rows gives the header
        df = pd.read_excel(excel_path, skiprows=2)
        # Filter out empty rows or rows that might be sub-headers
        df = df.dropna(subset=['Matière', 'Filière', 'Niveau'])
        
        day_map = {
            'Lundi': 1,
            'Mardi': 2,
            'Mercredi': 3,
            'Jeudi': 4,
            'Vendredi': 5,
            'Samedi': 6,
            'Dimanche': 7
        }

        print(f"Peuplement de la table Cours à partir de {excel_path}...")
        cours_count = 0
        for _, row in df.iterrows():
            filiere_nom = str(row['Filière']).strip()
            niveau_nom = str(row['Niveau']).strip()
            matiere = str(row['Matière']).strip()
            prof = str(row['Enseignant']).strip() if pd.notna(row['Enseignant']) else "À déterminer"
            salle = str(row['Salle']).strip() if pd.notna(row['Salle']) else "N/A"
            jour_str = str(row['Jour']).strip()
            horaire = str(row['Horaire']).strip()

            # Get or create Niveau and Filiere
            niveau, _ = Niveau.objects.get_or_create(nom=niveau_nom)
            filiere, _ = Filiere.objects.get_or_create(nom=filiere_nom)

            day_idx = day_map.get(jour_str, 1)

            Cours.objects.get_or_create(
                matiere=matiere,
                prof=prof,
                salle=salle,
                etablissement=etab,
                niveau=niveau,
                filiere=filiere,
                day_of_week=day_idx,
                heure=horaire
            )
            cours_count += 1
        print(f"Succès: {cours_count} cours ajoutés.")

    except Exception as e:
        print(f"Erreur lors de la lecture de l'Excel: {e}")

    # 3. Create dummy results with name "indisponible"
    # User requested: "pour le nom des sa ecript indisponible"
    # "don la du matricule de la de parametre app" -> likely referring to ESTIM001, 002...
    
    print("Peuplement de la table Resultat...")
    session, _ = SessionExamen.objects.get_or_create(
        nom="Examen Semestre 1 - 2025",
        defaults={'is_active': True, 'results_available': True}
    )

    matricules = ["ESTIM001", "ESTIM002", "ESTIM003", "ESTIM004", "ESTIM005"]
    for mat in matricules:
        moyenne = round(random.uniform(9.0, 18.0), 2)
        Resultat.objects.get_or_create(
            matricule=mat,
            session=session,
            defaults={
                'nom_etudiant': "indisponible", # Requested by user
                'moyenne': moyenne,
                'admis': moyenne >= 10,
                'details_notes': {
                    'Module 1': round(random.uniform(8, 18), 1),
                    'Module 2': round(random.uniform(8, 18), 1),
                    'Module 3': round(random.uniform(8, 18), 1),
                }
            }
        )
    print(f"Succès: {len(matricules)} résultats ajoutés avec le nom 'indisponible'.")

if __name__ == "__main__":
    populate()

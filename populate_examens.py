import os
import django
from datetime import date, time, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'estim_campus_api.settings')
django.setup()

from campus.models import Examen, Etablissement, Niveau, Filiere

def populate_examens():
    etabs = list(Etablissement.objects.all())
    niveaux = list(Niveau.objects.all())
    filieres = list(Filiere.objects.all())

    if not etabs or not niveaux or not filieres:
        print("Erreur: Assurez-vous d'avoir des établissements, niveaux et filières en base.")
        return

    data = [
        {
            'matiere': 'Mathématiques Discrètes',
            'type': 'Examen',
            'days_offset': 5,
            'heure': time(8, 30),
            'salle': 'Amphi A',
            'etab': etabs[0],
            'niveau': niveaux[1], # L2
            'filiere': filieres[0], # GI
        },
        {
            'matiere': 'Algorithmique & C',
            'type': 'Devoir',
            'days_offset': 2,
            'heure': time(10, 0),
            'salle': 'Labo 1',
            'etab': etabs[0],
            'niveau': niveaux[1], # L2
            'filiere': filieres[0], # GI
        },
        {
            'matiere': 'Comptabilité Générale',
            'type': 'Examen',
            'days_offset': 7,
            'heure': time(14, 0),
            'salle': 'Salle 102',
            'etab': etabs[1],
            'niveau': niveaux[2], # L3
            'filiere': filieres[1], # Gestion
        },
        {
            'matiere': 'Marketing Digital',
            'type': 'Rattrapage',
            'days_offset': 10,
            'heure': time(9, 0),
            'salle': 'Salle 204',
            'etab': etabs[0],
            'niveau': niveaux[0], # L1
            'filiere': filieres[2], # Communication
        },
        {
            'matiere': 'Management des RH',
            'type': 'Devoir',
            'days_offset': 3,
            'heure': time(11, 30),
            'salle': 'Salle 301',
            'etab': etabs[1],
            'niveau': niveaux[3], # M1
            'filiere': filieres[3], # RH
        },
        # Plus de données pour tester le filtrage
        {
            'matiere': 'Base de données SQL',
            'type': 'Examen',
            'days_offset': 6,
            'heure': time(8, 0),
            'salle': 'Amphi B',
            'etab': etabs[0],
            'niveau': niveaux[1], # L2
            'filiere': filieres[0], # GI
        },
    ]

    today = date.today()

    for item in data:
        Examen.objects.get_or_create(
            matiere=item['matiere'],
            date=today + timedelta(days=item['days_offset']),
            heure=item['heure'],
            salle=item['salle'],
            etablissement=item['etab'],
            niveau=item['niveau'],
            filiere=item['filiere'],
            type=item['type']
        )
    
    print(f"Succès: {len(data)} examens/devoirs ajoutés.")

if __name__ == "__main__":
    populate_examens()

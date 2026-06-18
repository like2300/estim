from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import Resultat, SessionExamen, Etablissement, Niveau, Filiere
from django.views.decorators.csrf import csrf_exempt
import io
import pandas as pd

def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_admin)
def dashboard_home(request):
    sessions = SessionExamen.objects.all().order_by('-created_at')
    total_students = Resultat.objects.count()
    total_sessions = SessionExamen.objects.count()
    
    context = {
        'sessions': sessions,
        'total_students': total_students,
        'total_sessions': total_sessions,
    }
    return render(request, 'dashboard/index.html', context)

@login_required
@user_passes_test(is_admin)
def dashboard_results(request):
    results = Resultat.objects.all().order_by('-created_at')[:100]
    return render(request, 'dashboard/results.html', {'results': results})

@login_required
@user_passes_test(is_admin)
def dashboard_sessions(request):
    sessions = SessionExamen.objects.all().order_by('-created_at')
    return render(request, 'dashboard/sessions.html', {'sessions': sessions})

@login_required
@user_passes_test(is_admin)
def dashboard_announcements(request):
    from .models import Annonce
    announcements = Annonce.objects.all().order_by('-date')
    return render(request, 'dashboard/announcements.html', {'announcements': announcements})

@login_required
@user_passes_test(is_admin)
def dashboard_inscriptions(request):
    from inscription.models import Inscription
    inscriptions = Inscription.objects.all().order_by('-created_at')
    return render(request, 'dashboard/inscriptions.html', {'inscriptions': inscriptions})

@login_required
@user_passes_test(is_admin)
def dashboard_schedule(request):
    from .models import Cours
    courses = Cours.objects.all().order_by('day_of_week', 'heure')
    return render(request, 'dashboard/schedule.html', {'courses': courses})

@login_required
@user_passes_test(is_admin)
def download_results_template(request):
    df = pd.DataFrame(columns=['Matricule', 'Nom', 'Moyenne', 'Admis', 'Maths', 'Anglais', 'Physique'])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultats')
    output.seek(0)
    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="template_resultats.xlsx"'
    return response

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def import_results_excel(request):
    if request.method == 'POST' and request.FILES.get('file'):
        excel_file = request.FILES['file']
        session_id = request.POST.get('session_id')
        if not session_id:
            return JsonResponse({'status': 'error', 'message': 'Veuillez sélectionner une session.'}, status=400)
        try:
            session = SessionExamen.objects.get(id=session_id)
            df = pd.read_excel(excel_file)
            count = 0
            for index, row in df.iterrows():
                matricule = str(row.get('Matricule', '')).strip()
                nom = str(row.get('Nom', '')).strip()
                moyenne = row.get('Moyenne', 0)
                admis_val = str(row.get('Admis', '')).strip().lower()
                admis = admis_val in ['oui', 'yes', 'true', '1', 'admis']
                if not matricule or not nom: continue
                details = {}
                known_cols = ['Matricule', 'Nom', 'Moyenne', 'Admis']
                for col in df.columns:
                    if col not in known_cols:
                        details[col] = str(row[col]) if pd.notnull(row[col]) else "0"
                # Mise à jour ou création pour éviter les doublons de matricule dans une session
                Resultat.objects.update_or_create(
                    matricule=matricule,
                    session=session,
                    defaults={
                        'nom_etudiant': nom,
                        'moyenne': moyenne,
                        'admis': admis,
                        'details_notes': details
                    }
                )
                count += 1
            return JsonResponse({'status': 'success', 'message': f'{count} résultats importés avec succès.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Erreur lors de l\'importation : {str(e)}'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée.'}, status=405)

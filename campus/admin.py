from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import (Annonce, Cours, CampusApp, Notification, Etablissement, 
                     Niveau, Filiere, HeroImage, Resultat, Examen, SessionExamen, Transaction, Paiement)

@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ('payer_matricule', 'target_matricule', 'amount', 'status', 'transaction_ref', 'created_at')
    list_filter = ('status', 'session')
    search_fields = ('payer_matricule', 'target_matricule', 'transaction_ref')

@admin.register(Paiement)
class PaiementAdmin(ModelAdmin):
    list_display = ('payer_matricule', 'target_matricule', 'reference', 'amount', 'created_at')
    list_filter = ('session',)
    search_fields = ('payer_matricule', 'target_matricule', 'reference')
    readonly_fields = ('created_at',)

@admin.register(SessionExamen)
class SessionExamenAdmin(ModelAdmin):
    list_display = ('nom', 'is_active', 'results_available', 'created_at')
    list_filter = ('is_active', 'results_available')

@admin.register(Examen)
class ExamenAdmin(ModelAdmin):
    list_display = ('matiere', 'type', 'date', 'heure', 'salle', 'niveau', 'etablissement')
    list_filter = ('type', 'etablissement', 'niveau', 'filiere', 'date')
    search_fields = ('matiere', 'salle')
    list_filter_sheet = True

@admin.register(Resultat)
class ResultatAdmin(ModelAdmin):
    list_display = ('matricule', 'nom_etudiant', 'session', 'moyenne', 'admis')
    list_filter = ('session', 'admis')
    search_fields = ('matricule', 'nom_etudiant')

@admin.register(Etablissement)
class EtablissementAdmin(ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)

@admin.register(Niveau)
class NiveauAdmin(ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)

@admin.register(Filiere)
class FiliereAdmin(ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)

@admin.register(Annonce)
class AnnonceAdmin(ModelAdmin):
    list_display = ('title', 'type', 'date')
    list_filter = ('type',)
    search_fields = ('title', 'description')
    # Unfold options
    compressed_fields = True  # Formulaire plus compact
    warn_unsaved_form = True  # Alerte si on quitte sans sauver

@admin.register(Cours)
class CoursAdmin(ModelAdmin):
    list_display = ('matiere', 'niveau', 'etablissement', 'day_of_week', 'heure')
    list_filter = ('etablissement', 'niveau', 'day_of_week', 'filiere')
    search_fields = ('matiere', 'prof', 'salle')
    list_filter_sheet = True # Filtres dans un panneau latéral propre

@admin.register(CampusApp)
class CampusAppAdmin(ModelAdmin):
    list_display = ('title', 'route')
    search_fields = ('title',)

@admin.register(HeroImage)
class HeroImageAdmin(ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')

@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ('title', 'is_read', 'created_at')
    list_filter = ('is_read',)
    readonly_fields = ('created_at',)

from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Inscription, FormConfig

@admin.register(Inscription)
class InscriptionAdmin(ModelAdmin):
    list_display = ('last_name', 'first_name', 'target_etablissement', 'annee_academique', 'email', 'phone', 'created_at')
    search_fields = ('last_name', 'first_name', 'email', 'phone', 'target_etablissement', 'annee_academique')
    list_filter = ('target_etablissement', 'annee_academique', 'created_at', 'sexe')

@admin.register(FormConfig)
class FormConfigAdmin(ModelAdmin):
    list_display = ('title', 'annee_academique', 'is_active')

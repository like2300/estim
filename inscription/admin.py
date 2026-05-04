import openpyxl
from django.http import HttpResponse
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Inscription, FormConfig

@admin.register(Inscription)
class InscriptionAdmin(ModelAdmin):
    list_display = ('last_name', 'first_name', 'target_etablissement', 'annee_academique', 'email', 'phone', 'created_at')
    search_fields = ('last_name', 'first_name', 'email', 'phone', 'target_etablissement', 'annee_academique')
    list_filter = ('target_etablissement', 'annee_academique', 'sexe', 'choix_cycle', 'choix_filiere', 'created_at')
    list_filter_sheet = True  # Filtres dans un panneau latéral propre (Unfold)
    change_list_template = "admin/inscription/inscription/change_list.html"
    
    # Actions standards (par sélection)
    actions = ['export_to_excel']
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('export-excel-global/', self.admin_site.admin_view(self.export_all_view), name='inscription_export_excel_global'),
        ]
        return custom_urls + urls

    def export_all_view(self, request):
        # Récupérer le queryset filtré actuel
        from django.contrib.admin.views.main import ChangeList
        
        list_display = self.get_list_display(request)
        list_display_links = self.get_list_display_links(request, list_display)
        list_filter = self.get_list_filter(request)
        search_fields = self.get_search_fields(request)
        
        cl = ChangeList(
            request, self.model, list_display, list_display_links,
            list_filter, self.date_hierarchy, search_fields,
            self.list_select_related, self.list_per_page, self.list_max_show_all,
            self.list_editable, self, self.sortable_by, self.search_help_text
        )
        queryset = cl.get_queryset(request)
        return self._generate_excel_response(queryset, filename="export_complet_filtré.xlsx")

    @admin.action(description="Exporter en Excel (Sélection)")
    def export_to_excel(self, request, queryset):
        return self._generate_excel_response(queryset)

    def export_all_to_excel(self, request):
        # Plus utilisé
        pass

    def _generate_excel_response(self, queryset, filename="inscriptions_export.xlsx"):
        # Création du classeur Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Inscriptions"

        # En-têtes
        headers = [
            'Nom', 'Prénom', 'Etablissement', 'Année', 'Date Naissance', 'Lieu Naissance',
            'Sexe', 'Nationalité', 'Téléphone', 'Email', 'Adresse', 'Tuteur', 'Tél Tuteur',
            'Série BAC', 'Année BAC', 'Etablissement BAC', 'Cycle Choisi', 'Filière principale',
            'Filière alternative', 'Date Inscription'
        ]
        ws.append(headers)

        # Données
        for obj in queryset:
            ws.append([
                obj.last_name, obj.first_name, obj.target_etablissement, obj.annee_academique,
                obj.dob.strftime('%d/%m/%Y') if obj.dob else '', obj.pob,
                obj.sexe, obj.nationalite, obj.phone, obj.email, obj.adresse, obj.tuteur, obj.tel_tuteur,
                obj.bac_serie, obj.bac_annee, obj.bac_etablissement, obj.choix_cycle, obj.choix_filiere,
                obj.alternative_filiere, obj.created_at.strftime('%d/%m/%Y %H:%M')
            ])

        # Préparation de la réponse HTTP
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response

@admin.register(FormConfig)
class FormConfigAdmin(ModelAdmin):
    list_display = ('title', 'annee_academique', 'is_active')

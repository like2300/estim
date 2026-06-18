from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (AnnonceViewSet, CoursViewSet, CampusAppViewSet,
                        NotificationViewSet, EtablissementViewSet,
                        NiveauViewSet, FiliereViewSet, HeroImageViewSet, 
                        ResultatViewSet, ExamenViewSet, SessionExamenViewSet, 
                        TransactionViewSet, PaiementViewSet, CalendrierAcademiqueViewSet, SiteWebViewSet)
from .dashboard_views import (dashboard_home, import_results_excel, download_results_template,
                              dashboard_results, dashboard_sessions, dashboard_announcements, 
                              dashboard_inscriptions, dashboard_schedule)

router = DefaultRouter()
router.register(r'annonces', AnnonceViewSet)
router.register(r'cours', CoursViewSet)
router.register(r'examens', ExamenViewSet)
router.register(r'apps', CampusAppViewSet)
router.register(r'hero', HeroImageViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'resultats', ResultatViewSet)
router.register(r'sessions', SessionExamenViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'paiements', PaiementViewSet)
router.register(r'calendrier', CalendrierAcademiqueViewSet)
router.register(r'sites-web', SiteWebViewSet)

router.register(r'etablissements', EtablissementViewSet)
router.register(r'niveaux', NiveauViewSet)
router.register(r'filieres', FiliereViewSet)

urlpatterns = [
    path('callback/', TransactionViewSet.as_view({'post': 'webhook'})),
    path('callback', TransactionViewSet.as_view({'post': 'webhook'})),
    
    # Dashboard Modern UI
    path('dashboard/', dashboard_home, name='dashboard_home'),
    path('dashboard/results/', dashboard_results, name='dashboard_results'),
    path('dashboard/sessions/', dashboard_sessions, name='dashboard_sessions'),
    path('dashboard/announcements/', dashboard_announcements, name='dashboard_announcements'),
    path('dashboard/inscriptions/', dashboard_inscriptions, name='dashboard_inscriptions'),
    path('dashboard/schedule/', dashboard_schedule, name='dashboard_schedule'),
    path('dashboard/import/', import_results_excel, name='import_results_excel'),
    path('dashboard/template/', download_results_template, name='download_results_template'),
    
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (AnnonceViewSet, CoursViewSet, CampusAppViewSet,
                        NotificationViewSet, EtablissementViewSet,
                        NiveauViewSet, FiliereViewSet, HeroImageViewSet, 
                        ResultatViewSet, ExamenViewSet, SessionExamenViewSet, TransactionViewSet)

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

router.register(r'etablissements', EtablissementViewSet)
router.register(r'niveaux', NiveauViewSet)
router.register(r'filieres', FiliereViewSet)

urlpatterns = [
    path('callback/', TransactionViewSet.as_view({'post': 'webhook'})),
    path('callback', TransactionViewSet.as_view({'post': 'webhook'})),
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InscriptionViewSet, inscription_form

router = DefaultRouter()
router.register(r'inscriptions', InscriptionViewSet)

urlpatterns = [
    path('', inscription_form, name='inscription_form'),
    path('api/', include(router.urls)),
]

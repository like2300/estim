from rest_framework import serializers
from .models import (Annonce, Cours, CampusApp, Notification, Etablissement, 
                     Niveau, Filiere, HeroImage, Resultat, Examen, SessionExamen, 
                     Transaction, Paiement)

class EtablissementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Etablissement
        fields = '__all__'

class NiveauSerializer(serializers.ModelSerializer):
    class Meta:
        model = Niveau
        fields = '__all__'

class FiliereSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filiere
        fields = '__all__'

class AnnonceSerializer(serializers.ModelSerializer):
    image_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Annonce
        fields = '__all__'

    def get_image_display(self, obj):
        image_url = obj.get_image_url
        if not image_url:
            return None
            
        request = self.context.get('request')
        if image_url.startswith('http'):
            return image_url
            
        if request:
            return request.build_absolute_uri(image_url)
            
        return image_url # Fallback to relative if no request context

class CoursSerializer(serializers.ModelSerializer):
    etablissement = serializers.StringRelatedField()
    niveau = serializers.StringRelatedField()
    filiere = serializers.StringRelatedField()
    
    class Meta:
        model = Cours
        fields = '__all__'

class CampusAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampusApp
        fields = '__all__'

class SessionExamenSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionExamen
        fields = "__all__"


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"


class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = "__all__"


class ResultatSerializer(serializers.ModelSerializer):
    session_nom = serializers.CharField(source="session.nom", read_only=True)

    class Meta:
        model = Resultat
        fields = "__all__"

class HeroImageSerializer(serializers.ModelSerializer):
    image_display = serializers.SerializerMethodField()
    class Meta:
        model = HeroImage
        fields = '__all__'
    def get_image_display(self, obj):
        image_url = obj.get_image_url
        if not image_url: return None
        request = self.context.get('request')
        if image_url.startswith('http'): return image_url
        if request: return request.build_absolute_uri(image_url)
        return image_url

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class ExamenSerializer(serializers.ModelSerializer):
    etablissement = serializers.StringRelatedField()
    niveau = serializers.StringRelatedField()
    filiere = serializers.StringRelatedField()
    
    class Meta:
        model = Examen
        fields = '__all__'

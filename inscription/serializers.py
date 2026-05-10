from rest_framework import serializers
from django.conf import settings
from .models import Inscription

class InscriptionSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()

    class Meta:
        model = Inscription
        fields = '__all__'

    def get_photo(self, obj):
        if not obj.photo:
            return None
            
        photo_url = obj.photo.url
        if photo_url.startswith('http'):
            return photo_url.replace('http://', 'https://') if 'alwaysdata.net' in photo_url else photo_url
            
        request = self.context.get('request')
        if request:
            full_url = request.build_absolute_uri(photo_url)
            if 'alwaysdata.net' in full_url:
                full_url = full_url.replace('http://', 'https://')
            return full_url
            
        return f"https://estim-campus.alwaysdata.net{photo_url}"

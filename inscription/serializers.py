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
        
        request = self.context.get('request')
        photo_url = obj.photo.url
        
        if request:
            full_url = request.build_absolute_uri(photo_url)
            # Force HTTPS in production if behind a proxy
            if not settings.DEBUG and full_url.startswith('http://'):
                full_url = full_url.replace('http://', 'https://')
            return full_url
            
        return photo_url

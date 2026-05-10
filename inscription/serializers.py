from rest_framework import serializers
from django.conf import settings
from .models import Inscription

class InscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscription
        fields = '__all__'

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.photo:
            photo_url = instance.photo.url
            request = self.context.get('request')
            if request:
                full_url = request.build_absolute_uri(photo_url)
                if 'alwaysdata.net' in full_url:
                    full_url = full_url.replace('http://', 'https://')
                ret['photo'] = full_url
            else:
                ret['photo'] = f"https://estim-campus.alwaysdata.net{photo_url}"
        return ret

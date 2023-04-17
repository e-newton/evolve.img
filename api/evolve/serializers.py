from rest_framework import serializers
from .models import EvolveRequest

class EvolveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvolveRequest
        fields = ('id', 'image', 'object', 'finished_generating', 'evolved_image')

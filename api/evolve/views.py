from django.shortcuts import render
from rest_framework import viewsets
from .serializers import EvolveRequestSerializer
from .models import EvolveRequest

# Create your views here.


# Create your views here.

# Post request
class EvolveRequestView(viewsets.mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = EvolveRequestSerializer
    queryset = EvolveRequest.objects.all()

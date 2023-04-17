from django.contrib import admin
from .models import EvolveRequest

class EvolveAdmin(admin.ModelAdmin):
    list_display = ('id', 'image')

# Register your models here.

admin.site.register(EvolveRequest, EvolveAdmin)

# Register your models here.

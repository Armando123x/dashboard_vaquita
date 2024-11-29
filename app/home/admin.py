from django.contrib import admin

from .models import Server, Station, StationData, StationDataPhoto, StationCommand

# Se registra los modelos en admin.py
admin.site.register(Server)
admin.site.register(Station)
admin.site.register(StationData)
admin.site.register(StationDataPhoto)
admin.site.register(StationCommand)
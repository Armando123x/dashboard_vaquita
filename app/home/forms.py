from django import forms
from .models import Station


class StationForm(forms.ModelForm):
    class Meta:
        model = Station
        fields = '__all__'  # Incluye todos los campos del modelo


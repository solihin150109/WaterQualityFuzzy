from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import WaterQualityMeasurement, Location

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'latitude', 'longitude', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class WaterQualityMeasurementForm(forms.ModelForm):
    class Meta:
        model = WaterQualityMeasurement
        fields = [
            'location', 'ph', 'do', 'bod', 'cod', 'total_coliform'
        ]

    ph = forms.FloatField(
        min_value=0, max_value=14.9,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    do = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1'})
    )
    bod = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    cod = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1'})
    )
    total_coliform = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].empty_label = "Pilih Lokasi..."
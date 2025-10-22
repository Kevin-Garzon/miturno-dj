from django import forms
from django.contrib.auth.models import User
from .models import Cliente, Empresa

class RegistroClienteForm(forms.ModelForm):
    username = forms.CharField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput)
    email = forms.EmailField()

    class Meta:
        model = Cliente
        fields = ['telefono']

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre_negocio', 'direccion', 'telefono']
        widgets = {
            'nombre_negocio': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary',
                'placeholder': 'Nombre del negocio'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary',
                'placeholder': 'Dirección'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary',
                'placeholder': 'Teléfono'
            }),
        }
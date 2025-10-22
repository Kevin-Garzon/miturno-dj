from django import forms
from django.contrib.auth.models import User
from .models import Cliente, Empresa, Servicio

class RegistroClienteForm(forms.ModelForm):
    username = forms.CharField(max_length=50, label="Usuario")
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")
    email = forms.EmailField(label="Correo electrónico")

    class Meta:
        model = Cliente
        fields = ['telefono']
        labels = {'telefono': 'Teléfono'}

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

class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['nombre', 'descripcion', 'duracion', 'precio', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary',
                'placeholder': 'Nombre del servicio'
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary resize-none',
                'placeholder': 'Descripción (opcional)'
            }),
            'duracion': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary',
                'placeholder': 'Duración en minutos'
            }),
            'precio': forms.NumberInput(attrs={
                'step': '0.01',
                'class': 'w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary',
                'placeholder': 'Precio del servicio'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary focus:ring-primary rounded border-gray-300'
            }),
        }
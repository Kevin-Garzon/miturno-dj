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

class RegistroEmpresaForm(forms.ModelForm):
    username = forms.CharField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput)
    email = forms.EmailField()

    class Meta:
        model = Empresa
        fields = ['nombre_negocio', 'direccion', 'telefono']

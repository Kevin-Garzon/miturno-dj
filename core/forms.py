from django import forms
from django.contrib.auth.models import User
from .models import Cliente, Empresa, Servicio
import re

# Formulario de registro para Cliente
class RegistroClienteForm(forms.ModelForm):
    username = forms.CharField(max_length=50, label="Usuario")
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")
    email = forms.EmailField(label="Correo electrónico")

    class Meta:
        model = Cliente
        fields = ['telefono']
        labels = {'telefono': 'Teléfono'}

    # --- VALIDACIONES ---
    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        patron = r'^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s]+$'
        if not re.match(patron, username):
            raise forms.ValidationError(
                "El usuario solo puede contener letras y espacios (sin números ni símbolos)."
            )
        return username

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono'].strip()
        if not telefono.isdigit():
            raise forms.ValidationError("El teléfono solo puede contener números.")
        return telefono

# Formulario para editar perfil de Cliente
class EditarClienteForm(forms.ModelForm):
    username = forms.CharField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = Cliente
        fields = ['telefono']

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        patron = r'^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s]+$'
        if not re.match(patron, username):
            raise forms.ValidationError(
                "El nombre de usuario solo puede contener letras y espacios (sin números ni símbolos)."
            )
        return username

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono'].strip()
        if not telefono.isdigit():
            raise forms.ValidationError("El teléfono solo puede contener números.")
        return telefono

# Formulario para editar Empresa
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

    # --- VALIDACIONES ---
    def clean_nombre_negocio(self):
        nombre = self.cleaned_data['nombre_negocio'].strip()
        # Debe tener al menos una letra; no permitir solo números/símbolos
        if not any(c.isalpha() for c in nombre):
            raise forms.ValidationError(
                "El nombre del negocio debe incluir letras; no puede ser solo números o símbolos."
            )
        return nombre

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono'].strip()
        if not telefono.isdigit():
            raise forms.ValidationError("El teléfono solo puede contener números.")
        return telefono

# Formulario para crear/editar Servicio
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

    # --- VALIDACIONES ---
    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        if not any(c.isalpha() for c in nombre):
            raise forms.ValidationError(
                "El nombre del servicio debe incluir letras; no puede ser solo números o símbolos."
            )
        return nombre
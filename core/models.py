from django.db import models
from django.contrib.auth.models import User

# Cliente (usuario final)
class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=15)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


# Empresa / Barbería
class Empresa(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre_negocio = models.CharField(max_length=100)
    direccion = models.CharField(max_length=150)
    telefono = models.CharField(max_length=15)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_negocio

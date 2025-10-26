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

# Servicio ofrecido por la empresa
class Servicio(models.Model):
    empresa = models.ForeignKey('Empresa', on_delete=models.CASCADE, related_name='servicios')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    duracion = models.PositiveIntegerField(help_text="Duración en minutos")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.nombre} ({self.empresa.nombre_negocio})"
    

# Disponibilidad semanal por día 
class Disponibilidad(models.Model):
    DIAS_SEMANA = [
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado'),
        ('domingo', 'Domingo'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='disponibilidades')
    dia = models.CharField(max_length=10, choices=DIAS_SEMANA, unique=True)

    # Jornada de la mañana
    hora_inicio_m = models.TimeField(blank=True, null=True)
    hora_fin_m = models.TimeField(blank=True, null=True)
    # Jornada de la tarde
    hora_inicio_t = models.TimeField(blank=True, null=True)
    hora_fin_t = models.TimeField(blank=True, null=True)

    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.get_dia_display()} (M: {self.hora_inicio_m}-{self.hora_fin_m} / T: {self.hora_inicio_t}-{self.hora_fin_t})"

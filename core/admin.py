from django.contrib import admin
from .models import Cliente, Empresa, Servicio, Disponibilidad

admin.site.register(Cliente)
admin.site.register(Empresa)

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'precio', 'duracion', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'empresa')
    search_fields = ('nombre', 'empresa__nombre_negocio')

@admin.register(Disponibilidad)
class DisponibilidadAdmin(admin.ModelAdmin):
    list_display = (
        'empresa',
        'dia',
        'hora_inicio_m',
        'hora_fin_m',
        'hora_inicio_t',
        'hora_fin_t',
        'activo',
    )
    list_filter = ('empresa', 'dia', 'activo')
    search_fields = ('empresa__nombre_negocio',)

from django.contrib import admin
from .models import Cliente, Empresa, Servicio, Disponibilidad, Cita    

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

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'servicio', 'empresa', 'fecha', 'hora_inicio', 'estado')
    list_filter = ('empresa', 'estado', 'fecha')
    search_fields = ('cliente__user__username', 'servicio__nombre', 'empresa__nombre_negocio')

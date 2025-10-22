from django.contrib import admin
from .models import Cliente, Empresa, Servicio

admin.site.register(Cliente)
admin.site.register(Empresa)

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'precio', 'duracion', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'empresa')
    search_fields = ('nombre', 'empresa__nombre_negocio')
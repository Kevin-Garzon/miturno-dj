from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('registro/cliente/', views.registro_cliente, name='registro_cliente'),
    path('login/cliente/', views.login_cliente, name='login_cliente'),
    path('login/empresa/', views.login_empresa, name='login_empresa'),
    path('dashboard/cliente/', views.dashboard_cliente, name='dashboard_cliente'),
    path('dashboard/empresa/', views.dashboard_empresa, name='dashboard_empresa'),
    path('empresa/configuracion/', views.editar_empresa, name='editar_empresa'),
    path('cliente/perfil/', views.perfil_cliente, name='perfil_cliente'),
    path('cliente/configuracion/', views.editar_cliente, name='editar_cliente'),
    path('empresa/servicios/', views.listar_servicios, name='listar_servicios'),
    path('empresa/servicios/nuevo/', views.crear_servicio, name='crear_servicio'),
    path('logout/', views.logout_view, name='logout'),
]

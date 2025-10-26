from django.urls import path
from . import views

urlpatterns = [

    # --- Vistas públicas ---
    path('', views.landing, name='landing'),
    path('registro/cliente/', views.registro_cliente, name='registro_cliente'),
    path('login/cliente/', views.login_cliente, name='login_cliente'),
    path('login/empresa/', views.login_empresa, name='login_empresa'),

    # --- Dashboards ---
    path('dashboard/cliente/', views.dashboard_cliente, name='dashboard_cliente'),
    path('dashboard/empresa/', views.dashboard_empresa, name='dashboard_empresa'),

    # --- Empresa / Barbería ---
    path('empresa/configuracion/', views.editar_empresa, name='editar_empresa'),

    # --- Cliente ---
    path('cliente/perfil/', views.perfil_cliente, name='perfil_cliente'),
    path('cliente/configuracion/', views.editar_cliente, name='editar_cliente'),
    path('cliente/servicios/<int:id>/', views.detalle_servicio, name='detalle_servicio'),
    path('cliente/servicios/<int:id>/disponibilidad/<str:dia>/', views.horarios_servicio, name='horarios_servicio'),



    # --- Servicios ---
    path('empresa/servicios/', views.listar_servicios, name='listar_servicios'),
    path('empresa/servicios/nuevo/', views.crear_servicio, name='crear_servicio'),
    path('empresa/servicios/<int:id>/editar/', views.editar_servicio, name='editar_servicio'),
    path('empresa/servicios/<int:id>/eliminar/', views.eliminar_servicio, name='eliminar_servicio'),

    # --- Clientes (panel empresa) ---
    path('empresa/clientes/', views.listar_clientes, name='listar_clientes'),
    path('empresa/clientes/crear/', views.crear_cliente_admin, name='crear_cliente_admin'),
    path('empresa/clientes/<int:id>/editar/', views.editar_cliente_admin, name='editar_cliente_admin'),
    path('empresa/clientes/<int:id>/eliminar/', views.eliminar_cliente_admin, name='eliminar_cliente_admin'),

    # --- Disponibilidad ---
    path('empresa/disponibilidad/', views.configurar_disponibilidad, name='configurar_disponibilidad'),


    # --- Cierre de sesión ---
    path('logout/', views.logout_view, name='logout'),
]

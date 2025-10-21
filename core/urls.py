from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('registro/cliente/', views.registro_cliente, name='registro_cliente'),
    path('registro/empresa/', views.registro_empresa, name='registro_empresa'),
    path('login/cliente/', views.login_cliente, name='login_cliente'),
    path('login/empresa/', views.login_empresa, name='login_empresa'),
    path('dashboard/cliente/', views.dashboard_cliente, name='dashboard_cliente'),
    path('dashboard/empresa/', views.dashboard_empresa, name='dashboard_empresa'),
]

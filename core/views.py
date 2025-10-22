from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .forms import RegistroClienteForm, EmpresaForm
from .models import Cliente, Empresa
from django.contrib.auth.decorators import login_required
from django.contrib import messages


# Landing
def landing(request):
    return render(request, 'landing.html')


# Registro Cliente
def registro_cliente(request):
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            email = form.cleaned_data['email']
            telefono = form.cleaned_data['telefono']
            user = User.objects.create_user(username=username, password=password, email=email)
            Cliente.objects.create(user=user, telefono=telefono)
            return redirect('login_cliente')
    else:
        form = RegistroClienteForm()
    return render(request, 'registro_cliente.html', {'form': form})



# Login Cliente
def login_cliente(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard_cliente')
    return render(request, 'login_cliente.html')


# Login Empresa
def login_empresa(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard_empresa')
    return render(request, 'login_empresa.html')


# Dashboards básicos
@login_required
def dashboard_cliente(request):
    return render(request, 'dashboard_cliente.html')

@login_required
def dashboard_empresa(request):
    return render(request, 'dashboard_empresa.html')


# Logout
def logout_view(request):
    logout(request)
    return redirect('landing')


@login_required
def editar_empresa(request):
    try:
        empresa = request.user.empresa  # accedemos al registro vinculado al usuario
    except Empresa.DoesNotExist:
        messages.error(request, "No se encontró la información de la empresa.")
        return redirect('dashboard_empresa')

    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, "Información actualizada correctamente.")
            return redirect('editar_empresa')
    else:
        form = EmpresaForm(instance=empresa)

    return render(request, 'empresa/editar_empresa.html', {'form': form})
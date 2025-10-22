from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegistroClienteForm, EmpresaForm, ServicioForm
from .models import Cliente, Empresa, Servicio


# ---------------------
# Decoradores personalizados
# ---------------------

def empresa_required(view_func):
    """Permite el acceso solo a usuarios con cuenta de empresa"""
    def wrapper(request, *args, **kwargs):
        try:
            request.user.empresa
            return view_func(request, *args, **kwargs)
        except Empresa.DoesNotExist:
            messages.error(request, "No tienes permiso para acceder a esta sección.")
            logout(request)
            return redirect('login_empresa')
    return wrapper


def cliente_required(view_func):
    """Permite el acceso solo a usuarios con cuenta de cliente"""
    def wrapper(request, *args, **kwargs):
        try:
            request.user.cliente
            return view_func(request, *args, **kwargs)
        except Cliente.DoesNotExist:
            messages.error(request, "No tienes permiso para acceder a esta sección.")
            logout(request)
            return redirect('login_cliente')
    return wrapper


# ---------------------
# Landing
# ---------------------
def landing(request):
    return render(request, 'landing.html')


# ---------------------
# Registro de cliente
# ---------------------
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

            messages.success(request, "Registro exitoso. Ahora puedes iniciar sesión.")
            return redirect('login_cliente')
    else:
        form = RegistroClienteForm()

    return render(request, 'registro_cliente.html', {'form': form})


# ---------------------
# Login Cliente
# ---------------------
def login_cliente(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Validar que sea cliente
            if Cliente.objects.filter(user=user).exists():
                login(request, user)
                return redirect('dashboard_cliente')
            else:
                messages.error(request, "Este usuario no tiene cuenta de cliente.")
                return redirect('login_cliente')
        else:
            messages.error(request, "Credenciales incorrectas.")
    return render(request, 'login_cliente.html')


# ---------------------
# Login Empresa
# ---------------------
def login_empresa(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Validar que sea empresa
            if Empresa.objects.filter(user=user).exists():
                login(request, user)
                return redirect('dashboard_empresa')
            else:
                messages.error(request, "Este usuario no tiene cuenta de empresa.")
                return redirect('login_empresa')
        else:
            messages.error(request, "Credenciales incorrectas.")
    return render(request, 'login_empresa.html')


# ---------------------
# Logout
# ---------------------
def logout_view(request):
    logout(request)
    return redirect('landing')


# ---------------------
# Dashboards
# ---------------------
@login_required
@cliente_required
def dashboard_cliente(request):
    return render(request, 'dashboard_cliente.html')


@login_required
@empresa_required
def dashboard_empresa(request):
    return render(request, 'dashboard_empresa.html')


# ---------------------
# Empresa: Configuración y Servicios
# ---------------------
@login_required
@empresa_required
def editar_empresa(request):
    # Limpia mensajes anteriores
    storage = messages.get_messages(request)
    storage.used = True
    try:
        empresa = request.user.empresa
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


@login_required
@empresa_required
def listar_servicios(request):
    empresa = request.user.empresa
    servicios = Servicio.objects.filter(empresa=empresa).order_by('-fecha_creacion')

    return render(request, 'empresa/servicios/listar_servicios.html', {'servicios': servicios})


@login_required
@empresa_required
def crear_servicio(request):
    empresa = request.user.empresa

    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            servicio = form.save(commit=False)
            servicio.empresa = empresa
            servicio.save()
            messages.success(request, 'El servicio fue creado exitosamente.')
            return redirect('listar_servicios')
    else:
        form = ServicioForm()

    return render(request, 'empresa/servicios/crear_servicio.html', {'form': form})


@login_required
@empresa_required
def editar_servicio(request, id):
    empresa = request.user.empresa
    servicio = get_object_or_404(Servicio, id=id, empresa=empresa)

    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            form.save()
            messages.success(request, 'El servicio se actualizó correctamente.')
            return redirect('listar_servicios')
    else:
        form = ServicioForm(instance=servicio)

    return render(request, 'empresa/servicios/editar_servicio.html', {'form': form, 'servicio': servicio})


@login_required
@empresa_required
def eliminar_servicio(request, id):
    empresa = request.user.empresa
    servicio = get_object_or_404(Servicio, id=id, empresa=empresa)

    if request.method == 'POST':
        servicio.delete()
        messages.success(request, 'El servicio fue eliminado correctamente.')
        return redirect('listar_servicios')

    return render(request, 'empresa/servicios/eliminar_servicio.html', {'servicio': servicio})

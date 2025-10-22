from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .forms import RegistroClienteForm, EmpresaForm, ServicioForm
from .models import Cliente, Empresa, Servicio
from django.contrib.auth.decorators import login_required
from django.contrib import messages


# --- LANDING PAGE ---
def landing(request):
    return render(request, 'landing.html')


# --- REGISTRO DE CLIENTE ---

def registro_cliente(request):
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            telefono = form.cleaned_data.get('telefono')

            # Verificar si el usuario o correo ya existen
            if User.objects.filter(username=username).exists():
                messages.error(request, "El nombre de usuario ya está registrado.")
                return render(request, 'registro_cliente.html', {'form': form})
            if User.objects.filter(email=email).exists():
                messages.error(request, "El correo electrónico ya está registrado.")
                return render(request, 'registro_cliente.html', {'form': form})

            # Crear usuario y cliente
            user = User.objects.create_user(username=username, email=email, password=password)
            Cliente.objects.create(user=user, telefono=telefono)

            # Iniciar sesión automáticamente
            login(request, user)
            messages.success(request, f"¡Bienvenido {username}! Tu cuenta fue creada correctamente.")
            return redirect('dashboard_cliente')

        else:
            messages.error(request, "Por favor corrige los errores del formulario.")
    else:
        form = RegistroClienteForm()

    return render(request, 'registro_cliente.html', {'form': form})
# --- LOGIN CLIENTE ---
def login_cliente(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if hasattr(user, 'cliente'):
                login(request, user)
                return redirect('dashboard_cliente')
            else:
                messages.error(request, "Este usuario no está registrado como cliente.")
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    return render(request, 'login_cliente.html')


# --- LOGIN EMPRESA (SOY BARBERÍA) ---
def login_empresa(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Si es admin o staff, entra directo
            if user.is_superuser or user.is_staff:
                login(request, user)
                return redirect('dashboard_empresa')
            # Si es empresa registrada
            elif hasattr(user, 'empresa'):
                login(request, user)
                return redirect('dashboard_empresa')
            else:
                messages.error(request, "Este usuario no pertenece a ninguna barbería.")
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    return render(request, 'login_empresa.html')


# --- DASHBOARDS ---
@login_required
def dashboard_cliente(request):
    if not hasattr(request.user, 'cliente'):
        messages.error(request, "No tienes permisos para acceder al panel de cliente.")
        return redirect('dashboard_empresa')
    return render(request, 'dashboard_cliente.html')


@login_required
def dashboard_empresa(request):
    if not (hasattr(request.user, 'empresa') or request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No tienes permisos para acceder al panel de barbería.")
        return redirect('dashboard_cliente')
    return render(request, 'dashboard_empresa.html')


# --- LOGOUT ---
def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('landing')


# --- SECCIÓN EMPRESA / CONFIGURACIÓN ---
@login_required
def editar_empresa(request):
    if not (hasattr(request.user, 'empresa') or request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('dashboard_cliente')

    empresa = getattr(request.user, 'empresa', None)
    if not empresa:
        # Si es admin, usa la primera empresa existente (para evitar errores)
        empresa = Empresa.objects.first()

    if not empresa:
        messages.error(request, "No hay empresas registradas para editar.")
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


# --- SERVICIOS ---
@login_required
def listar_servicios(request):
    if not (hasattr(request.user, 'empresa') or request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('dashboard_cliente')

    if hasattr(request.user, 'empresa'):
        empresa = request.user.empresa
        servicios = Servicio.objects.filter(empresa=empresa).order_by('-fecha_creacion')
    else:
        servicios = Servicio.objects.all().order_by('-fecha_creacion')

    return render(request, 'empresa/servicios/listar_servicios.html', {'servicios': servicios})

@login_required
def crear_servicio(request):
    # Verificar permisos
    if not (hasattr(request.user, 'empresa') or request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('dashboard_cliente')

    # Obtener empresa asociada (solo si existe)
    empresa = getattr(request.user, 'empresa', None)

    # Si no tiene empresa y no es admin, bloquear
    if not empresa and not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No tienes una barbería registrada para crear servicios.")
        return redirect('listar_servicios')

    # Si el admin quiere crear un servicio, debe seleccionar una empresa existente
    if request.user.is_superuser or request.user.is_staff:
        # Si hay al menos una empresa en la base, usar la primera
        if not empresa:
            empresa = Empresa.objects.first()
            if not empresa:
                messages.error(request, "No existe ninguna barbería registrada para asociar el servicio.")
                return redirect('listar_servicios')

    # Procesar formulario
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            servicio = form.save(commit=False)
            servicio.empresa = empresa
            servicio.save()
            messages.success(request, 'El servicio fue creado exitosamente.')
            return redirect('listar_servicios')
        else:
            messages.error(request, 'Revisa los datos del formulario.')
    else:
        form = ServicioForm()

    return render(request, 'empresa/servicios/crear_servicio.html', {'form': form})



@login_required
def editar_servicio(request, id):
    if not (hasattr(request.user, 'empresa') or request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('dashboard_cliente')

    if hasattr(request.user, 'empresa'):
        empresa = request.user.empresa
        servicio = get_object_or_404(Servicio, id=id, empresa=empresa)
    else:
        servicio = get_object_or_404(Servicio, id=id)

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
def eliminar_servicio(request, id):
    if not (hasattr(request.user, 'empresa') or request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('dashboard_cliente')

    if hasattr(request.user, 'empresa'):
        empresa = request.user.empresa
        servicio = get_object_or_404(Servicio, id=id, empresa=empresa)
    else:
        servicio = get_object_or_404(Servicio, id=id)

    if request.method == 'POST':
        servicio.delete()
        messages.success(request, 'El servicio fue eliminado correctamente.')
        return redirect('listar_servicios')
    return render(request, 'empresa/servicios/eliminar_servicio.html', {'servicio': servicio})


# --- USUARIOS ---
@login_required
def listar_usuarios(request):
    if not (hasattr(request.user, 'empresa') or request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('dashboard_cliente')

    usuarios = User.objects.all().order_by('username')
    return render(request, 'empresa/usuarios/usuarios.html', {'usuarios': usuarios})


@login_required
def editar_usuarios(request, id):
    if not (hasattr(request.user, 'empresa') or request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('dashboard_cliente')

    usuario = get_object_or_404(User, id=id)
    if request.method == 'POST':
        usuario.username = request.POST.get('username')
        usuario.email = request.POST.get('email')
        usuario.is_active = 'is_active' in request.POST
        usuario.save()
        messages.success(request, 'Usuario actualizado correctamente.')
        return redirect('listar_usuarios')
    return render(request, 'empresa/usuarios/editar_usuarios.html', {'usuario': usuario})


@login_required
def eliminar_usuario(request, id):
    if not (hasattr(request.user, 'empresa') or request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('dashboard_cliente')

    usuario = get_object_or_404(User, id=id)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, f'El usuario "{usuario.username}" fue eliminado correctamente.')
        return redirect('listar_usuarios')
    return render(request, 'empresa/usuarios/eliminar_usuarios.html', {'usuario': usuario})

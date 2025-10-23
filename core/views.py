from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegistroClienteForm, EmpresaForm, ServicioForm, EditarClienteForm
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
    # Obtener la primera empresa (asumiendo que solo hay una)
    try:
        empresa = Empresa.objects.first()
        servicios = Servicio.objects.filter(empresa=empresa, activo=True).order_by('nombre')
    except:
        empresa = None
        servicios = []
    
    return render(request, 'dashboard_cliente.html', {
        'empresa': empresa,
        'servicios': servicios
    })


@login_required
@empresa_required
def dashboard_empresa(request):
    empresa = request.user.empresa
    servicios_activos = empresa.servicios.filter(activo=True).count()
    citas_dia = 0  # aún no implementado
    clientes_total = 0  # si luego quieres contar clientes

    context = {
        'servicios_activos': servicios_activos,
        'citas_dia': citas_dia,
        'clientes_total': clientes_total,
    }
    return render(request, 'dashboard_empresa.html', context)



# Logout
def logout_view(request):
    logout(request)
    return redirect('landing')


@login_required
def perfil_cliente(request):
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        messages.error(request, "No se encontró la información del cliente.")
        return redirect('dashboard_cliente')
    
    return render(request, 'cliente/perfil_cliente.html', {
        'cliente': cliente
    })


@login_required
def editar_cliente(request):
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        messages.error(request, "No se encontró la información del cliente.")
        return redirect('dashboard_cliente')

    if request.method == 'POST':
        form = EditarClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            new_username = form.cleaned_data['username']
            
            # Verificar si el nuevo username ya existe (excluyendo el usuario actual)
            if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
                messages.error(request, "Este nombre de usuario ya está en uso. Por favor elige otro.")
                return render(request, 'cliente/editar_cliente.html', {'form': form})
            
            # Actualizar username del User
            user = request.user
            user.username = new_username
            
            # Actualizar password si se proporcionó una nueva
            password = form.cleaned_data['password']
            password_changed = False
            if password:
                user.set_password(password)
                password_changed = True
            
            user.save()
            form.save()
            
            # Si se cambió la contraseña, volver a autenticar al usuario
            if password_changed:
                user = authenticate(request, username=user.username, password=password)
                if user is not None:
                    login(request, user)
            
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect('perfil_cliente')
    else:
        form = EditarClienteForm(instance=cliente, initial={
            'username': request.user.username
        })

    return render(request, 'cliente/editar_cliente.html', {'form': form})


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
@empresa_required
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
@empresa_required
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
@empresa_required
def listar_clientes(request):
    # Solo usuarios que son clientes
    clientes = Cliente.objects.select_related('user').order_by('user__username')

    return render(request, 'empresa/clientes/listar_clientes.html', {
        'clientes': clientes
    })


@login_required
@empresa_required
def editar_cliente_admin(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    user = cliente.user  # relación directa con el usuario

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        activo = 'is_active' in request.POST

        user.username = username
        user.email = email
        user.is_active = activo
        user.save()

        cliente.telefono = telefono
        cliente.save()

        messages.success(request, "Cliente actualizado correctamente.")
        return redirect('listar_clientes')

    return render(request, 'empresa/clientes/editar_cliente.html', {
        'cliente': cliente,
        'user': user
    })



@login_required
@empresa_required
def eliminar_cliente_admin(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    user = cliente.user

    if request.method == 'POST':
        user.delete()
        messages.success(request, f"El cliente '{user.username}' fue eliminado correctamente.")
        return redirect('listar_clientes')

    return render(request, 'empresa/clientes/eliminar_cliente.html', {'cliente': cliente})

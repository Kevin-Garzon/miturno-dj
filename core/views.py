from datetime import datetime, timedelta, time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localtime

from .forms import RegistroClienteForm, EmpresaForm, ServicioForm, EditarClienteForm
from .models import Cliente, Empresa, Servicio, Disponibilidad


# ============================================================
# DECORADORES (para restringir acceso según tipo de usuario)
# ============================================================

def empresa_required(view_func):
    """Solo deja entrar a usuarios que tengan perfil de empresa"""
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
    """Solo deja entrar a usuarios que tengan perfil de cliente"""
    def wrapper(request, *args, **kwargs):
        try:
            request.user.cliente
            return view_func(request, *args, **kwargs)
        except Cliente.DoesNotExist:
            messages.error(request, "No tienes permiso para acceder a esta sección.")
            logout(request)
            return redirect('login_cliente')
    return wrapper


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

def landing(request):
    """Página inicial del sitio"""
    return render(request, 'landing.html')


# ============================================================
# REGISTRO Y LOGIN DE CLIENTES / EMPRESA
# ============================================================

def registro_cliente(request):
    """Registro de nuevos clientes"""
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

            # Crear usuario y cliente asociados
            user = User.objects.create_user(username=username, email=email, password=password)
            Cliente.objects.create(user=user, telefono=telefono)

            messages.success(request, "Registro exitoso. Ahora puedes iniciar sesión.")
            return redirect('login_cliente')
    else:
        form = RegistroClienteForm()

    return render(request, 'registro_cliente.html', {'form': form})


def login_cliente(request):
    """Inicio de sesión para clientes"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if Cliente.objects.filter(user=user).exists():
                login(request, user)
                return redirect('dashboard_cliente')
            else:
                messages.error(request, "Este usuario no tiene cuenta de cliente.")
        else:
            messages.error(request, "Credenciales incorrectas.")
    return render(request, 'login_cliente.html')


def login_empresa(request):
    """Inicio de sesión para empresa"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if Empresa.objects.filter(user=user).exists():
                login(request, user)
                return redirect('dashboard_empresa')
            else:
                messages.error(request, "Este usuario no tiene cuenta de empresa.")
        else:
            messages.error(request, "Credenciales incorrectas.")
    return render(request, 'login_empresa.html')


def logout_view(request):
    """Cerrar sesión (funciona para ambos tipos de usuarios)"""
    logout(request)
    return redirect('landing')


# ============================================================
# DASHBOARDS (pantallas principales de cliente y empresa)
# ============================================================

@login_required
@cliente_required
def dashboard_cliente(request):
    """
    Dashboard del cliente:
    Muestra los servicios activos de la única empresa disponible.
    """
    empresa = Empresa.objects.first()
    servicios = Servicio.objects.filter(empresa=empresa, activo=True).order_by('nombre') if empresa else []
    
    return render(request, 'dashboard_cliente.html', {
        'empresa': empresa,
        'servicios': servicios
    })


@login_required
@empresa_required
def dashboard_empresa(request):
    """
    Dashboard de la empresa:
    Muestra algunos datos de resumen (servicios activos, clientes, etc.)
    """
    empresa = request.user.empresa
    servicios_activos = empresa.servicios.filter(activo=True).count()
    clientes_total = Cliente.objects.count()

    context = {
        'servicios_activos': servicios_activos,
        'citas_dia': 0,  # todavía no se ha implementado el módulo de citas
        'clientes_total': clientes_total,
    }
    return render(request, 'dashboard_empresa.html', context)


# ============================================================
# PERFIL Y CONFIGURACIÓN DE CLIENTES
# ============================================================

@login_required
def perfil_cliente(request):
    """Muestra el perfil del cliente logueado"""
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        messages.error(request, "No se encontró la información del cliente.")
        return redirect('dashboard_cliente')
    
    return render(request, 'cliente/perfil_cliente.html', {'cliente': cliente})


@login_required
def editar_cliente(request):
    """Permite al cliente editar su información (usuario, teléfono, contraseña)"""
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        messages.error(request, "No se encontró la información del cliente.")
        return redirect('dashboard_cliente')

    if request.method == 'POST':
        form = EditarClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            new_username = form.cleaned_data['username']

            # Evita duplicar usernames
            if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
                messages.error(request, "Este nombre de usuario ya está en uso.")
                return render(request, 'cliente/editar_cliente.html', {'form': form})

            # Actualizar datos del usuario
            user = request.user
            user.username = new_username

            # Si el cliente escribió una nueva contraseña
            password = form.cleaned_data['password']
            if password:
                user.set_password(password)
                user.save()
                user = authenticate(request, username=user.username, password=password)
                if user:
                    login(request, user)
            else:
                user.save()

            # Guardar datos del cliente (teléfono, etc.)
            form.save()

            messages.success(request, "Perfil actualizado correctamente.")
            return redirect('perfil_cliente')
    else:
        form = EditarClienteForm(instance=cliente, initial={'username': request.user.username})

    return render(request, 'cliente/editar_cliente.html', {'form': form})


# ============================================================
# SERVICIOS (vista detalle y horarios disponibles para cliente)
# ============================================================

@login_required
@cliente_required
def detalle_servicio(request, id):
    """Muestra detalle de un servicio y calcula las franjas horarias disponibles"""
    empresa = Empresa.objects.first()
    servicio = get_object_or_404(Servicio, id=id, empresa=empresa, activo=True)

    dias_disponibles = Disponibilidad.objects.filter(empresa=empresa, activo=True).order_by('id')
    duracion = servicio.duracion
    franjas = {}

    for d in dias_disponibles:
        # Mañana
        if d.hora_inicio_m and d.hora_fin_m:
            hora_actual = datetime.combine(datetime.today(), d.hora_inicio_m)
            hora_fin = datetime.combine(datetime.today(), d.hora_fin_m)
            franjas[d.dia + '_m'] = []
            while hora_actual + timedelta(minutes=duracion) <= hora_fin:
                fin_slot = hora_actual + timedelta(minutes=duracion)
                franjas[d.dia + '_m'].append(f"{hora_actual.time().strftime('%H:%M')} - {fin_slot.time().strftime('%H:%M')}")
                hora_actual = fin_slot

        # Tarde
        if d.hora_inicio_t and d.hora_fin_t:
            hora_actual = datetime.combine(datetime.today(), d.hora_inicio_t)
            hora_fin = datetime.combine(datetime.today(), d.hora_fin_t)
            franjas[d.dia + '_t'] = []
            while hora_actual + timedelta(minutes=duracion) <= hora_fin:
                fin_slot = hora_actual + timedelta(minutes=duracion)
                franjas[d.dia + '_t'].append(f"{hora_actual.time().strftime('%H:%M')} - {fin_slot.time().strftime('%H:%M')}")
                hora_actual = fin_slot

    context = {
        'servicio': servicio,
        'empresa': empresa,
        'franjas': franjas,
        'dias_disponibles': dias_disponibles,
    }
    return render(request, 'cliente/detalle_servicio.html', context)


@login_required
@cliente_required
def horarios_servicio(request, id, dia):
    """Muestra las franjas de un día específico"""
    empresa = Empresa.objects.first()
    servicio = get_object_or_404(Servicio, id=id, empresa=empresa, activo=True)
    disponibilidad = Disponibilidad.objects.filter(empresa=empresa, dia=dia, activo=True).first()

    franjas = []
    if disponibilidad:
        duracion = servicio.duracion

        # Mañana
        if disponibilidad.hora_inicio_m and disponibilidad.hora_fin_m:
            hora_actual = datetime.combine(datetime.today(), disponibilidad.hora_inicio_m)
            hora_fin = datetime.combine(datetime.today(), disponibilidad.hora_fin_m)
            while hora_actual + timedelta(minutes=duracion) <= hora_fin:
                fin_slot = hora_actual + timedelta(minutes=duracion)
                franjas.append(f"{hora_actual.time().strftime('%H:%M')} - {fin_slot.time().strftime('%H:%M')}")
                hora_actual = fin_slot

        # Tarde
        if disponibilidad.hora_inicio_t and disponibilidad.hora_fin_t:
            hora_actual = datetime.combine(datetime.today(), disponibilidad.hora_inicio_t)
            hora_fin = datetime.combine(datetime.today(), disponibilidad.hora_fin_t)
            while hora_actual + timedelta(minutes=duracion) <= hora_fin:
                fin_slot = hora_actual + timedelta(minutes=duracion)
                franjas.append(f"{hora_actual.time().strftime('%H:%M')} - {fin_slot.time().strftime('%H:%M')}")
                hora_actual = fin_slot

    return render(request, 'cliente/horarios_servicio.html', {
        'servicio': servicio,
        'empresa': empresa,
        'dia': dia,
        'disponibilidad': disponibilidad,
        'franjas': franjas,
    })


# ============================================================
# CONFIGURACIÓN DE EMPRESA Y CRUD DE SERVICIOS
# ============================================================

@login_required
@empresa_required
def editar_empresa(request):
    """Permite editar la información de la empresa"""
    messages.get_messages(request).used = True
    empresa = request.user.empresa

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
    """Lista todos los servicios registrados por la empresa"""
    empresa = request.user.empresa
    servicios = Servicio.objects.filter(empresa=empresa).order_by('-fecha_creacion')
    return render(request, 'empresa/servicios/listar_servicios.html', {'servicios': servicios})


@login_required
@empresa_required
def crear_servicio(request):
    """Formulario para crear un nuevo servicio"""
    empresa = request.user.empresa

    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            servicio = form.save(commit=False)
            servicio.empresa = empresa
            servicio.save()
            messages.success(request, 'El servicio fue creado exitosamente.')
            return redirect('listar_servicios')
        messages.error(request, 'Revisa los datos del formulario.')
    else:
        form = ServicioForm()

    return render(request, 'empresa/servicios/crear_servicio.html', {'form': form})


@login_required
@empresa_required
def editar_servicio(request, id):
    """Editar información de un servicio existente"""
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
    """Confirma y elimina un servicio"""
    empresa = request.user.empresa
    servicio = get_object_or_404(Servicio, id=id, empresa=empresa)

    if request.method == 'POST':
        servicio.delete()
        messages.success(request, 'El servicio fue eliminado correctamente.')
        return redirect('listar_servicios')

    return render(request, 'empresa/servicios/eliminar_servicio.html', {'servicio': servicio})


# ============================================================
# CLIENTES (desde el panel de la empresa)
# ============================================================

@login_required
@empresa_required
def listar_clientes(request):
    """Lista todos los clientes registrados en el sistema"""
    clientes = Cliente.objects.select_related('user').order_by('user__username')
    return render(request, 'empresa/clientes/listar_clientes.html', {'clientes': clientes})


@login_required
@empresa_required
def editar_cliente_admin(request, id):
    """Editar la información de un cliente desde el panel de la empresa"""
    cliente = get_object_or_404(Cliente, id=id)
    user = cliente.user

    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.is_active = 'is_active' in request.POST
        user.save()

        cliente.telefono = request.POST.get('telefono')
        cliente.save()

        messages.success(request, "Cliente actualizado correctamente.")
        return redirect('listar_clientes')

    return render(request, 'empresa/clientes/editar_cliente.html', {'cliente': cliente, 'user': user})


@login_required
@empresa_required
def eliminar_cliente_admin(request, id):
    """Permite eliminar un cliente (y su usuario asociado)"""
    cliente = get_object_or_404(Cliente, id=id)
    user = cliente.user

    if request.method == 'POST':
        user.delete()
        messages.success(request, f"El cliente '{user.username}' fue eliminado correctamente.")
        return redirect('listar_clientes')

    return render(request, 'empresa/clientes/eliminar_cliente.html', {'cliente': cliente})


# ============================================================
# DISPONIBILIDAD (horarios de trabajo de la empresa)
# ============================================================

DIAS_ORDEN = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']


def ensure_disponibilidad_inicial():
    """
    Crea automáticamente las 7 filas (lunes a domingo) con horarios base.
    Por defecto activa de lunes a sábado y deja domingo inactivo.
    """
    empresa = Empresa.objects.first()
    if not empresa:
        return

    existentes = set(Disponibilidad.objects.values_list('dia', flat=True))
    por_crear = [d for d in DIAS_ORDEN if d not in existentes]

    for d in por_crear:
        Disponibilidad.objects.create(
            empresa=empresa,
            dia=d,
            hora_inicio_m=time(8, 0),
            hora_fin_m=time(12, 0),
            hora_inicio_t=time(14, 0),
            hora_fin_t=time(18, 0),
            activo=(d != 'domingo')
        )


@login_required
@empresa_required
def configurar_disponibilidad(request):
    """Permite configurar los horarios de atención (mañana/tarde) por día"""
    ensure_disponibilidad_inicial()
    dias = Disponibilidad.objects.all().order_by('id')  # solo hay una empresa

    if request.method == 'POST':
        for d in dias:
            ini_m = request.POST.get(f'inicio_m_{d.id}')
            fin_m = request.POST.get(f'fin_m_{d.id}')
            ini_t = request.POST.get(f'inicio_t_{d.id}')
            fin_t = request.POST.get(f'fin_t_{d.id}')
            activo = bool(request.POST.get(f'activo_{d.id}', False))

            if activo and (not ini_m or not fin_m or not ini_t or not fin_t):
                messages.warning(request, f"Por favor completa los horarios para {d.get_dia_display()} antes de activarlo.")
                return redirect('configurar_disponibilidad')

            d.hora_inicio_m = ini_m or None
            d.hora_fin_m = fin_m or None
            d.hora_inicio_t = ini_t or None
            d.hora_fin_t = fin_t or None
            d.activo = activo
            d.save()

        messages.success(request, "Disponibilidad actualizada correctamente.")
        return redirect('configurar_disponibilidad')

    return render(request, 'empresa/disponibilidad.html', {'dias': dias})

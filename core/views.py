from datetime import datetime, timedelta, time, date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import re

from .forms import RegistroClienteForm, EmpresaForm, ServicioForm, EditarClienteForm
from .models import Cliente, Empresa, Servicio, Disponibilidad, Cita


# ============================================================
# 1. CONSTANTES GLOBALES
# ============================================================

DIAS_ORDEN = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']


# ============================================================
# 2. DECORADORES
# ============================================================

def empresa_required(view_func):
    """Restringe acceso solo a usuarios que tengan perfil de empresa"""
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
    """Restringe acceso solo a usuarios que tengan perfil de cliente"""
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
# 3. HELPERS (FUNCIONES DE APOYO)
# ============================================================

def get_next_date_for_day(dia_slug):
    """Devuelve la fecha de la próxima ocurrencia del día indicado."""
    dia_slug = dia_slug.lower()
    mapa = {
        'lunes': 0,
        'martes': 1,
        'miercoles': 2,
        'miércoles': 2,
        'jueves': 3,
        'viernes': 4,
        'sabado': 5,
        'sábado': 5,
        'domingo': 6,
    }
    objetivo = mapa.get(dia_slug)
    hoy = date.today()

    if objetivo is None:
        return hoy

    diff = (objetivo - hoy.weekday()) % 7
    return hoy + timedelta(days=diff)


def ensure_disponibilidad_inicial():
    """
    Crea las 7 filas de disponibilidad si aún no existen.
    Por defecto activa lunes-sábado y deja domingo inactivo.
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


# ============================================================
# 4. LANDING
# ============================================================

def landing(request):
    """Página inicial"""
    return render(request, 'landing.html')


# ============================================================
# 5. REGISTRO Y LOGIN
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

            # Validar usuario y correo únicos
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


def login_cliente(request):
    """Login de cliente"""
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
    """Login de empresa"""
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
    """Cerrar sesión"""
    logout(request)
    return redirect('landing')


# ============================================================
# 6. DASHBOARDS
# ============================================================

@login_required
@cliente_required
def dashboard_cliente(request):
    """Dashboard para clientes"""
    empresa = Empresa.objects.first()
    servicios = Servicio.objects.filter(empresa=empresa, activo=True).order_by('nombre') if empresa else []

    hoy = date.today()
    proximas_citas = 0

    if hasattr(request.user, 'cliente'):
        proximas_citas = Cita.objects.filter(
            cliente=request.user.cliente,
            fecha__gte=hoy
        ).exclude(estado='cancelada').count()

    return render(request, 'dashboard_cliente.html', {
        'empresa': empresa,
        'servicios': servicios,
        'proximas_citas': proximas_citas,
    })


@login_required
@empresa_required
def dashboard_empresa(request):
    """Dashboard para empresas"""
    empresa = request.user.empresa

    servicios_activos = empresa.servicios.filter(activo=True).count()
    clientes_total = Cliente.objects.count()

    hoy = date.today()

    # Citas del día
    citas_hoy = Cita.objects.filter(
        empresa=empresa,
        fecha=hoy,
        estado__in=["pendiente", "confirmada"]
    ).count()

    # Próximas citas ordenadas por proximidad
    citas_recientes = (
        Cita.objects.filter(
            empresa=empresa,
            estado__in=["pendiente", "confirmada"],
            fecha__gte=hoy
        )
        .order_by("fecha", "hora_inicio")[:10]
    )

    return render(request, 'dashboard_empresa.html', {
        'servicios_activos': servicios_activos,
        'clientes_total': clientes_total,
        'citas_hoy': citas_hoy,
        'citas_recientes': citas_recientes,
    })


# ============================================================
# 7. CLIENTE – PERFIL Y CONFIGURACIÓN
# ============================================================

@login_required
def perfil_cliente(request):
    """Perfil del cliente"""
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        messages.error(request, "No se encontró la información del cliente.")
        return redirect('dashboard_cliente')

    return render(request, 'cliente/perfil_cliente.html', {'cliente': cliente})


@login_required
def editar_cliente(request):
    """Edición del perfil del cliente"""
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        messages.error(request, "No se encontró la información del cliente.")
        return redirect('dashboard_cliente')

    if request.method == 'POST':
        form = EditarClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            new_username = form.cleaned_data['username']

            if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
                messages.error(request, "Este nombre de usuario ya está en uso.")
                return render(request, 'cliente/editar_cliente.html', {'form': form})

            user = request.user
            user.username = new_username

            password = form.cleaned_data['password']
            if password:
                user.set_password(password)
                user.save()
                login(request, user)
            else:
                user.save()

            form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect('perfil_cliente')

    else:
        form = EditarClienteForm(instance=cliente, initial={'username': request.user.username})

    return render(request, 'cliente/editar_cliente.html', {'form': form})


# ============================================================
# 8. CLIENTE – SERVICIOS
# ============================================================

@login_required
@cliente_required
def detalle_servicio(request, id):
    """Vista de detalle del servicio y listado de horarios posibles"""
    empresa = Empresa.objects.first()
    servicio = get_object_or_404(Servicio, id=id, empresa=empresa, activo=True)

    dias_disponibles = Disponibilidad.objects.filter(empresa=empresa, activo=True).order_by('id')
    duracion = servicio.duracion
    franjas = {}

    for d in dias_disponibles:
        # Mañana
        if d.hora_inicio_m and d.hora_fin_m:
            hora_actual = datetime.combine(date.today(), d.hora_inicio_m)
            hora_fin = datetime.combine(date.today(), d.hora_fin_m)
            franjas[d.dia + '_m'] = []

            while hora_actual + timedelta(minutes=duracion) <= hora_fin:
                fin_slot = hora_actual + timedelta(minutes=duracion)
                franjas[d.dia + '_m'].append(
                    f"{hora_actual.time().strftime('%H:%M')} - {fin_slot.time().strftime('%H:%M')}"
                )
                hora_actual = fin_slot

        # Tarde
        if d.hora_inicio_t and d.hora_fin_t:
            hora_actual = datetime.combine(date.today(), d.hora_inicio_t)
            hora_fin = datetime.combine(date.today(), d.hora_fin_t)
            franjas[d.dia + '_t'] = []

            while hora_actual + timedelta(minutes=duracion) <= hora_fin:
                fin_slot = hora_actual + timedelta(minutes=duracion)
                franjas[d.dia + '_t'].append(
                    f"{hora_actual.time().strftime('%H:%M')} - {fin_slot.time().strftime('%H:%M')}"
                )
                hora_actual = fin_slot

    return render(request, 'cliente/detalle_servicio.html', {
        'servicio': servicio,
        'empresa': empresa,
        'franjas': franjas,
        'dias_disponibles': dias_disponibles,
    })


# ============================================================
# 9. CLIENTE – VER HORARIOS
# ============================================================

@login_required
@cliente_required
def horarios_servicio(request, id, dia):
    """Muestra las franjas disponibles filtrando horas pasadas y solapamientos"""
    empresa = Empresa.objects.first()
    servicio = get_object_or_404(Servicio, id=id, empresa=empresa, activo=True)
    disponibilidad = Disponibilidad.objects.filter(empresa=empresa, dia=dia, activo=True).first()

    franjas = []
    if disponibilidad:
        duracion = servicio.duracion
        fecha_real = get_next_date_for_day(dia)
        hoy = date.today()

        hora_actual_sistema = datetime.now().time() if fecha_real == hoy else None

        citas_ocupadas = Cita.objects.filter(
            empresa=empresa,
            fecha=fecha_real
        ).exclude(estado='cancelada')

        rangos_ocupados = [(c.hora_inicio, c.hora_fin) for c in citas_ocupadas]

        def solapada(inicio, fin):
            for ini_occ, fin_occ in rangos_ocupados:
                if inicio < fin_occ and fin > ini_occ:
                    return True
            return False

        # Mañana
        if disponibilidad.hora_inicio_m and disponibilidad.hora_fin_m:
            hora_actual = datetime.combine(fecha_real, disponibilidad.hora_inicio_m)
            hora_fin = datetime.combine(fecha_real, disponibilidad.hora_fin_m)

            while hora_actual + timedelta(minutes=duracion) <= hora_fin:
                fin_slot = hora_actual + timedelta(minutes=duracion)
                inicio_t = hora_actual.time()
                fin_t = fin_slot.time()

                if hora_actual_sistema and inicio_t <= hora_actual_sistema:
                    hora_actual = fin_slot
                    continue

                if not solapada(inicio_t, fin_t):
                    franjas.append(f"{inicio_t.strftime('%H:%M')} - {fin_t.strftime('%H:%M')}")

                hora_actual = fin_slot

        # Tarde
        if disponibilidad.hora_inicio_t and disponibilidad.hora_fin_t:
            hora_actual = datetime.combine(fecha_real, disponibilidad.hora_inicio_t)
            hora_fin = datetime.combine(fecha_real, disponibilidad.hora_fin_t)

            while hora_actual + timedelta(minutes=duracion) <= hora_fin:
                fin_slot = hora_actual + timedelta(minutes=duracion)
                inicio_t = hora_actual.time()
                fin_t = fin_slot.time()

                if hora_actual_sistema and inicio_t <= hora_actual_sistema:
                    hora_actual = fin_slot
                    continue

                if not solapada(inicio_t, fin_t):
                    franjas.append(f"{inicio_t.strftime('%H:%M')} - {fin_t.strftime('%H:%M')}")

                hora_actual = fin_slot

    return render(request, 'cliente/horarios_servicio.html', {
        'servicio': servicio,
        'empresa': empresa,
        'dia': dia,
        'disponibilidad': disponibilidad,
        'franjas': franjas,
    })


# ============================================================
# 10. CLIENTE – RESUMEN Y CONFIRMACIÓN DE CITA
# ============================================================

@login_required
@cliente_required
def resumen_cita(request, id, dia):
    """Resumen de cita antes de confirmarla"""
    empresa = Empresa.objects.first()
    servicio = get_object_or_404(Servicio, id=id, empresa=empresa, activo=True)
    cliente = request.user.cliente

    hora_range = request.GET.get('hora')
    if not hora_range:
        messages.error(request, "Debes seleccionar un horario válido.")
        return redirect('horarios_servicio', id=id, dia=dia)

    try:
        inicio_str, fin_str = [h.strip() for h in hora_range.split('-')]
    except ValueError:
        messages.error(request, "Formato de horario no válido.")
        return redirect('horarios_servicio', id=id, dia=dia)

    fecha = get_next_date_for_day(dia)

    return render(request, 'cliente/resumen_cita.html', {
        'servicio': servicio,
        'empresa': empresa,
        'cliente': cliente,
        'dia': dia,
        'fecha': fecha,
        'fecha_iso': fecha.strftime("%Y-%m-%d"),
        'hora_inicio': inicio_str,
        'hora_fin': fin_str,
    })


@login_required
@cliente_required
def confirmar_cita(request):
    """Crea la cita luego de validar solapamientos"""
    if request.method != 'POST':
        return redirect('dashboard_cliente')

    empresa = Empresa.objects.first()
    cliente = request.user.cliente

    servicio_id = request.POST.get('servicio_id')
    fecha_str = request.POST.get('fecha')
    dia = request.POST.get('dia')
    hora_inicio_str = request.POST.get('hora_inicio')
    hora_fin_str = request.POST.get('hora_fin')

    servicio = get_object_or_404(Servicio, id=servicio_id, empresa=empresa, activo=True)

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        hora_inicio = datetime.strptime(hora_inicio_str, "%H:%M").time()
        hora_fin = datetime.strptime(hora_fin_str, "%H:%M").time()
    except Exception:
        messages.error(request, "Los datos de la cita no son válidos.")
        return redirect('horarios_servicio', id=servicio.id, dia=dia)

    citas_existentes = Cita.objects.filter(
        empresa=empresa,
        fecha=fecha
    ).exclude(estado="cancelada")

    for c in citas_existentes:
        if hora_inicio < c.hora_fin and hora_fin > c.hora_inicio:
            messages.error(request, "Ese horario ya no está disponible.")
            return redirect('horarios_servicio', id=servicio.id, dia=dia)

    Cita.objects.create(
        cliente=cliente,
        empresa=empresa,
        servicio=servicio,
        dia=dia,
        fecha=fecha,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        estado='pendiente',
    )

    messages.success(request, "Tu cita ha sido agendada correctamente.")
    return redirect('dashboard_cliente')


# ============================================================
# 11. CLIENTE – MIS CITAS
# ============================================================

@login_required
@cliente_required
def mis_citas(request):
    """Listado de citas futuras del cliente"""
    cliente = request.user.cliente
    hoy = date.today()

    citas = Cita.objects.filter(
        cliente=cliente,
        fecha__gte=hoy
    ).exclude(estado='cancelada').order_by('fecha', 'hora_inicio')

    return render(request, 'cliente/mis_citas.html', {'citas': citas})


@login_required
@cliente_required
def cancelar_cita(request, id):
    """Cancelación de cita por parte del cliente"""
    cliente = request.user.cliente
    cita = get_object_or_404(Cita, id=id, cliente=cliente)

    if cita.estado == 'confirmada':
        messages.error(request, "No puedes cancelar una cita confirmada.")
        return redirect('mis_citas')

    cita.estado = 'cancelada'
    cita.save()

    messages.success(request, "La cita fue cancelada correctamente.")
    return redirect('mis_citas')


# ============================================================
# 12. EMPRESA – CONFIGURACIÓN
# ============================================================

@login_required
@empresa_required
def editar_empresa(request):
    """Edición de la información de la empresa"""
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


# ============================================================
# 13. EMPRESA – SERVICIOS
# ============================================================

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
            messages.success(request, "El servicio fue creado exitosamente.")
            return redirect('listar_servicios')
        messages.error(request, "Revisa los datos del formulario.")
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
            messages.success(request, "El servicio se actualizó correctamente.")
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
        messages.success(request, "El servicio fue eliminado correctamente.")
        return redirect('listar_servicios')

    return render(request, 'empresa/servicios/eliminar_servicio.html', {'servicio': servicio})


# ============================================================
# 14. EMPRESA – CITAS
# ============================================================

@login_required
@empresa_required
def listar_citas_empresa(request):
    empresa = request.user.empresa

    filtro_fecha = request.GET.get("fecha")
    filtro_estado = request.GET.get("estado")
    filtro_cliente = request.GET.get("cliente")

    hoy = date.today()

    citas = Cita.objects.filter(empresa=empresa).order_by("fecha", "hora_inicio")

    if filtro_fecha == "hoy":
        citas = citas.filter(fecha=hoy)
    elif filtro_fecha == "manana":
        citas = citas.filter(fecha=hoy + timedelta(days=1))
    elif filtro_fecha == "semana":
        citas = citas.filter(fecha__range=(hoy, hoy + timedelta(days=7)))
    elif filtro_fecha == "mes":
        citas = citas.filter(fecha__month=hoy.month, fecha__year=hoy.year)

    if filtro_estado in ["pendiente", "confirmada", "cancelada"]:
        citas = citas.filter(estado=filtro_estado)

    if filtro_cliente:
        citas = citas.filter(cliente_id=filtro_cliente)

    clientes = Cliente.objects.order_by("user__username")

    return render(request, "empresa/citas/listar_citas.html", {
        "citas": citas,
        "clientes": clientes,
        "filtro_fecha": filtro_fecha,
        "filtro_estado": filtro_estado,
        "filtro_cliente": filtro_cliente,
    })


@login_required
@empresa_required
def confirmar_cita_empresa(request, id):
    empresa = request.user.empresa
    cita = get_object_or_404(Cita, id=id, empresa=empresa)

    if cita.estado != "pendiente":
        messages.warning(request, "Esta cita no se puede confirmar.")
        return redirect('listar_citas')

    cita.estado = "confirmada"
    cita.save()

    messages.success(request, "La cita ha sido confirmada.")
    return redirect('listar_citas')


@login_required
@empresa_required
def cancelar_cita_empresa(request, id):
    empresa = request.user.empresa
    cita = get_object_or_404(Cita, id=id, empresa=empresa)

    if cita.estado == "cancelada":
        messages.info(request, "La cita ya estaba cancelada.")
        return redirect('listar_citas')

    cita.estado = "cancelada"
    cita.save()

    messages.success(request, "La cita ha sido cancelada.")
    return redirect('listar_citas')


# ============================================================
# 15. EMPRESA – CLIENTES
# ============================================================

@login_required
@empresa_required
def listar_clientes(request):
    clientes = Cliente.objects.select_related('user').order_by('user__username')
    return render(request, 'empresa/clientes/listar_clientes.html', {'clientes': clientes})


@login_required
@empresa_required
def editar_cliente_admin(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    user = cliente.user

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()

        patron = r'^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s]+$'
        if not re.match(patron, username):
            messages.error(request, "El nombre de usuario solo puede contener letras y espacios.")
            return render(request, 'empresa/clientes/editar_cliente.html', {'cliente': cliente, 'user': user})

        if telefono and not telefono.isdigit():
            messages.error(request, "El teléfono solo puede contener números.")
            return render(request, 'empresa/clientes/editar_cliente.html', {'cliente': cliente, 'user': user})

        if User.objects.filter(username=username).exclude(id=user.id).exists():
            messages.error(request, "Este nombre de usuario ya está en uso.")
            return render(request, 'empresa/clientes/editar_cliente.html', {'cliente': cliente, 'user': user})

        user.username = username
        user.email = email
        user.is_active = 'is_active' in request.POST
        user.save()

        cliente.telefono = telefono
        cliente.save()

        messages.success(request, "Cliente actualizado correctamente.")
        return redirect('listar_clientes')

    return render(request, 'empresa/clientes/editar_cliente.html', {'cliente': cliente, 'user': user})


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


# ============================================================
# 16. EMPRESA – DISPONIBILIDAD
# ============================================================

@login_required
@empresa_required
def configurar_disponibilidad(request):
    """Configuración de horarios de disponibilidad de la empresa"""
    ensure_disponibilidad_inicial()
    dias = Disponibilidad.objects.all().order_by('id')

    if request.method == 'POST':
        for d in dias:
            ini_m = request.POST.get(f'inicio_m_{d.id}')
            fin_m = request.POST.get(f'fin_m_{d.id}')
            ini_t = request.POST.get(f'inicio_t_{d.id}')
            fin_t = request.POST.get(f'fin_t_{d.id}')
            activo = bool(request.POST.get(f'activo_{d.id}', False))

            if activo and (not ini_m or not fin_m or not ini_t or not fin_t):
                messages.warning(request, f"Completa los horarios para {d.get_dia_display()}.")
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

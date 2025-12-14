from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.utils import timezone
from datetime import timedelta
from functools import wraps
from core.models import Mesas, Sillas, Armarios, Cajoneras, Escritorios, Utensilios, Idea, UserClientes, Pago, Pedido, Factura
from core.forms import IdeaForm
from .models import EmpresaRegistrada
from .forms import EmpresaRegistroForm, EmpresaRegistroSimpleForm
import json
import hashlib
import pyotp
import qrcode
import io
import base64

# Decorador personalizado para verificar autenticación de empresas
def empresa_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'empresa_id' not in request.session:
            messages.warning(request, 'Debe iniciar sesión para acceder a esta página.')
            return redirect('loginEmpresa_login')
        return view_func(request, *args, **kwargs)
    return wrapper

# Importar vistas adicionales
from .views_estadisticas import estadisticas_view, inventario_view, actualizar_inventario_view, descargar_estadisticas_pdf

# Vista para registro de empresas simplificado
def registro_empresa_view(request):
    """Vista para el registro de nuevas empresas (simplificado)"""
    if request.method == 'POST':
        form = EmpresaRegistroSimpleForm(request.POST)
        if form.is_valid():
            try:
                empresa = form.save()
                # Guardar el ID de la empresa en la sesión para configurar 2FA
                request.session['empresa_temp_id'] = empresa.id
                messages.success(request, f'¡Empresa registrada exitosamente! Para iniciar sesión use su NIT: {empresa.nit}')
                return redirect('configurar_2fa_empresa')
            except Exception as e:
                messages.error(request, f'Error al registrar la empresa: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = EmpresaRegistroSimpleForm()
    
    return render(request, 'Empresas/registro_empresa_simple.html', {'form': form})

# Vista para login de empresas
def login_empresa_view(request):
    """Vista para el login de empresas registradas"""
    if request.method == 'POST':
        nombre_empresa = request.POST.get('username')
        password = request.POST.get('password')
        
        if not nombre_empresa or not password:
            messages.error(request, 'Por favor complete todos los campos.')
            return render(request, 'Empresas/login_empresa.html')
        
        try:
            # Buscar la empresa por nombre (case insensitive)
            try:
                empresa = EmpresaRegistrada.objects.get(nombre_empresa__iexact=nombre_empresa)
            except EmpresaRegistrada.DoesNotExist:
                messages.error(request, 'No existe una empresa con ese nombre.')
                return render(request, 'Empresas/login_empresa.html')
            
            # Verificar la contraseña
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if empresa.password != password_hash:
                messages.error(request, 'Contraseña incorrecta.')
                return render(request, 'Empresas/login_empresa.html')
            
            # Verificar si la cuenta está activa
            if not empresa.is_active:
                messages.error(request, 'Su cuenta está inactiva. Contacte al administrador.')
                return render(request, 'Empresas/login_empresa.html')
            
            # Verificar si tiene 2FA configurado (OBLIGATORIO)
            if not empresa.two_factor_enabled:
                messages.warning(request, 'Debe configurar la autenticación de dos factores para continuar.')
                request.session['empresa_temp_id'] = empresa.id
                return redirect('configurar_2fa_empresa')
            
            # Si tiene 2FA habilitado, solicitar código
            request.session['empresa_login_temp'] = empresa.id
            return redirect('verificar_2fa_login_empresa')
                
        except Exception as e:
            messages.error(request, f'Error al iniciar sesión: {str(e)}')
    
    return render(request, 'Empresas/login_empresa.html')

# Vista para verificar código 2FA en login
def verificar_2fa_empresa_login(request):
    """Vista para verificar el código TOTP durante el login"""
    empresa_id = request.session.get('empresa_login_temp')
    
    if not empresa_id:
        messages.error(request, 'Sesión inválida.')
        return redirect('loginEmpresa_login')
    
    try:
        empresa = EmpresaRegistrada.objects.get(id=empresa_id)
    except EmpresaRegistrada.DoesNotExist:
        messages.error(request, 'Empresa no encontrada.')
        return redirect('loginEmpresa_login')
    
    # Verificar que la empresa tenga configurado el secret de 2FA
    if not empresa.two_factor_secret:
        messages.warning(request, 'Debe configurar la autenticación de dos factores para continuar.')
        request.session['empresa_temp_id'] = empresa.id
        del request.session['empresa_login_temp']
        return redirect('configurar_2fa_empresa')
    
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        
        if not codigo:
            messages.error(request, 'Debe ingresar el código de verificación.')
            return render(request, 'Empresas/verificar_2fa_login.html', {'empresa': empresa})
        
        # Verificar código TOTP
        totp = pyotp.TOTP(empresa.two_factor_secret)
        if totp.verify(codigo, valid_window=1):  # Permite 30 segundos antes/después
            # Código correcto - iniciar sesión
            request.session['empresa_id'] = empresa.id
            request.session['empresa_username'] = empresa.username
            request.session['empresa_nombre'] = empresa.nombre_empresa
            empresa.last_login = timezone.now()
            empresa.save()
            
            del request.session['empresa_login_temp']
            messages.success(request, f'¡Bienvenido {empresa.nombre_empresa}!')
            return redirect('dashboardEmpresa')
        else:
            messages.error(request, 'Código incorrecto. Intente nuevamente.')
    
    return render(request, 'Empresas/verificar_2fa_login.html', {'empresa': empresa})

# Vista para configurar 2FA después del registro (OBLIGATORIO)
def configurar_2fa_empresa_view(request):
    """Vista para configurar la autenticación de dos factores con código QR (OBLIGATORIO)"""
    empresa_id = request.session.get('empresa_temp_id')
    
    if not empresa_id:
        messages.error(request, 'Sesión inválida. Por favor, registre su empresa nuevamente.')
        return redirect('registro_empresa')
    
    try:
        empresa = EmpresaRegistrada.objects.get(id=empresa_id)
    except EmpresaRegistrada.DoesNotExist:
        messages.error(request, 'Empresa no encontrada.')
        return redirect('registro_empresa')
    
    # Generar clave secreta si no existe
    if not empresa.two_factor_secret:
        empresa.two_factor_secret = pyotp.random_base32()
        empresa.save()
    
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        
        if not codigo:
            messages.error(request, 'Debe ingresar el código de verificación.')
        else:
            # Verificar código TOTP
            totp = pyotp.TOTP(empresa.two_factor_secret)
            if totp.verify(codigo, valid_window=1):
                # Código correcto - activar 2FA
                empresa.two_factor_enabled = True
                empresa.save()
                
                del request.session['empresa_temp_id']
                messages.success(request, '¡Autenticación de dos factores configurada exitosamente! Ya puede iniciar sesión.')
                return redirect('loginEmpresa_login')
            else:
                messages.error(request, 'Código incorrecto. Escanee el QR nuevamente e intente con el código actual.')
    
    # Generar código QR
    totp = pyotp.TOTP(empresa.two_factor_secret)
    provisioning_uri = totp.provisioning_uri(
        name=empresa.nombre_empresa,
        issuer_name='TIHR - Tu Idea Hecha Realidad'
    )
    
    # Crear imagen QR
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir a base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    context = {
        'empresa': empresa,
        'obligatorio': True,
        'qr_code': qr_code_base64,
        'secret_key': empresa.two_factor_secret
    }
    
    return render(request, 'Empresas/configurar_2fa.html', context)

# Create your views here.

@empresa_login_required
def Dasboard_view(request):
    return render(request,'Empresas/dashboardEmpresa.html')

def GestionarProductos_view(request):
    # Obtener todos los productos de todas las categorías
    mesas = Mesas.objects.all()
    sillas = Sillas.objects.all()
    armarios = Armarios.objects.all()
    cajoneras = Cajoneras.objects.all()
    escritorios = Escritorios.objects.all()
    utensilios = Utensilios.objects.all()
    
    context = {
        'mesas': mesas,
        'sillas': sillas,
        'armarios': armarios,
        'cajoneras': cajoneras,
        'escritorios': escritorios,
        'utensilios': utensilios,
    }
    return render(request, 'Empresas/GestiProductos.html', context)

def Armarios_view2(request):
    armarios = Armarios.objects.all()
    context = {'armarios':armarios}
    return render(request, 'Empresas/GestiProductos.html', context)

def agregar_producto_view2(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        precio = request.POST.get('precio')
        imagen = request.FILES.get('imagen')
        categoria = request.POST.get('categoria')

        # Guardar el producto en el modelo correspondiente según la categoría
        if categoria == 'mesas':
            nuevo_producto = Mesas(
                nombre1=nombre,
                descripcion1=descripcion,
                precio1=precio,
                imagen1=imagen
            )
        elif categoria == 'sillas':
            nuevo_producto = Sillas(
                nombre2=nombre,
                descripcion2=descripcion,
                precio2=precio,
                imagen2=imagen
            )
        elif categoria == 'armarios':
            nuevo_producto = Armarios(
                nombre3=nombre,
                descripcion3=descripcion,
                precio3=precio,
                imagen3=imagen
            )
        elif categoria == 'cajoneras':
            nuevo_producto = Cajoneras(
                nombre4=nombre,
                descripcion4=descripcion,
                precio4=precio,
                imagen4=imagen
            )
        elif categoria == 'escritorios':
            nuevo_producto = Escritorios(
                nombre5=nombre,
                descripcion5=descripcion,
                precio5=precio,
                imagen5=imagen
            )
        elif categoria == 'utensilios':
            nuevo_producto = Utensilios(
                nombre6=nombre,
                descripcion6=descripcion,
                precio6=precio,
                imagen6=imagen
            )
        else:
            messages.error(request, 'Categoría no válida')
            return render(request, 'Empresas/agregar_producto2.html')
        
        nuevo_producto.save()
        messages.success(request, 'Producto agregado exitosamente')
        return redirect('GestiProductos')

    return render(request, 'Empresas/agregar_producto2.html')

def editar_producto_view2(request, categoria, producto_id):
    # Obtener el producto según la categoría
    producto = None
    modelo = None
    
    if categoria == 'mesas':
        modelo = Mesas
        try:
            producto = Mesas.objects.get(id=producto_id)
        except Mesas.DoesNotExist:
            return redirect('GestiProductos')
    elif categoria == 'sillas':
        modelo = Sillas
        try:
            producto = Sillas.objects.get(id=producto_id)
        except Sillas.DoesNotExist:
            return redirect('GestiProductos')
    elif categoria == 'armarios':
        modelo = Armarios
        try:
            producto = Armarios.objects.get(id=producto_id)
        except Armarios.DoesNotExist:
            return redirect('GestiProductos')
    elif categoria == 'cajoneras':
        modelo = Cajoneras
        try:
            producto = Cajoneras.objects.get(id=producto_id)
        except Cajoneras.DoesNotExist:
            return redirect('GestiProductos')
    elif categoria == 'escritorios':
        modelo = Escritorios
        try:
            producto = Escritorios.objects.get(id=producto_id)
        except Escritorios.DoesNotExist:
            return redirect('GestiProductos')
    elif categoria == 'utensilios':
        modelo = Utensilios
        try:
            producto = Utensilios.objects.get(id=producto_id)
        except Utensilios.DoesNotExist:
            return redirect('GestiProductos')
    else:
        return redirect('GestiProductos')

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        precio = request.POST.get('precio')
        
        # Actualizar según la categoría
        if categoria == 'mesas':
            producto.nombre1 = nombre
            producto.descripcion1 = descripcion
            producto.precio1 = precio
            if 'imagen' in request.FILES:
                producto.imagen1 = request.FILES['imagen']
        elif categoria == 'sillas':
            producto.nombre2 = nombre
            producto.descripcion2 = descripcion
            producto.precio2 = precio
            if 'imagen' in request.FILES:
                producto.imagen2 = request.FILES['imagen']
        elif categoria == 'armarios':
            producto.nombre3 = nombre
            producto.descripcion3 = descripcion
            producto.precio3 = precio
            if 'imagen' in request.FILES:
                producto.imagen3 = request.FILES['imagen']
        elif categoria == 'cajoneras':
            producto.nombre4 = nombre
            producto.descripcion4 = descripcion
            producto.precio4 = precio
            if 'imagen' in request.FILES:
                producto.imagen4 = request.FILES['imagen']
        elif categoria == 'escritorios':
            producto.nombre5 = nombre
            producto.descripcion5 = descripcion
            producto.precio5 = precio
            if 'imagen' in request.FILES:
                producto.imagen5 = request.FILES['imagen']
        elif categoria == 'utensilios':
            producto.nombre6 = nombre
            producto.descripcion6 = descripcion
            producto.precio6 = precio
            if 'imagen' in request.FILES:
                producto.imagen6 = request.FILES['imagen']
        
        producto.save()
        messages.success(request, 'Producto actualizado exitosamente')
        return redirect('GestiProductos')

    context = {
        'producto': producto,
        'categoria': categoria
    }
    return render(request, 'Empresas/editar_producto2.html', context)

def eliminar_producto_view2(request, categoria, producto_id):
    # Cambiar estado de activo/inactivo del producto según la categoría
    try:
        if categoria == 'mesas':
            producto = Mesas.objects.get(id=producto_id)
        elif categoria == 'sillas':
            producto = Sillas.objects.get(id=producto_id)
        elif categoria == 'armarios':
            producto = Armarios.objects.get(id=producto_id)
        elif categoria == 'cajoneras':
            producto = Cajoneras.objects.get(id=producto_id)
        elif categoria == 'escritorios':
            producto = Escritorios.objects.get(id=producto_id)
        elif categoria == 'utensilios':
            producto = Utensilios.objects.get(id=producto_id)
        else:
            return redirect('GestiProductos')
        
        # Cambiar el estado en lugar de eliminar
        producto.is_active = not producto.is_active
        producto.save()
        
        if producto.is_active:
            messages.success(request, 'Producto habilitado exitosamente')
        else:
            messages.success(request, 'Producto inhabilitado exitosamente')
    except:
        messages.error(request, 'Error al cambiar el estado del producto')
    
    return redirect('GestiProductos')

def listid(request):
    return render(request,'Empresas/listid.html')

@empresa_login_required
def empresa_ideas_view(request):
    """
    Vista para que las empresas gestionen las ideas.
    """
    # Obtener empresa de la sesión
    try:
        empresa = EmpresaRegistrada.objects.get(id=request.session['empresa_id'])
    except EmpresaRegistrada.DoesNotExist:
        return redirect('loginEmpresa')

    # Agrupar ideas por autor (usuario)
    from django.db.models import Count, Q
    
    # Obtener todas las ideas
    todas_ideas = Idea.objects.values_list('autor', flat=True).distinct()
    
    # Obtener usuarios que tienen ideas
    usuarios_con_ideas = []
    for username in todas_ideas:
        try:
            usuario = UserClientes.objects.get(usernameCliente=username)
            cantidad = Idea.objects.filter(autor=username).count()
            usuario.cantidad_ideas = cantidad
            usuarios_con_ideas.append(usuario)
        except UserClientes.DoesNotExist:
            continue
    
    # Ordenar por cantidad de ideas
    usuarios_con_ideas.sort(key=lambda x: x.cantidad_ideas, reverse=True)
    
    context = {
        'usuarios_con_ideas': usuarios_con_ideas,
        'empresa': empresa
    }
    
    return render(request, 'Empresas/ideas_empresa.html', context)
    
def perfilUsuario_view(request):
    return render(request,'Empresas/listid.html')

@empresa_login_required
def ver_imagen_idea(request, idea_id):
    """
    Vista para que las empresas vean la imagen de una idea.
    """
    
    idea = get_object_or_404(Idea, pk=idea_id)
    
    context = {
        'idea': idea
    }
    
    return render(request, 'Empresas/ver_imagen_idea.html', context)

@empresa_login_required
def ver_modelo_3d_idea(request, idea_id):
    """
    Vista para que las empresas vean el modelo 3D de una idea.
    """
    
    idea = get_object_or_404(Idea, pk=idea_id)
    
    context = {
        'idea': idea
    }
    
    return render(request, 'Empresas/ver_modelo_3d_idea.html', context)

@ensure_csrf_cookie
@empresa_login_required
def usuarios_view(request):
    """
    Vista para gestión de usuarios (clientes y empresas)
    """
    users = UserClientes.objects.all()
    empresas = EmpresaRegistrada.objects.all()
    context = {
        'users': users,
        'empresas': empresas,
        'csrf_token': get_token(request)
    }
    return render(request,'Empresas/usuarios2.html', context)

def get_csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})

@require_POST
def toggle_user_status(request, user_id, user_type, action):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
    
    if action not in ['enable', 'disable']:
        return JsonResponse({'success': False, 'error': 'Acción inválida'}, status=400)
        
    try:
        if user_type == 'cliente':
            user = UserClientes.objects.get(id=user_id)
        elif user_type == 'empresa':
            user = EmpresaRegistrada.objects.get(id=user_id)
        else:
            return JsonResponse({'success': False, 'error': 'Tipo de usuario inválido'}, status=400)
            
        # Actualizar el estado
        new_status = action == 'enable'
        if user.is_active == new_status:
            return JsonResponse({'success': False, 'error': 'El usuario ya está en ese estado'}, status=400)
            
        user.is_active = new_status
        user.status_changed_at = timezone.now()
        user.save()
        
        return JsonResponse({
            'success': True,
            'status': 'Activo' if user.is_active else 'Inactivo',
            'action': 'disable' if user.is_active else 'enable'
        })
    except (UserClientes.DoesNotExist, EmpresaRegistrada.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@empresa_login_required
def gestion_pedidos_view(request):
    """Vista para gestión de pedidos por parte de la empresa"""
    
    # Agrupar pedidos por cliente
    from django.db.models import Count
    
    clientes_con_pedidos = UserClientes.objects.filter(
        pedidos__isnull=False
    ).annotate(
        cantidad_pedidos=Count('pedidos')
    ).order_by('-cantidad_pedidos')
    
    context = {
        'clientes_con_pedidos': clientes_con_pedidos,
    }
    
    return render(request, 'Empresas/gestion_pedidos.html', context)


@empresa_login_required
def obtener_pedidos_cliente_view(request, cliente_id):
    """Vista para obtener los pedidos de un cliente específico"""
    try:
        cliente = UserClientes.objects.get(id=cliente_id)
        pedidos = Pedido.objects.filter(cliente=cliente).select_related('pago').order_by('-fecha_creacion')
        
        pedidos_data = []
        for pedido in pedidos:
            try:
                productos_parseados = json.loads(pedido.productos)
                cantidad_productos = sum(int(p.get('cantidad', 0)) for p in productos_parseados)
            except:
                productos_parseados = []
                cantidad_productos = 0
            
            pedidos_data.append({
                'id': pedido.id,
                'estado': pedido.estado,
                'monto_total': float(pedido.monto_total),
                'cantidad_productos': cantidad_productos,
                'productos': productos_parseados,
                'fecha_creacion': pedido.fecha_creacion.strftime('%d/%m/%Y'),
                'numero_seguimiento': pedido.numero_seguimiento or '',
                'empresa_envio': pedido.empresa_envio or '',
                'direccion': pedido.direccion or 'No especificada',
                'ciudad': pedido.ciudad or '',
                'departamento': pedido.departamento or '',
                'pago_id': pedido.pago.id,
            })
        
        return JsonResponse({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'username': cliente.usernameCliente,
                'email': cliente.email
            },
            'pedidos': pedidos_data
        })
        
    except UserClientes.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cliente no encontrado'}, status=404)
    except Exception as e:
        print(f"Error en obtener_pedidos_cliente_view: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@empresa_login_required
@require_POST
def actualizar_estado_pedido_view(request, pedido_id):
    """Vista para actualizar el estado de un pedido"""
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        nuevo_estado = request.POST.get('estado')
        numero_seguimiento = request.POST.get('numero_seguimiento', '')
        empresa_envio = request.POST.get('empresa_envio', '')
        
        # Validar estado
        estados_validos = ['procesando', 'empacado', 'enviado', 'en_transito', 'entregado', 'cancelado']
        if nuevo_estado not in estados_validos:
            return JsonResponse({'success': False, 'error': 'Estado no válido'}, status=400)
        
        pedido.estado = nuevo_estado
        
        if numero_seguimiento:
            pedido.numero_seguimiento = numero_seguimiento
        if empresa_envio:
            pedido.empresa_envio = empresa_envio
        
        # Si se marca como entregado, guardar fecha
        if nuevo_estado == 'entregado' and not pedido.fecha_entrega_real:
            pedido.fecha_entrega_real = timezone.now()
        
        pedido.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Estado del pedido actualizado'
        })
        
    except Pedido.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pedido no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@empresa_login_required
def gestion_pagos_view(request):
    """Vista para gestión de pagos por parte de la empresa"""
    
    # Agrupar pagos por cliente
    from django.db.models import Count
    
    clientes_con_pagos = UserClientes.objects.filter(
        pagos__isnull=False
    ).annotate(
        cantidad_pagos=Count('pagos')
    ).order_by('-cantidad_pagos')
    
    context = {
        'clientes_con_pagos': clientes_con_pagos,
    }
    
    return render(request, 'Empresas/gestion_pagos.html', context)


@empresa_login_required
def obtener_pagos_cliente_view(request, cliente_id):
    """Vista para obtener los pagos de un cliente específico"""
    try:
        cliente = UserClientes.objects.get(id=cliente_id)
        pagos = Pago.objects.filter(cliente=cliente).order_by('-fecha_creacion')
        
        pagos_data = []
        for pago in pagos:
            try:
                productos_parseados = json.loads(pago.productos)
                cantidad_productos = sum(int(p.get('cantidad', 0)) for p in productos_parseados)
            except:
                productos_parseados = []
                cantidad_productos = 0
            
            pagos_data.append({
                'id': pago.id,
                'estado': pago.estado,
                'monto_total': float(pago.monto_total),
                'cantidad_productos': cantidad_productos,
                'productos': productos_parseados,
                'fecha_creacion': pago.fecha_creacion.strftime('%d/%m/%Y'),
                'comprobante_url': pago.comprobante.url if pago.comprobante else '',
                'notas_empresa': pago.notas_empresa or '',
            })
        
        return JsonResponse({
            'success': True,
            'pagos': pagos_data
        })
    except UserClientes.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cliente no encontrado'}, status=404)
    except Exception as e:
        print(f"Error en obtener_pagos_cliente_view: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@empresa_login_required
@require_POST
def confirmar_pago_view(request, pago_id):
    """Vista para confirmar un pago y crear pedido automáticamente"""
    try:
        pago = Pago.objects.get(id=pago_id)
        
        # Verificar que el pago no haya sido confirmado anteriormente
        if pago.estado == 'confirmado':
            return JsonResponse({'success': False, 'error': 'Este pago ya fue confirmado anteriormente'}, status=400)
        
        # Descontar productos del inventario ANTES de confirmar
        try:
            import json
            from core.models import Mesas, Sillas, Armarios, Cajoneras, Escritorios, Utensilios
            
            productos = json.loads(pago.productos)
            print(f"=== INICIANDO DEDUCCIÓN DE INVENTARIO ===")
            print(f"Pago ID: {pago.id}")
            print(f"Productos a descontar: {productos}")
            
            # Mapeo de categorías a modelos (soportar múltiples formatos)
            modelos_map = {
                'mesas': Mesas,
                'mesa': Mesas,
                'sillas': Sillas,
                'silla': Sillas,
                'armarios': Armarios,
                'armario': Armarios,
                'cajoneras': Cajoneras,
                'cajonera': Cajoneras,
                'escritorios': Escritorios,
                'escritorio': Escritorios,
                'utensilios': Utensilios,
                'utensilio': Utensilios,
            }
            
            # Primero verificar que hay suficiente stock de todos los productos
            items_a_descontar = []
            for producto in productos:
                categoria = producto.get('categoria', producto.get('tipo', '')).lower()
                producto_id = producto.get('id')
                cantidad = int(producto.get('cantidad', 0))
                
                print(f"\n>>> Producto: {producto}")
                print(f">>> Categoría extraída: '{categoria}'")
                print(f">>> ID: {producto_id}, Cantidad: {cantidad}")
                
                modelo = modelos_map.get(categoria)
                
                if modelo and producto_id and cantidad > 0:
                    try:
                        item = modelo.objects.get(id=producto_id)
                        print(f"Verificando: {categoria} ID={producto_id}, Stock={item.cantidad_disponible}, Solicitado={cantidad}")
                        
                        if item.cantidad_disponible < cantidad:
                            print(f"⚠ Stock insuficiente para {categoria} ID {producto_id}")
                            return JsonResponse({
                                'success': False, 
                                'error': f'Stock insuficiente para {categoria}. Disponible: {item.cantidad_disponible}, Solicitado: {cantidad}'
                            }, status=400)
                        
                        items_a_descontar.append({'item': item, 'cantidad': cantidad, 'categoria': categoria})
                    except modelo.DoesNotExist:
                        print(f"✗ Producto {categoria} ID {producto_id} no encontrado")
                        return JsonResponse({
                            'success': False, 
                            'error': f'Producto {categoria} no encontrado en el inventario'
                        }, status=404)
            
            # Si llegamos aquí, hay suficiente stock. Proceder a descontar
            for data in items_a_descontar:
                item = data['item']
                cantidad = data['cantidad']
                categoria = data['categoria']
                
                stock_anterior = item.cantidad_disponible
                item.cantidad_disponible -= cantidad
                
                # Deshabilitar automáticamente si el stock llega a 0
                if item.cantidad_disponible <= 0:
                    item.is_active = False
                    print(f"⚠ {categoria} ID={item.id} deshabilitado automáticamente (stock agotado)")
                
                item.save()
                print(f"✓ {categoria} actualizado: {stock_anterior} -> {item.cantidad_disponible}")
            
            print(f"=== FIN DEDUCCIÓN DE INVENTARIO ===")
        except json.JSONDecodeError as e:
            print(f"ERROR al parsear productos JSON: {e}")
            return JsonResponse({'success': False, 'error': 'Error al procesar productos'}, status=500)
        except Exception as e:
            print(f"ERROR CRÍTICO al descontar inventario: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': f'Error al descontar inventario: {str(e)}'}, status=500)
        
        # Ahora sí confirmar el pago
        pago.estado = 'confirmado'
        pago.fecha_confirmacion = timezone.now()
        
        # Obtener notas opcionales
        notas = request.POST.get('notas', '')
        if notas:
            pago.notas_empresa = notas
        
        pago.save()
        
        # Verificar si ya existe un pedido para este pago
        if not hasattr(pago, 'pedido'):
            # Obtener datos guardados del cliente si existen
            cliente = pago.cliente
            
            # Crear el pedido con los datos guardados del cliente (si los tiene)
            pedido = Pedido.objects.create(
                pago=pago,
                cliente=cliente,
                productos=pago.productos,
                monto_total=pago.monto_total,
                estado='procesando',
                fecha_entrega_estimada=timezone.now().date() + timedelta(days=7),
                # Auto-rellenar con datos guardados del cliente
                nombre_completo=cliente.nombre_completo if cliente.nombre_completo else '',
                telefono=cliente.telefono if cliente.telefono else '',
                direccion=cliente.direccion if cliente.direccion else '',
                ciudad=cliente.ciudad if cliente.ciudad else '',
                departamento=cliente.departamento if cliente.departamento else '',
                codigo_postal=cliente.codigo_postal if cliente.codigo_postal else ''
            )
            print(f"Pedido #{pedido.id} creado exitosamente con datos del cliente")
        
        # Generar factura automáticamente
        try:
            # Verificar si ya existe una factura para este pago
            if hasattr(pago, 'factura'):
                print(f"Factura ya existe para el pago #{pago.id}: {pago.factura.numero_factura}")
            else:
                # Generar número de factura único
                numero_factura = f"FACT-{pago.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
                
                # Crear la factura usando los datos del pago (que el cliente ingresó en el formulario)
                factura = Factura.objects.create(
                    pago=pago,
                    numero_factura=numero_factura,
                    cliente=cliente,
                    nombre_cliente=pago.nombre_completo if pago.nombre_completo else cliente.usernameCliente,
                    email_cliente=pago.email if pago.email else cliente.email,
                    telefono_cliente=pago.telefono if pago.telefono else '',
                    direccion_cliente=pago.direccion if pago.direccion else '',
                    ciudad_cliente=cliente.ciudad if cliente.ciudad else '',
                    departamento_cliente=cliente.departamento if cliente.departamento else '',
                    productos=pago.productos,  # Mismo JSON de productos
                    subtotal=pago.monto_total,
                    impuestos=0,  # Por ahora sin impuestos
                    total=pago.monto_total
                )
                print(f"✅ Factura {factura.numero_factura} generada exitosamente automáticamente")
        except Exception as e:
            print(f"ERROR al generar factura: {e}")
            import traceback
            traceback.print_exc()
            # No retornar error, solo log - la factura no es crítica para el flujo
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Pago confirmado, inventario actualizado y pedido creado. El cliente debe completar sus datos de envío.',
            'redirect_url': f'/crear-pedido/{pago.id}/'
        })
        
    except Pago.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pago no encontrado'}, status=404)
    except Exception as e:
        print(f"ERROR GENERAL en confirmar_pago_view: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@empresa_login_required
@require_POST  
def rechazar_pago_view(request, pago_id):
    """Vista para rechazar un pago"""
    try:
        from core.models import MensajePago
        
        pago = Pago.objects.get(id=pago_id)
        empresa = EmpresaRegistrada.objects.get(id=request.session['empresa_id'])
        
        # Obtener notas obligatorias al rechazar
        notas = request.POST.get('notas', '')
        if not notas:
            return JsonResponse({'success': False, 'error': 'Debes proporcionar una razón para rechazar el pago'}, status=400)
        
        pago.estado = 'rechazado'
        pago.notas_empresa = notas
        pago.save()
        
        # Crear mensaje inicial en el chat
        MensajePago.objects.create(
            pago=pago,
            remitente_tipo='empresa',
            remitente_nombre=empresa.username,
            mensaje=f"Pago rechazado. Motivo: {notas}",
            leido=False
        )
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Pago rechazado'
        })
        
    except Pago.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pago no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
def update_user(request):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
        
    try:
        user_id = request.POST.get('userId')
        user_type = request.POST.get('userType')
        username = request.POST.get('username')
        
        if not user_id or not user_type or not username:
            return JsonResponse({'success': False, 'error': 'Faltan datos requeridos'}, status=400)
        
        if user_type == 'cliente':
            user = UserClientes.objects.get(id=user_id)
            # Verificar si el nombre de usuario ya existe
            if UserClientes.objects.filter(usernameCliente=username).exclude(id=user_id).exists():
                return JsonResponse({'success': False, 'error': 'El nombre de usuario ya está en uso'}, status=400)
            
            # Validar email
            email = request.POST.get('email')
            if not email:
                return JsonResponse({'success': False, 'error': 'El email es requerido'}, status=400)
                
            user.usernameCliente = username
            user.email = email
        elif user_type == 'empresa':
            user = EmpresaRegistrada.objects.get(id=user_id)
            # Verificar si el nombre de usuario ya existe
            if EmpresaRegistrada.objects.filter(username=username).exclude(id=user_id).exists():
                return JsonResponse({'success': False, 'error': 'El nombre de usuario ya está en uso'}, status=400)
            
            # Actualizar email de empresa también
            email = request.POST.get('email')
            if email:
                user.email = email
            
            user.username = username
        else:
            return JsonResponse({'success': False, 'error': 'Tipo de usuario inválido'}, status=400)
            
        user.save()
        return JsonResponse({
            'success': True,
            'message': 'Usuario actualizado correctamente',
            'data': {
                'id': user.id,
                'username': username,
                'email': getattr(user, 'email', None),
                'type': user_type,
                'is_active': user.is_active
            }
        })
    except (UserClientes.DoesNotExist, EmpresaRegistrada.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# La función estadisticas_view se importa desde views_estadisticas.py
# No debe estar duplicada aquí

@empresa_login_required
@require_POST
def contactar_usuario_idea(request, idea_id):
    """Vista para que la empresa contacte al usuario sobre la idea"""
    from core.models import MensajeIdea
    
    print(f"=== CONTACTAR USUARIO IDEA ===")
    print(f"Idea ID: {idea_id}")
    print(f"Session empresa_id: {request.session.get('empresa_id')}")
    print(f"POST data: {request.POST}")
    
    try:
        empresa = EmpresaRegistrada.objects.get(id=request.session['empresa_id'])
        print(f"Empresa encontrada: {empresa.username}")
        
        idea = Idea.objects.get(id=idea_id)
        print(f"Idea encontrada: {idea.titulo}")
        
        # Verificar que la empresa es la asignada
        if idea.empresa_asignada != empresa:
            print(f"ERROR: Empresa no asignada. Asignada: {idea.empresa_asignada}, Actual: {empresa}")
            return JsonResponse({'success': False, 'error': 'No tienes permiso para contactar sobre esta idea'}, status=403)
        
        mensaje = request.POST.get('mensaje', '')
        print(f"Mensaje recibido: '{mensaje}'")
        
        if not mensaje:
            print("ERROR: Mensaje vacío")
            return JsonResponse({'success': False, 'error': 'Debes escribir un mensaje'}, status=400)
        
        # Crear mensaje en el sistema de chat
        MensajeIdea.objects.create(
            idea=idea,
            remitente_tipo='empresa',
            remitente_nombre=empresa.username,
            mensaje=mensaje,
            leido=False,
            es_solicitud_permiso=False
        )
        
        # Mantener compatibilidad con el campo antiguo
        idea.mensaje_empresa = mensaje
        idea.save()
        print("Mensaje guardado exitosamente")
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Mensaje enviado al usuario exitosamente'
        })
        
    except Idea.DoesNotExist:
        print("ERROR: Idea no encontrada")
        return JsonResponse({'success': False, 'error': 'Idea no encontrada'}, status=404)
    except EmpresaRegistrada.DoesNotExist:
        print("ERROR: Empresa no encontrada")
        return JsonResponse({'success': False, 'error': 'Empresa no encontrada'}, status=404)
    except Exception as e:
        print(f"ERROR INESPERADO: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@empresa_login_required
@require_POST
def solicitar_permiso_publicacion(request, idea_id):
    """Vista para que la empresa solicite permiso para publicar la idea"""
    from core.models import MensajeIdea
    
    print(f"=== SOLICITAR PERMISO PUBLICACIÓN ===")
    print(f"Idea ID: {idea_id}")
    print(f"Session empresa_id: {request.session.get('empresa_id')}")
    print(f"POST data: {request.POST}")
    
    try:
        empresa = EmpresaRegistrada.objects.get(id=request.session['empresa_id'])
        print(f"Empresa encontrada: {empresa.username}")
        
        idea = Idea.objects.get(id=idea_id)
        print(f"Idea encontrada: {idea.titulo}, Estado: {idea.estado}")
        
        # Verificar que la empresa es la asignada y la idea está finalizada
        # Comparar usando el username ya que idea.empresa_asignada es UserEmpresa
        if not idea.empresa_asignada or idea.empresa_asignada.usernameEmpresa != empresa.username:
            print(f"ERROR: Empresa no asignada. Asignada: {idea.empresa_asignada}, Actual: {empresa.username}")
            return JsonResponse({'success': False, 'error': 'No tienes permiso sobre esta idea'}, status=403)
        
        if idea.estado != 'finalizada':
            print(f"ERROR: Estado incorrecto. Estado actual: {idea.estado}")
            return JsonResponse({'success': False, 'error': 'La idea debe estar finalizada'}, status=400)
        
        mensaje = request.POST.get('mensaje', '')
        print(f"Mensaje recibido: '{mensaje}'")
        
        if not mensaje:
            print("ERROR: Mensaje vacío")
            return JsonResponse({'success': False, 'error': 'Debes escribir un mensaje de solicitud'}, status=400)
        
        # Crear mensaje de solicitud de permiso en el sistema de chat
        MensajeIdea.objects.create(
            idea=idea,
            remitente_tipo='empresa',
            remitente_nombre=empresa.username,
            mensaje=mensaje,
            leido=False,
            es_solicitud_permiso=True  # Marca especial para solicitudes de permiso
        )
        
        # Mantener compatibilidad con el campo antiguo
        idea.mensaje_empresa = mensaje
        idea.save()
        print("Solicitud guardada exitosamente")
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Solicitud de permiso enviada al usuario'
        })
        
    except Idea.DoesNotExist:
        print("ERROR: Idea no encontrada")
        return JsonResponse({'success': False, 'error': 'Idea no encontrada'}, status=404)
    except EmpresaRegistrada.DoesNotExist:
        print("ERROR: Empresa no encontrada")
        return JsonResponse({'success': False, 'error': 'Empresa no encontrada'}, status=404)
    except Exception as e:
        print(f"ERROR INESPERADO: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@empresa_login_required
def publicar_idea_como_producto(request, idea_id):
    """Vista para publicar una idea como producto"""
    try:
        empresa = EmpresaRegistrada.objects.get(id=request.session['empresa_id'])
        idea = Idea.objects.get(id=idea_id)
        
        # Verificar permisos (comparar usando username ya que empresa_asignada es UserEmpresa)
        if not idea.empresa_asignada or idea.empresa_asignada.usernameEmpresa != empresa.username:
            messages.error(request, 'No tienes permiso sobre esta idea')
            return redirect('empresa_ideas')
        
        if not idea.permiso_publicacion:
            messages.error(request, 'No tienes permiso del usuario para publicar esta idea')
            return redirect('empresa_ideas')
        
        if idea.publicada_como_producto:
            messages.warning(request, 'Esta idea ya fue publicada como producto')
            return redirect('empresa_ideas')
        
        if request.method == 'POST':
            nombre = request.POST.get('nombre')
            descripcion = request.POST.get('descripcion')
            precio = request.POST.get('precio')
            cantidad = request.POST.get('cantidad', 0)
            categoria = request.POST.get('categoria')
            
            if not all([nombre, descripcion, precio, categoria]):
                messages.error(request, 'Todos los campos son obligatorios')
                return render(request, 'Empresas/publicar_idea_producto.html', {'idea': idea})
            
            # Crear el producto según la categoría seleccionada
            try:
                if categoria == 'mesas':
                    producto = Mesas.objects.create(
                        nombre1=nombre,
                        descripcion1=descripcion,
                        precio1=precio,
                        imagen1=idea.imagen if idea.imagen else None,
                        cantidad_disponible=int(cantidad)
                    )
                elif categoria == 'sillas':
                    producto = Sillas.objects.create(
                        nombre2=nombre,
                        descripcion2=descripcion,
                        precio2=precio,
                        imagen2=idea.imagen if idea.imagen else None,
                        cantidad_disponible=int(cantidad)
                    )
                elif categoria == 'armarios':
                    producto = Armarios.objects.create(
                        nombre3=nombre,
                        descripcion3=descripcion,
                        precio3=precio,
                        imagen3=idea.imagen if idea.imagen else None,
                        cantidad_disponible=int(cantidad)
                    )
                elif categoria == 'cajoneras':
                    producto = Cajoneras.objects.create(
                        nombre4=nombre,
                        descripcion4=descripcion,
                        precio4=precio,
                        imagen4=idea.imagen if idea.imagen else None,
                        cantidad_disponible=int(cantidad)
                    )
                elif categoria == 'escritorios':
                    producto = Escritorios.objects.create(
                        nombre5=nombre,
                        descripcion5=descripcion,
                        precio5=precio,
                        imagen5=idea.imagen if idea.imagen else None,
                        cantidad_disponible=int(cantidad)
                    )
                elif categoria == 'utensilios':
                    producto = Utensilios.objects.create(
                        nombre6=nombre,
                        descripcion6=descripcion,
                        precio6=precio,
                        imagen6=idea.imagen if idea.imagen else None,
                        cantidad_disponible=int(cantidad)
                    )
                else:
                    messages.error(request, 'Categoría no válida')
                    return render(request, 'Empresas/publicar_idea_producto.html', {'idea': idea})
                
                # Marcar la idea como publicada
                idea.publicada_como_producto = True
                idea.fecha_publicacion = timezone.now()
                idea.save()
                
                messages.success(request, f'¡Idea publicada exitosamente como producto en la categoría {categoria}!')
                return redirect('GestiProductos')
                
            except Exception as e:
                messages.error(request, f'Error al crear el producto: {str(e)}')
                return render(request, 'Empresas/publicar_idea_producto.html', {'idea': idea})
        
        return render(request, 'Empresas/publicar_idea_producto.html', {'idea': idea})
        
    except Idea.DoesNotExist:
        messages.error(request, 'Idea no encontrada')
        return redirect('empresa_ideas')
    except EmpresaRegistrada.DoesNotExist:
        messages.error(request, 'Empresa no encontrada')
        return redirect('loginEmpresa')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('empresa_ideas')


@empresa_login_required
def obtener_mensajes_pago_view(request, pago_id):
    """Vista para obtener los mensajes de un pago"""
    from core.models import MensajePago
    
    try:
        pago = Pago.objects.get(id=pago_id)
        mensajes = MensajePago.objects.filter(pago=pago).order_by('fecha_envio')
        
        mensajes_data = []
        for mensaje in mensajes:
            mensajes_data.append({
                'id': mensaje.id,
                'remitente_tipo': mensaje.remitente_tipo,
                'remitente_nombre': mensaje.remitente_nombre,
                'mensaje': mensaje.mensaje,
                'imagen': mensaje.imagen.url if mensaje.imagen else None,
                'fecha_envio': mensaje.fecha_envio.strftime('%d/%m/%Y'),
                'leido': mensaje.leido
            })
        
        return JsonResponse({
            'success': True,
            'mensajes': mensajes_data
        })
        
    except Pago.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pago no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@empresa_login_required
@require_POST
def enviar_mensaje_pago_view(request, pago_id):
    """Vista para enviar un mensaje en el chat de un pago"""
    from core.models import MensajePago
    
    try:
        empresa = EmpresaRegistrada.objects.get(id=request.session['empresa_id'])
        pago = Pago.objects.get(id=pago_id)
        
        mensaje = request.POST.get('mensaje', '').strip()
        imagen = request.FILES.get('imagen', None)
        
        if not mensaje and not imagen:
            return JsonResponse({'success': False, 'error': 'Debes enviar un mensaje o una imagen'}, status=400)
        
        # Crear el mensaje
        nuevo_mensaje = MensajePago.objects.create(
            pago=pago,
            remitente_tipo='empresa',
            remitente_nombre=empresa.username,
            mensaje=mensaje if mensaje else '[Imagen enviada]',
            imagen=imagen,
            leido=False
        )
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Mensaje enviado exitosamente'
        })
        
    except Pago.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pago no encontrado'}, status=404)
    except EmpresaRegistrada.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Empresa no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@empresa_login_required
def obtener_ideas_usuario_view(request, usuario_id):
    """Vista para obtener las ideas de un usuario específico"""
    try:
        usuario = UserClientes.objects.get(id=usuario_id)
        ideas = Idea.objects.filter(autor=usuario.usernameCliente).order_by('-fecha_creacion')
        
        ideas_data = []
        for idea in ideas:
            ideas_data.append({
                'id': idea.id,
                'titulo': idea.titulo,
                'descripcion': idea.descripcion,
                'estado': idea.estado,
                'fecha_creacion': idea.fecha_creacion.strftime('%d/%m/%Y'),
                'tiene_imagen': bool(idea.imagen),
                'tiene_modelo_3d': bool(idea.modelo_3d),
                'empresa_asignada': idea.empresa_asignada.usernameEmpresa if idea.empresa_asignada else None,
                'permiso_publicacion': idea.permiso_publicacion,
                'publicada_como_producto': idea.publicada_como_producto,
            })
        
        return JsonResponse({
            'success': True,
            'usuario': {
                'id': usuario.id,
                'username': usuario.usernameCliente
            },
            'ideas': ideas_data
        })
        
    except UserClientes.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        print(f"Error en obtener_ideas_usuario_view: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@empresa_login_required
def obtener_detalle_idea_view(request, idea_id):
    """Vista para obtener los detalles completos de una idea con URLs de archivos"""
    try:
        idea = Idea.objects.get(id=idea_id)
        
        # Formatear medidas con nombres legibles
        medidas_formateadas = None
        if idea.medidas:
            from core.forms import CATEGORIA_MEDIDAS
            medidas_formateadas = {}
            categoria = idea.categoria
            
            if categoria in CATEGORIA_MEDIDAS:
                campos_categoria = CATEGORIA_MEDIDAS.get(categoria, [])
                for medida in campos_categoria:
                    campo = medida.get('campo')
                    if campo in idea.medidas:
                        nombre = medida.get('nombre', campo)
                        unidad = medida.get('unidad', '')
                        valor = idea.medidas[campo]
                        medidas_formateadas[nombre] = f"{valor} {unidad}"
        
        return JsonResponse({
            'success': True,
            'titulo': idea.titulo,
            'descripcion': idea.descripcion or 'Sin descripción',
            'categoria': idea.get_categoria_display(),
            'estado': idea.get_estado_display(),
            'autor': idea.autor,
            'fecha_creacion': idea.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'empresa_asignada': idea.empresa_asignada.usernameEmpresa if idea.empresa_asignada else 'No asignada',
            'medidas': medidas_formateadas,
            'imagen_url': idea.imagen.url if idea.imagen else None,
            'modelo_3d_url': idea.modelo_3d.url if idea.modelo_3d else None,
        })
        
    except Idea.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Idea no encontrada'}, status=404)
    except Exception as e:
        print(f"Error en obtener_detalle_idea_view: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@empresa_login_required
@require_POST
def rechazar_idea_view(request, idea_id):
    """Vista para rechazar una idea y enviar mensaje al usuario"""
    from core.models import MensajeIdea
    
    print(f"=== RECHAZAR IDEA ===")
    print(f"Idea ID: {idea_id}")
    print(f"Session empresa_id: {request.session.get('empresa_id')}")
    print(f"POST data: {request.POST}")
    
    try:
        empresa = EmpresaRegistrada.objects.get(id=request.session['empresa_id'])
        print(f"Empresa encontrada: {empresa.username}")
        
        idea = Idea.objects.get(id=idea_id)
        print(f"Idea encontrada: {idea.titulo}, Estado: {idea.estado}")
        
        # Verificar que la idea esté pendiente
        if idea.estado != 'pendiente':
            print(f"ERROR: Estado incorrecto. Estado actual: {idea.estado}")
            return JsonResponse({'success': False, 'error': 'Solo se pueden rechazar ideas pendientes'}, status=400)
        
        motivo = request.POST.get('motivo', '').strip()
        print(f"Motivo recibido: '{motivo}'")
        
        if not motivo:
            print("ERROR: Motivo vacío")
            return JsonResponse({'success': False, 'error': 'Debes proporcionar un motivo de rechazo'}, status=400)
        
        # Cambiar el estado a rechazado
        idea.estado = 'rechazada'
        idea.empresa_asignada = empresa  # Asignar empresa para poder chatear
        idea.save()
        
        # Crear mensaje de rechazo en el sistema de chat
        MensajeIdea.objects.create(
            idea=idea,
            remitente_tipo='empresa',
            remitente_nombre=empresa.username,
            mensaje=f"Idea rechazada. Motivo: {motivo}",
            leido=False,
            es_solicitud_permiso=False
        )
        
        print("Idea rechazada exitosamente")
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Idea rechazada y notificación enviada al usuario'
        })
        
    except Idea.DoesNotExist:
        print("ERROR: Idea no encontrada")
        return JsonResponse({'success': False, 'error': 'Idea no encontrada'}, status=404)
    except EmpresaRegistrada.DoesNotExist:
        print("ERROR: Empresa no encontrada")
        return JsonResponse({'success': False, 'error': 'Empresa no encontrada'}, status=404)
    except Exception as e:
        print(f"ERROR INESPERADO: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@empresa_login_required
@require_POST
def aceptar_idea_view(request, idea_id):
    """Vista para aceptar una idea pendiente"""
    try:
        # Obtener la empresa registrada y buscar el UserEmpresa correspondiente
        empresa_registrada = EmpresaRegistrada.objects.get(id=request.session['empresa_id'])
        
        # Buscar o crear un UserEmpresa con el username de la empresa
        from core.models import UserEmpresa
        user_empresa, created = UserEmpresa.objects.get_or_create(
            usernameEmpresa=empresa_registrada.username,
            defaults={
                'passwordEmpresa': empresa_registrada.password,
                'email': empresa_registrada.email,
                'is_active': empresa_registrada.is_active
            }
        )
        
        idea = Idea.objects.get(id=idea_id)
        
        # Verificar que la idea esté pendiente
        if idea.estado != 'pendiente':
            return JsonResponse({'success': False, 'error': 'Solo se pueden aceptar ideas pendientes'}, status=400)
        
        # Cambiar el estado a en_proceso
        idea.estado = 'en_proceso'
        idea.empresa_asignada = user_empresa
        idea.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Idea aceptada exitosamente',
            'nuevo_estado': 'en_proceso'
        })
        
    except Idea.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Idea no encontrada'}, status=404)
    except EmpresaRegistrada.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Empresa no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error: {str(e)}'}, status=500)


@empresa_login_required
@require_POST
def completar_idea_view(request, idea_id):
    """Vista para completar una idea en proceso"""
    try:
        # Obtener la empresa registrada y buscar el UserEmpresa correspondiente
        empresa_registrada = EmpresaRegistrada.objects.get(id=request.session['empresa_id'])
        
        from core.models import UserEmpresa
        try:
            user_empresa = UserEmpresa.objects.get(usernameEmpresa=empresa_registrada.username)
        except UserEmpresa.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Usuario empresa no encontrado'}, status=404)
        
        idea = Idea.objects.get(id=idea_id)
        
        # Verificar permisos
        if idea.empresa_asignada != user_empresa:
            return JsonResponse({'success': False, 'error': 'No tienes permiso sobre esta idea'}, status=403)
        
        if idea.estado != 'en_proceso':
            return JsonResponse({'success': False, 'error': 'Solo se pueden completar ideas en proceso'}, status=400)
        
        # Cambiar el estado a completada
        idea.estado = 'completada'
        idea.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Idea completada exitosamente',
            'nuevo_estado': 'completada'
        })
        
    except Idea.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Idea no encontrada'}, status=404)
    except EmpresaRegistrada.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Empresa no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error: {str(e)}'}, status=500)


@empresa_login_required
@require_POST
def finalizar_idea_view(request, idea_id):
    """Vista para finalizar una idea completada"""
    try:
        # Obtener la empresa registrada y buscar el UserEmpresa correspondiente
        empresa_registrada = EmpresaRegistrada.objects.get(id=request.session['empresa_id'])
        
        from core.models import UserEmpresa
        try:
            user_empresa = UserEmpresa.objects.get(usernameEmpresa=empresa_registrada.username)
        except UserEmpresa.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Usuario empresa no encontrado'}, status=404)
        
        idea = Idea.objects.get(id=idea_id)
        
        # Verificar permisos
        if idea.empresa_asignada != user_empresa:
            return JsonResponse({'success': False, 'error': 'No tienes permiso sobre esta idea'}, status=403)
        
        if idea.estado != 'completada':
            return JsonResponse({'success': False, 'error': 'Solo se pueden finalizar ideas completadas'}, status=400)
        
        # Cambiar el estado a finalizada
        idea.estado = 'finalizada'
        idea.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Idea finalizada exitosamente',
            'nuevo_estado': 'finalizada'
        })
        
    except Idea.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Idea no encontrada'}, status=404)
    except EmpresaRegistrada.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Empresa no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error: {str(e)}'}, status=500)


@empresa_login_required
def ver_factura_view(request, pago_id):
    """Vista para mostrar la factura generada de un pago"""
    try:
        # Verificar que el pago existe
        pago = get_object_or_404(Pago, id=pago_id)
        
        # Verificar que el pago tiene factura
        if not hasattr(pago, 'factura'):
            messages.error(request, 'Este pago no tiene una factura generada.')
            return redirect('gestion_pagos')
        
        factura = pago.factura
        
        # Parsear los productos del JSON
        productos_list = json.loads(factura.productos)
        
        # Procesar cada producto para agregar información adicional
        productos_detallados = []
        for item in productos_list:
            categoria = item['categoria']
            producto_id = item['id']
            cantidad = item['cantidad']
            
            # Obtener el producto según la categoría
            modelo_map = {
                'mesas': Mesas,
                'sillas': Sillas,
                'armarios': Armarios,
                'cajoneras': Cajoneras,
                'escritorios': Escritorios,
                'utensilios': Utensilios
            }
            
            if categoria in modelo_map:
                try:
                    Modelo = modelo_map[categoria]
                    if categoria == 'mesas':
                        producto = Modelo.objects.get(id=producto_id)
                        nombre = producto.nombre1
                        precio = producto.precio1
                    elif categoria == 'sillas':
                        producto = Modelo.objects.get(id=producto_id)
                        nombre = producto.nombre2
                        precio = producto.precio2
                    elif categoria == 'armarios':
                        producto = Modelo.objects.get(id=producto_id)
                        nombre = producto.nombre3
                        precio = producto.precio3
                    elif categoria == 'cajoneras':
                        producto = Modelo.objects.get(id=producto_id)
                        nombre = producto.nombre4
                        precio = producto.precio4
                    elif categoria == 'escritorios':
                        producto = Modelo.objects.get(id=producto_id)
                        nombre = producto.nombre5
                        precio = producto.precio5
                    elif categoria == 'utensilios':
                        producto = Modelo.objects.get(id=producto_id)
                        nombre = producto.nombre6
                        precio = producto.precio6
                    
                    subtotal = float(precio) * cantidad
                    
                    productos_detallados.append({
                        'nombre': nombre,
                        'categoria': categoria,
                        'cantidad': cantidad,
                        'precio_unitario': precio,
                        'subtotal': subtotal
                    })
                except Exception as e:
                    print(f"Error al procesar producto {categoria} #{producto_id}: {e}")
        
        context = {
            'factura': factura,
            'pago': pago,
            'productos': productos_detallados
        }
        
        return render(request, 'Empresas/factura.html', context)
        
    except Exception as e:
        print(f"Error en ver_factura_view: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Error al mostrar la factura: {str(e)}')
        return redirect('gestion_pagos')

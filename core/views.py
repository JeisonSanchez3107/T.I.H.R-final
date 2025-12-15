from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Case, When, IntegerField
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from .forms import LoginForm, AgregarForm, LoginFormEmpresa, IdeaForm
from .logic import obtener_respuesta
import json
import pyotp
import qrcode
from io import BytesIO
import base64
from .models import UserClientes, Mesas, Sillas, Armarios, Cajoneras, Escritorios, Utensilios, Pedido, Pago, UserEmpresa, CarritoTemporal, Idea, Factura, Comentario
# Create your views here.
def home(request):
    # Obtener comentarios aprobados primero, luego otros estados, limitado a 10
    comentarios = Comentario.objects.annotate(
        orden_estado=Case(
            When(estado='aprobado', then=1),
            When(estado='rechazado', then=3),
            When(estado='pendiente', then=2),
            output_field=IntegerField(),
        )
    ).order_by('orden_estado', '-fecha_aprobacion', '-fecha_creacion')[:10]
    
    # Obtener un producto activo de cada categoría para mostrar en el landing
    mesa_destacada = Mesas.objects.filter(is_active=True).first()
    silla_destacada = Sillas.objects.filter(is_active=True).first()
    armario_destacado = Armarios.objects.filter(is_active=True).first()
    cajonera_destacada = Cajoneras.objects.filter(is_active=True).first()
    escritorio_destacado = Escritorios.objects.filter(is_active=True).first()
    utensilio_destacado = Utensilios.objects.filter(is_active=True).first()
    
    context = {
        'comentarios': comentarios,
        'mesa_destacada': mesa_destacada,
        'silla_destacada': silla_destacada,
        'armario_destacado': armario_destacado,
        'cajonera_destacada': cajonera_destacada,
        'escritorio_destacado': escritorio_destacado,
        'utensilio_destacado': utensilio_destacado,
    }
    return render(request, "core/home.html", context)

def productos(request):
    # Obtener el usuario de la sesión
    usernameCliente = request.session.get('usernameCliente')
    usuario = None
    if usernameCliente:
        try:
            usuario = UserClientes.objects.get(usernameCliente=usernameCliente)
        except UserClientes.DoesNotExist:
            pass
    
    # Obtener solo productos activos de la base de datos (límite de 10 para el carrusel)
    mesas = Mesas.objects.filter(is_active=True)[:10]
    sillas = Sillas.objects.filter(is_active=True)[:10]
    armarios = Armarios.objects.filter(is_active=True)[:10]
    cajoneras = Cajoneras.objects.filter(is_active=True)[:10]
    escritorios = Escritorios.objects.filter(is_active=True)[:10]
    utensilios = Utensilios.objects.filter(is_active=True)[:10]
    
    # Filtrar productos que están completamente reservados en otros carritos
    # (excluyendo el carrito del usuario actual si existe)
    if usuario:
        # Para cada categoría, verificar disponibilidad real
        for mesa in mesas:
            # Cantidad total en otros carritos (excluyendo el usuario actual)
            en_otros_carritos = CarritoTemporal.objects.filter(
                producto_tipo='mesa',
                producto_id=mesa.id
            ).exclude(usuario=usuario).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
            
            # Calcular disponibilidad real
            mesa.disponibilidad_real = mesa.cantidad_disponible - en_otros_carritos
            
        for silla in sillas:
            en_otros_carritos = CarritoTemporal.objects.filter(
                producto_tipo='silla',
                producto_id=silla.id
            ).exclude(usuario=usuario).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
            silla.disponibilidad_real = silla.cantidad_disponible - en_otros_carritos
            
        for armario in armarios:
            en_otros_carritos = CarritoTemporal.objects.filter(
                producto_tipo='armario',
                producto_id=armario.id
            ).exclude(usuario=usuario).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
            armario.disponibilidad_real = armario.cantidad_disponible - en_otros_carritos
            
        for cajonera in cajoneras:
            en_otros_carritos = CarritoTemporal.objects.filter(
                producto_tipo='cajonera',
                producto_id=cajonera.id
            ).exclude(usuario=usuario).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
            cajonera.disponibilidad_real = cajonera.cantidad_disponible - en_otros_carritos
            
        for escritorio in escritorios:
            en_otros_carritos = CarritoTemporal.objects.filter(
                producto_tipo='escritorio',
                producto_id=escritorio.id
            ).exclude(usuario=usuario).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
            escritorio.disponibilidad_real = escritorio.cantidad_disponible - en_otros_carritos
            
        for utensilio in utensilios:
            en_otros_carritos = CarritoTemporal.objects.filter(
                producto_tipo='utensilio',
                producto_id=utensilio.id
            ).exclude(usuario=usuario).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
            utensilio.disponibilidad_real = utensilio.cantidad_disponible - en_otros_carritos
        
        # Filtrar productos con disponibilidad real > 0
        mesas = [m for m in mesas if m.disponibilidad_real > 0]
        sillas = [s for s in sillas if s.disponibilidad_real > 0]
        armarios = [a for a in armarios if a.disponibilidad_real > 0]
        cajoneras = [c for c in cajoneras if c.disponibilidad_real > 0]
        escritorios = [e for e in escritorios if e.disponibilidad_real > 0]
        utensilios = [u for u in utensilios if u.disponibilidad_real > 0]
    
    context = {
        'usuario': usuario,
        'mesas': mesas,
        'sillas': sillas,
        'armarios': armarios,
        'cajoneras': cajoneras,
        'escritorios': escritorios,
        'utensilios': utensilios,
    }
    
    return render(request, 'core/productos.html', context)

def contact(request):
    # Obtener el usuario de la sesión
    usernameCliente = request.session.get('usernameCliente')
    usuario = None
    if usernameCliente:
        try:
            usuario = UserClientes.objects.get(usernameCliente=usernameCliente)
        except UserClientes.DoesNotExist:
            pass
    
    mensaje_enviado = False
    error_mensaje = None
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '').strip()
        mensaje = request.POST.get('mensaje', '').strip()
        
        # Validar campos
        if not (nombre and email and mensaje):
            error_mensaje = 'Por favor, completa todos los campos.'
        else:
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                
                # Preparar el correo
                asunto = f'Nuevo mensaje de contacto de {nombre}'
                contenido = f"""
Has recibido un nuevo mensaje desde el formulario de contacto:

Nombre: {nombre}
Email: {email}

Mensaje:
{mensaje}

---
Este mensaje fue enviado desde el formulario de contacto de Tu Idea Hecha Realidad.
                """
                
                # Enviar correo a la empresa
                send_mail(
                    asunto,
                    contenido,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.EMAIL_HOST_USER],  # Correo de la empresa
                    fail_silently=False,
                )
                
                mensaje_enviado = True
            except Exception as e:
                error_mensaje = f'Error al enviar el mensaje: {str(e)}'
    
    return render(request, 'core/contact.html', {
        'usuario': usuario,
        'mensaje_enviado': mensaje_enviado,
        'error_mensaje': error_mensaje
    })

def Login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            usernameCliente = form.cleaned_data['usernameCliente']
            passwordCliente = form.cleaned_data['passwordCliente']
            try:
                user = UserClientes.objects.get(usernameCliente=usernameCliente, passwordCliente=passwordCliente)
                
                # Verificar si el usuario está deshabilitado
                if not user.is_active:
                    error_message = "Tu cuenta ha sido inhabilitada. Contacta con la empresa por el correo: tuideahecharealidad01@gmail.com"
                    return render(request, 'core/login.html', {'error_message': error_message, 'form': form})
                
                # Verificar si tiene 2FA habilitado
                if user.two_factor_enabled:
                    # Guardar temporalmente el username y redirigir a verificación 2FA
                    request.session['username_2fa_temp'] = usernameCliente
                    request.session.modified = True
                    return redirect('verificar_2fa_login')
                
                # Login normal sin 2FA
                request.session['usernameCliente'] = usernameCliente
                request.session.modified = True
                return redirect('productos')
            except UserClientes.DoesNotExist:
                error_message = "Usuario o contraseña incorrectos"
                return render(request, 'core/login.html', {'error_message': error_message, 'form': form})
    else:
        form = LoginForm()
    return render(request,'core/login.html', {'form': form})

def LoginEmpresa_view(request):
    if request.method == 'POST':
        form = LoginFormEmpresa(request.POST)
        if form.is_valid():
            usernameEmpresa = form.cleaned_data['usernameEmpresa']
            passwordEmpresa = form.cleaned_data['passwordEmpresa']
            try:
                userEmpresa = UserEmpresa.objects.get(usernameEmpresa=usernameEmpresa, passwordEmpresa=passwordEmpresa)
                
                # Verificar si la empresa está deshabilitada
                if not userEmpresa.is_active:
                    error_message = "Tu cuenta ha sido inhabilitada. Contacta con la empresa por el correo: tuideahecharealidad01@gmail.com"
                    return render(request, 'core/loginEmpresa.html', {'error_message': error_message, 'form': form})
                
                # Verificar si tiene 2FA configurado (OBLIGATORIO para empresas)
                if not userEmpresa.two_factor_enabled:
                    # Primera vez o sin 2FA configurado - forzar configuración
                    request.session['empresa_2fa_setup'] = userEmpresa.usernameEmpresa
                    request.session.modified = True
                    return redirect('configurar_2fa_empresa')
                
                # Si tiene 2FA, redirigir a verificación
                request.session['username_2fa_temp_empresa'] = usernameEmpresa
                request.session.modified = True
                return redirect('verificar_2fa_login_empresa')
                
            except UserEmpresa.DoesNotExist:
                error_message = "Usuario o contraseña incorrectos"
                return render(request, 'core/loginEmpresa.html', {'error_message': error_message})
    else:
        form = LoginFormEmpresa()
    return render(request,'core/loginEmpresa.html', {'form': form})

def Logout_view(request):
    # Limpiar datos específicos de la sesión
    request.session.pop('usernameEmpresa', None)
    request.session.pop('empresa_id', None)
    # Limpiar toda la sesión
    logout(request)
    return redirect('home')

def Home2_view(request):
    return render(request,'core/home2.html')

def Home3_view(request):
    # Obtener el usuario de la sesión
    usernameCliente = request.session.get('usernameCliente')
    usuario = None
    if usernameCliente:
        try:
            usuario = UserClientes.objects.get(usernameCliente=usernameCliente)
        except UserClientes.DoesNotExist:
            pass
    return render(request, 'core/home3.html', {'usuario': usuario})

def registro(request):
    if request.method == "POST":
        form = AgregarForm(request.POST)
        if form.is_valid():
            # Generar código de verificación de 4 dígitos
            import random
            codigo_verificacion = str(random.randint(1000, 9999))
            
            # Guardar temporalmente los datos en la sesión
            request.session['registro_temp'] = {
                'usernameCliente': form.cleaned_data['usernameCliente'],
                'email': form.cleaned_data['email'],
                'telefono': form.cleaned_data['telefono'],
                'passwordCliente': form.cleaned_data['passwordCliente'],
                'codigo_verificacion': codigo_verificacion
            }
            
            # Enviar código por correo con formato HTML
            from django.core.mail import send_mail
            from django.conf import settings
            
            email_subject = 'Código de Verificación - TIHR Gangazos'
            email_message = f'''
¡Hola {form.cleaned_data['usernameCliente']}!

Gracias por registrarte en TIHR Gangazos - Tu Idea Hecha Realidad.

Tu código de verificación es:

    {codigo_verificacion}

Por favor, ingresa este código en la página de verificación para completar tu registro.

Este código expirará en 10 minutos por seguridad.

Si no solicitaste este registro, puedes ignorar este correo.

---
Atentamente,
El equipo de TIHR Gangazos
Tu Idea Hecha Realidad
            '''
            
            try:
                send_mail(
                    email_subject,
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [form.cleaned_data['email']],
                    fail_silently=False,
                )
                
                from django.contrib import messages
                messages.success(request, f'Se ha enviado un código de verificación a {form.cleaned_data["email"]}. Por favor, revisa tu bandeja de entrada.')
                return redirect('verificar_codigo')
            
            except Exception as e:
                from django.contrib import messages
                messages.error(request, f'Error al enviar el código: {str(e)}. Por favor, verifica que tu correo electrónico sea válido.')
    else:
        form = AgregarForm()
    context = {'form': form}
    return render(request, 'core/registro.html', context)

def verificar_codigo(request):
    if 'registro_temp' not in request.session:
        from django.contrib import messages
        messages.error(request, 'No hay un registro pendiente de verificación')
        return redirect('registro')
    
    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo')
        registro_temp = request.session.get('registro_temp')
        
        if codigo_ingresado == registro_temp['codigo_verificacion']:
            # Crear el usuario
            nuevo_usuario = UserClientes(
                usernameCliente=registro_temp['usernameCliente'],
                email=registro_temp['email'],
                telefono=registro_temp['telefono'],
                passwordCliente=registro_temp['passwordCliente']
            )
            nuevo_usuario.save()
            
            # Limpiar la sesión
            del request.session['registro_temp']
            
            from django.contrib import messages
            messages.success(request, '¡Registro exitoso! Ahora puedes iniciar sesión')
            return redirect('login')
        else:
            from django.contrib import messages
            messages.error(request, 'Código incorrecto. Por favor, intenta de nuevo.')
    
    return render(request, 'core/verificar_codigo.html', {
        'email': request.session.get('registro_temp', {}).get('email')
    })

def reglas(request):
    return render(request,"core/reglas.html")

def idea(request):
    # Obtener el usuario de la sesión
    usernameCliente = request.session.get('usernameCliente')
    usuario = None
    if usernameCliente:
        try:
            usuario = UserClientes.objects.get(usernameCliente=usernameCliente)
        except UserClientes.DoesNotExist:
            pass
    return render(request, 'core/idea.html', {'usuario': usuario})

def carrito(request):
    # Obtener el usuario de la sesión
    usernameCliente = request.session.get('usernameCliente')
    usuario = None
    if usernameCliente:
        try:
            usuario = UserClientes.objects.get(usernameCliente=usernameCliente)
        except UserClientes.DoesNotExist:
            pass
    return render(request, 'core/carrito.html', {'usuario': usuario})

def MetodosPago(request):
    return render(request,"core/MetodosPago.html")

def chatbot(request):
    # Inicializa el historial del chat en la sesión si no existe
    if 'chat_history' not in request.session:
        request.session['chat_history'] = []
        # Añade un mensaje de bienvenida inicial del bot solo la primera vez
        request.session['chat_history'].append({"sender": "bot", "message": "¡Hola! Soy tu asistente de IA. ¿En qué puedo ayudarte hoy?"})

    if request.method == "POST":
        mensaje_usuario = request.POST.get("mensaje", "").strip()
        if mensaje_usuario:
            # Añade el mensaje del usuario al historial
            request.session['chat_history'].append({"sender": "user", "message": mensaje_usuario})
            
            # Obtiene la respuesta del bot
            respuesta_bot = obtener_respuesta(mensaje_usuario)
            
            # Añade la respuesta del bot al historial
            request.session['chat_history'].append({"sender": "bot", "message": respuesta_bot})
            
            # Marca la sesión como modificada para asegurar que Django la guarde
            request.session.modified = True

    # Pasa el historial completo a la plantilla
    return render(request, "chatbot.html", {"chat_history": request.session['chat_history']})

def ideas_view(request):
    """
    Maneja la creación y visualización de ideas usando ModelForm.
    """
    # Obtener el usuario de la sesión
    usernameCliente = request.session.get('usernameCliente')
    usuario = None
    if usernameCliente:
        try:
            usuario = UserClientes.objects.get(usernameCliente=usernameCliente)
        except UserClientes.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = IdeaForm(request.POST, request.FILES)
        if form.is_valid():
            # Guardar sin commit para agregar el autor y medidas
            idea = form.save(commit=False)
            # Asignar automáticamente el nombre del usuario de la sesión
            if usuario:
                idea.autor = usuario.usernameCliente
            
            # Procesar medidas JSON del formulario
            medidas_json = request.POST.get('medidas', '')
            if medidas_json:
                try:
                    idea.medidas = json.loads(medidas_json)
                except:
                    idea.medidas = None
            
            idea.save()
            return redirect('idea')
    else:
        form = IdeaForm()

    # Recupera todas las ideas de la base de datos
    ideas = Idea.objects.all().order_by('-fecha_creacion')
    
    # Filtrar las ideas del usuario actual
    mis_ideas = ideas.filter(autor=usernameCliente) if usernameCliente else []
    
    # Agregar información del usuario a cada idea y serializar medidas
    for idea in ideas:
        try:
            idea.usuario = UserClientes.objects.get(usernameCliente=idea.autor)
        except UserClientes.DoesNotExist:
            idea.usuario = None
        # Serializar medidas a JSON string para el template
        if idea.medidas:
            idea.medidas_json = json.dumps(idea.medidas)
        else:
            idea.medidas_json = 'null'
    
    # Serializar medidas para mis_ideas también
    for idea in mis_ideas:
        if idea.medidas:
            idea.medidas_json = json.dumps(idea.medidas)
        else:
            idea.medidas_json = 'null'
    
    return render(request, 'core/idea.html', {
        'form': form,
        'ideas': ideas,
        'mis_ideas': mis_ideas,
        'usuario': usuario,
    })

@require_http_methods(["POST"])
def editar_idea_view(request, idea_id):
    """
    Vista para editar una idea existente (solo si está pendiente y no ha superado el límite de ediciones).
    """
    usernameCliente = request.session.get('usernameCliente')
    
    if not usernameCliente:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)
    
    try:
        # Verificar que la idea existe y pertenece al usuario
        idea = Idea.objects.get(id=idea_id, autor=usernameCliente)
        
        # Solo permitir editar si está pendiente
        if idea.estado != 'pendiente':
            return JsonResponse({
                'success': False, 
                'error': 'Solo puedes editar ideas que están en estado pendiente'
            }, status=400)
        
        # Verificar límite de ediciones
        if idea.veces_editada >= 3:
            return JsonResponse({
                'success': False, 
                'error': 'Has alcanzado el límite de 3 ediciones para esta idea'
            }, status=400)
        
        # Actualizar los campos
        titulo = request.POST.get('titulo', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        categoria = request.POST.get('categoria', '').strip()
        
        if not titulo or not descripcion or not categoria:
            return JsonResponse({
                'success': False, 
                'error': 'Todos los campos son requeridos'
            }, status=400)
        
        idea.titulo = titulo
        idea.descripcion = descripcion
        idea.categoria = categoria
        
        # Manejar imagen si se subió una nueva
        if 'imagen' in request.FILES:
            idea.imagen = request.FILES['imagen']
        
        # Manejar medidas JSON
        medidas_json = request.POST.get('medidas', '')
        if medidas_json:
            try:
                idea.medidas = json.loads(medidas_json)
            except:
                pass
        
        # Incrementar contador de ediciones
        idea.veces_editada += 1
        idea.save()
        
        ediciones_restantes = 3 - idea.veces_editada
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Idea actualizada exitosamente. Te quedan {ediciones_restantes} ediciones disponibles',
            'veces_editada': idea.veces_editada,
            'ediciones_restantes': ediciones_restantes
        })
        
    except Idea.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Idea no encontrada o no tienes permiso para editarla'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=500)

def empresa_ideas_view(request):
    """
    Vista para que las empresas gestionen las ideas.
    """
    ideas = Idea.objects.all().order_by('-fecha_creacion')
    
    if request.method == 'POST':
        idea_id = request.POST.get('idea_id')
        accion = request.POST.get('accion')
        
        if idea_id and accion:
            idea = Idea.objects.get(pk=idea_id)
            if accion == 'aceptar':
                idea.estado = 'en_proceso'
                idea.empresa_asignada = request.user.userempresa
                idea.save()
            elif accion == 'completar':
                idea.estado = 'completada'
                idea.save()
    
    return render(request, 'Empresas/ideas_empresa.html', {
        'ideas': ideas
    })
    
def perfilUsuario_view(request):
    username = request.session.get('usernameCliente')
    if not username:
        return redirect('login')
    
    try:
        usuario = UserClientes.objects.get(usernameCliente=username)
        
        # Contar compras confirmadas (pagos confirmados)
        compras_realizadas = Pago.objects.filter(
            cliente=usuario,
            estado='confirmado'
        ).count()
        
        # Contar ideas enviadas por el usuario
        ideas_enviadas = Idea.objects.filter(autor=username).count()
        
        context = {
            'usuario': usuario,
            'compras_realizadas': compras_realizadas,
            'ideas_enviadas': ideas_enviadas,
        }
        return render(request, 'core/perfilUsuario.html', context)
    except UserClientes.DoesNotExist:
        return redirect('login')

# Vistas para Comentarios
from .models import Comentario
from .forms import ComentarioForm, PerfilUsuarioForm
from django.contrib import messages
from django.urls import reverse

def comentarios_view(request):
    # Obtener el usuario de la sesión
    usernameCliente = request.session.get('usernameCliente')
    usuario = None
    if usernameCliente:
        try:
            usuario = UserClientes.objects.get(usernameCliente=usernameCliente)
        except UserClientes.DoesNotExist:
            pass
    
    # Obtener todos los comentarios ordenados por fecha
    comentarios = Comentario.objects.all().order_by('-fecha_creacion')
    
    context = {
        'comentarios': comentarios,
        'usuario': usuario,
    }
    return render(request, 'core/comentarios.html', context)

def crear_comentario_view(request):
    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            # Asignar el usuario actual al comentario
            # Aqu� asumimos que tienes el usuario en la sesi�n o autenticaci�n
            # Deber�s ajustar esto seg�n tu l�gica de autenticaci�n
            try:
                # Intenta obtener el usuario de la sesi�n
                username = request.session.get('usernameCliente')
                if username:
                    usuario = UserClientes.objects.get(usernameCliente=username)
                    comentario.usuario = usuario
                    comentario.save()
                    messages.success(request, 'Comentario publicado exitosamente')
                    return redirect('comentarios')
                else:
                    messages.error(request, 'Debes iniciar sesi�n para comentar')
                    return redirect('login')
            except UserClientes.DoesNotExist:
                messages.error(request, 'Usuario no encontrado')
                return redirect('login')
    else:
        form = ComentarioForm()
    
    return render(request, 'core/crear_comentario.html', {'form': form})

def eliminar_comentario_view(request, comentario_id):
    try:
        comentario = Comentario.objects.get(id=comentario_id)
        # Verificar que el usuario sea el due�o del comentario
        username = request.session.get('usernameCliente')
        if username:
            usuario = UserClientes.objects.get(usernameCliente=username)
            if comentario.usuario == usuario:
                comentario.delete()
                messages.success(request, 'Comentario eliminado exitosamente')
            else:
                messages.error(request, 'No tienes permiso para eliminar este comentario')
        else:
            messages.error(request, 'Debes iniciar sesi�n')
    except Comentario.DoesNotExist:
        messages.error(request, 'Comentario no encontrado')
    except UserClientes.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
    
    return redirect('comentarios')

# Vistas para Perfil de Usuario
def editar_perfil_view(request):
    username = request.session.get('usernameCliente')
    if not username:
        messages.error(request, 'Debes iniciar sesi�n para editar tu perfil')
        return redirect('login')
    
    try:
        usuario = UserClientes.objects.get(usernameCliente=username)
        
        if request.method == 'POST':
            form = PerfilUsuarioForm(request.POST, request.FILES, instance=usuario)
            if form.is_valid():
                # Verificar si se est�n cambiando las contrase�as
                password_actual = form.cleaned_data.get('passwordCliente_actual')
                password_nueva = form.cleaned_data.get('passwordCliente_nueva')
                
                if password_actual and password_nueva:
                    # Verificar que la contrase�a actual sea correcta
                    if usuario.passwordCliente == password_actual:
                        usuario.passwordCliente = password_nueva
                    else:
                        messages.error(request, 'La contrase�a actual es incorrecta')
                        return render(request, 'core/editar_perfil.html', {'form': form})
                
                # Guardar el formulario
                form.save()
                
                # Actualizar el username en la sesi�n si cambi�
                request.session['usernameCliente'] = usuario.usernameCliente
                request.session.modified = True
                
                messages.success(request, 'Perfil actualizado exitosamente')
                return redirect('perfilUsuario')
        else:
            form = PerfilUsuarioForm(instance=usuario)
        
        context = {
            'form': form,
            'usuario': usuario,
        }
        return render(request, 'core/editar_perfil.html', context)
    except UserClientes.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('login')

# Vistas para gestión de comentarios por Empresa
def empresa_comentarios_view(request):
    """Vista para que las empresas vean y gestionen comentarios"""
    # Verificar que sea una empresa autenticada
    empresa_id = request.session.get('empresa_id')
    if not empresa_id:
        messages.error(request, 'Debes iniciar sesión como empresa')
        return redirect('login_empresa')
    
    # Agrupar comentarios por cliente
    from django.db.models import Count
    
    clientes_con_comentarios = UserClientes.objects.annotate(
        cantidad_comentarios=Count('comentarios')
    ).filter(
        cantidad_comentarios__gt=0
    ).order_by('-cantidad_comentarios')
    
    context = {
        'clientes_con_comentarios': clientes_con_comentarios,
    }
    return render(request, 'Empresas/gestion_comentarios.html', context)


def obtener_comentarios_cliente_view(request, cliente_id):
    """Vista para obtener los comentarios de un cliente específico"""
    # Verificar que sea una empresa autenticada
    empresa_id = request.session.get('empresa_id')
    if not empresa_id:
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=401)
    
    try:
        from django.http import JsonResponse
        cliente = UserClientes.objects.get(id=cliente_id)
        comentarios = Comentario.objects.filter(usuario=cliente).order_by('-fecha_creacion')
        
        comentarios_data = []
        for comentario in comentarios:
            comentarios_data.append({
                'id': comentario.id,
                'contenido': comentario.contenido,
                'estado': comentario.estado,
                'fecha_creacion': comentario.fecha_creacion.strftime('%d/%m/%Y'),
                'fecha_aprobacion': comentario.fecha_aprobacion.strftime('%d/%m/%Y') if comentario.fecha_aprobacion else None,
            })
        
        return JsonResponse({
            'success': True,
            'comentarios': comentarios_data
        })
    except UserClientes.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cliente no encontrado'}, status=404)
    except Exception as e:
        print(f"Error en obtener_comentarios_cliente_view: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def aprobar_comentario_view(request, comentario_id):
    """Vista para aprobar un comentario"""
    # Verificar que sea una empresa autenticada
    empresa_id = request.session.get('empresa_id')
    if not empresa_id:
        messages.error(request, 'Debes iniciar sesión como empresa')
        return redirect('login_empresa')
    
    try:
        comentario = Comentario.objects.get(id=comentario_id)
        comentario.estado = 'aprobado'
        comentario.fecha_aprobacion = timezone.now()
        comentario.save()
        messages.success(request, 'Comentario aprobado exitosamente')
    except Comentario.DoesNotExist:
        messages.error(request, 'Comentario no encontrado')
    
    return redirect('empresa_comentarios')

def rechazar_comentario_view(request, comentario_id):
    """Vista para rechazar un comentario"""
    # Verificar que sea una empresa autenticada
    empresa_id = request.session.get('empresa_id')
    if not empresa_id:
        messages.error(request, 'Debes iniciar sesión como empresa')
        return redirect('login_empresa')
    
    try:
        comentario = Comentario.objects.get(id=comentario_id)
        comentario.estado = 'rechazado'
        comentario.fecha_aprobacion = None
        comentario.save()
        messages.success(request, 'Comentario rechazado')
    except Comentario.DoesNotExist:
        messages.error(request, 'Comentario no encontrado')
    
    return redirect('empresa_comentarios')

@require_http_methods(["POST"])
def procesar_pago(request):
    """Vista para procesar el pago con comprobante"""
    # Verificar que el usuario esté autenticado
    usernameCliente = request.session.get('usernameCliente')
    if not usernameCliente:
        return JsonResponse({'success': False, 'error': 'Usuario no autenticado'}, status=401)
    
    try:
        # Obtener el cliente
        cliente = UserClientes.objects.get(usernameCliente=usernameCliente)
        
        # Obtener datos del formulario
        nombre_completo = request.POST.get('nombre_completo')
        cedula = request.POST.get('cedula')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        metodo_pago = request.POST.get('metodo_pago')
        monto_total = request.POST.get('monto_total')
        productos = request.POST.get('productos')
        comprobante = request.FILES.get('comprobante')
        
        # Validar datos requeridos
        if not all([nombre_completo, cedula, email, telefono, direccion, metodo_pago, monto_total, productos, comprobante]):
            return JsonResponse({'success': False, 'error': 'Faltan datos requeridos'}, status=400)
        
        # Validar que la cédula solo contenga números
        if not cedula.isdigit():
            return JsonResponse({'success': False, 'error': 'La cédula debe contener solo números'}, status=400)
        
        # Validar que el teléfono solo contenga números
        if not telefono.isdigit():
            return JsonResponse({'success': False, 'error': 'El teléfono debe contener solo números'}, status=400)
        
        # Validar dirección
        if len(direccion) < 10:
            return JsonResponse({'success': False, 'error': 'La dirección debe tener al menos 10 caracteres'}, status=400)
        
        # Actualizar perfil del usuario con la información del formulario
        cliente.nombre_completo = nombre_completo
        cliente.telefono = telefono
        cliente.direccion = direccion
        if not cliente.email:
            cliente.email = email
        cliente.save()
        
        # Crear el registro de pago
        pago = Pago.objects.create(
            cliente=cliente,
            nombre_completo=nombre_completo,
            cedula=cedula,
            email=email,
            telefono=telefono,
            direccion=direccion,
            metodo_pago=metodo_pago,
            monto_total=float(monto_total),
            comprobante=comprobante,
            productos=productos,
            estado='pendiente'
        )
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Pago registrado exitosamente',
            'pago_id': pago.id
        })
        
    except UserClientes.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cliente no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def crear_pedido_view(request, pago_id):
    """Vista para crear un pedido después de confirmar el pago"""
    # Verificar sesión de cliente
    if 'usernameCliente' not in request.session:
        return redirect('login')
    
    try:
        # Obtener cliente y pago
        cliente = UserClientes.objects.get(usernameCliente=request.session['usernameCliente'])
        pago = Pago.objects.get(id=pago_id, cliente=cliente)
        
        # Verificar que el pago esté confirmado
        if pago.estado != 'confirmado':
            return redirect('carrito')
        
        # Verificar que no exista ya un pedido para este pago
        if hasattr(pago, 'pedido'):
            return redirect('mis_pedidos')
        
        if request.method == 'POST':
            from datetime import timedelta
            from django.utils import timezone
            
            # NOTA: El inventario ya fue descontado cuando la empresa confirmó el pago
            # Aquí solo actualizamos los datos de envío del pedido existente
            
            # Obtener datos del formulario
            nombre_completo = request.POST.get('nombre_completo')
            telefono = request.POST.get('telefono')
            direccion = request.POST.get('direccion')
            ciudad = request.POST.get('ciudad')
            departamento = request.POST.get('departamento')
            codigo_postal = request.POST.get('codigo_postal', '')
            notas_adicionales = request.POST.get('notas_adicionales', '')
            
            # Guardar dirección predeterminada del cliente si está marcado
            guardar_direccion = request.POST.get('guardar_direccion') == 'on'
            if guardar_direccion:
                cliente.nombre_completo = nombre_completo
                cliente.telefono = telefono
                cliente.direccion = direccion
                cliente.ciudad = ciudad
                cliente.departamento = departamento
                cliente.codigo_postal = codigo_postal
                cliente.save()
            
            # El pedido ya debe existir (creado por confirmar_pago_view)
            try:
                pedido = Pedido.objects.get(pago=pago)
                
                # Actualizar los datos de envío
                pedido.nombre_completo = nombre_completo
                pedido.telefono = telefono
                pedido.direccion = direccion
                pedido.ciudad = ciudad
                pedido.departamento = departamento
                pedido.codigo_postal = codigo_postal
                pedido.notas_adicionales = notas_adicionales
                pedido.save()
                
            except Pedido.DoesNotExist:
                # Si por alguna razón no existe el pedido, crearlo
                pedido = Pedido.objects.create(
                    pago=pago,
                    cliente=cliente,
                    nombre_completo=nombre_completo,
                    telefono=telefono,
                    direccion=direccion,
                    ciudad=ciudad,
                    departamento=departamento,
                    codigo_postal=codigo_postal,
                    notas_adicionales=notas_adicionales,
                    productos=pago.productos,
                    monto_total=pago.monto_total,
                    estado='procesando',
                    fecha_entrega_estimada=timezone.now().date() + timedelta(days=7)
                )
            
            return redirect('mis_pedidos')
        
        # Parsear productos del pago
        try:
            productos = json.loads(pago.productos)
        except:
            productos = []
        
        context = {
            'pago': pago,
            'productos': productos,
            'cliente': cliente
        }
        
        return render(request, 'core/crear_pedido.html', context)
        
    except (UserClientes.DoesNotExist, Pago.DoesNotExist):
        return redirect('carrito')

def mis_pedidos_view(request):
    """Vista para ver los pedidos del cliente"""
    # Verificar sesión de cliente
    if 'usernameCliente' not in request.session:
        from django.contrib import messages
        messages.error(request, 'Debes estar logeado para ver tus pedidos')
        return redirect('login')
    
    try:
        cliente = UserClientes.objects.get(usernameCliente=request.session['usernameCliente'])
        pedidos = Pedido.objects.filter(cliente=cliente).order_by('-fecha_creacion')
        
        # Mapeo de categorías a modelos y campos
        modelos_map = {
            'mesas': {'modelo': Mesas, 'campo_imagen': 'imagen1', 'campo_nombre': 'nombre1'},
            'mesa': {'modelo': Mesas, 'campo_imagen': 'imagen1', 'campo_nombre': 'nombre1'},
            'sillas': {'modelo': Sillas, 'campo_imagen': 'imagen2', 'campo_nombre': 'nombre2'},
            'silla': {'modelo': Sillas, 'campo_imagen': 'imagen2', 'campo_nombre': 'nombre2'},
            'armarios': {'modelo': Armarios, 'campo_imagen': 'imagen3', 'campo_nombre': 'nombre3'},
            'armario': {'modelo': Armarios, 'campo_imagen': 'imagen3', 'campo_nombre': 'nombre3'},
            'cajoneras': {'modelo': Cajoneras, 'campo_imagen': 'imagen4', 'campo_nombre': 'nombre4'},
            'cajonera': {'modelo': Cajoneras, 'campo_imagen': 'imagen4', 'campo_nombre': 'nombre4'},
            'escritorios': {'modelo': Escritorios, 'campo_imagen': 'imagen5', 'campo_nombre': 'nombre5'},
            'escritorio': {'modelo': Escritorios, 'campo_imagen': 'imagen5', 'campo_nombre': 'nombre5'},
            'utensilios': {'modelo': Utensilios, 'campo_imagen': 'imagen6', 'campo_nombre': 'nombre6'},
            'utensilio': {'modelo': Utensilios, 'campo_imagen': 'imagen6', 'campo_nombre': 'nombre6'},
        }
        
        # Agregar numeración secuencial por usuario
        pedidos_list = list(pedidos)
        total_pedidos = len(pedidos_list)
        for idx, pedido in enumerate(pedidos_list):
            pedido.numero_secuencial = total_pedidos - idx
            # Agregar pago_id si existe
            pedido.pago_id = pedido.pago.id if pedido.pago else None
        
        # Parsear productos para cada pedido y obtener imágenes
        for pedido in pedidos_list:
            try:
                productos_parseados = json.loads(pedido.productos)
                
                # Agregar imágenes a cada producto
                for producto in productos_parseados:
                    # Intentar obtener categoría de 'categoria' o 'tipo'
                    categoria = (producto.get('categoria') or producto.get('tipo', '')).lower()
                    producto_id = producto.get('id')
                    
                    print(f"DEBUG: Procesando producto ID={producto_id}, categoria='{categoria}'")
                    
                    # Obtener configuración del modelo
                    config = modelos_map.get(categoria)
                    
                    if config and producto_id:
                        try:
                            modelo = config['modelo']
                            item = modelo.objects.get(id=producto_id)
                            
                            # Obtener imagen
                            campo_imagen = config['campo_imagen']
                            if hasattr(item, campo_imagen):
                                imagen_field = getattr(item, campo_imagen)
                                if imagen_field:
                                    producto['imagen'] = imagen_field.url
                                else:
                                    producto['imagen'] = None
                            else:
                                producto['imagen'] = None
                        except modelo.DoesNotExist:
                            producto['imagen'] = None
                        except Exception as ex:
                            producto['imagen'] = None
                    else:
                        producto['imagen'] = None
                
                # Serializar a JSON string para el template
                pedido.productos_json = json.dumps(productos_parseados)
                pedido.productos_parseados = productos_parseados
            except Exception as e:
                pedido.productos_json = '[]'
                pedido.productos_parseados = []
        
        # Verificar si hay pedidos sin datos de envío
        pedidos_sin_datos = []
        for pedido in pedidos_list:
            if not pedido.direccion or not pedido.telefono:
                pedidos_sin_datos.append(pedido)
        
        context = {
            'pedidos': pedidos,
            'cliente': cliente,
            'usuario': cliente,  # Añadir para compatibilidad con el template
            'pedidos_sin_datos': pedidos_sin_datos  # Pedidos que necesitan completar datos
        }
        
        return render(request, 'core/mis_pedidos_nuevo.html', context)
        
    except UserClientes.DoesNotExist:
        from django.contrib import messages
        messages.error(request, 'Usuario no encontrado')
        return redirect('login')

def detalle_pedido_view(request, pedido_id):
    """Vista para ver el detalle de un pedido específico"""
    # Verificar sesión de cliente
    if 'usernameCliente' not in request.session:
        return redirect('login')
    
    try:
        cliente = UserClientes.objects.get(usernameCliente=request.session['usernameCliente'])
        pedido = Pedido.objects.get(id=pedido_id, cliente=cliente)
        
        # Parsear productos
        try:
            pedido.productos_parseados = json.loads(pedido.productos)
        except:
            pedido.productos_parseados = []
        
        context = {
            'pedido': pedido,
            'cliente': cliente
        }
        
        return render(request, 'core/detalle_pedido.html', context)
        
    except (UserClientes.DoesNotExist, Pedido.DoesNotExist):
        return redirect('mis_pedidos')

def completar_datos_envio_view(request, pedido_id):
    """Vista para completar los datos de envío de un pedido"""
    if 'usernameCliente' not in request.session:
        return redirect('login')
    
    if request.method == 'POST':
        try:
            cliente = UserClientes.objects.get(usernameCliente=request.session['usernameCliente'])
            pedido = Pedido.objects.get(id=pedido_id, cliente=cliente)
            
            # Actualizar datos de envío
            pedido.nombre_completo = request.POST.get('nombre_completo')
            pedido.telefono = request.POST.get('telefono')
            pedido.direccion = request.POST.get('direccion')
            pedido.ciudad = request.POST.get('ciudad')
            pedido.departamento = request.POST.get('departamento')
            pedido.codigo_postal = request.POST.get('codigo_postal', '')
            pedido.notas_adicionales = request.POST.get('notas_adicionales', '')
            
            pedido.save()
            
            return redirect('mis_pedidos')
            
        except (UserClientes.DoesNotExist, Pedido.DoesNotExist):
            return redirect('mis_pedidos')
    
    return redirect('mis_pedidos')

def editar_ubicacion_pedido_view(request, pedido_id):
    """Vista para editar la ubicación de entrega de un pedido específico"""
    if 'usernameCliente' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)
    
    if request.method == 'POST':
        try:
            cliente = UserClientes.objects.get(usernameCliente=request.session['usernameCliente'])
            pedido = Pedido.objects.get(id=pedido_id, cliente=cliente)
            
            # Obtener datos del formulario
            nombre_completo = request.POST.get('nombre_completo')
            telefono = request.POST.get('telefono')
            direccion = request.POST.get('direccion')
            ciudad = request.POST.get('ciudad')
            departamento = request.POST.get('departamento')
            codigo_postal = request.POST.get('codigo_postal', '')
            
            # Actualizar datos de ubicación del pedido
            pedido.nombre_completo = nombre_completo
            pedido.telefono = telefono
            pedido.direccion = direccion
            pedido.ciudad = ciudad
            pedido.departamento = departamento
            pedido.codigo_postal = codigo_postal
            pedido.save()
            
            # Si el checkbox está marcado, también guardar en el cliente
            guardar_direccion = request.POST.get('guardar_direccion') == 'on'
            if guardar_direccion:
                cliente.nombre_completo = nombre_completo
                cliente.telefono = telefono
                cliente.direccion = direccion
                cliente.ciudad = ciudad
                cliente.departamento = departamento
                cliente.codigo_postal = codigo_postal
                cliente.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Ubicación actualizada correctamente'
            })
            
        except UserClientes.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Cliente no encontrado'}, status=404)
        except Pedido.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Pedido no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


def ver_factura_cliente_view(request, pago_id):
    """Vista para que los clientes vean su factura"""
    # Verificar que el usuario está autenticado
    usernameCliente = request.session.get('usernameCliente')
    if not usernameCliente:
        return redirect('login')
    
    try:
        cliente = UserClientes.objects.get(usernameCliente=usernameCliente)
        
        # Verificar que el pago pertenece al cliente
        pago = Pago.objects.get(id=pago_id, cliente=cliente)
        
        # Verificar que el pago tiene factura
        if not hasattr(pago, 'factura'):
            from django.contrib import messages
            messages.error(request, 'Este pago no tiene una factura generada.')
            return redirect('mis_pedidos')
        
        factura = pago.factura
        
        # Parsear los productos del JSON
        productos_list = json.loads(factura.productos)
        
        # Procesar cada producto para agregar información adicional
        productos_detallados = []
        for item in productos_list:
            # Manejar tanto 'categoria' como 'tipo' (campo usado en el carrito)
            categoria = item.get('categoria') or item.get('tipo')
            producto_id = item.get('id')
            cantidad = item.get('cantidad', 1)
            
            # Si el producto ya tiene nombre y precio (del carrito), usarlos directamente
            if 'nombre' in item and 'precio' in item:
                productos_detallados.append({
                    'nombre': item['nombre'],
                    'categoria': categoria,
                    'cantidad': cantidad,
                    'precio_unitario': float(item['precio']),
                    'subtotal': float(item['precio']) * cantidad
                })
                continue
            
            # Si no, buscar en la base de datos
            if not categoria or not producto_id:
                print(f"Producto sin categoría o ID: {item}")
                continue
            
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
        
        # Verificar si se quiere descargar como PDF
        formato = request.GET.get('formato', 'html')
        
        context = {
            'factura': factura,
            'pago': pago,
            'productos': productos_detallados,
            'cliente': cliente
        }
        
        if formato == 'pdf':
            return generar_factura_pdf(context)
        
        return render(request, 'core/factura_cliente.html', context)
        
    except UserClientes.DoesNotExist:
        return redirect('login')
    except Pago.DoesNotExist:
        from django.contrib import messages
        messages.error(request, 'Pago no encontrado o no tienes permiso para verlo.')
        return redirect('mis_pedidos')
    except Exception as e:
        print(f"Error en ver_factura_cliente_view: {e}")
        import traceback
        traceback.print_exc()
        from django.contrib import messages
        messages.error(request, f'Error al mostrar la factura: {str(e)}')
        return redirect('mis_pedidos')

def generar_factura_pdf(context):
    """Genera un PDF de la factura usando xhtml2pdf"""
    try:
        from xhtml2pdf import pisa
        from django.template.loader import get_template
        
        # Usar plantilla específica para PDF
        template = get_template('core/factura_pdf.html')
        html = template.render(context)
        
        # Crear respuesta HTTP para PDF
        response = HttpResponse(content_type='application/pdf')
        factura_numero = context['factura'].numero_factura
        response['Content-Disposition'] = f'attachment; filename="Factura_{factura_numero}.pdf"'
        
        # Generar PDF con encoding UTF-8
        pisa_status = pisa.CreatePDF(
            html.encode('utf-8'),
            dest=response,
            encoding='utf-8'
        )
        
        if pisa_status.err:
            # Log del error para debugging
            print(f"Error en generación PDF: {pisa_status.err}")
            return HttpResponse('Error al generar el PDF. Por favor, contacte al administrador.', status=500)
        
        return response
        
    except ImportError as ie:
        print(f"Error de importación: {ie}")
        return HttpResponse('La librería xhtml2pdf no está instalada. Por favor, ejecute: pip install xhtml2pdf', status=500)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error al generar PDF: {e}")
        print(error_trace)
        return HttpResponse(f'Error al generar el PDF: {str(e)}', status=500)

def get_cantidad_disponible_view(request):
    """Vista API para obtener la cantidad disponible de un producto"""
    tipo = request.GET.get('tipo')
    producto_id = request.GET.get('id')
    
    if not tipo or not producto_id:
        return JsonResponse({'error': 'Parámetros incompletos'}, status=400)
    
    try:
        modelos = {
            'mesa': Mesas,
            'silla': Sillas,
            'armario': Armarios,
            'cajonera': Cajoneras,
            'escritorio': Escritorios,
            'utensilio': Utensilios,
        }
        
        modelo = modelos.get(tipo)
        if not modelo:
            return JsonResponse({'error': 'Tipo de producto no válido'}, status=400)
        
        producto = modelo.objects.get(id=producto_id)
        
        # Verificar si el producto está activo
        if not producto.is_active:
            return JsonResponse({
                'cantidad_disponible': 0,
                'producto_activo': False,
                'mensaje': 'Producto no disponible'
            })
        
        # Obtener el usuario actual
        usernameCliente = request.session.get('usernameCliente')
        usuario = None
        if usernameCliente:
            try:
                usuario = UserClientes.objects.get(usernameCliente=usernameCliente)
            except UserClientes.DoesNotExist:
                pass
        
        # Calcular cantidad en otros carritos (excluyendo el usuario actual)
        if usuario:
            en_otros_carritos = CarritoTemporal.objects.filter(
                producto_tipo=tipo,
                producto_id=producto_id
            ).exclude(usuario=usuario).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        else:
            en_otros_carritos = CarritoTemporal.objects.filter(
                producto_tipo=tipo,
                producto_id=producto_id
            ).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        
        # Disponibilidad real
        cantidad_disponible_real = producto.cantidad_disponible - en_otros_carritos
        
        # Obtener el nombre del producto según el tipo
        campo_nombre_map = {
            'mesa': 'nombre1',
            'silla': 'nombre2',
            'armario': 'nombre3',
            'cajonera': 'nombre4',
            'escritorio': 'nombre5',
            'utensilio': 'nombre6',
        }
        
        campo_nombre = campo_nombre_map.get(tipo)
        nombre_producto = getattr(producto, campo_nombre, 'Producto')
        
        return JsonResponse({
            'cantidad_disponible': max(0, cantidad_disponible_real),
            'nombre': nombre_producto
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def verificar_notificaciones_ideas(request):
    """Vista API para verificar si el usuario tiene notificaciones de ideas"""
    usernameCliente = request.session.get('usernameCliente')
    
    if not usernameCliente:
        return JsonResponse({'has_notifications': False})
    
    try:
        # Buscar ideas del usuario con mensajes de empresa o solicitudes de permiso
        has_notif = Idea.objects.filter(autor=usernameCliente).filter(
            mensaje_empresa__isnull=False
        ).exclude(mensaje_empresa='').exists()
        
        return JsonResponse({'has_notifications': has_notif})
        
    except Exception as e:
        return JsonResponse({'has_notifications': False, 'error': str(e)})

@require_http_methods(["POST"])
@csrf_exempt
def responder_mensaje_empresa(request, idea_id):
    """Vista para que el cliente responda al mensaje de la empresa"""
    usernameCliente = request.session.get('usernameCliente')
    if not usernameCliente:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)
    
    try:
        idea = Idea.objects.get(id=idea_id, autor=usernameCliente)
        respuesta = request.POST.get('respuesta', '')
        
        if not respuesta:
            return JsonResponse({'success': False, 'error': 'La respuesta no puede estar vacía'}, status=400)
        
        idea.respuesta_cliente = respuesta
        idea.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Respuesta enviada exitosamente'
        })
        
    except Idea.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Idea no encontrada o no tienes permiso'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def otorgar_permiso_publicacion(request, idea_id):
    """Vista para que el cliente otorgue permiso de publicación"""
    usernameCliente = request.session.get('usernameCliente')
    if not usernameCliente:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)
    
    try:
        idea = Idea.objects.get(id=idea_id, autor=usernameCliente)
        
        if idea.estado != 'finalizada':
            return JsonResponse({'success': False, 'error': 'La idea debe estar finalizada'}, status=400)
        
        idea.permiso_publicacion = True
        idea.fecha_permiso = timezone.now()
        idea.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Permiso otorgado exitosamente. La empresa ya puede publicar tu idea como producto.'
        })
        
    except Idea.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Idea no encontrada o no tienes permiso'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def revocar_permiso_publicacion(request, idea_id):
    """Vista para que el cliente revoque el permiso de publicación"""
    usernameCliente = request.session.get('usernameCliente')
    if not usernameCliente:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)
    
    try:
        idea = Idea.objects.get(id=idea_id, autor=usernameCliente)
        
        if idea.publicada_como_producto:
            return JsonResponse({'success': False, 'error': 'No puedes revocar el permiso, la idea ya fue publicada como producto'}, status=400)
        
        idea.permiso_publicacion = False
        idea.fecha_permiso = None
        idea.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Permiso revocado exitosamente'
        })
        
    except Idea.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Idea no encontrada o no tienes permiso'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ==================== VISTAS PARA AUTENTICACIÓN DE DOS FACTORES (2FA) ====================

def activar_2fa_view(request):
    """Vista para activar la autenticación de dos factores"""
    username = request.session.get('usernameCliente')
    if not username:
        return redirect('login')
    
    try:
        usuario = UserClientes.objects.get(usernameCliente=username)
        
        if request.method == 'POST':
            email = request.POST.get('email')
            password = request.POST.get('passwordCliente')
            
            # Validar que el email coincida con el de la base de datos
            if email != usuario.email:
                messages.error(request, 'El correo electrónico no coincide con el registrado')
                return render(request, 'core/activar_2fa.html', {'usuario': usuario})
            
            # Validar la contraseña
            if password != usuario.passwordCliente:
                messages.error(request, 'La contraseña es incorrecta')
                return render(request, 'core/activar_2fa.html', {'usuario': usuario})
            
            # Generar el secreto para 2FA
            if not usuario.two_factor_secret:
                secret = pyotp.random_base32()
                usuario.two_factor_secret = secret
                usuario.save()
            
            # Guardar en sesión que se está configurando 2FA
            request.session['configurando_2fa'] = True
            request.session.modified = True
            
            return redirect('mostrar_qr_2fa')
        
        context = {
            'usuario': usuario,
        }
        return render(request, 'core/activar_2fa.html', context)
        
    except UserClientes.DoesNotExist:
        return redirect('login')

def mostrar_qr_2fa_view(request):
    """Vista para mostrar el código QR para configurar 2FA"""
    username = request.session.get('usernameCliente')
    configurando = request.session.get('configurando_2fa', False)
    
    if not username or not configurando:
        return redirect('perfilUsuario')
    
    try:
        usuario = UserClientes.objects.get(usernameCliente=username)
        
        if not usuario.two_factor_secret:
            return redirect('activar_2fa')
        
        # Crear el URI para el código QR
        totp = pyotp.TOTP(usuario.two_factor_secret)
        provisioning_uri = totp.provisioning_uri(
            name=usuario.email,
            issuer_name='Tu Idea Hecha Realidad'
        )
        
        # Generar código QR
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir imagen a base64 para mostrar en template
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        context = {
            'usuario': usuario,
            'qr_code': img_base64,
            'secret_key': usuario.two_factor_secret,
        }
        
        return render(request, 'core/mostrar_qr_2fa.html', context)
        
    except UserClientes.DoesNotExist:
        return redirect('login')

def verificar_2fa_setup_view(request):
    """Vista para verificar el código 2FA durante la configuración"""
    username = request.session.get('usernameCliente')
    configurando = request.session.get('configurando_2fa', False)
    
    if not username or not configurando:
        return redirect('perfilUsuario')
    
    try:
        usuario = UserClientes.objects.get(usernameCliente=username)
        
        if request.method == 'POST':
            codigo = request.POST.get('codigo')
            
            if not codigo:
                messages.error(request, 'Por favor ingresa el código de verificación')
                return redirect('mostrar_qr_2fa')
            
            # Verificar el código
            totp = pyotp.TOTP(usuario.two_factor_secret)
            if totp.verify(codigo, valid_window=1):
                # Activar 2FA
                usuario.two_factor_enabled = True
                usuario.save()
                
                # Limpiar sesión
                request.session.pop('configurando_2fa', None)
                request.session.modified = True
                
                messages.success(request, '¡Autenticación de dos factores activada exitosamente!')
                return redirect('perfilUsuario')
            else:
                messages.error(request, 'Código de verificación incorrecto. Intenta nuevamente.')
                return redirect('mostrar_qr_2fa')
        
        return redirect('mostrar_qr_2fa')
        
    except UserClientes.DoesNotExist:
        return redirect('login')

def verificar_2fa_login_view(request):
    """Vista para verificar el código 2FA durante el login"""
    username_temp = request.session.get('username_2fa_temp')
    
    if not username_temp:
        return redirect('login')
    
    try:
        usuario = UserClientes.objects.get(usernameCliente=username_temp)
        
        if request.method == 'POST':
            codigo = request.POST.get('codigo')
            
            if not codigo:
                messages.error(request, 'Por favor ingresa el código de verificación')
                return render(request, 'core/verificar_2fa_login.html', {'usuario': usuario})
            
            # Verificar el código
            totp = pyotp.TOTP(usuario.two_factor_secret)
            if totp.verify(codigo, valid_window=1):
                # Login exitoso
                request.session['usernameCliente'] = username_temp
                request.session.pop('username_2fa_temp', None)
                request.session.modified = True
                
                messages.success(request, '¡Inicio de sesión exitoso!')
                return redirect('productos')
            else:
                messages.error(request, 'Código de verificación incorrecto. Intenta nuevamente.')
                return render(request, 'core/verificar_2fa_login.html', {'usuario': usuario})
        
        context = {
            'usuario': usuario,
        }
        return render(request, 'core/verificar_2fa_login.html', context)
        
    except UserClientes.DoesNotExist:
        return redirect('login')

def desactivar_2fa_view(request):
    """Vista para desactivar la autenticación de dos factores"""
    username = request.session.get('usernameCliente')
    if not username:
        return redirect('login')
    
    try:
        usuario = UserClientes.objects.get(usernameCliente=username)
        
        if request.method == 'POST':
            password = request.POST.get('passwordCliente')
            
            # Validar la contraseña
            if password != usuario.passwordCliente:
                messages.error(request, 'La contraseña es incorrecta')
                return redirect('perfilUsuario')
            
            # Desactivar 2FA
            usuario.two_factor_enabled = False
            usuario.two_factor_secret = None
            usuario.save()
            
            messages.success(request, 'Autenticación de dos factores desactivada exitosamente')
            return redirect('perfilUsuario')
        
        return redirect('perfilUsuario')
        
    except UserClientes.DoesNotExist:
        return redirect('login')


# ==================== VISTAS PARA 2FA DE EMPRESAS (OBLIGATORIO) ====================

def configurar_2fa_empresa_view(request):
    """Vista para configuración OBLIGATORIA de 2FA para empresas"""
    username_empresa = request.session.get('empresa_2fa_setup')
    
    if not username_empresa:
        return redirect('loginEmpresa')
    
    try:
        empresa = UserEmpresa.objects.get(usernameEmpresa=username_empresa)
        
        if request.method == 'POST':
            email = request.POST.get('email')
            password = request.POST.get('passwordEmpresa')
            
            # Validar que el email coincida
            if email and email != empresa.email:
                messages.error(request, 'El correo electrónico no coincide con el registrado')
                return render(request, 'core/configurar_2fa_empresa.html', {'empresa': empresa})
            
            # Validar la contraseña
            if password != empresa.passwordEmpresa:
                messages.error(request, 'La contraseña es incorrecta')
                return render(request, 'core/configurar_2fa_empresa.html', {'empresa': empresa})
            
            # Generar el secreto para 2FA
            if not empresa.two_factor_secret:
                secret = pyotp.random_base32()
                empresa.two_factor_secret = secret
                empresa.save()
            
            # Marcar que está en configuración
            request.session['configurando_2fa_empresa'] = True
            request.session.modified = True
            
            return redirect('mostrar_qr_2fa_empresa')
        
        context = {
            'empresa': empresa,
            'es_obligatorio': True,
        }
        return render(request, 'core/configurar_2fa_empresa.html', context)
        
    except UserEmpresa.DoesNotExist:
        return redirect('loginEmpresa')

def mostrar_qr_2fa_empresa_view(request):
    """Vista para mostrar el código QR para configurar 2FA de empresa"""
    username_empresa = request.session.get('empresa_2fa_setup')
    configurando = request.session.get('configurando_2fa_empresa', False)
    
    if not username_empresa or not configurando:
        return redirect('loginEmpresa')
    
    try:
        empresa = UserEmpresa.objects.get(usernameEmpresa=username_empresa)
        
        if not empresa.two_factor_secret:
            return redirect('configurar_2fa_empresa')
        
        # Crear el URI para el código QR
        totp = pyotp.TOTP(empresa.two_factor_secret)
        provisioning_uri = totp.provisioning_uri(
            name=empresa.email if empresa.email else empresa.usernameEmpresa,
            issuer_name='Tu Idea Hecha Realidad - Empresa'
        )
        
        # Generar código QR
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir imagen a base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        context = {
            'empresa': empresa,
            'qr_code': img_base64,
            'secret_key': empresa.two_factor_secret,
            'es_obligatorio': True,
        }
        
        return render(request, 'core/mostrar_qr_2fa_empresa.html', context)
        
    except UserEmpresa.DoesNotExist:
        return redirect('loginEmpresa')

def verificar_2fa_setup_empresa_view(request):
    """Vista para verificar el código 2FA durante la configuración de empresa"""
    username_empresa = request.session.get('empresa_2fa_setup')
    configurando = request.session.get('configurando_2fa_empresa', False)
    
    if not username_empresa or not configurando:
        return redirect('loginEmpresa')
    
    try:
        empresa = UserEmpresa.objects.get(usernameEmpresa=username_empresa)
        
        if request.method == 'POST':
            codigo = request.POST.get('codigo')
            
            if not codigo:
                messages.error(request, 'Por favor ingresa el código de verificación')
                return redirect('mostrar_qr_2fa_empresa')
            
            # Verificar el código
            totp = pyotp.TOTP(empresa.two_factor_secret)
            if totp.verify(codigo, valid_window=1):
                # Activar 2FA
                empresa.two_factor_enabled = True
                empresa.save()
                
                # Limpiar sesiones de configuración
                request.session.pop('empresa_2fa_setup', None)
                request.session.pop('configurando_2fa_empresa', None)
                
                # Establecer sesión normal de empresa
                request.session['usernameEmpresa'] = empresa.usernameEmpresa
                request.session['empresa_id'] = empresa.id
                request.session.modified = True
                
                messages.success(request, '¡Autenticación de dos factores configurada exitosamente!')
                return redirect('dashboardEmpresa')
            else:
                messages.error(request, 'Código de verificación incorrecto. Intenta nuevamente.')
                return redirect('mostrar_qr_2fa_empresa')
        
        return redirect('mostrar_qr_2fa_empresa')
        
    except UserEmpresa.DoesNotExist:
        return redirect('loginEmpresa')

def verificar_2fa_login_empresa_view(request):
    """Vista para verificar el código 2FA durante el login de empresa"""
    username_temp = request.session.get('username_2fa_temp_empresa')
    
    if not username_temp:
        return redirect('loginEmpresa')
    
    try:
        empresa = UserEmpresa.objects.get(usernameEmpresa=username_temp)
        
        if request.method == 'POST':
            codigo = request.POST.get('codigo')
            
            if not codigo:
                messages.error(request, 'Por favor ingresa el código de verificación')
                return render(request, 'core/verificar_2fa_login_empresa.html', {'empresa': empresa})
            
            # Verificar el código
            totp = pyotp.TOTP(empresa.two_factor_secret)
            if totp.verify(codigo, valid_window=1):
                # Login exitoso
                request.session['usernameEmpresa'] = username_temp
                request.session['empresa_id'] = empresa.id
                request.session.pop('username_2fa_temp_empresa', None)
                request.session.modified = True
                
                messages.success(request, '¡Inicio de sesión exitoso!')
                return redirect('dashboardEmpresa')
            else:
                messages.error(request, 'Código de verificación incorrecto. Intenta nuevamente.')
                return render(request, 'core/verificar_2fa_login_empresa.html', {'empresa': empresa})
        
        context = {
            'empresa': empresa,
        }
        return render(request, 'core/verificar_2fa_login_empresa.html', context)
        
    except UserEmpresa.DoesNotExist:
        return redirect('loginEmpresa')


# ==================== VISTAS PARA SINCRONIZACIÓN DE CARRITO ====================

@require_http_methods(["POST"])
@csrf_exempt
def sincronizar_carrito_view(request):
    """Vista para sincronizar el carrito del usuario con la base de datos"""
    usernameCliente = request.session.get('usernameCliente')
    if not usernameCliente:
        return JsonResponse({'success': False, 'error': 'Usuario no autenticado'}, status=401)
    
    try:
        from .models import CarritoTemporal
        usuario = UserClientes.objects.get(usernameCliente=usernameCliente)
        
        # Obtener datos del carrito desde el request
        carrito_data = json.loads(request.body)
        
        # Mapeo de tipos a modelos
        modelos_map = {
            'mesa': Mesas,
            'silla': Sillas,
            'armario': Armarios,
            'cajonera': Cajoneras,
            'escritorio': Escritorios,
            'utensilio': Utensilios,
        }
        
        # Limpiar carrito anterior del usuario
        CarritoTemporal.objects.filter(usuario=usuario).delete()
        
        # Agregar nuevos items (solo productos activos y con stock)
        items_invalidos = []
        for item in carrito_data:
            producto_tipo = item['tipo']
            producto_id = item['id']
            cantidad = item['cantidad']
            
            # Validar que el producto existe, está activo y tiene stock
            modelo = modelos_map.get(producto_tipo)
            if modelo:
                try:
                    producto = modelo.objects.get(id=producto_id)
                    
                    # Validar que el producto esté activo
                    if not producto.is_active:
                        items_invalidos.append(f"{producto_tipo} ID {producto_id} (deshabilitado)")
                        continue
                    
                    # Validar que haya stock suficiente
                    if producto.cantidad_disponible < cantidad:
                        items_invalidos.append(f"{producto_tipo} ID {producto_id} (stock insuficiente)")
                        continue
                    
                    # Si pasa las validaciones, agregar al carrito
                    CarritoTemporal.objects.create(
                        usuario=usuario,
                        producto_tipo=producto_tipo,
                        producto_id=producto_id,
                        cantidad=cantidad
                    )
                except modelo.DoesNotExist:
                    items_invalidos.append(f"{producto_tipo} ID {producto_id} (no encontrado)")
        
        if items_invalidos:
            return JsonResponse({
                'success': False, 
                'error': 'Algunos productos no están disponibles',
                'items_invalidos': items_invalidos
            }, status=400)
        
        return JsonResponse({'success': True, 'mensaje': 'Carrito sincronizado'})
        
    except UserClientes.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def limpiar_carrito_view(request):
    """Vista para limpiar el carrito del usuario en la base de datos"""
    usernameCliente = request.session.get('usernameCliente')
    if not usernameCliente:
        return JsonResponse({'success': False, 'error': 'Usuario no autenticado'}, status=401)
    
    try:
        usuario = UserClientes.objects.get(usernameCliente=usernameCliente)
        
        # Eliminar todos los items del carrito del usuario
        CarritoTemporal.objects.filter(usuario=usuario).delete()
        
        return JsonResponse({'success': True, 'mensaje': 'Carrito limpiado'})
        
    except UserClientes.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from .models import Idea, UserEmpresa, MensajeIdea

# ========== ENDPOINT DE PRUEBA ==========

def test_session(request):
    """Endpoint para probar que la sesión funciona"""
    return JsonResponse({
        'session_keys': list(request.session.keys()),
        'usernameCliente': request.session.get('usernameCliente'),
        'usernameEmpresa': request.session.get('usernameEmpresa'),
        'session_key': request.session.session_key
    })

# ========== APIs PARA SISTEMA DE CHAT ==========

@require_http_methods(["GET"])
def api_conversaciones(request):
    """API para obtener todas las conversaciones del usuario actual"""
    print("\n" + "="*50)
    print("API CONVERSACIONES LLAMADA")
    print("="*50)
    
    try:
        # Determinar si es cliente o empresa
        username_cliente = request.session.get('usernameCliente')
        username_empresa = request.session.get('usernameEmpresa')
        
        print(f"Session keys: {list(request.session.keys())}")
        print(f"Cliente: {username_cliente}")
        print(f"Empresa: {username_empresa}")
        
        conversaciones = []
        tipo_usuario = None
        
        if username_cliente:
            # Usuario cliente: todas las ideas propias que tengan empresa asignada
            ideas = Idea.objects.filter(
                autor=username_cliente,
                empresa_asignada__isnull=False
            ).select_related('empresa_asignada').prefetch_related('mensajes').order_by('-fecha_creacion')
            tipo_usuario = 'cliente'
            print(f"Ideas del cliente '{username_cliente}' con empresa asignada: {ideas.count()}")
            
        elif username_empresa:
            # Usuario empresa: todas las ideas asignadas a esta empresa
            empresa = UserEmpresa.objects.get(usernameEmpresa=username_empresa)
            ideas = Idea.objects.filter(
                empresa_asignada=empresa
            ).prefetch_related('mensajes').order_by('-fecha_creacion')
            tipo_usuario = 'empresa'
            print(f"Ideas asignadas a empresa '{username_empresa}': {ideas.count()}")
            
        else:
            print("ERROR: No hay sesión activa")
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=401)
        
        # Construir conversaciones
        for idea in ideas:
            print(f"\n- Procesando idea: {idea.titulo} (ID: {idea.id})")
            
            # Contar mensajes totales y no leídos
            total_mensajes = idea.mensajes.count()
            mensajes_no_leidos = idea.mensajes.filter(
                leido=False
            ).exclude(
                remitente_tipo=tipo_usuario
            ).count()
            
            print(f"  Total mensajes: {total_mensajes}")
            print(f"  Mensajes no leídos: {mensajes_no_leidos}")
            
            # Obtener último mensaje o mensaje predeterminado
            ultimo_mensaje_obj = idea.mensajes.order_by('-fecha_envio').first()
            if ultimo_mensaje_obj:
                ultimo_mensaje = ultimo_mensaje_obj.mensaje[:50] + '...' if len(ultimo_mensaje_obj.mensaje) > 50 else ultimo_mensaje_obj.mensaje
                ultima_actualizacion = ultimo_mensaje_obj.fecha_envio.strftime('%d/%m/%Y %H:%M')
            else:
                ultimo_mensaje = "Inicia la conversación"
                ultima_actualizacion = idea.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            
            # Verificar si hay solicitud de permiso pendiente
            tiene_solicitud_permiso = idea.mensajes.filter(
                es_solicitud_permiso=True,
                remitente_tipo='empresa'
            ).exists() and not idea.permiso_publicacion
            
            # Obtener nombre del otro participante
            if tipo_usuario == 'cliente':
                otro_nombre = idea.empresa_asignada.usernameEmpresa
            else:
                otro_nombre = idea.autor
            
            conversacion = {
                'id': idea.id,
                'titulo': idea.titulo,
                'estado': idea.estado,
                'mensajes_no_leidos': mensajes_no_leidos,
                'total_mensajes': total_mensajes,
                'ultimo_mensaje': ultimo_mensaje,
                'ultima_actualizacion': ultima_actualizacion,
                'tiene_solicitud_permiso': tiene_solicitud_permiso,
                'permiso_otorgado': idea.permiso_publicacion,
                'otro_participante': otro_nombre
            }
            conversaciones.append(conversacion)
            print(f"  ✅ Conversación agregada")
        
        print(f"\n✅ Total conversaciones: {len(conversaciones)}")
        
        return JsonResponse({
            'success': True,
            'conversaciones': conversaciones,
            'tipo_usuario': tipo_usuario
        })
    
    except Exception as e:
        print(f"❌ ERROR en api_conversaciones: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
        
    except Exception as e:
        print(f"ERROR en api_conversaciones: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_mensajes_idea(request, idea_id):
    """API para obtener todos los mensajes de una idea específica"""
    try:
        # Determinar si es cliente o empresa
        username_cliente = request.session.get('usernameCliente')
        username_empresa = request.session.get('usernameEmpresa')
        
        if not username_cliente and not username_empresa:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=401)
        
        idea = Idea.objects.get(id=idea_id)
        
        # Verificar permisos
        if username_cliente and idea.autor != username_cliente:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
        elif username_empresa:
            empresa = UserEmpresa.objects.get(usernameEmpresa=username_empresa)
            if idea.empresa_asignada != empresa:
                return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
        
        # Obtener mensajes
        mensajes = idea.mensajes.all().order_by('fecha_envio')
        mensajes_data = [{
            'id': msg.id,
            'remitente_tipo': msg.remitente_tipo,
            'remitente_nombre': msg.remitente_nombre,
            'mensaje': msg.mensaje,
            'fecha_envio': msg.fecha_envio.strftime('%d/%m/%Y %H:%M'),
            'leido': msg.leido,
            'es_solicitud_permiso': msg.es_solicitud_permiso
        } for msg in mensajes]
        
        return JsonResponse({
            'success': True,
            'mensajes': mensajes_data,
            'idea': {
                'id': idea.id,
                'titulo': idea.titulo,
                'estado': idea.estado,
                'permiso_otorgado': idea.permiso_publicacion,
                'fecha_permiso': idea.fecha_permiso.strftime('%d/%m/%Y %H:%M') if idea.fecha_permiso else None
            }
        })
        
    except Idea.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Idea no encontrada'}, status=404)
    except Exception as e:
        print(f"Error en api_mensajes_idea: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
def api_enviar_mensaje(request, idea_id):
    """API para enviar un mensaje en una conversación"""
    try:
        # Determinar si es cliente o empresa
        username_cliente = request.session.get('usernameCliente')
        username_empresa = request.session.get('usernameEmpresa')
        
        if not username_cliente and not username_empresa:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=401)
        
        idea = Idea.objects.get(id=idea_id)
        mensaje_texto = request.POST.get('mensaje', '').strip()
        
        if not mensaje_texto:
            return JsonResponse({'success': False, 'error': 'El mensaje no puede estar vacío'}, status=400)
        
        # Determinar remitente
        if username_cliente:
            if idea.autor != username_cliente:
                return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
            remitente_tipo = 'cliente'
            remitente_nombre = username_cliente
        else:
            empresa = UserEmpresa.objects.get(usernameEmpresa=username_empresa)
            if idea.empresa_asignada != empresa:
                return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
            remitente_tipo = 'empresa'
            remitente_nombre = username_empresa
        
        # Crear mensaje
        mensaje = MensajeIdea.objects.create(
            idea=idea,
            remitente_tipo=remitente_tipo,
            remitente_nombre=remitente_nombre,
            mensaje=mensaje_texto,
            leido=False,
            es_solicitud_permiso=False
        )
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Mensaje enviado correctamente',
            'mensaje_id': mensaje.id
        })
        
    except Idea.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Idea no encontrada'}, status=404)
    except Exception as e:
        print(f"Error en api_enviar_mensaje: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
def api_marcar_leidos(request, idea_id):
    """API para marcar los mensajes de una idea como leídos"""
    try:
        # Determinar si es cliente o empresa
        username_cliente = request.session.get('usernameCliente')
        username_empresa = request.session.get('usernameEmpresa')
        
        if not username_cliente and not username_empresa:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=401)
        
        idea = Idea.objects.get(id=idea_id)
        
        # Determinar qué mensajes marcar como leídos (los del otro tipo)
        if username_cliente:
            tipo_para_marcar = 'empresa'
        else:
            tipo_para_marcar = 'cliente'
        
        # Marcar mensajes como leídos
        idea.mensajes.filter(
            remitente_tipo=tipo_para_marcar,
            leido=False
        ).update(leido=True)
        
        return JsonResponse({'success': True})
        
    except Idea.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Idea no encontrada'}, status=404)
    except Exception as e:
        print(f"Error en api_marcar_leidos: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ========== APIs PARA CHAT DE PAGOS ==========

@require_http_methods(["GET"])
def api_mensajes_pago(request, pago_id):
    """API para obtener todos los mensajes de un pago específico"""
    from .models import Pago, MensajePago, UserClientes
    
    print(f"\n{'='*60}")
    print(f"API MENSAJES PAGO - ID: {pago_id}")
    print(f"{'='*60}")
    
    try:
        # Determinar si es cliente o empresa
        username_cliente = request.session.get('usernameCliente')
        username_empresa = request.session.get('usernameEmpresa')
        
        print(f"Username Cliente: {username_cliente}")
        print(f"Username Empresa: {username_empresa}")
        
        if not username_cliente and not username_empresa:
            print("❌ ERROR: No hay sesión activa")
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=401)
        
        pago = Pago.objects.get(id=pago_id)
        print(f"✓ Pago encontrado: #{pago.id} - Cliente: {pago.cliente.usernameCliente}")
        
        # Verificar permisos
        if username_cliente:
            cliente = UserClientes.objects.get(usernameCliente=username_cliente)
            if pago.cliente != cliente:
                print(f"❌ ERROR: Cliente no autorizado")
                return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
        elif username_empresa:
            # La empresa puede ver cualquier pago
            print(f"✓ Empresa autorizada para ver todos los pagos")
        
        # Obtener mensajes
        mensajes = MensajePago.objects.filter(pago=pago).order_by('fecha_envio')
        print(f"✓ Mensajes encontrados: {mensajes.count()}")
        
        for msg in mensajes:
            print(f"  - Mensaje #{msg.id}: {msg.remitente_tipo} - {msg.remitente_nombre} - {msg.mensaje[:50]}")
        
        mensajes_data = [{
            'id': msg.id,
            'remitente_tipo': msg.remitente_tipo,
            'remitente_nombre': msg.remitente_nombre,
            'mensaje': msg.mensaje,
            'imagen': msg.imagen.url if msg.imagen else None,
            'fecha_envio': msg.fecha_envio.strftime('%d/%m/%Y %H:%M'),
            'leido': msg.leido
        } for msg in mensajes]
        
        print(f"✓ Retornando {len(mensajes_data)} mensajes")
        print(f"{'='*60}\n")
        
        return JsonResponse({
            'success': True,
            'mensajes': mensajes_data,
            'pago': {
                'id': pago.id,
                'estado': pago.estado,
                'monto_total': float(pago.monto_total)
            }
        })
        
    except Pago.DoesNotExist:
        print(f"❌ ERROR: Pago no encontrado")
        return JsonResponse({'success': False, 'error': 'Pago no encontrado'}, status=404)
    except Exception as e:
        print(f"❌ ERROR CRÍTICO en api_mensajes_pago: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
def api_enviar_mensaje_pago(request, pago_id):
    """API para enviar un mensaje en el chat de un pago"""
    from .models import Pago, MensajePago, UserClientes
    
    try:
        # Determinar si es cliente o empresa
        username_cliente = request.session.get('usernameCliente')
        username_empresa = request.session.get('usernameEmpresa')
        
        if not username_cliente and not username_empresa:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=401)
        
        pago = Pago.objects.get(id=pago_id)
        mensaje_texto = request.POST.get('mensaje', '').strip()
        imagen = request.FILES.get('imagen', None)
        
        if not mensaje_texto and not imagen:
            return JsonResponse({'success': False, 'error': 'Debes enviar un mensaje o una imagen'}, status=400)
        
        # Determinar remitente
        if username_cliente:
            cliente = UserClientes.objects.get(usernameCliente=username_cliente)
            if pago.cliente != cliente:
                return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
            remitente_tipo = 'cliente'
            remitente_nombre = username_cliente
        else:
            remitente_tipo = 'empresa'
            remitente_nombre = username_empresa
        
        # Crear mensaje
        mensaje = MensajePago.objects.create(
            pago=pago,
            remitente_tipo=remitente_tipo,
            remitente_nombre=remitente_nombre,
            mensaje=mensaje_texto if mensaje_texto else '[Imagen enviada]',
            imagen=imagen,
            leido=False
        )
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Mensaje enviado correctamente',
            'mensaje_id': mensaje.id
        })
        
    except Pago.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pago no encontrado'}, status=404)
    except Exception as e:
        print(f"Error en api_enviar_mensaje_pago: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_conversaciones_pagos(request):
    """API para obtener todas las conversaciones de pagos (cliente o empresa)"""
    from .models import Pago, MensajePago, UserClientes
    
    print(f"\n{'='*60}")
    print(f"API CONVERSACIONES PAGOS")
    print(f"{'='*60}")
    
    try:
        username_cliente = request.session.get('usernameCliente')
        username_empresa = request.session.get('usernameEmpresa')
        
        print(f"Username Cliente: {username_cliente}")
        print(f"Username Empresa: {username_empresa}")
        
        if not username_cliente and not username_empresa:
            print("❌ ERROR: No hay sesión activa")
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=401)
        
        conversaciones = []
        
        if username_cliente:
            # Cliente: ver sus pagos rechazados
            cliente = UserClientes.objects.get(usernameCliente=username_cliente)
            pagos = Pago.objects.filter(
                cliente=cliente,
                estado='rechazado'
            ).prefetch_related('mensajes').order_by('-fecha_creacion')
            
            print(f"✓ Cliente: {cliente.usernameCliente}")
            print(f"✓ Pagos rechazados: {pagos.count()}")
            
            tipo_mensajes_no_leidos = 'empresa'
            otro_participante_nombre = 'Empresa'
            
        else:
            # Empresa: ver TODOS los pagos que tienen mensajes (cualquier estado)
            # Obtener IDs de pagos que tienen al menos un mensaje
            pagos_con_mensajes_ids = MensajePago.objects.values_list('pago_id', flat=True).distinct()
            print(f"✓ Pagos con mensajes IDs: {list(pagos_con_mensajes_ids)}")
            
            pagos = Pago.objects.filter(
                id__in=pagos_con_mensajes_ids
            ).prefetch_related('mensajes', 'cliente').order_by('-fecha_creacion')
            
            print(f"✓ Empresa: {username_empresa}")
            print(f"✓ Total pagos con mensajes: {pagos.count()}")
            
            tipo_mensajes_no_leidos = 'cliente'
            otro_participante_nombre = None  # Se define por pago
        
        for pago in pagos:
            # Contar mensajes
            total_mensajes = pago.mensajes.count()
            mensajes_no_leidos = pago.mensajes.filter(
                leido=False,
                remitente_tipo=tipo_mensajes_no_leidos
            ).count()
            
            # Obtener último mensaje
            ultimo_mensaje_obj = pago.mensajes.order_by('-fecha_envio').first()
            if ultimo_mensaje_obj:
                ultimo_mensaje = ultimo_mensaje_obj.mensaje[:50] + '...' if len(ultimo_mensaje_obj.mensaje) > 50 else ultimo_mensaje_obj.mensaje
                ultima_actualizacion = ultimo_mensaje_obj.fecha_envio.strftime('%d/%m/%Y %H:%M')
            else:
                ultimo_mensaje = pago.notas_empresa or "Pago rechazado"
                ultima_actualizacion = pago.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            
            # Para empresa, el otro participante es el cliente
            if username_empresa:
                otro_participante_nombre = pago.cliente.usernameCliente
            
            conversacion = {
                'id': pago.id,
                'estado': pago.estado,
                'monto_total': float(pago.monto_total),
                'mensajes_no_leidos': mensajes_no_leidos,
                'total_mensajes': total_mensajes,
                'ultimo_mensaje': ultimo_mensaje,
                'ultima_actualizacion': ultima_actualizacion,
                'otro_participante': otro_participante_nombre
            }
            conversaciones.append(conversacion)
        
        return JsonResponse({
            'success': True,
            'conversaciones': conversaciones
        })
        
    except UserClientes.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cliente no encontrado'}, status=404)
    except Exception as e:
        print(f"Error en api_conversaciones_pagos: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
def api_marcar_leidos_pago(request, pago_id):
    """API para marcar los mensajes de un pago como leídos"""
    from .models import Pago, MensajePago, UserClientes
    
    try:
        username_cliente = request.session.get('usernameCliente')
        username_empresa = request.session.get('usernameEmpresa')
        
        if not username_cliente and not username_empresa:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=401)
        
        pago = Pago.objects.get(id=pago_id)
        
        # Determinar qué mensajes marcar como leídos (los del otro tipo)
        if username_cliente:
            tipo_para_marcar = 'empresa'
        else:
            tipo_para_marcar = 'cliente'
        
        # Marcar mensajes como leídos
        MensajePago.objects.filter(
            pago=pago,
            remitente_tipo=tipo_para_marcar,
            leido=False
        ).update(leido=True)
        
        return JsonResponse({'success': True})
        
    except Pago.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pago no encontrado'}, status=404)
    except Exception as e:
        print(f"Error en api_marcar_leidos_pago: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

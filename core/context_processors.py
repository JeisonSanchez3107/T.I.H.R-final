from .models import Idea, UserClientes, UserEmpresa, MensajeIdea


def idea_notifications(request):
    """Context processor que añade has_idea_notifications al contexto global.

    - Busca en la sesión 'usernameCliente' o 'usernameEmpresa'.
    - Para clientes: verifica si tienen mensajes no leídos de empresas.
    - Para empresas: verifica si tienen mensajes no leídos de clientes.
    """
    username_cliente = request.session.get('usernameCliente')
    username_empresa = request.session.get('usernameEmpresa')
    has_notif = False
    
    try:
        if username_cliente:
            # Cliente: buscar mensajes no leídos de empresas
            has_notif = MensajeIdea.objects.filter(
                idea__autor=username_cliente,
                remitente_tipo='empresa',
                leido=False
            ).exists()
            
        elif username_empresa:
            # Empresa: buscar mensajes no leídos de clientes
            empresa = UserEmpresa.objects.get(usernameEmpresa=username_empresa)
            has_notif = MensajeIdea.objects.filter(
                idea__empresa_asignada=empresa,
                remitente_tipo='cliente',
                leido=False
            ).exists()
            
    except Exception as e:
        # En caso de cualquier error, no romper la página
        print(f"Error en idea_notifications: {str(e)}")
        has_notif = False

    return {
        'has_idea_notifications': has_notif
    }

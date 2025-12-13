from django.shortcuts import render
from core.models import Armarios, Escritorios, Sillas, Cajoneras, Mesas, Utensilios, UserClientes

def carpinteria(request):
    # Obtener el usuario de la sesión
    usernameCliente = request.session.get('usernameCliente')
    usuario = None
    if usernameCliente:
        try:
            usuario = UserClientes.objects.get(usernameCliente=usernameCliente)
        except UserClientes.DoesNotExist:
            pass
    
    armarios = Armarios.objects.filter(is_active=True)
    context = {
        'armarios': armarios,
        'usuario': usuario
    }
    return render(request, "Productos/carpinteria.html", context)

def marroquineria(request):
    # Obtener el usuario de la sesión
    usernameCliente = request.session.get('usernameCliente')
    usuario = None
    if usernameCliente:
        try:
            usuario = UserClientes.objects.get(usernameCliente=usernameCliente)
        except UserClientes.DoesNotExist:
            pass
    
    escritorios = Escritorios.objects.filter(is_active=True)
    context = {
        'escritorios': escritorios,
        'usuario': usuario
    }
    return render(request, "Productos/marroquineria.html", context)

def tapiceria(request):
    # Obtener el usuario de la sesión
    usernameCliente = request.session.get('usernameCliente')
    usuario = None
    if usernameCliente:
        try:
            usuario = UserClientes.objects.get(usernameCliente=usernameCliente)
        except UserClientes.DoesNotExist:
            pass
    
    utensilios = Utensilios.objects.filter(is_active=True)
    context = {
        'utensilios': utensilios,
        'usuario': usuario
    }
    return render(request, "Productos/tapiceria.html", context)

def vidrieria(request):
    # Obtener el usuario de la sesión
    usernameCliente = request.session.get('usernameCliente')
    usuario = None
    if usernameCliente:
        try:
            usuario = UserClientes.objects.get(usernameCliente=usernameCliente)
        except UserClientes.DoesNotExist:
            pass
    
    sillas = Sillas.objects.filter(is_active=True)
    context = {
        'sillas': sillas,
        'usuario': usuario
    }
    return render(request, "Productos/vidrieria.html", context)

def metaleria(request):
    # Obtener el usuario de la sesión
    usernameCliente = request.session.get('usernameCliente')
    usuario = None
    if usernameCliente:
        try:
            usuario = UserClientes.objects.get(usernameCliente=usernameCliente)
        except UserClientes.DoesNotExist:
            pass
    
    cajoneras = Cajoneras.objects.filter(is_active=True)
    context = {
        'cajoneras': cajoneras,
        'usuario': usuario
    }
    return render(request, "Productos/metaleria.html", context)

def ceramica(request):
    # Obtener el usuario de la sesión
    usernameCliente = request.session.get('usernameCliente')
    usuario = None
    if usernameCliente:
        try:
            usuario = UserClientes.objects.get(usernameCliente=usernameCliente)
        except UserClientes.DoesNotExist:
            pass
    
    mesas = Mesas.objects.filter(is_active=True)
    context = {
        'mesas': mesas,
        'usuario': usuario
    }
    return render(request, "Productos/ceramica.html", context)

# Create your views here.

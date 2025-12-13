"""
Script para eliminar todo el contenido de las tablas Idea y MensajeIdea
sin eliminar las tablas en sí.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Gangazos1.settings')
django.setup()

from core.models import Idea, MensajeIdea

def eliminar_contenido_ideas():
    """Elimina todos los registros de Idea y MensajeIdea"""
    
    print("=== Eliminando contenido de gestión de ideas ===\n")
    
    # Contar registros antes de eliminar
    total_mensajes = MensajeIdea.objects.count()
    total_ideas = Idea.objects.count()
    
    print(f"Mensajes de ideas encontrados: {total_mensajes}")
    print(f"Ideas encontradas: {total_ideas}\n")
    
    if total_mensajes == 0 and total_ideas == 0:
        print("✓ No hay contenido para eliminar. Las tablas ya están vacías.\n")
        return
    
    # Confirmar eliminación
    respuesta = input("¿Estás seguro de eliminar todo el contenido? (s/n): ")
    
    if respuesta.lower() != 's':
        print("\n✗ Operación cancelada.\n")
        return
    
    # Eliminar mensajes primero (tienen foreign key a Idea)
    if total_mensajes > 0:
        MensajeIdea.objects.all().delete()
        print(f"✓ {total_mensajes} mensajes eliminados")
    
    # Eliminar ideas
    if total_ideas > 0:
        Idea.objects.all().delete()
        print(f"✓ {total_ideas} ideas eliminadas")
    
    print("\n=== Proceso completado ===")
    print("Las tablas Idea y MensajeIdea siguen existiendo pero están vacías.")
    print("Los usuarios pueden seguir creando ideas si es necesario.\n")

if __name__ == '__main__':
    eliminar_contenido_ideas()

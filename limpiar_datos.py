"""
Script para limpiar datos de usuarios, pagos y pedidos de la base de datos
Ejecutar con: python manage.py shell < limpiar_datos.py
"""

from core.models import User, UserClientes, UserEmpresa, Pago, Pedido, Comentario, CarritoTemporal
from django.utils import timezone

print("=== Iniciando limpieza de datos ===\n")

# Eliminar usuarios User (modelo antiguo)
user_count = User.objects.count()
if user_count > 0:
    User.objects.all().delete()
    print(f"✓ Eliminados {user_count} registros de User")
else:
    print("✓ No hay registros de User para eliminar")

# Eliminar CarritoTemporal
carrito_count = CarritoTemporal.objects.count()
if carrito_count > 0:
    CarritoTemporal.objects.all().delete()
    print(f"✓ Eliminados {carrito_count} registros de CarritoTemporal")
else:
    print("✓ No hay registros de CarritoTemporal para eliminar")

# Eliminar Pagos
pago_count = Pago.objects.count()
if pago_count > 0:
    Pago.objects.all().delete()
    print(f"✓ Eliminados {pago_count} registros de Pago")
else:
    print("✓ No hay registros de Pago para eliminar")

# Eliminar Pedidos
pedido_count = Pedido.objects.count()
if pedido_count > 0:
    Pedido.objects.all().delete()
    print(f"✓ Eliminados {pedido_count} registros de Pedido")
else:
    print("✓ No hay registros de Pedido para eliminar")

# Eliminar Comentarios
comentario_count = Comentario.objects.count()
if comentario_count > 0:
    Comentario.objects.all().delete()
    print(f"✓ Eliminados {comentario_count} registros de Comentario")
else:
    print("✓ No hay registros de Comentario para eliminar")

# Eliminar UserClientes
cliente_count = UserClientes.objects.count()
if cliente_count > 0:
    UserClientes.objects.all().delete()
    print(f"✓ Eliminados {cliente_count} registros de UserClientes")
else:
    print("✓ No hay registros de UserClientes para eliminar")

# Eliminar UserEmpresa
empresa_count = UserEmpresa.objects.count()
if empresa_count > 0:
    UserEmpresa.objects.all().delete()
    print(f"✓ Eliminados {empresa_count} registros de UserEmpresa")
else:
    print("✓ No hay registros de UserEmpresa para eliminar")

print("\n=== Limpieza completada ===")
print(f"Total de registros eliminados: {user_count + carrito_count + pago_count + pedido_count + comentario_count + cliente_count + empresa_count}")

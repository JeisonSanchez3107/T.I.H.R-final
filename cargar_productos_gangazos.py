from core.models import Mesas, Sillas, Armarios, Cajoneras, Escritorios, Utensilios

def cargar_productos():
    # Mesas
    Mesas.objects.create(nombre1='Mesa Comedor Clásica', descripcion1='Mesa de comedor en madera maciza, ideal para 6 personas.', precio1=450000, cantidad_disponible=10, is_active=True)
    Mesas.objects.create(nombre1='Mesa Escritorio Moderna', descripcion1='Escritorio compacto para oficina o estudio.', precio1=320000, cantidad_disponible=8, is_active=True)
    # Sillas
    Sillas.objects.create(nombre2='Silla Ergonómica', descripcion2='Silla con soporte lumbar y asiento acolchado.', precio2=120000, cantidad_disponible=15, is_active=True)
    Sillas.objects.create(nombre2='Silla de Comedor', descripcion2='Silla de comedor en madera y tapizado.', precio2=95000, cantidad_disponible=20, is_active=True)
    # Armarios
    Armarios.objects.create(nombre3='Armario 2 Puertas', descripcion3='Armario compacto para ropa corta y larga.', precio3=600000, cantidad_disponible=5, is_active=True)
    # Cajoneras
    Cajoneras.objects.create(nombre4='Cajonera 3 Cajones', descripcion4='Cajonera de madera con correderas metálicas.', precio4=180000, cantidad_disponible=12, is_active=True)
    # Escritorios
    Escritorios.objects.create(nombre5='Escritorio Juvenil', descripcion5='Escritorio para habitación juvenil, resistente y moderno.', precio5=250000, cantidad_disponible=7, is_active=True)
    # Utensilios
    Utensilios.objects.create(nombre6='Porta Cubiertos', descripcion6='Utensilio de cocina en madera para cubiertos.', precio6=35000, cantidad_disponible=30, is_active=True)
    print('Productos de gangazos cargados correctamente.')

if __name__ == '__main__':
    cargar_productos()
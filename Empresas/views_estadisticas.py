from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from core.models import UserClientes, Pedido, Pago, Mesas, Sillas, Armarios, Cajoneras, Escritorios, Utensilios
from django.db.models import Sum, Count, Q
from datetime import datetime
import io
import base64

def estadisticas_view(request):
    """Vista para mostrar estadísticas de la empresa"""
    if 'empresa_id' not in request.session:
        return redirect('login_empresa')
    
    # Estadísticas de usuarios
    total_usuarios = UserClientes.objects.count()
    usuarios_activos = UserClientes.objects.filter(is_active=True).count()
    
    # Estadísticas de productos con cantidades en inventario
    total_mesas = Mesas.objects.count()
    inventario_mesas = Mesas.objects.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
    
    total_sillas = Sillas.objects.count()
    inventario_sillas = Sillas.objects.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
    
    total_armarios = Armarios.objects.count()
    inventario_armarios = Armarios.objects.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
    
    total_cajoneras = Cajoneras.objects.count()
    inventario_cajoneras = Cajoneras.objects.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
    
    total_escritorios = Escritorios.objects.count()
    inventario_escritorios = Escritorios.objects.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
    
    total_utensilios = Utensilios.objects.count()
    inventario_utensilios = Utensilios.objects.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
    
    # Total de productos publicados y en inventario
    total_productos = total_mesas + total_sillas + total_armarios + total_cajoneras + total_escritorios + total_utensilios
    total_inventario = inventario_mesas + inventario_sillas + inventario_armarios + inventario_cajoneras + inventario_escritorios + inventario_utensilios
    
    # Estadísticas de pedidos
    total_pedidos = Pedido.objects.count()
    pedidos_procesando = Pedido.objects.filter(estado='procesando').count()
    pedidos_enviado = Pedido.objects.filter(estado='enviado').count()
    pedidos_en_transito = Pedido.objects.filter(estado='en_transito').count()
    pedidos_entregado = Pedido.objects.filter(estado='entregado').count()
    
    # Estadísticas de pagos
    total_pagos = Pago.objects.count()
    pagos_pendientes = Pago.objects.filter(estado='pendiente').count()
    pagos_confirmados = Pago.objects.filter(estado='confirmado').count()
    pagos_rechazados = Pago.objects.filter(estado='rechazado').count()
    
    # Ingresos totales
    ingresos_totales = Pago.objects.filter(estado='confirmado').aggregate(total=Sum('monto_total'))['total'] or 0
    
    context = {
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'total_productos': total_productos,
        'total_inventario': total_inventario,
        'total_mesas': total_mesas,
        'inventario_mesas': inventario_mesas,
        'total_sillas': total_sillas,
        'inventario_sillas': inventario_sillas,
        'total_armarios': total_armarios,
        'inventario_armarios': inventario_armarios,
        'total_cajoneras': total_cajoneras,
        'inventario_cajoneras': inventario_cajoneras,
        'total_escritorios': total_escritorios,
        'inventario_escritorios': inventario_escritorios,
        'total_utensilios': total_utensilios,
        'inventario_utensilios': inventario_utensilios,
        'total_pedidos': total_pedidos,
        'pedidos_procesando': pedidos_procesando,
        'pedidos_enviado': pedidos_enviado,
        'pedidos_en_transito': pedidos_en_transito,
        'pedidos_entregado': pedidos_entregado,
        'total_pagos': total_pagos,
        'pagos_pendientes': pagos_pendientes,
        'pagos_confirmados': pagos_confirmados,
        'pagos_rechazados': pagos_rechazados,
        'ingresos_totales': ingresos_totales,
    }
    
    return render(request, 'Empresas/estadisticas.html', context)

def inventario_view(request):
    """Vista para gestionar el inventario de productos"""
    if 'empresa_id' not in request.session:
        return redirect('login_empresa')
    
    # Obtener todos los productos
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
    
    return render(request, 'Empresas/inventario.html', context)

@require_POST
def actualizar_inventario_view(request):
    """Vista para actualizar la cantidad disponible de un producto"""
    if 'empresa_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=401)
    
    try:
        producto_tipo = request.POST.get('tipo')
        producto_id = request.POST.get('id')
        nueva_cantidad = int(request.POST.get('cantidad'))
        
        # Obtener el modelo correcto según el tipo
        modelos = {
            'mesa': Mesas,
            'silla': Sillas,
            'armario': Armarios,
            'cajonera': Cajoneras,
            'escritorio': Escritorios,
            'utensilio': Utensilios
        }
        
        modelo = modelos.get(producto_tipo)
        if not modelo:
            return JsonResponse({'success': False, 'error': 'Tipo de producto inválido'}, status=400)
        
        producto = modelo.objects.get(id=producto_id)
        producto.cantidad_disponible = nueva_cantidad
        producto.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Inventario actualizado: {nueva_cantidad} unidades disponibles'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def descargar_estadisticas_pdf(request):
    """Genera y descarga un PDF con las estadísticas de ventas y gráficas"""
    if 'empresa_id' not in request.session:
        return redirect('login_empresa')
    
    try:
        from xhtml2pdf import pisa
        from django.template.loader import get_template
        import matplotlib
        matplotlib.use('Agg')  # Usar backend sin interfaz gráfica
        import matplotlib.pyplot as plt
        
        # Obtener todas las estadísticas (reutilizando la lógica de estadisticas_view)
        total_usuarios = UserClientes.objects.count()
        usuarios_activos = UserClientes.objects.filter(is_active=True).count()
        
        # Estadísticas de productos
        total_mesas = Mesas.objects.count()
        inventario_mesas = Mesas.objects.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
        total_sillas = Sillas.objects.count()
        inventario_sillas = Sillas.objects.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
        total_armarios = Armarios.objects.count()
        inventario_armarios = Armarios.objects.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
        total_cajoneras = Cajoneras.objects.count()
        inventario_cajoneras = Cajoneras.objects.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
        total_escritorios = Escritorios.objects.count()
        inventario_escritorios = Escritorios.objects.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
        total_utensilios = Utensilios.objects.count()
        inventario_utensilios = Utensilios.objects.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
        
        total_productos = total_mesas + total_sillas + total_armarios + total_cajoneras + total_escritorios + total_utensilios
        total_inventario = inventario_mesas + inventario_sillas + inventario_armarios + inventario_cajoneras + inventario_escritorios + inventario_utensilios
        
        # Estadísticas de pedidos
        total_pedidos = Pedido.objects.count()
        pedidos_procesando = Pedido.objects.filter(estado='procesando').count()
        pedidos_enviado = Pedido.objects.filter(estado='enviado').count()
        pedidos_entregado = Pedido.objects.filter(estado='entregado').count()
        
        # Estadísticas de pagos
        pagos_pendientes = Pago.objects.filter(estado='pendiente').count()
        pagos_confirmados = Pago.objects.filter(estado='confirmado').count()
        pagos_rechazados = Pago.objects.filter(estado='rechazado').count()
        ingresos_totales = Pago.objects.filter(estado='confirmado').aggregate(total=Sum('monto_total'))['total'] or 0
        
        # Generar gráficas en base64 para incrustar en el PDF
        
        # Gráfica 1: Productos por categoría (Gráfica de barras)
        fig1, ax1 = plt.figure(figsize=(8, 5)), plt.gca()
        categorias = ['Mesas', 'Sillas', 'Armarios', 'Cajoneras', 'Escritorios', 'Utensilios']
        cantidades = [total_mesas, total_sillas, total_armarios, total_cajoneras, total_escritorios, total_utensilios]
        colores = ['#A0662F', '#7A3E0E', '#8B4513', '#D2691E', '#CD853F', '#DEB887']
        
        ax1.bar(categorias, cantidades, color=colores)
        ax1.set_xlabel('Categorías', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Cantidad de Productos', fontsize=12, fontweight='bold')
        ax1.set_title('Productos por Categoría', fontsize=14, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        buffer1 = io.BytesIO()
        plt.savefig(buffer1, format='png', dpi=150, bbox_inches='tight')
        buffer1.seek(0)
        grafica1_base64 = base64.b64encode(buffer1.read()).decode()
        plt.close()
        
        # Gráfica 2: Estado de pedidos (Gráfica de pastel)
        fig2, ax2 = plt.figure(figsize=(7, 5)), plt.gca()
        estados_pedidos = ['Procesando', 'Enviado', 'Entregado']
        cantidades_pedidos = [pedidos_procesando, pedidos_enviado, pedidos_entregado]
        colores_pedidos = ['#FFA500', '#4169E1', '#32CD32']
        
        # Filtrar solo valores mayores a 0
        datos_filtrados = [(e, c, col) for e, c, col in zip(estados_pedidos, cantidades_pedidos, colores_pedidos) if c > 0]
        if datos_filtrados:
            estados_f, cantidades_f, colores_f = zip(*datos_filtrados)
            ax2.pie(cantidades_f, labels=estados_f, autopct='%1.1f%%', colors=colores_f, startangle=90)
            ax2.set_title('Estado de Pedidos', fontsize=14, fontweight='bold')
        else:
            ax2.text(0.5, 0.5, 'Sin datos', ha='center', va='center', fontsize=16)
            ax2.set_title('Estado de Pedidos', fontsize=14, fontweight='bold')
        
        buffer2 = io.BytesIO()
        plt.savefig(buffer2, format='png', dpi=150, bbox_inches='tight')
        buffer2.seek(0)
        grafica2_base64 = base64.b64encode(buffer2.read()).decode()
        plt.close()
        
        # Gráfica 3: Estado de pagos (Gráfica de pastel)
        fig3, ax3 = plt.figure(figsize=(7, 5)), plt.gca()
        estados_pagos = ['Pendiente', 'Confirmado', 'Rechazado']
        cantidades_pagos = [pagos_pendientes, pagos_confirmados, pagos_rechazados]
        colores_pagos = ['#FFA500', '#32CD32', '#DC143C']
        
        # Filtrar solo valores mayores a 0
        datos_pagos_filtrados = [(e, c, col) for e, c, col in zip(estados_pagos, cantidades_pagos, colores_pagos) if c > 0]
        if datos_pagos_filtrados:
            estados_pf, cantidades_pf, colores_pf = zip(*datos_pagos_filtrados)
            ax3.pie(cantidades_pf, labels=estados_pf, autopct='%1.1f%%', colors=colores_pf, startangle=90)
            ax3.set_title('Estado de Pagos', fontsize=14, fontweight='bold')
        else:
            ax3.text(0.5, 0.5, 'Sin datos', ha='center', va='center', fontsize=16)
            ax3.set_title('Estado de Pagos', fontsize=14, fontweight='bold')
        
        buffer3 = io.BytesIO()
        plt.savefig(buffer3, format='png', dpi=150, bbox_inches='tight')
        buffer3.seek(0)
        grafica3_base64 = base64.b64encode(buffer3.read()).decode()
        plt.close()
        
        # Preparar el contexto para el template
        context = {
            'fecha_generacion': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'total_usuarios': total_usuarios,
            'usuarios_activos': usuarios_activos,
            'total_productos': total_productos,
            'total_inventario': total_inventario,
            'total_mesas': total_mesas,
            'inventario_mesas': inventario_mesas,
            'total_sillas': total_sillas,
            'inventario_sillas': inventario_sillas,
            'total_armarios': total_armarios,
            'inventario_armarios': inventario_armarios,
            'total_cajoneras': total_cajoneras,
            'inventario_cajoneras': inventario_cajoneras,
            'total_escritorios': total_escritorios,
            'inventario_escritorios': inventario_escritorios,
            'total_utensilios': total_utensilios,
            'inventario_utensilios': inventario_utensilios,
            'total_pedidos': total_pedidos,
            'pedidos_procesando': pedidos_procesando,
            'pedidos_enviado': pedidos_enviado,
            'pedidos_entregado': pedidos_entregado,
            'pagos_pendientes': pagos_pendientes,
            'pagos_confirmados': pagos_confirmados,
            'pagos_rechazados': pagos_rechazados,
            'ingresos_totales': ingresos_totales,
            'grafica1': grafica1_base64,
            'grafica2': grafica2_base64,
            'grafica3': grafica3_base64,
        }
        
        # Cargar y renderizar el template
        template = get_template('Empresas/estadisticas_pdf.html')
        html = template.render(context)
        
        # Crear respuesta HTTP para PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Estadisticas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        
        # Generar PDF
        pisa_status = pisa.CreatePDF(
            html.encode('utf-8'),
            dest=response,
            encoding='utf-8'
        )
        
        if pisa_status.err:
            return HttpResponse('Error al generar el PDF', status=500)
        
        return response
        
    except ImportError as e:
        error_msg = str(e)
        if 'matplotlib' in error_msg:
            return HttpResponse('Error: La librería matplotlib no está instalada. Por favor, ejecute: pip install matplotlib', status=500)
        elif 'xhtml2pdf' in error_msg:
            return HttpResponse('Error: La librería xhtml2pdf no está instalada. Por favor, ejecute: pip install xhtml2pdf', status=500)
        else:
            return HttpResponse(f'Error de importación: {error_msg}', status=500)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error al generar PDF de estadísticas: {e}")
        print(error_trace)
        return HttpResponse(f'Error al generar el PDF: {str(e)}', status=500)

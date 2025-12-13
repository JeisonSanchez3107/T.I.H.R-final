"""
URL configuration for Gangazos1 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include,re_path
from django.conf import settings
from django.conf.urls.static import static
from core import views
from Empresas import views as empresas_views

urlpatterns = [
    path('',views.home,name='home'),
    path('', views.chatbot, name="chatbot"),
    path('contact/',views.contact,name='contact'),
    path('reglas/',views.reglas,name='reglas'),
    path('productos/',views.productos,name='productos'),
    path('registro/',views.registro,name='registro'),
    path('verificar-codigo/',views.verificar_codigo,name='verificar_codigo'),
    path('login/',views.Login_view,name='login'),
    path('loginEmpresa/',empresas_views.registro_empresa_view,name='loginEmpresa'),
    path('loginEmpresa/login/',empresas_views.login_empresa_view,name='loginEmpresa_login'),
    path('logout/',views.Logout_view,name='logout'),
    path('home2/',views.Home2_view,name='home2'),
    path('home3/',views.Home3_view,name='home3'),
    path('carrito', views.carrito, name='carrito'),
    path('MetodosPago', views.MetodosPago, name='MetodosPago'),
    path('procesar-pago/', views.procesar_pago, name='procesar_pago'),
    path('idea/', views.ideas_view, name='idea'),
    path('perfilUsuario/', views.perfilUsuario_view, name='perfilUsuario'),
    # URLs para autenticación de dos factores (2FA)
    path('activar-2fa/', views.activar_2fa_view, name='activar_2fa'),
    path('mostrar-qr-2fa/', views.mostrar_qr_2fa_view, name='mostrar_qr_2fa'),
    path('verificar-2fa-setup/', views.verificar_2fa_setup_view, name='verificar_2fa_setup'),
    path('verificar-2fa-login/', views.verificar_2fa_login_view, name='verificar_2fa_login'),
    path('desactivar-2fa/', views.desactivar_2fa_view, name='desactivar_2fa'),
    # URLs para autenticación de dos factores (2FA) para EMPRESAS - OBLIGATORIO
    path('configurar-2fa-empresa/', empresas_views.configurar_2fa_empresa_view, name='configurar_2fa_empresa'),
    path('mostrar-qr-2fa-empresa/', views.mostrar_qr_2fa_empresa_view, name='mostrar_qr_2fa_empresa'),
    path('verificar-2fa-setup-empresa/', views.verificar_2fa_setup_empresa_view, name='verificar_2fa_setup_empresa'),
    path('verificar-2fa-login-empresa/', empresas_views.verificar_2fa_empresa_login, name='verificar_2fa_login_empresa'),
    # Incluir URLs de comentarios y perfil desde core
    path('comentarios/', views.comentarios_view, name='comentarios'),
    path('comentarios/crear/', views.crear_comentario_view, name='crear_comentario'),
    path('comentarios/eliminar/<int:comentario_id>/', views.eliminar_comentario_view, name='eliminar_comentario'),
    path('perfil/editar/', views.editar_perfil_view, name='editar_perfil'),
    # URLs para gestión de comentarios por empresa
    path('empresa/comentarios/', views.empresa_comentarios_view, name='empresa_comentarios'),
    path('obtener-comentarios-cliente/<int:cliente_id>/', views.obtener_comentarios_cliente_view, name='obtener_comentarios_cliente'),
    path('empresa/comentarios/aprobar/<int:comentario_id>/', views.aprobar_comentario_view, name='aprobar_comentario'),
    path('empresa/comentarios/rechazar/<int:comentario_id>/', views.rechazar_comentario_view, name='rechazar_comentario'),
    # URLs para pedidos
    path('pedido/crear/<int:pago_id>/', views.crear_pedido_view, name='crear_pedido'),
    path('mis-pedidos/', views.mis_pedidos_view, name='mis_pedidos'),
    path('pedido/<int:pedido_id>/', views.detalle_pedido_view, name='detalle_pedido'),
    path('pedido/<int:pedido_id>/completar-datos/', views.completar_datos_envio_view, name='completar_datos_envio'),
    path('editar-ubicacion-pedido/<int:pedido_id>/', views.editar_ubicacion_pedido_view, name='editar_ubicacion_pedido'),
    path('factura-cliente/<int:pago_id>/', views.ver_factura_cliente_view, name='ver_factura_cliente'),
    # API para obtener cantidad disponible de productos
    path('api/producto/cantidad-disponible/', views.get_cantidad_disponible_view, name='api_cantidad_disponible'),
    # API para sincronizar carrito
    path('api/carrito/sincronizar/', views.sincronizar_carrito_view, name='sincronizar_carrito'),
    path('api/carrito/limpiar/', views.limpiar_carrito_view, name='limpiar_carrito'),
    # Incluir URLs de core (APIs de chat)
    path('', include('core.urls')),
    path('',include('Productos.urls')),
    path('',include('Empresas.urls')),
    path('admin/', admin.site.urls),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.urls import path, include
from . import views
from . import views_chat

urlpatterns = [
    # APIs para sistema de chat
    path('api/test-session/', views_chat.test_session, name='test_session'),
    path('api/conversaciones/', views_chat.api_conversaciones, name='api_conversaciones'),
    path('api/mensajes-idea/<int:idea_id>/', views_chat.api_mensajes_idea, name='api_mensajes_idea'),
    path('api/enviar-mensaje/<int:idea_id>/', views_chat.api_enviar_mensaje, name='api_enviar_mensaje'),
    path('api/marcar-leidos/<int:idea_id>/', views_chat.api_marcar_leidos, name='api_marcar_leidos'),
    # URLs para ideas - interacción cliente
    path('idea/responder/<int:idea_id>/', views.responder_mensaje_empresa, name='responder_mensaje_empresa'),
    path('idea/otorgar-permiso/<int:idea_id>/', views.otorgar_permiso_publicacion, name='otorgar_permiso_publicacion'),
    path('idea/revocar-permiso/<int:idea_id>/', views.revocar_permiso_publicacion, name='revocar_permiso_publicacion'),
    # URLs para chat de pagos - interacción cliente y empresa
    path('api/mensajes-pago/<int:pago_id>/', views_chat.api_mensajes_pago, name='api_mensajes_pago'),
    path('api/enviar-mensaje-pago/<int:pago_id>/', views_chat.api_enviar_mensaje_pago, name='api_enviar_mensaje_pago'),
    path('api/conversaciones-pagos/', views_chat.api_conversaciones_pagos, name='api_conversaciones_pagos'),
    path('api/marcar-leidos-pago/<int:pago_id>/', views_chat.api_marcar_leidos_pago, name='api_marcar_leidos_pago'),
]
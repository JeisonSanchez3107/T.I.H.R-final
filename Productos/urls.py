from django.urls import path, include
from . import views

urlpatterns = [
    path('carpinteria/', views.carpinteria, name='carpinteria'),
    path('marroquineria/', views.marroquineria, name='marroquineria'),
    path('tapiceria/', views.tapiceria, name='tapiceria'),
    path('vidrieria/', views.vidrieria, name='vidrieria'),
    path('metaleria/', views.metaleria, name='metaleria'),
    path('ceramica/', views.ceramica, name='ceramica'),

]
from django.contrib import admin
from .models import EmpresaRegistrada

@admin.register(EmpresaRegistrada)
class EmpresaRegistradaAdmin(admin.ModelAdmin):
    list_display = ('nombre_empresa', 'nit', 'email', 'ciudad', 'is_active', 'is_verified', 'fecha_registro')
    list_filter = ('is_active', 'is_verified', 'ciudad', 'departamento')
    search_fields = ('nombre_empresa', 'nit', 'email', 'username')
    readonly_fields = ('fecha_registro', 'last_login')
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre_empresa', 'nit', 'razon_social')
        }),
        ('Contacto', {
            'fields': ('email', 'telefono', 'telefono_alternativo', 'direccion', 'ciudad', 'departamento', 'codigo_postal')
        }),
        ('Representante Legal', {
            'fields': ('nombre_representante', 'cedula_representante', 'email_representante')
        }),
        ('Acceso', {
            'fields': ('username', 'password')
        }),
        ('Información Adicional', {
            'fields': ('descripcion', 'logo', 'sitio_web')
        }),
        ('Estado y Control', {
            'fields': ('is_active', 'is_verified', 'fecha_registro', 'last_login')
        }),
    )

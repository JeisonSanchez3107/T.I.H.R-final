from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from django.utils import timezone

class EmpresaRegistrada(models.Model):
    """Modelo para empresas que se registran en la plataforma"""
    
    # Información básica de la empresa
    nombre_empresa = models.CharField(max_length=200, unique=True, verbose_name="Nombre de la Empresa")
    nit = models.CharField(max_length=50, unique=True, verbose_name="NIT")
    razon_social = models.CharField(max_length=200, blank=True, null=True, verbose_name="Razón Social")
    
    # Datos de contacto
    email = models.EmailField(unique=True, validators=[EmailValidator()], verbose_name="Correo Electrónico")
    telefono_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="El número debe tener el formato: '+999999999'. Hasta 15 dígitos."
    )
    telefono = models.CharField(validators=[telefono_validator], max_length=17, blank=True, null=True, verbose_name="Teléfono")
    telefono_alternativo = models.CharField(validators=[telefono_validator], max_length=17, blank=True, null=True, verbose_name="Teléfono Alternativo")
    
    # Dirección
    direccion = models.CharField(max_length=300, blank=True, null=True, verbose_name="Dirección")
    ciudad = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ciudad")
    departamento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Departamento")
    codigo_postal = models.CharField(max_length=10, blank=True, null=True, verbose_name="Código Postal")
    
    # Representante legal
    nombre_representante = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nombre del Representante Legal")
    cedula_representante = models.CharField(max_length=20, blank=True, null=True, verbose_name="Cédula del Representante")
    email_representante = models.EmailField(blank=True, null=True, validators=[EmailValidator()], verbose_name="Email del Representante")
    
    # Credenciales de acceso
    username = models.CharField(max_length=100, unique=True, verbose_name="Usuario")
    password = models.CharField(max_length=255, verbose_name="Contraseña")
    
    # Información adicional
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción de la Empresa")
    logo = models.ImageField(upload_to='uploads/empresas/logos/', blank=True, null=True, verbose_name="Logo")
    sitio_web = models.URLField(blank=True, null=True, verbose_name="Sitio Web")
    
    # Control y estado
    fecha_registro = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Registro")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_verified = models.BooleanField(default=False, verbose_name="Verificado")
    last_login = models.DateTimeField(blank=True, null=True, verbose_name="Último Acceso")
    
    # Autenticación de dos factores
    two_factor_enabled = models.BooleanField(default=False, verbose_name="2FA Habilitado")
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True, verbose_name="Clave Secreta TOTP")
    two_factor_code = models.CharField(max_length=6, blank=True, null=True)
    two_factor_code_expires = models.DateTimeField(blank=True, null=True)
    telefono_2fa = models.CharField(max_length=17, blank=True, null=True, verbose_name="Teléfono para 2FA")
    email_2fa = models.EmailField(blank=True, null=True, verbose_name="Email para 2FA")
    
    class Meta:
        verbose_name = "Empresa Registrada"
        verbose_name_plural = "Empresas Registradas"
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f"{self.nombre_empresa} - {self.nit}"

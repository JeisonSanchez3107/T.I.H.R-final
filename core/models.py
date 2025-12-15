from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator

class User(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.username

class Mesas(models.Model):
    nombre1 = models.CharField(max_length=100)
    descripcion1 = models.CharField(max_length=250, default='', blank=True,null=True)
    precio1 = models.DecimalField(max_digits=10, decimal_places=2)
    imagen1 = models.ImageField(upload_to='uploads/productos/')
    cantidad_disponible = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
class Sillas(models.Model):
    nombre2 = models.CharField(max_length=100)
    descripcion2 = models.CharField(max_length=250, default='', blank=True,null=True)
    precio2 = models.DecimalField(max_digits=10, decimal_places=2)
    imagen2 = models.ImageField(upload_to='uploads/productos/')
    cantidad_disponible = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
class Armarios(models.Model):
    nombre3 = models.CharField(max_length=100)
    descripcion3 = models.CharField(max_length=250, default='', blank=True,null=True)
    precio3 = models.DecimalField(max_digits=10, decimal_places=2)
    imagen3 = models.ImageField(upload_to='uploads/productos/')
    cantidad_disponible = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
class Cajoneras(models.Model):
    nombre4 = models.CharField(max_length=100)
    descripcion4 = models.CharField(max_length=250, default='', blank=True,null=True)
    precio4 = models.DecimalField(max_digits=10, decimal_places=2)
    imagen4 = models.ImageField(upload_to='uploads/productos/')
    cantidad_disponible = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
class Escritorios(models.Model):
    nombre5 = models.CharField(max_length=100)
    descripcion5 = models.CharField(max_length=250, default='', blank=True,null=True)
    precio5 = models.DecimalField(max_digits=10, decimal_places=2)
    imagen5 = models.ImageField(upload_to='uploads/productos/')
    cantidad_disponible = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
class Utensilios(models.Model):
    nombre6 = models.CharField(max_length=100)
    descripcion6 = models.CharField(max_length=250, default='', blank=True,null=True)
    precio6 = models.DecimalField(max_digits=10, decimal_places=2)
    imagen6 = models.ImageField(upload_to='uploads/productos/')
    cantidad_disponible = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

class UserClientes(models.Model):
    usernameCliente = models.CharField(max_length=100, unique=True)
    passwordCliente = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    last_modified = models.DateTimeField(auto_now=True)
    status_changed_at = models.DateTimeField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    foto_perfil = models.ImageField(upload_to='uploads/perfiles/', blank=True, null=True)
    
    # Campos para autenticación de dos factores (2FA)
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)
    
    # Dirección predeterminada para envíos
    nombre_completo = models.CharField(max_length=200, blank=True, null=True)
    cedula = models.CharField(max_length=20, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True, validators=[RegexValidator(r'^\d{7,15}$', 'Ingrese un número de teléfono válido (solo números, 7-15 dígitos)')])
    direccion = models.CharField(max_length=300, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    departamento = models.CharField(max_length=100, blank=True, null=True)
    codigo_postal = models.CharField(max_length=10, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if self.is_active != getattr(self, '_original_is_active', True):
            self.status_changed_at = timezone.now()
        super().save(*args, **kwargs)
        self._original_is_active = self.is_active
    
    def __str__(self):
        return self.usernameCliente
    
class UserEmpresa(models.Model):
    usernameEmpresa = models.CharField(max_length=100, unique=True)
    passwordEmpresa = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    last_modified = models.DateTimeField(auto_now=True)
    status_changed_at = models.DateTimeField(null=True, blank=True)
    
    # Campos para autenticación de dos factores (2FA) - OBLIGATORIO para empresas
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.is_active != getattr(self, '_original_is_active', True):
            self.status_changed_at = timezone.now()
        super().save(*args, **kwargs)
        self._original_is_active = self.is_active

    def __str__(self):
        return self.usernameEmpresa
    
class Idea(models.Model):
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('completada', 'Completada'),
        ('finalizada', 'Finalizada'),
        ('rechazada', 'Rechazada'),
    ]
    CATEGORIA_CHOICES = [
        ('mesas', 'Mesas'),
        ('sillas', 'Sillas'),
        ('cajoneras', 'Cajoneras'),
        ('armarios', 'Armarios'),
        ('utensilios', 'Utensilios'),
        ('escritorios', 'Escritorios'),
    ]
    
    titulo = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=250, default='', blank=True, null=True)
    autor = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='uploads/ideas/', blank=True, null=True)
    modelo_3d = models.FileField(upload_to='uploads/ideas/modelos3d/', blank=True, null=True)
    estado = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendiente')
    empresa_asignada = models.ForeignKey(UserEmpresa, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Nuevos campos para contacto y publicación
    mensaje_empresa = models.TextField(max_length=1000, blank=True, null=True, help_text='Mensaje de la empresa al cliente sobre la idea')
    respuesta_cliente = models.TextField(max_length=1000, blank=True, null=True, help_text='Respuesta del cliente a la empresa')
    permiso_publicacion = models.BooleanField(default=False, help_text='Permiso del cliente para publicar como producto')
    fecha_permiso = models.DateTimeField(null=True, blank=True)
    publicada_como_producto = models.BooleanField(default=False)
    fecha_publicacion = models.DateTimeField(null=True, blank=True)
    
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='mesas')
    medidas = models.JSONField(blank=True, null=True, help_text='Medidas personalizadas del producto')
    veces_editada = models.IntegerField(default=0, help_text='Número de veces que se ha editado la idea')
    
    def __str__(self):
        return self.titulo

class MensajeIdea(models.Model):
    """Modelo para almacenar mensajes entre empresa y cliente sobre una idea"""
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name='mensajes')
    remitente_tipo = models.CharField(max_length=10, choices=[('empresa', 'Empresa'), ('cliente', 'Cliente')])
    remitente_nombre = models.CharField(max_length=100)  # username de quien envía
    mensaje = models.TextField(max_length=1000)
    fecha_envio = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)
    
    # Campo especial para solicitud de permiso
    es_solicitud_permiso = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['fecha_envio']
    
    def __str__(self):
        return f"{self.remitente_tipo} - {self.idea.titulo} - {self.fecha_envio}"

class Comentario(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]
    
    usuario = models.ForeignKey(UserClientes, on_delete=models.CASCADE, related_name='comentarios')
    contenido = models.TextField(max_length=500)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Comentario de {self.usuario.usernameCliente} - {self.fecha_creacion.strftime('%d/%m/%Y')}"

class Pago(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('rechazado', 'Rechazado'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('nequi', 'Nequi'),
        ('bancolombia', 'Bancolombia'),
        ('davivienda', 'Davivienda'),
    ]
    
    cliente = models.ForeignKey(UserClientes, on_delete=models.CASCADE, related_name='pagos')
    nombre_completo = models.CharField(max_length=200, blank=True, default='')
    cedula = models.CharField(max_length=20, blank=True, default='')
    email = models.EmailField(max_length=100, blank=True, default='')
    telefono = models.CharField(max_length=20, blank=True, default='')
    direccion = models.CharField(max_length=300, blank=True, default='')
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    comprobante = models.ImageField(upload_to='uploads/comprobantes/')
    productos = models.TextField()  # JSON string con los productos del carrito
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)
    notas_empresa = models.TextField(max_length=500, blank=True, null=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Pago de {self.cliente.usernameCliente} - ${self.monto_total} - {self.get_estado_display()}"

class Pedido(models.Model):
    ESTADO_PEDIDO_CHOICES = [
        ('procesando', 'Procesando'),
        ('empacado', 'Empacado'),
        ('enviado', 'Enviado'),
        ('en_transito', 'En Tránsito'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    
    pago = models.OneToOneField(Pago, on_delete=models.CASCADE, related_name='pedido')
    cliente = models.ForeignKey(UserClientes, on_delete=models.CASCADE, related_name='pedidos')
    
    # Datos de envío (opcionales hasta que el cliente los complete)
    nombre_completo = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=300, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    departamento = models.CharField(max_length=100, blank=True, null=True)
    codigo_postal = models.CharField(max_length=10, blank=True, null=True)
    notas_adicionales = models.TextField(max_length=500, blank=True, null=True)
    
    # Estado y seguimiento
    estado = models.CharField(max_length=20, choices=ESTADO_PEDIDO_CHOICES, default='procesando')
    numero_seguimiento = models.CharField(max_length=100, blank=True, null=True)
    empresa_envio = models.CharField(max_length=100, blank=True, null=True)
    
    # Productos y monto
    productos = models.TextField()  # JSON string con los productos
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_entrega_estimada = models.DateField(null=True, blank=True)
    fecha_entrega_real = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.usernameCliente} - {self.get_estado_display()}"


class MensajePago(models.Model):
    """Modelo para almacenar mensajes entre empresa y cliente sobre un pago"""
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE, related_name='mensajes')
    remitente_tipo = models.CharField(max_length=10, choices=[('empresa', 'Empresa'), ('cliente', 'Cliente')])
    remitente_nombre = models.CharField(max_length=100)  # username de quien envía
    mensaje = models.TextField(max_length=1000)
    imagen = models.ImageField(upload_to='uploads/chat_pagos/', blank=True, null=True)
    fecha_envio = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['fecha_envio']
    
    def __str__(self):
        return f"{self.remitente_tipo} - Pago #{self.pago.id} - {self.fecha_envio}"


class CarritoTemporal(models.Model):
    """Modelo para rastrear productos temporalmente reservados en carritos de usuarios"""
    usuario = models.ForeignKey(UserClientes, on_delete=models.CASCADE, related_name='carrito_items')
    producto_tipo = models.CharField(max_length=20)  # 'mesa', 'silla', 'armario', etc.
    producto_id = models.IntegerField()
    cantidad = models.IntegerField(default=1)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('usuario', 'producto_tipo', 'producto_id')
        ordering = ['-fecha_actualizacion']
    
    def __str__(self):
        return f"{self.usuario.usernameCliente} - {self.producto_tipo} #{self.producto_id} ({self.cantidad})"


class Factura(models.Model):
    """Modelo para almacenar facturas generadas al confirmar pagos"""
    pago = models.OneToOneField(Pago, on_delete=models.CASCADE, related_name='factura')
    numero_factura = models.CharField(max_length=50, unique=True)
    cliente = models.ForeignKey(UserClientes, on_delete=models.CASCADE, related_name='facturas')
    
    # Datos del cliente al momento de la factura
    nombre_cliente = models.CharField(max_length=200)
    email_cliente = models.EmailField(max_length=100, blank=True)
    telefono_cliente = models.CharField(max_length=20, blank=True)
    direccion_cliente = models.CharField(max_length=300, blank=True)
    ciudad_cliente = models.CharField(max_length=100, blank=True)
    departamento_cliente = models.CharField(max_length=100, blank=True)
    
    # Productos y montos
    productos = models.TextField()  # JSON string con detalles de productos
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    impuestos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Fechas
    fecha_emision = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_emision']
    
    def __str__(self):
        return f"Factura {self.numero_factura} - {self.nombre_cliente}"

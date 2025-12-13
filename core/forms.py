from django import forms
from .models import UserClientes, Idea, Comentario, Pago
import re
import random

class LoginForm(forms.Form):
    usernameCliente = forms.CharField(max_length=100)
    passwordCliente = forms.CharField(max_length=100, widget=forms.PasswordInput)

class AgregarForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Correo electrónico')
    passwordCliente = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput,
        label='Contraseña',
        help_text='Mínimo 8 caracteres'
    )
    
    class Meta:
        model = UserClientes
        fields = ['usernameCliente', 'email', 'passwordCliente']
    
    def clean_usernameCliente(self):
        username = self.cleaned_data.get('usernameCliente')
        
        # Validar que solo contenga letras, números y guiones bajos
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise forms.ValidationError('El nombre de usuario solo puede contener letras, números y guiones bajos')
        
        # Verificar si el username ya existe
        if UserClientes.objects.filter(usernameCliente=username).exists():
            # Generar sugerencias de nombres disponibles
            sugerencias = []
            for i in range(3):
                numero = random.randint(1, 999)
                sugerencia = f"{username}{numero}"
                if not UserClientes.objects.filter(usernameCliente=sugerencia).exists():
                    sugerencias.append(sugerencia)
            
            # Agregar sugerencias con guiones bajos
            for sufijo in ['_user', '_01', '_pro']:
                sugerencia = f"{username}{sufijo}"
                if not UserClientes.objects.filter(usernameCliente=sugerencia).exists() and len(sugerencias) < 5:
                    sugerencias.append(sugerencia)
            
            mensaje = f'Nombre de usuario ya existente. Sugerencias disponibles: {", ".join(sugerencias)}'
            raise forms.ValidationError(mensaje)
        
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Validar formato de Gmail
        if not email.endswith('@gmail.com'):
            raise forms.ValidationError('Solo se permiten correos de Gmail (@gmail.com)')
        
        # Verificar si el email ya existe en la base de datos
        if UserClientes.objects.filter(email=email).exists():
            raise forms.ValidationError('Correo ya utilizado. Por favor, utiliza otro correo electrónico.')
        
        # Verificar si el email existe en Gmail usando DNS
        try:
            from dns import resolver # type: ignore
            import re
            
            # Extraer el dominio
            domain = email.split('@')[1]
            
            # Verificar registros MX del dominio
            try:
                mx_records = resolver.resolve(domain, 'MX')
                if not mx_records:
                    raise forms.ValidationError('El dominio del correo no es válido.')
            except:
                raise forms.ValidationError('No se pudo verificar el correo. Asegúrate de que sea un correo de Gmail válido.')
            
            # Validación adicional del formato del email
            email_pattern = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
            if not re.match(email_pattern, email):
                raise forms.ValidationError('Formato de correo inválido.')
                
        except ImportError:
            # Si no está disponible la librería DNS, solo hacer validación básica
            pass
        
        return email
    
    def clean_passwordCliente(self):
        password = self.cleaned_data.get('passwordCliente')
        
        if len(password) < 8:
            raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres')
        
        return password

class LoginFormEmpresa(forms.Form):
    usernameEmpresa = forms.CharField(max_length=100)
    passwordEmpresa = forms.CharField(max_length=100, widget=forms.PasswordInput)

class IdeaForm(forms.ModelForm):
    class Meta:
        model = Idea
        fields = ['titulo', 'descripcion', 'ancho', 'altura', 'imagen', 'modelo_3d']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 5}),
            'ancho': forms.NumberInput(attrs={
                'placeholder': 'Ej: 50',
                'step': '0.01',
                'min': '0.01',
                'required': True
            }),
            'altura': forms.NumberInput(attrs={
                'placeholder': 'Ej: 100',
                'step': '0.01',
                'min': '0.01',
                'required': True
            }),
        }
        labels = {
            'modelo_3d': 'Modelo 3D (.glb)',
            'ancho': 'Ancho (cm)',
            'altura': 'Altura (cm)',
        }
        help_texts = {
            'modelo_3d': 'Sube un archivo de modelo 3D en formato .glb',
            'ancho': 'Ancho en centímetros',
            'altura': 'Altura en centímetros',
        }
    
    def clean_ancho(self):
        ancho = self.cleaned_data.get('ancho')
        if ancho is None or ancho <= 0:
            raise forms.ValidationError('El ancho debe ser mayor a 0')
        return ancho
    
    def clean_altura(self):
        altura = self.cleaned_data.get('altura')
        if altura is None or altura <= 0:
            raise forms.ValidationError('La altura debe ser mayor a 0')
        return altura

class IdeaUpdateForm(forms.ModelForm):
    class Meta:
        model = Idea
        fields = ['estado']

class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['contenido']
        widgets = {
            'contenido': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Escribe tu comentario aqu�...',
                'class': 'form-control'
            }),
        }
        labels = {
            'contenido': 'Tu comentario',
        }

class PerfilUsuarioForm(forms.ModelForm):
    passwordCliente_actual = forms.CharField(
        max_length=100,
        widget=forms.PasswordInput(attrs={'placeholder': 'Contrase�a actual'}),
        required=False,
        label='Contrase�a actual'
    )
    passwordCliente_nueva = forms.CharField(
        max_length=100,
        widget=forms.PasswordInput(attrs={'placeholder': 'Nueva contrase�a'}),
        required=False,
        label='Nueva contrase�a'
    )
    passwordCliente_confirmar = forms.CharField(
        max_length=100,
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirmar contrase�a'}),
        required=False,
        label='Confirmar contrase�a'
    )
    
    class Meta:
        model = UserClientes
        fields = ['usernameCliente', 'email', 'foto_perfil', 'nombre_completo', 'cedula', 'telefono', 'direccion', 'ciudad', 'departamento']
        widgets = {
            'usernameCliente': forms.TextInput(attrs={'placeholder': 'Nombre de usuario'}),
            'email': forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com'}),
            'nombre_completo': forms.TextInput(attrs={'placeholder': 'Nombre completo'}),
            'cedula': forms.TextInput(attrs={'placeholder': 'Número de cédula'}),
            'telefono': forms.TextInput(attrs={'placeholder': 'Teléfono (Ej: 3001234567)'}),
            'direccion': forms.TextInput(attrs={'placeholder': 'Dirección completa'}),
            'ciudad': forms.TextInput(attrs={'placeholder': 'Ciudad'}),
            'departamento': forms.TextInput(attrs={'placeholder': 'Departamento'}),
        }
        labels = {
            'usernameCliente': 'Nombre de usuario',
            'email': 'Correo electrónico',
            'foto_perfil': 'Foto de perfil',
            'nombre_completo': 'Nombre completo',
            'cedula': 'Cédula',
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
            'ciudad': 'Ciudad',
            'departamento': 'Departamento',
        }
    
    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if cedula:
            # Validar que solo contenga números
            if not cedula.isdigit():
                raise forms.ValidationError('La cédula debe contener solo números')
            # Validar longitud
            if len(cedula) < 6 or len(cedula) > 20:
                raise forms.ValidationError('La cédula debe tener entre 6 y 20 dígitos')
        return cedula
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Validar que solo contenga números
            if not telefono.isdigit():
                raise forms.ValidationError('El teléfono debe contener solo números')
            # Validar longitud
            if len(telefono) < 7 or len(telefono) > 15:
                raise forms.ValidationError('El teléfono debe tener entre 7 y 15 dígitos')
        return telefono
    
    def clean(self):
        cleaned_data = super().clean()
        password_actual = cleaned_data.get('passwordCliente_actual')
        password_nueva = cleaned_data.get('passwordCliente_nueva')
        password_confirmar = cleaned_data.get('passwordCliente_confirmar')
        
        if password_nueva or password_confirmar:
            if not password_actual:
                raise forms.ValidationError('Debes ingresar tu contrase�a actual para cambiarla')
            if password_nueva != password_confirmar:
                raise forms.ValidationError('Las contrase�as nuevas no coinciden')
            if len(password_nueva) < 6:
                raise forms.ValidationError('La contrase�a debe tener al menos 6 caracteres')
        
        return cleaned_data


class PagoForm(forms.ModelForm):
    """Formulario para procesar pagos con datos del cliente"""
    nombre_completo = forms.CharField(
        max_length=200,
        required=True,
        label='Nombre completo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su nombre completo'
        })
    )
    
    cedula = forms.CharField(
        max_length=20,
        required=True,
        label='Cédula',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su número de cédula'
        })
    )
    
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com',
            'readonly': 'readonly'  # Email pre-rellenado no editable
        })
    )
    
    telefono = forms.CharField(
        max_length=20,
        required=True,
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 3001234567'
        })
    )
    
    direccion = forms.CharField(
        max_length=300,
        required=True,
        label='Dirección',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Calle 123 #45-67'
        })
    )
    
    class Meta:
        model = Pago
        fields = ['nombre_completo', 'cedula', 'email', 'telefono', 'direccion', 'metodo_pago', 'comprobante']
        widgets = {
            'metodo_pago': forms.Select(attrs={'class': 'form-control'}),
            'comprobante': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
        }
    
    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        # Validar que solo contenga números
        if not cedula.isdigit():
            raise forms.ValidationError('La cédula debe contener solo números')
        # Validar longitud
        if len(cedula) < 6 or len(cedula) > 20:
            raise forms.ValidationError('La cédula debe tener entre 6 y 20 dígitos')
        return cedula
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        # Validar que solo contenga números
        if not telefono.isdigit():
            raise forms.ValidationError('El teléfono debe contener solo números')
        # Validar longitud
        if len(telefono) < 7 or len(telefono) > 15:
            raise forms.ValidationError('El teléfono debe tener entre 7 y 15 dígitos')
        return telefono
    
    def clean_direccion(self):
        direccion = self.cleaned_data.get('direccion')
        # Validar longitud mínima
        if len(direccion) < 10:
            raise forms.ValidationError('La dirección debe tener al menos 10 caracteres')
        return direccion

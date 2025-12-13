from django import forms
from .models import EmpresaRegistrada
from django.core.exceptions import ValidationError
import hashlib

class EmpresaRegistroSimpleForm(forms.ModelForm):
    """Formulario simplificado para registro de empresas"""
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar Contraseña'
        }),
        label="",
        required=True
    )
    
    class Meta:
        model = EmpresaRegistrada
        fields = ['nombre_empresa', 'email', 'nit', 'password']
        labels = {
            'nombre_empresa': '',
            'email': '',
            'nit': '',
            'password': '',
        }
        widgets = {
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}),
            'nombre_empresa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la Empresa'}),
            'nit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NIT'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError({
                    'password_confirm': 'Las contraseñas no coinciden'
                })
        elif not password_confirm:
            raise ValidationError({
                'password_confirm': 'Debe confirmar su contraseña'
            })
        
        return cleaned_data
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if EmpresaRegistrada.objects.filter(email=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado")
        return email
    
    def clean_nit(self):
        nit = self.cleaned_data.get('nit')
        if EmpresaRegistrada.objects.filter(nit=nit).exists():
            raise ValidationError("Este NIT ya está registrado")
        return nit
    
    def save(self, commit=True):
        empresa = super().save(commit=False)
        # Generar username automáticamente a partir del NIT
        empresa.username = f"empresa_{self.cleaned_data['nit']}"
        # Hash de la contraseña
        empresa.password = hashlib.sha256(self.cleaned_data['password'].encode()).hexdigest()
        
        if commit:
            empresa.save()
        return empresa

class EmpresaRegistroForm(forms.ModelForm):
    """Formulario para registro de empresas"""
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar Contraseña'
        }),
        label="Confirmar Contraseña"
    )
    
    terminos_condiciones = forms.BooleanField(
        required=True,
        label="Acepto los términos y condiciones"
    )
    
    class Meta:
        model = EmpresaRegistrada
        fields = [
            'nombre_empresa', 'nit', 'razon_social', 'email', 'telefono', 
            'telefono_alternativo', 'direccion', 'ciudad', 'departamento', 
            'codigo_postal', 'nombre_representante', 'cedula_representante', 
            'email_representante', 'username', 'password', 'descripcion', 
            'logo', 'sitio_web'
        ]
        widgets = {
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}),
            'nombre_empresa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la Empresa'}),
            'nit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NIT'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Razón Social'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@empresa.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+57 300 123 4567'}),
            'telefono_alternativo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+57 300 123 4567 (Opcional)'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección completa'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ciudad'}),
            'departamento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Departamento'}),
            'codigo_postal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código Postal (Opcional)'}),
            'nombre_representante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo del representante'}),
            'cedula_representante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cédula'}),
            'email_representante': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@representante.com'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario para iniciar sesión'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Descripción de la empresa', 'rows': 4}),
            'sitio_web': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.empresa.com (Opcional)'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Las contraseñas no coinciden")
        
        return password_confirm
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if EmpresaRegistrada.objects.filter(username=username).exists():
            raise ValidationError("Este nombre de usuario ya está en uso")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if EmpresaRegistrada.objects.filter(email=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado")
        return email
    
    def clean_nit(self):
        nit = self.cleaned_data.get('nit')
        if EmpresaRegistrada.objects.filter(nit=nit).exists():
            raise ValidationError("Este NIT ya está registrado")
        return nit
    
    def save(self, commit=True):
        empresa = super().save(commit=False)
        # Hash de la contraseña
        empresa.password = hashlib.sha256(self.cleaned_data['password'].encode()).hexdigest()
        
        if commit:
            empresa.save()
        return empresa

import os
import re

# Patrón a buscar (footer antiguo)
old_pattern = r'<div class="social-container">\s*<a href="https://www\.instagram\.com/[^"]*" class="social-icon" aria-label="Instagram">\s*<span>📷</span>\s*</a>\s*<div class="social-username">@Gangazos Thir</div>\s*</div>\s*<div class="social-container">\s*<a href="https://www\.facebook\.com/[^"]*" class="social-icon" aria-label="Facebook">\s*<span>📘</span>\s*</a>\s*<div class="social-username">/gangazoz_thir</div>\s*</div>'

# Nuevo código a insertar
new_code = '''<a href="https://www.instagram.com/tu_idea_hecha_realidad?igsh=Y3ByM2lyZGcwNHVy" class="social-icon-img" aria-label="Instagram">
                        <img src="{% static 'core/img/instagram-icon.png' %}" alt="Instagram" class="social-logo">
                    </a>
                    <a href="https://www.facebook.com/share/1ACEVZbZHV/" class="social-icon-img" aria-label="Facebook">
                        <img src="{% static 'core/img/facebook-icon.png' %}" alt="Facebook" class="social-logo">
                    </a>'''

# Archivos a actualizar
files = [
    'core/templates/core/productos.html',
    'core/templates/core/comentarios.html',
    'core/templates/core/contact.html',
    'core/templates/core/editar_perfil.html',
    'core/templates/core/idea.html',
    'core/templates/core/mis_pedidos_nuevo.html',
    'core/templates/core/perfilUsuario.html',
    'core/templates/core/reglas.html'
]

updated_count = 0

for file_path in files:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = re.sub(old_pattern, new_code, content, flags=re.DOTALL)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'✓ Actualizado: {file_path}')
            updated_count += 1
        else:
            print(f'- Sin cambios: {file_path}')
    else:
        print(f'✗ No encontrado: {file_path}')

print(f'\nTotal archivos actualizados: {updated_count}')

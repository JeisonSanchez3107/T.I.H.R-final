import json
from django import template

register = template.Library()

@register.filter(name='tojson')
def tojson(value):
    """Convierte un valor de Python a JSON."""
    if value is None:
        return 'null'
    return json.dumps(value)

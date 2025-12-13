def obtener_respuesta(mensaje_usuario):
    # Convierte el mensaje del usuario a minúsculas y elimina espacios al inicio/final
    mensaje = mensaje_usuario.lower().strip()

    # Respuestas predefinidas
    # Puedes añadir más palabras clave y respuestas aquí
    if "asesor" in mensaje or "comunicar" in mensaje or "contacto" in mensaje or "si" == mensaje or "sí" == mensaje:
        return "Claro, para comunicarte con un asesor de carpintería, puedes llamarnos al +57 310 123 4567 o escribirnos a carpinteria@tuideahecharealidad.com. ¡Estaremos encantados de ayudarte!"
    elif "madera" in mensaje or "tipos de madera" in mensaje:
        return "Trabajamos con maderas de alta calidad como roble, cedro, pino y teca. ¿Hay alguna en particular que te interese?"
    elif "muebles" in mensaje or "diseños" in mensaje or "personalizados" in mensaje:
        return "Creamos muebles personalizados para cualquier espacio, desde cocinas y armarios hasta camas y escritorios. Cuéntanos tu idea y la haremos realidad."
    elif "presupuesto" in mensaje or "cotizacion" in mensaje or "cuanto cuesta" in mensaje:
        return "Para un presupuesto detallado, te invitamos a contactar a nuestros asesores. Necesitamos más detalles de tu proyecto para darte una cifra exacta."
    elif "ayuda" in mensaje or "opciones" in mensaje:
        return "Escribe palabras clave como 'madera', 'muebles', 'presupuesto' o 'asesor' para obtener información. ¡O hazme cualquier otra pregunta sobre carpintería!"
    elif "hola" in mensaje or "saludo" in mensaje or "que tal" in mensaje:
        return "¡Hola! Bienvenido de nuevo a la sección de carpintería de Tu Idea Hecha Realidad. ¿En qué más puedo ayudarte hoy?"
    elif "no" == mensaje:
        return "Entendido. Si cambias de opinión o tienes otra pregunta, estoy aquí para ayudarte."
    else:
        # Respuesta predeterminada si no se reconoce la palabra clave
        return "Lo siento, no entiendo esa palabra. Escribe 'ayuda' para ver opciones, o 'asesor' si deseas contactar a alguien."

# Diccionario de reemplazos comunes tras leer archivos en latin1
reemplazos = {
    'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
    'Ã±': 'ñ', 'Ã¼': 'ü', 'ï¿½': 'ó', '�': '', 'Ã': 'í',
}

def limpiar_texto(texto):
    if isinstance(texto, str):
        for mal, bien in reemplazos.items():
            texto = texto.replace(mal, bien)
    return texto
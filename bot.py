import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from telethon import TelegramClient, events

# Asegurar compatibilidad con consolas de Windows (evitar fallos con emojis o caracteres especiales)
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Credenciales de API (soporta variables de entorno o valores por defecto)
API_ID = int(os.getenv('API_ID', '31029230'))
API_HASH = os.getenv('API_HASH', '027e3d6b82fc3330defc4fcd1ee0a06a')
MI_CANAL = os.getenv('TELEGRAM_CHANNEL', '@GangasOfertasChollos')

REPO_PATH = Path(__file__).resolve().parent
DATA_PATH = REPO_PATH / 'data'
IMAGES_PATH = DATA_PATH / 'images'
DICCIONARIO_PATH = REPO_PATH / 'categorias.json'
MAX_OFERTAS = 30

client = TelegramClient('sesion_json_bot', API_ID, API_HASH)

def cargar_diccionario():
    """Carga el diccionario de palabras clave por categoría."""
    try:
        with open(DICCIONARIO_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Error al cargar diccionario: {e}")
        return {}

PALABRAS_CATEGORIAS = cargar_diccionario()

def normalizar(texto):
    """Elimina tildes y convierte a minúsculas para comparaciones insensibles a acentos."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()

def clasificar_oferta(texto):
    """Clasifica la oferta en una categoría en base a coincidencias en el diccionario."""
    texto_norm = normalizar(texto)
    puntuaciones = {}
    for categoria, palabras in PALABRAS_CATEGORIAS.items():
        total = 0
        for palabra in palabras:
            palabra_norm = normalizar(palabra)
            patron = r'(?<!\w)' + re.escape(palabra_norm) + r'(?!\w)'
            if re.search(patron, texto_norm):
                total += 1
        puntuaciones[categoria] = total

    if puntuaciones:
        mejor_categoria = max(puntuaciones, key=puntuaciones.get)
        if puntuaciones[mejor_categoria] > 0:
            return mejor_categoria
    return 'general'

def extraer_enlace_amazon(texto, mensaje=None):
    """Extrae enlaces de Amazon (amazon.es, amzn.to, amzn.eu, amazon.com) del texto o entidades."""
    # Buscar en el texto plano
    patron = r'https?://(?:www\.)?(?:amazon\.[a-z.]+|amzn\.(?:to|eu))/[^\s<>)]+'
    m = re.search(patron, texto, re.I)
    if m:
        return m.group(0).rstrip('.,')

    # Buscar en entidades de enlace embebido si existen
    if mensaje and getattr(mensaje, 'entities', None):
        for ent in mensaje.entities:
            url = getattr(ent, 'url', None)
            if url and re.search(r'(?:amazon\.[a-z.]+|amzn\.(?:to|eu))', url, re.I):
                return url.rstrip('.,')

    return ''

def extraer_precio(texto):
    """Extrae el precio de oferta en formato numérico con símbolo euro, priorizando el precio rebajado."""
    if not texto:
        return ''

    # 1. Prioridad: precio precedido de 'ahora', 'oferta', 'precio', 'por', 'baja a', 'rebajado a'
    m_prioridad = re.search(r'(?:ahora|oferta|precio|por|baja a|rebajado a)\s*[:=]?\s*(\d+[,.]\d{2})\s*€', texto, re.I)
    if m_prioridad:
        return m_prioridad.group(1).replace(',', '.') + ' €'

    # 2. Eliminar precios tachados con markdown (~~precio~~)
    texto_sin_tachados = re.sub(r'~~.*?~~', '', texto)

    # 3. Buscar todos los precios en el texto no tachado
    precios = re.findall(r'(\d+[,.]\d{2})\s*€|€\s*(\d+[,.]\d{2})|(\d+)\s*€', texto_sin_tachados)
    if precios:
        # Extraer el valor no vacío de cada match
        lista_precios = [p[0] or p[1] or p[2] for p in precios if (p[0] or p[1] or p[2])]
        if lista_precios:
            # En ofertas con "Antes X € Ahora Y €", el último es el precio de compra
            return lista_precios[-1].replace(',', '.') + ' €'

    return ''

def extraer_titulo(texto):
    """Extrae la primera línea del texto limpiando formato Markdown (*, _, `, etc.)."""
    # Eliminar asteriscos de negrita, tildes invertidas y caracteres markdown
    texto_limpio = re.sub(r'[*_~`]+', '', texto)
    lineas = [x.strip() for x in texto_limpio.splitlines() if x.strip()]
    if not lineas:
        return 'Oferta Amazon'
    titulo = lineas[0]
    # Limitar longitud razonable
    return titulo[:200]

async def descargar_imagen(mensaje):
    """Descarga la imagen/foto asociada al mensaje de Telegram y retorna la ruta relativa."""
    if not mensaje or not getattr(mensaje, 'media', None):
        return ''

    try:
        IMAGES_PATH.mkdir(parents=True, exist_ok=True)
        # Comprobar si ya existe imagen previa para este ID
        existentes = list(IMAGES_PATH.glob(f"{mensaje.id}.*"))
        if existentes:
            return f"data/images/{existentes[0].name}"

        # Descargar media usando Telethon
        base_destino = IMAGES_PATH / f"{mensaje.id}"
        ruta_descargada = await mensaje.download_media(file=str(base_destino))
        if ruta_descargada:
            nombre_archivo = Path(ruta_descargada).name
            print(f"[IMG] Imagen descargada: data/images/{nombre_archivo}")
            return f"data/images/{nombre_archivo}"
    except Exception as e:
        print(f"[!] Error al descargar imagen de mensaje {getattr(mensaje, 'id', '?')}: {e}")

    return ''

def _guardar_en_archivo(archivo, oferta):
    """Inserta una oferta en un archivo JSON controlando duplicados y límite máximo."""
    try:
        datos = json.loads(archivo.read_text(encoding='utf-8')) if archivo.exists() else []
    except Exception:
        datos = []

    # Comprobar duplicados por ID de mensaje o enlace de Amazon
    enlace = oferta.get('amazon_url')
    oferta_id = oferta.get('id')

    es_duplicada = any(
        (oferta_id and x.get('id') == oferta_id) or
        (enlace and x.get('amazon_url') == enlace)
        for x in datos
    )

    if es_duplicada:
        return False

    datos.insert(0, oferta)
    archivo.write_text(json.dumps(datos[:MAX_OFERTAS], ensure_ascii=False, indent=4), encoding='utf-8')
    return True

async def actualizar_json(categoria, mensaje):
    """Procesa y guarda la oferta en el JSON de su categoría y en el JSON general."""
    DATA_PATH.mkdir(parents=True, exist_ok=True)
    texto = mensaje.text or ''
    enlace = extraer_enlace_amazon(texto, mensaje)
    titulo = extraer_titulo(texto)
    precio = extraer_precio(texto)
    ruta_imagen = await descargar_imagen(mensaje)

    oferta = {
        'id': mensaje.id,
        'date': mensaje.date.isoformat() if mensaje.date else '',
        'title': titulo,
        'price': precio,
        'amazon_url': enlace,
        'image': ruta_imagen,
        'categoria': categoria
    }

    # Guardar en la categoría correspondiente
    archivo_cat = DATA_PATH / f'{categoria}.json'
    guardado_cat = _guardar_en_archivo(archivo_cat, oferta)
    if guardado_cat:
        print(f'[OK] Guardado en categoria: {archivo_cat}')
    else:
        print(f'[=] Oferta ya existia en {categoria}.json')

    # Si no es general, guardar también en general.json como feed global
    if categoria != 'general':
        archivo_gen = DATA_PATH / 'general.json'
        guardado_gen = _guardar_en_archivo(archivo_gen, oferta)
        if guardado_gen:
            print(f'[OK] Sincronizado en feed general: {archivo_gen}')

@client.on(events.NewMessage(chats=MI_CANAL))
async def detector_ofertas(event):
    """Manejador de nuevos mensajes en el canal de Telegram."""
    texto = event.message.text
    if not texto and not event.message.media:
        return

    categoria = clasificar_oferta(texto or '')
    print(f'[+] Nuevo mensaje ID {event.message.id} -> Categoria: {categoria}')
    await actualizar_json(categoria, event.message)

if __name__ == '__main__':
    print('========================================')
    print(' BOT OFERTAS AMAZON - CON SOPORTE IMÁGENES')
    print(f' Canal: {MI_CANAL}')
    print(f' Directorio datos: {DATA_PATH}')
    print(f' Directorio imágenes: {IMAGES_PATH}')
    print(f' Diccionario: {DICCIONARIO_PATH}')
    print('========================================')
    client.start()
    client.run_until_disconnected()

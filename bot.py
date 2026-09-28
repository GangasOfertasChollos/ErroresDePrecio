import asyncio
import html as html_lib
import json
import logging
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE LOGGING
# ─────────────────────────────────────────────
LOG_PATH = Path(__file__).resolve().parent / 'bot.log'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),               # Consola
        logging.FileHandler(LOG_PATH, encoding='utf-8')  # Archivo bot.log
    ]
)
log = logging.getLogger('bot_ofertas')

# Evitar fallos con emojis o caracteres especiales en consolas Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ─────────────────────────────────────────────
# CARGAR .env SI EXISTE
# ─────────────────────────────────────────────
_env_path = Path(__file__).resolve().parent / '.env'
if _env_path.exists():
    log.info(f"Cargando variables de entorno desde {_env_path}")
    with open(_env_path, encoding='utf-8') as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _key, _, _val = _line.partition('=')
                os.environ.setdefault(_key.strip(), _val.strip())
else:
    log.warning(f"No se encontró archivo .env en {_env_path}. Usando variables de entorno del sistema.")

from telethon import TelegramClient, events

# ─────────────────────────────────────────────
# CREDENCIALES Y CONFIGURACIÓN
# ─────────────────────────────────────────────
def _leer_int(nombre, por_defecto):
    """Lee un entero del entorno tolerando valores vacíos o inválidos."""
    bruto = str(os.getenv(nombre, '') or '').strip()
    if not bruto:
        return por_defecto
    try:
        return int(bruto)
    except ValueError:
        log.warning(f"Valor no numérico en {nombre}='{bruto}', se usa {por_defecto}")
        return por_defecto

API_ID   = _leer_int('API_ID', 0)
API_HASH = os.getenv('API_HASH', '').strip()
MI_CANAL = os.getenv('TELEGRAM_CHANNEL', '@GangasOfertasChollos').strip()

if not API_ID or not API_HASH:
    log.critical("API_ID o API_HASH no configurados. Revisa tu archivo .env")
    sys.exit(1)

REPO_PATH        = Path(__file__).resolve().parent
DATA_PATH        = REPO_PATH / 'data'
IMAGES_PATH      = DATA_PATH / 'images'
DICCIONARIO_PATH = REPO_PATH / 'categorias.json'
MAX_OFERTAS      = _leer_int('MAX_OFERTAS', 30)
BACKFILL_LIMIT   = _leer_int('BACKFILL_LIMIT', 100)
TIMEOUT_UNFURL   = _leer_int('TIMEOUT_UNFURL', 15)
USAR_UNFURL      = str(os.getenv('USAR_UNFURL', '1')).strip().lower() not in ('0', 'false', 'no')

# Cache de og:image por URL publica: evita repetir la peticion en cada arranque
# del backfill y si el mismo mensaje se procesa mas de una vez.
_CACHE_IMAGENES = {}

# Publicacion automatica en el repositorio. Sin esto el bot escribe los JSON
# pero la web no se actualiza hasta que alguien haga git push a mano.
AUTO_PUBLICAR   = str(os.getenv('AUTO_PUBLICAR', '0')).strip().lower() in ('1', 'true', 'yes', 'si')
GIT_RAMA        = os.getenv('GIT_RAMA', 'main').strip()
GIT_REMOTO      = os.getenv('GIT_REMOTO', 'origin').strip()
PUBLICAR_CADA_S = _leer_int('PUBLICAR_CADA_SEGUNDOS', 60)

# Serializa las escrituras de los JSON. Los handlers de Telethon se ejecutan de
# forma concurrente y la lectura+escritura de un archivo debe ser indivisible.
LOCK_ARCHIVOS = asyncio.Lock()
# Evita lanzar dos pushes de git a la vez.
LOCK_PUBLICAR = asyncio.Lock()
_ultima_publicacion = 0.0

log.info(f"Canal objetivo     : {MI_CANAL}")
log.info(f"Directorio de datos: {DATA_PATH}")
log.info(f"Directorio imagenes: {IMAGES_PATH}")
log.info(f"Diccionario        : {DICCIONARIO_PATH}")
log.info(f"Max. ofertas/JSON  : {MAX_OFERTAS}")
log.info(f"Backfill al inicio : {BACKFILL_LIMIT} mensajes (0 = desactivado)")
log.info(f"Unfurling imagen   : {USAR_UNFURL}" + (f" (timeout {TIMEOUT_UNFURL}s)" if USAR_UNFURL else " (desactivado)"))
log.info(f"Auto-publicacion   : {AUTO_PUBLICAR}" + (f" -> {GIT_REMOTO}/{GIT_RAMA} cada {PUBLICAR_CADA_S}s" if AUTO_PUBLICAR else " (desactivada)"))

client = TelegramClient('sesion_json_bot', API_ID, API_HASH)

# ─────────────────────────────────────────────
# DICCIONARIO DE CATEGORÍAS
# ─────────────────────────────────────────────
def cargar_diccionario():
    """Carga el diccionario de palabras clave por categoria."""
    try:
        with open(DICCIONARIO_PATH, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        log.info(f"Diccionario cargado: {len(datos)} categorias -> {list(datos.keys())}")
        return datos
    except FileNotFoundError:
        log.error(f"Archivo de diccionario no encontrado: {DICCIONARIO_PATH}")
        return {}
    except Exception as e:
        log.error(f"Error al cargar diccionario: {e}")
        return {}

PALABRAS_CATEGORIAS = cargar_diccionario()

# ─────────────────────────────────────────────
# FUNCIONES DE PROCESAMIENTO
# ─────────────────────────────────────────────
def normalizar(texto):
    """Elimina tildes y convierte a minusculas para comparaciones insensibles a acentos."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()

def precompilar_patrones(diccionario):
    """Normaliza y compila las palabras clave una sola vez al arrancar.

    Antes se recalculaba normalizar()+re.escape() en cada mensaje por cada
    palabra (~190), lo que multiplicaba el trabajo de forma innecesaria.
    """
    patrones = {}
    for categoria, palabras in diccionario.items():
        compilados = []
        for palabra in palabras:
            palabra_norm = normalizar(palabra)
            if not palabra_norm:
                continue
            compilados.append((
                palabra,
                re.compile(r'(?<!\w)' + re.escape(palabra_norm) + r'(?!\w)')
            ))
        patrones[categoria] = compilados
    log.info(f"Patrones compilados: {sum(len(v) for v in patrones.values())} palabras en {len(patrones)} categorias")
    return patrones

PATRONES_CATEGORIAS = precompilar_patrones(PALABRAS_CATEGORIAS)

def clasificar_oferta(texto):
    """Clasifica la oferta en una categoria en base a coincidencias en el diccionario.

    En caso de empate gana la categoria que aparece antes en categorias.json,
    porque max() devuelve el primer maximo al recorrer el diccionario en orden.
    """
    if not texto or not texto.strip():
        log.debug("  [CLASIF] Texto vacio -> general")
        return 'general'

    texto_norm = normalizar(texto)
    puntuaciones = {}
    mejor_categoria = None
    mejor_puntuacion = 0

    for categoria, compilados in PATRONES_CATEGORIAS.items():
        total = 0
        coincidencias = []
        for palabra, patron in compilados:
            if patron.search(texto_norm):
                total += 1
                coincidencias.append(palabra)
        puntuaciones[categoria] = total
        if total > 0:
            log.debug(f"  [CLASIF] {categoria}: {total} coincidencias -> {coincidencias}")
        # '>' estricto: conserva la primera categoria en caso de empate
        if total > mejor_puntuacion:
            mejor_puntuacion = total
            mejor_categoria = categoria

    if mejor_categoria:
        log.debug(f"  [CLASIF] Categoria asignada: {mejor_categoria} (puntuacion: {mejor_puntuacion})")
        return mejor_categoria

    log.debug("  [CLASIF] Sin coincidencias -> general")
    return 'general'

def extraer_enlace_amazon(texto, mensaje=None):
    """Extrae enlaces de Amazon (amazon.es, amzn.to, amzn.eu, amazon.com) del texto o entidades."""
    # Buscar en el texto plano
    m = RE_ENLACE_PLANO.search(texto)
    if m:
        enlace = m.group(0).rstrip('.,')
        log.debug(f"  [ENLACE] Encontrado en texto: {enlace}")
        return enlace

    # Buscar en entidades de enlace embebido si existen
    if mensaje and getattr(mensaje, 'entities', None):
        for ent in mensaje.entities:
            url = getattr(ent, 'url', None)
            if url and RE_DOMINIO_AMAZON.search(url):
                enlace = url.rstrip('.,')
                log.debug(f"  [ENLACE] Encontrado en entidades: {enlace}")
                return enlace

    log.debug("  [ENLACE] No se encontro enlace de Amazon")
    return ''

# ─────────────────────────────────────────────
# PATRONES DE EXTRACCIÓN
# ─────────────────────────────────────────────
# Importe con separador de millares opcional en las dos convenciones:
# '199' · '1.299' · '199,50' · '1.299,50' · '1,299.50'
NUMERO_PRECIO = r'(?:\d{1,3}(?:\.\d{3})+(?:,\d{2})?|\d{1,3}(?:,\d{3})+(?:\.\d{2})?|\d+(?:[.,]\d{2})?|\d+)'

# Cualquier precio del texto, con o sin decimales y con € delante o detrás
RE_PRECIO_CUALQUIERA = re.compile(
    r'(' + NUMERO_PRECIO + r')\s*\u20ac|\u20ac\s*(' + NUMERO_PRECIO + r')'
)
# Palabras clave que preceden al precio rebajado
RE_PRECIO_PRIORIDAD = re.compile(
    r'(?:ahora|oferta|precio|por|baja a|rebajado a|rebajado de|cuesta)\s*[:=]?\s*'
    r'(?:de\s*)?(?:a\s*)?\u20ac?\s*(' + NUMERO_PRECIO + r')\s*\u20ac?',
    re.I
)
RE_TACHADO = re.compile(r'~~.*?~~')

# ── Enlaces de Amazon ──
# El canal usa dos formas: el enlace directo (amazon.es/dp/ASIN?tag=...)
# y acortadores. 'amzlink.to' es el que aparece en el canal, 'amzn.to' el
# habitual de Amazon. Ambos se aceptan.
DOMINIOS_LINK = r'(?:amazon\.[a-z.]{2,6}|(?:amzn|amzlink)\.(?:to|eu|link))'
RE_ENLACE_PLANO = re.compile(
    r'https?://(?:www\.)?' + DOMINIOS_LINK + r'/[^\s<>)\]]+', re.I
)
RE_DOMINIO_AMAZON = re.compile(r'(?://|\.)' + DOMINIOS_LINK + r'(?:/|$)', re.I)
# ASIN de un enlace de producto de Amazon
RE_ASIN = re.compile(r'/(?:dp|gp/product|gp/aw/d|product)/([A-Z0-9]{10})(?:[/?]|$)', re.I)

# ── Formato del canal ──
# Los mensajes del canal tienen una estructura fija:
#   <emoji> TITULO
#   💸 Ahora: 13,99 €
#   🏷️ Antes: 25,99 €
#   📉 Descuento: -46 %
#   💰 Ahorras: 12,00 €
#   🔗
#   <enlace>
# Se aprovechan esas etiquetas, que son mucho mas fiables que buscar "el
# ultimo numero" en el texto.
RE_AHORA   = re.compile(r'(?:ahora|antes\s*rebajado|cuesta)\s*:?\s*(' + NUMERO_PRECIO + r')\s*\u20ac', re.I)
RE_ANTES   = re.compile(r'(?:antes|valia|precio\s*anterior)\s*:?\s*(' + NUMERO_PRECIO + r')\s*\u20ac', re.I)
RE_PORCENTAJE = re.compile(r'descuento\s*:?\s*-?\s*(\d{1,2})\s*%', re.I)

# Emojis y simbolos que preceden al titulo o a las etiquetas del canal
RE_EMOJI_INICIAL = re.compile(
    r'^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u2B00-\u2BFF\s\u00A0]+', re.UNICODE
)
# Una linea que, tras quitarle los emojis, no tiene letras ni digitos no es un
# titulo: asi se descartan de golpe el emoji del enlace, los hashtags y los
# emojis sueltos que preceden al texto.
RE_SOLO_EMOJI = re.compile(r'^[\W_]+$', re.UNICODE)
# Palabras que delatan una linea de estructura del canal, no el nombre del producto
# El emoji del enlace del canal (🔗) delante de texto tambien se descarta
RE_EMOJI_ENLACE = re.compile(r'^🔗', re.UNICODE)
# Palabras que delatan una linea de estructura del canal, no el nombre del producto
RE_LINEA_ETIQUETA = re.compile(
    r'^(?:ahora|antes|descuento|ahorras|precio|oferta|ver|comprar|amazon|enlace|'
    r'discount|save|price|was|now)\b', re.I
)

# --- Imagenes (unfurling) ---
# La miniatura se obtiene de la pagina publica del mensaje en t.me, que expone
# la imagen en og:image. Es la unica via que funciona: pedir la imagen a la
# ficha de amazon.es devuelve una pagina de CAPTCHA a cualquier cliente
# automatizado, y la URL de la imagen no se puede deducir del ASIN.
RE_TME_POST = re.compile(r'^https?://t\.me/(?P<canal>[A-Za-z0-9_+\-]+)/(?P<id>\d+)', re.I)
RE_OG_IMAGE = re.compile(
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', re.I
)
# La misma etiqueta puede venir con content antes que property, segun como
# el servidor serialice los atributos.
RE_OG_IMAGE_ALT = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', re.I
)
# URL de imagen terminada en extension, por si el mensaje incluye una
RE_IMAGEN_CUALQUIERA = re.compile(
    r'https?://[^\s<>)\]"]+\.(?:jpe?g|png|webp|gif)(?:\?[^\s<>)\]"]*)?', re.I
)



def _formatear_precio(bruto):
    """Normaliza '1.299,50' / '1,299.50' / '199€' a un importe con 2 decimales.

    Acepta las dos convenciones de separador (europea y anglosajona) y devuelve
    siempre '1234.50 €' para que el orden numérico sea fiable.
    """
    numero = re.sub(r'[^\d.,]', '', str(bruto))
    if not numero:
        return ''

    if ',' in numero and '.' in numero:
        # El separador que aparece mas a la derecha es el decimal
        if numero.rfind(',') > numero.rfind('.'):
            numero = numero.replace('.', '').replace(',', '.')
        else:
            numero = numero.replace(',', '')
    elif ',' in numero:
        entero, _, decimal = numero.rpartition(',')
        numero = f"{entero}.{decimal}" if len(decimal) == 2 else f"{entero}{decimal}"
    elif '.' in numero:
        entero, _, decimal = numero.rpartition('.')
        # '1.299' es separador de millares; '19.99' es decimal
        numero = f"{entero}.{decimal}" if len(decimal) == 2 else f"{entero}{decimal}"

    try:
        return f"{float(numero):.2f} \u20ac"
    except ValueError:
        return ''

def extraer_precio(texto):
    """Extrae el precio de oferta priorizando el precio rebajado."""
    if not texto:
        log.debug("  [PRECIO] Texto vacio, sin precio")
        return ''

    # 1. El formato del canal: "💸 Ahora: 13,99 €" es inequivoco
    m_ahora = RE_AHORA.search(texto)
    if m_ahora:
        precio = _formatear_precio(m_ahora.group(1))
        log.debug(f"  [PRECIO] Precio de oferta del canal: {precio}")
        return precio

    # 2. Prioridad: precio precedido de palabras clave (ej. "Por 199€")
    m_prioridad = RE_PRECIO_PRIORIDAD.search(texto)
    if m_prioridad:
        precio = _formatear_precio(m_prioridad.group(1))
        log.debug(f"  [PRECIO] Detectado con prioridad: {precio}")
        return precio

    # 3. Si solo hay un precio tachado y el actual no aparece, se descarta
    #    el tachado y se toma lo que queda
    texto_sin_tachados = RE_TACHADO.sub('', texto)

    # 4. Si el texto lo permite, buscar el precio más bajo (el chollo real)
    precios = [next(g for g in p if g) for p in RE_PRECIO_CUALQUIERA.findall(texto_sin_tachados)]
    if precios:
        try:
            mejor = min(precios, key=lambda p: float(_formatear_precio(p).split(' ')[0]))
            precio = _formatear_precio(mejor)
            log.debug(f"  [PRECIO] Detectado: {precio} (todos: {precios})")
            return precio
        except ValueError:
            pass

    log.debug("  [PRECIO] No se encontro precio")
    return ''

def extraer_descuento(texto):
    """Extrae el porcentaje de descuento del formato del canal ('-46 %')."""
    m = RE_PORCENTAJE.search(texto or '')
    if m:
        log.debug(f"  [DESCUENTO] {m.group(1)} %")
        return f"-{m.group(1)}%"
    return ''

def extraer_precio_antes(texto):
    """Extrae el precio original del formato del canal ('🏷️ Antes: 25,99 €').

    Permite pintar el precio tachado en la web y que se vea el ahorro real.
    """
    m = RE_ANTES.search(texto or '')
    if m:
        precio = _formatear_precio(m.group(1))
        log.debug(f"  [PRECIO ANTES] {precio}")
        return precio
    return ''

def extraer_titulo(texto):
    """Extrae el titulo del producto del formato del canal.

    Las primeras lineas del mensaje son estructura ('💸 Ahora: 13,99 €',
    '🏷️ Antes: ...', '🔗', enlaces, hashtags), no el nombre del producto. Se
    descartan y se devuelve la primera linea que parece un titulo de verdad.
    """
    texto_limpio = re.sub(r'[*_~`]+', '', texto or '')
    lineas = [x.strip() for x in texto_limpio.splitlines() if x.strip()]
    if not lineas:
        log.debug("  [TITULO] Sin lineas validas -> 'Oferta Amazon'")
        return 'Oferta Amazon'

    for linea in lineas:
        # El emoji del enlace del canal. Se comprueba sobre la linea original
        # porque RE_EMOJI_INICIAL se loeria antes.
        if RE_EMOJI_ENLACE.match(linea):
            continue

        # quitar el emoji inicial ('🩹 VANSKIVA - ...' -> 'VANSKIVA - ...')
        limpio = RE_EMOJI_INICIAL.sub('', linea).strip()

        # descartar etiquetas del canal, precios, enlaces y hashtags
        if RE_LINEA_ETIQUETA.match(limpio):
            continue
        if RE_PRECIO_CUALQUIERA.fullmatch(limpio) or RE_ENLACE_PLANO.fullmatch(limpio):
            continue
        if limpio.startswith('#') or limpio.startswith('http'):
            continue
        # solo emojis, simbolos o signos: no es un titulo
        if RE_SOLO_EMOJI.match(limpio):
            continue
        # demasiado corto para ser un nombre de producto
        if len(limpio) < 3:
            continue

        titulo = limpio[:200]
        log.debug(f"  [TITULO] '{titulo}'")
        return titulo

    log.debug("  [TITULO] Ninguna linea parecia un titulo")
    return 'Oferta Amazon'

async def _pedir_og_image(url_publica):
    """Descarga la pagina publica del mensaje en t.me y devuelve su og:image.

    Es 'link unfurling', lo mismo que hacen Facebook, WhatsApp o Slack al
    pegar un enlace. La pagina de t.me expone la imagen del mensaje en la
    etiqueta og:image y responde sin CAPTCHA (~0,8 s), al contrario que la
    ficha de amazon.es, que devuelve siempre una pagina de verificacion.
    """
    if url_publica in _CACHE_IMAGENES:
        return _CACHE_IMAGENES[url_publica]

    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                       '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'),
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'es-ES,es;q=0.9',
    }
    try:
        peticion = urllib.request.Request(url_publica, headers=headers)
        pagina = await asyncio.to_thread(
            urllib.request.urlopen, peticion, None, TIMEOUT_UNFURL
        )
        html = (await asyncio.to_thread(pagina.read)).decode('utf-8', 'replace')
        pagina.close()

        m = RE_OG_IMAGE.search(html) or RE_OG_IMAGE_ALT.search(html)
        if m:
            url = html_lib.unescape(m.group(1))
            _CACHE_IMAGENES[url_publica] = url
            log.debug(f"  [IMG] og:image obtenida: {url[:80]}")
            return url
        log.debug("  [IMG] La pagina no trae og:image")
    except Exception as e:
        log.warning(f"  [IMG] No se pudo obtener og:image de {url_publica}: {e}")

    _CACHE_IMAGENES[url_publica] = ''
    return ''

async def extraer_imagen(texto, mensaje=None):
    """Devuelve la URL de la miniatura de la oferta, sin descargarla a disco.

    Orden de busqueda:
      1. URL de imagen que venga escrita en el propio mensaje.
      2. Unfurling de la pagina publica del mensaje (https://t.me/canal/ID),
         que es de donde sale la miniatura que ya usas en Telegram.
    """
    # 1) URL de imagen en el texto
    m = RE_IMAGEN_CUALQUIERA.search(texto or '')
    if m:
        url = m.group(0).rstrip('.,')
        log.debug(f"  [IMG] URL de imagen en el texto: {url[:80]}")
        return url

    # 1b) URL de imagen en las entidades del mensaje
    if mensaje and getattr(mensaje, 'entities', None):
        for ent in mensaje.entities:
            url = getattr(ent, 'url', None)
            if url and RE_IMAGEN_CUALQUIERA.search(url):
                log.debug(f"  [IMG] URL de imagen en una entidad: {url[:80]}")
                return url

    # 2) Unfurling: la pagina publica del mensaje trae la miniatura en og:image
    if not USAR_UNFURL:
        log.debug("  [IMG] Unfurling desactivado (USAR_UNFURL=0)")
        return ''

    url_publica = url_publica_mensaje(mensaje)
    if url_publica:
        return await _pedir_og_image(url_publica)

    log.debug("  [IMG] Sin imagen disponible; se publicara sin ella")
    return ''

def url_publica_mensaje(mensaje):
    """Construye la URL publica https://t.me/<canal>/<id> del mensaje.

    Solo funciona si el bot esta en el canal: sin el nombre publico no se
    puede deducir la URL a partir del id.
    """
    if not mensaje:
        return ''
    chat = getattr(mensaje, 'chat', None) or getattr(mensaje, 'peer_id', None)
    canal = getattr(chat, 'username', None) if chat else None
    if not canal:
        return ''
    return f'https://t.me/{canal}/{mensaje.id}'

def _leer_json(archivo):
    """Lee un JSON de ofertas devolviendo siempre una lista."""
    try:
        if archivo.exists():
            contenido = archivo.read_text(encoding='utf-8').strip()
            datos = json.loads(contenido) if contenido else []
            if not isinstance(datos, list):
                log.error(f"  [JSON] {archivo.name} no contiene una lista, se reinicia")
                return []
            return datos
        log.warning(f"  [JSON] Archivo no existia, se creara: {archivo}")
        return []
    except json.JSONDecodeError as e:
        log.error(f"  [JSON] Error al parsear {archivo}: {e}. Se reinicia con lista vacia.")
        return []
    except Exception as e:
        log.error(f"  [JSON] Error al leer {archivo}: {e}")
        return []

def _escribir_json_atomico(archivo, datos):
    """Escribe el JSON en un temporal y lo renombra, para que una subida a medio
    hacer nunca deje un archivo corrupto que GitHub Pages sirva."""
    temporal = archivo.with_name(archivo.name + '.tmp')
    temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=4) + '\n', encoding='utf-8')
    os.replace(temporal, archivo)

def _guardar_en_archivo(archivo, oferta):
    """Inserta una oferta en un JSON controlando duplicados y limite maximo.

    OJO: el llamante debe tomar LOCK_ARCHIVOS. Ordenar por ID de Telegram
    (creciente) en lugar de insertar al principio es lo que permite que el
    backfill no machaque las ofertas mas recientes: el recorte descarta siempre
    el ID mas bajo, no el primero de la lista.
    """
    datos = _leer_json(archivo)

    enlace    = oferta.get('amazon_url')
    oferta_id = oferta.get('id')

    # Comprobar duplicados por ID de mensaje o enlace de Amazon
    es_duplicada = any(
        (oferta_id and x.get('id') == oferta_id) or
        (enlace and x.get('amazon_url') == enlace)
        for x in datos
    )

    if es_duplicada:
        log.info(f"  [JSON] Oferta duplicada (ID={oferta_id}), se omite en {archivo.name}")
        return False

    datos.append(oferta)
    datos.sort(key=lambda x: x.get('id') or 0, reverse=True)
    datos_guardados = datos[:MAX_OFERTAS]

    try:
        _escribir_json_atomico(archivo, datos_guardados)
        log.info(f"  [JSON] Guardado en {archivo.name} (total: {len(datos_guardados)} ofertas)")
        if len(datos) > len(datos_guardados):
            log.info(f"  [JSON] Recortadas {len(datos) - len(datos_guardados)} ofertas antiguas de {archivo.name}")
        return True
    except Exception as e:
        log.error(f"  [JSON] Error al escribir {archivo}: {e}")
        return False

def limpiar_imagenes_huerfanas():
    """Retirada: las imagenes ya no se guardan en disco.

    Antes el bot descargaba cada foto a data/images/ y esta funcion borraba las
    que ningun JSON referenciaba. Ahora `image` guarda la URL de la CDN de
    Amazon, asi que no hay nada que limpiar. Se mantiene la funcion vacia para
    no romper llamadas antiguas, y avisa si data/images/ sigue existiendo.
    """
    if IMAGES_PATH.exists() and any(IMAGES_PATH.iterdir()):
        log.warning(f"  [IMG] {IMAGES_PATH} ya no se usa. "
                    f"Borra sus imagenes antiguas o elimina el directorio.")
    return 0

async def actualizar_json(categoria, mensaje):
    """Procesa y guarda la oferta en el JSON de su categoria y en el JSON general."""
    DATA_PATH.mkdir(parents=True, exist_ok=True)

    # mensaje.text puede ser None en Telethon, mensaje.message es el fallback
    texto  = mensaje.text or getattr(mensaje, 'message', '') or ''
    enlace  = extraer_enlace_amazon(texto, mensaje)
    titulo  = extraer_titulo(texto)
    precio  = extraer_precio(texto)
    descuento = extraer_descuento(texto)
    precio_antes = extraer_precio_antes(texto)
    # URL de la miniatura, enlazada en vez de descargada
    url_imagen = await extraer_imagen(texto, mensaje)

    log.info(f"  [OFERTA] Titulo   : {titulo}")
    log.info(f"  [OFERTA] Precio   : {precio if precio else '(no detectado)'}")
    if precio_antes:
        log.info(f"  [OFERTA] Antes    : {precio_antes}")
    if descuento:
        log.info(f"  [OFERTA] Descuento: {descuento}")
    log.info(f"  [OFERTA] Enlace   : {enlace if enlace else '(no detectado)'}")
    log.info(f"  [OFERTA] Imagen   : {url_imagen if url_imagen else '(sin imagen)'}")
    log.info(f"  [OFERTA] Categoria: {categoria}")

    if not enlace:
        log.warning("  [OFERTA] Sin enlace Amazon -> la oferta se guarda sin URL")

    oferta = {
        'id':         mensaje.id,
        'date':       mensaje.date.isoformat() if mensaje.date else '',
        'title':      titulo,
        'price':      precio,
        'old_price':  precio_antes,
        'discount':   descuento,
        'amazon_url': enlace,
        'image':      url_imagen,
        'categoria':  categoria
    }

    # Guardar en la categoria correspondiente y en el feed global.
    # El cerrojo cubre la lectura+escritura de ambos archivos: sin el, dos
    # mensajes concurrentes perdian ofertas al pisarse.
    async with LOCK_ARCHIVOS:
        archivo_cat  = DATA_PATH / f'{categoria}.json'
        guardado_cat = _guardar_en_archivo(archivo_cat, oferta)

        archivo_gen  = DATA_PATH / 'general.json'
        guardado_gen = _guardar_en_archivo(archivo_gen, oferta)

    if not guardado_cat and not guardado_gen:
        log.warning(f"  [OFERTA] La oferta (ID={mensaje.id}) era duplicada en todos los archivos")

# ─────────────────────────────────────────────
# HANDLER DE NUEVOS MENSAJES
# ─────────────────────────────────────────────
async def procesar_mensaje(msg, origen='nuevo'):
    """Clasifica y guarda un mensaje. Compartido por el handler y el backfill."""
    texto  = msg.text or getattr(msg, 'message', '') or ''

    if not texto and not msg.media:
        log.debug(f"[MENSAJE] ID={msg.id} ignorado: sin texto ni media")
        return False

    categoria = clasificar_oferta(texto)
    log.info(f"[PROCESO] Procesando ID={msg.id} ({origen}) -> Categoria: {categoria}")
    await actualizar_json(categoria, msg)
    return True

# ─────────────────────────────────────────────
# PUBLICACIÓN AUTOMÁTICA EN GIT
# ─────────────────────────────────────────────
def _git(*args):
    """Ejecuta un comando git en la raiz del proyecto y devuelve (ok, salida)."""
    try:
        proc = subprocess.run(
            ['git', *args], cwd=REPO_PATH,
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=120
        )
    except FileNotFoundError:
        log.error("[GIT] git no esta instalado o no esta en el PATH")
        return False, 'git no encontrado'
    except subprocess.TimeoutExpired:
        log.error(f"[GIT] 'git {' '.join(args)}' tardo mas de 120s")
        return False, 'timeout'
    salida = (proc.stdout or '') + (proc.stderr or '')
    return proc.returncode == 0, salida.strip()

async def publicar_en_git(forzar=False):
    """Sube data/ al repositorio para que GitHub Pages sirva el cambio.

    El bot escribe los JSON, pero sin esto la web solo se actualiza cuando
    alguien ejecuta git add/commit/push a mano. Se agrupa la subida cada
    PUBLICAR_CADA_SEGUNDOS segundos en lugar de un commit por oferta.
    """
    global _ultima_publicacion

    if not AUTO_PUBLICAR:
        return False

    ahora = time.monotonic()
    if not forzar and (ahora - _ultima_publicacion) < PUBLICAR_CADA_S:
        return False

    # El 'await to_thread' cede el control sin bloquear el event loop: git
    # puede tardar segundos y no debe congelar la escucha de mensajes.
    async with LOCK_PUBLICAR:
        _ultima_publicacion = time.monotonic()
        log.info("[GIT] Publicando cambios de data/ ...")
        try:
            ok, salida = await asyncio.to_thread(_git, 'add', 'data/')
            if not ok:
                log.error(f"[GIT] Fallo en 'git add data/': {salida}")
                return False

            ok, salida = await asyncio.to_thread(_git, 'status', '--porcelain', '--', 'data/')
            if not salida:
                log.info("[GIT] No hay cambios que publicar")
                return False

            total = len(_leer_json(DATA_PATH / 'general.json'))
            mensaje = f"Actualizar ofertas ({total} en general.json)"
            ok, salida = await asyncio.to_thread(_git, 'commit', '-m', mensaje)
            if not ok:
                log.error(f"[GIT] Fallo en commit: {salida}")
                return False

            ok, salida = await asyncio.to_thread(_git, 'push', GIT_REMOTO, GIT_RAMA)
            if not ok:
                log.error(f"[GIT] Fallo en 'git push {GIT_REMOTO} {GIT_RAMA}': {salida}")
                return False

            log.info(f"[GIT] Publicado: {mensaje}")
            return True
        except Exception as e:
            log.exception(f"[GIT] Error inesperado publicando: {e}")
            return False

@client.on(events.NewMessage(chats=MI_CANAL))
async def detector_ofertas(event):
    """Manejador de nuevos mensajes en el canal de Telegram."""
    try:
        msg = event.message
        log.info("=" * 60)
        log.info(f"[MENSAJE] ID={msg.id} | Fecha={msg.date} | Media: {bool(msg.media)}")
        log.info(f"[MENSAJE] Texto (120 chars): {(msg.text or '')[:120].strip()!r}")
        await procesar_mensaje(msg)
        log.info(f"[PROCESO] ID={msg.id} procesado correctamente")
        await publicar_en_git()
    except Exception as e:
        log.exception(f"[ERROR] Fallo al procesar mensaje ID={getattr(event.message, 'id', '?')}: {e}")

# ─────────────────────────────────────────────
# ARRANQUE
# ─────────────────────────────────────────────
# Telefono del intento de inicio de sesion en curso. Telethon invoca
# code_callback() sin argumentos, asi que el telefono no se puede recibir ahi:
# lo aporta pedir_telefono(), que sustituye al prompt por defecto de Telethon.
_TELEFONO = None

def pedir_telefono():
    """Callback de telefono: sustituye al prompt de Telethon para dejar rastro
    en el log y poder nombrar el numero en los avisos posteriores.
    """
    global _TELEFONO
    log.warning("=" * 60)
    log.warning("[AUTENTICACIÓN] Necesito tu teléfono con prefijo internacional (p. ej. +34 6XX XXX XXX).")
    log.warning("=" * 60)
    try:
        _TELEFONO = input("Teléfono: ").strip()
    except (EOFError, KeyboardInterrupt):
        log.error("[AUTENTICACIÓN] Entrada cancelada, no se puede autorizar la sesión.")
        return ""
    return _TELEFONO

def solicitar_codigo(phone=None):
    """Callback de autenticacion: avisa por log antes de pedir el codigo por consola.

    Telethon llama a este callback con el telefono como argumento (telethon/client/auth.py
    lo tipa asiq), por lo que debe aceptar un parametro phone opcional.

    Antes el bot se quedaba esperando input() en silencio cuando la sesion
    expiraba, tanto en un servicio como en una consola.
    """
    telefono = phone or _TELEFONO or "tu teléfono"
    log.warning("=" * 60)
    log.warning(f"[AUTENTICACIÓN] Telegram pide confirmar el inicio de sesión en {telefono}.")
    log.warning("[AUTENTICACIÓN] El código llega por SMS o en la app Telegram > Dispositivos.")
    log.warning("[AUTENTICACIÓN] Si ejecutas esto como servicio, borra 'sesion_json_bot.session'")
    log.warning("[AUTENTICACIÓN] y reinicia de forma interactiva para autorizarlo.")
    log.warning("=" * 60)
    try:
        codigo = input(f"Código de confirmación para {telefono}: ").strip()
        return codigo or None
    except (EOFError, KeyboardInterrupt):
        log.error("[AUTENTICACIÓN] Entrada cancelada, no se puede autorizar la sesión.")
        return None

async def recuperar_mensajes_perdidos():
    """Recupera ofertas publicadas mientras el bot estaba apagado.

    events.NewMessage solo dispara con mensajes nuevos, asi que una parada de
    horas dejaba huecos en el JSON. Se procesan del mas antiguo al mas reciente
    para que el orden por ID en _guardar_en_archivo quede correcto.
    """
    if BACKFILL_LIMIT <= 0:
        log.info("[BACKFILL] Desactivado (BACKFILL_LIMIT=0)")
        return

    log.info(f"[BACKFILL] Recuperando hasta {BACKFILL_LIMIT} mensajes recientes...")
    try:
        mensajes = await client.get_messages(MI_CANAL, limit=BACKFILL_LIMIT)
    except Exception as e:
        log.error(f"[BACKFILL] No se pudo leer el historial: {e}")
        return

    if not mensajes:
        log.info("[BACKFILL] No hay mensajes en el canal")
        return

    procesados = 0
    for msg in reversed(mensajes):   # del mas antiguo al mas reciente
        try:
            if await procesar_mensaje(msg, origen='backfill'):
                procesados += 1
        except Exception as e:
            log.error(f"[BACKFILL] Fallo con el mensaje {getattr(msg, 'id', '?')}: {e}")

    log.info(f"[BACKFILL] {procesados}/{len(mensajes)} mensajes procesados")
    if procesados:
        await publicar_en_git(forzar=True)

async def main():
    log.info("=" * 60)
    log.info(" BOT OFERTAS AMAZON - INICIANDO")
    log.info(f" Archivo de log: {LOG_PATH}")
    log.info("=" * 60)

    try:
        conectado = await client.start(phone=pedir_telefono, code_callback=solicitar_codigo)
    except Exception as e:
        log.critical(f"[ERROR] No se pudo iniciar la sesion de Telegram: {e}")
        sys.exit(1)

    if not conectado:
        log.critical("[ERROR] Autorizacion fallida. El bot no se ejecuta.")
        sys.exit(1)

    me = await client.get_me()
    log.info(f"[SESION] Conectado como {me.first_name or '?'} (id={me.id})")

    await recuperar_mensajes_perdidos()

    log.info("[CONECTADO] Bot escuchando mensajes nuevos...")
    # run_until_disconnected devuelve True si la conexion se perdio y hay que
    # reconectar, por eso se envuelve en un bucle en lugar de llamar una vez.
    while True:
        try:
            reconectar = await client.run_until_disconnected()
        except (asyncio.CancelledError, KeyboardInterrupt):
            raise
        except Exception as e:
            log.exception(f"[ERROR] Conexion perdida: {e}. Reintentando en 10 s...")
            await asyncio.sleep(10)
            continue
        if not reconectar:
            break
        log.warning("[CONEXION] Perdida. Reconectando en 5 s...")
        await asyncio.sleep(5)

    # Ultimo intento de subir lo pendiente antes de salir.
    await publicar_en_git(forzar=True)
    log.info("[DESCONEXION] Bot detenido.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.warning("[DESCONEXION] Interrumpido por el usuario.")
    finally:
        # asyncio.run cancela las tareas pendientes al interrupting: publicar
        # aqui garantiza que las ofertas de los ultimos segundos no se pierdan.
        if AUTO_PUBLICAR and _ultima_publicacion:
            try:
                if _git('status', '--porcelain', '--', 'data/')[1]:
                    log.info("[GIT] Publicando cambios pendientes tras la interrupcion...")
                    _git('add', 'data/')
                    _git('commit', '-m', 'Actualizar ofertas (cierre del bot)')
                    _git('push', GIT_REMOTO, GIT_RAMA)
                    log.info("[GIT] Cambios pendientes publicados")
            except Exception:
                pass

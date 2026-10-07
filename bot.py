import asyncio
import html as html_lib
import json
import logging
import os
import re
import shutil
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
# Tope del feed global de la portada (general.json).
MAX_OFERTAS      = _leer_int('MAX_OFERTAS', 100)
# Tope de cada seccion de categoria. Es menor a proposito: las paginas de
# categoria son un escaparate de lo que acaba de bajar de precio, no un archivo
# historico, asi que interesa que se renueven rapido en lugar de acumular 100
# ofertas donde 30 ya se ven a la primera pagina.
MAX_OFERTAS_CATEGORIA = _leer_int('MAX_OFERTAS_CATEGORIA', 30)
BACKFILL_LIMIT   = _leer_int('BACKFILL_LIMIT', 130)
# Al arrancar, el catalogo se vacia y se vuelve a construir con los ultimos
# BACKFILL_LIMIT mensajes del canal. Asi los JSON nunca acumulan ofertas
# viejas ni edits a mano: lo publicado es siempre el estado actual del canal.
#
# BACKFILL_LIMIT tiene que ser MAYOR que MAX_OFERTAS a proposito, no por error:
# de cada BACKFILL_LIMIT mensajes solo se publica los que son publicables
# (con enlace, titulo y precio). De los 100 mensajes del canal 84 eran ofertas,
# asi que para llenar 100 huecos hay que leer mas de 100. El recorte de
# _guardar_en_archivo se queda con las MAX_OFERTAS mas recientes, que es
# exactamente lo que se quiere.
#
# La comparacion es contra MAX_OFERTAS y no contra MAX_OFERTAS_CATEGORIA porque
# el feed global es el que mas oferta necesita: es el unico que hay que leer
# bastante historial para llenar. Las secciones se llenan antes y les sobra.
#
# El error seria el contrario: leer menos de lo que se guarda, porque entonces
# nunca se llenan los huecos. Eso si se avisa y se corrige.
if BACKFILL_LIMIT < MAX_OFERTAS:
    log.warning(f"BACKFILL_LIMIT={BACKFILL_LIMIT} es menor que MAX_OFERTAS={MAX_OFERTAS}: "
                f"no hay mensajes suficientes para llenar el catalogo. "
                f"Se sube BACKFILL_LIMIT a {MAX_OFERTAS}.")
    BACKFILL_LIMIT = MAX_OFERTAS
REINICIAR_CATALOGO = str(os.getenv('REINICIAR_CATALOGO', '1')).strip().lower() not in ('0', 'false', 'no')
TIMEOUT_UNFURL   = _leer_int('TIMEOUT_UNFURL', 15)
USAR_UNFURL      = str(os.getenv('USAR_UNFURL', '1')).strip().lower() not in ('0', 'false', 'no')

# Cache de og:image por URL publica: evita repetir la peticion en cada arranque
# del backfill y si el mismo mensaje se procesa mas de una vez.
_CACHE_IMAGENES = {}

# Motivo -> numero de ofertas descartadas. Lo rellena actualizar_json y lo
# vacia el backfill en cada arranque, para poder cerrar con un resumen de por
# que se quedaron fuera los mensajes que no son publicables.
_DESCARTES = {}

# Publicacion automatica en el repositorio. Sin esto el bot escribe los JSON
# pero la web no se actualiza hasta que alguien haga git push a mano.
AUTO_PUBLICAR   = str(os.getenv('AUTO_PUBLICAR', '0')).strip().lower() in ('1', 'true', 'yes', 'si')
GIT_RAMA        = os.getenv('GIT_RAMA', 'main').strip()
GIT_REMOTO      = os.getenv('GIT_REMOTO', 'origin').strip()
PUBLICAR_CADA_S = _leer_int('PUBLICAR_CADA_SEGUNDOS', 60)

# Regenerar el HTML a partir de los JSON antes de subirlo. Las paginas de
# catalogo se sirven con las ofertas ya escritas dentro (ver
# generar_categorias.py): si no se regeneran, el JSON avanza y el HTML se
# queda en la tanda anterior, con lo que un crawler no ve las ofertas nuevas.
# El orden importa: primero el HTML (que lee data/), despues el sitemap (que
# comprueba que las paginas existan).
#
# Si un generador falla NO se aborta la publicacion: es preferible subir los
# JSON con el HTML viejo a no subir nada. El error queda en el log.
REGENERAR_HTML   = str(os.getenv('REGENERAR_HTML', '1')).strip().lower() in ('1', 'true', 'yes', 'si')
GENERADORES      = ('generar_categorias.py', 'generar_guias.py', 'generar_sitemap.py')

# Paginas que escriben los generadores, todas en la raiz del repo. Se listan
# una a una en vez de usar 'git add *.html' porque un pathspec con comodin
# tambien alcanzaria BlackFriday/ y PrimeDays/, que no deben entrar en el
# commit del bot ni por error ni por una diferencia de contenido alli.
def _paginas_generadas():
    from contenido_categoria import CONTENIDO
    from guias import GUIAS
    return [f"{slug}.html" for slug in CONTENIDO] + \
           ["guias.html"] + [f"{g[0]}.html" for g in GUIAS] + ["sitemap.xml"]

# Segundos que el bot aguanta antes de cerrar solo, para poder usarlo como
# tarea programada (launchd/cron/Task Scheduler) en vez de como servicio
# eterno. 0 = no se para solo.
DURACION_S      = _leer_int('DURACION_SEGUNDOS', 0)

# Motivos de descarte acumulados en este arranque, para que el resumen del
# backfill diga por que se quedaron fuera mensajes y no solo cuantos. La
# reinicia _vaciar_catalogo, que es quien empieza cada reconstruccion.
_DESCARTES = {}

# Serializa las escrituras de los JSON. Los handlers de Telethon se ejecutan de
# forma concurrente y la lectura+escritura de un archivo debe ser indivisible.
LOCK_ARCHIVOS = asyncio.Lock()
# Evita lanzar dos pushes de git a la vez.
LOCK_PUBLICAR = asyncio.Lock()
_ultima_publicacion = 0.0

# Se levanta cuando hay que cerrar el bot (senal del sistema, DURACION_S
# agotada o fallo de la sesion). main() lo consulta para salir del bucle de
# escucha y hacer el push final, de modo que parar nunca exige un hardkill.
_evento_parada = None

log.info(f"Canal objetivo     : {MI_CANAL}")
log.info(f"Directorio de datos: {DATA_PATH}")
log.info(f"Diccionario        : {DICCIONARIO_PATH}")
log.info(f"Max. ofertas general: {MAX_OFERTAS}")
log.info(f"Max. ofertas/seccion: {MAX_OFERTAS_CATEGORIA}")
log.info(f"Backfill al inicio : {BACKFILL_LIMIT} mensajes (0 = desactivado)")
log.info(f"Reinicio catalogo  : {REINICIAR_CATALOGO}" + ("" if REINICIAR_CATALOGO else " (se conserva lo que haya)"))
log.info(f"Unfurling imagen   : {USAR_UNFURL}" + (f" (timeout {TIMEOUT_UNFURL}s)" if USAR_UNFURL else " (desactivado)"))
log.info(f"Auto-publicacion   : {AUTO_PUBLICAR}" + (f" -> {GIT_REMOTO}/{GIT_RAMA} cada {PUBLICAR_CADA_S}s" if AUTO_PUBLICAR else " (desactivada)"))
log.info(f"Duracion           : " + (f"{DURACION_S}s, para solo" if DURACION_S else "indefinida (hasta Ctrl+C o SIGTERM)"))

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
# El emoji del enlace del canal (🔗) delante de texto tambien se descarta
RE_EMOJI_ENLACE = re.compile(r'^🔗', re.UNICODE)
# Palabras que delatan una linea de estructura del canal, no el nombre del producto.
# La palabra solo delata una etiqueta si va seguida de un separador de campo
# ('Ahora:' / 'Precio ='), de un precio ('Ahora 10,00 €', 'Save 20%') o si la
# linea se acaba ahi ('Oferta'). Antes bastaba con '^precio', y eso tiraba el
# titulo entero de productos reales que empiezan por una de esas palabras:
# "Amazon Echo Dot 4", "Precio unico pack 3", "Ahora mismo tu movil"... Al
# perder el titulo, extraer_titulo devolvia el marcador 'Oferta Amazon' y
# _motivo_descarte descartaba la oferta entera, en silencio. Con 100 mensajes en
# el backfill eso son ofertas que nunca se publican.
RE_LINEA_ETIQUETA = re.compile(
    r'^(?:ahora|antes|descuento|ahorras|precio|oferta|ver|comprar|amazon|enlace|'
    r'discount|save|price|was|now)\b'
    r'(?:'
      r'\s*[:=]'                                     # 'Precio:' / 'Ahora: lo que sea'
    r'|'
      r'\s*[-–—]?\s*[-+]?\d[\d.,]*\s*(?:%|€|eur)'    # 'Ahora 10,00 €' / 'Ahora - 10,00 €'
    r'|'
      r'\s*$'                                         # 'Oferta' a secas
    r')',
    re.I
)
# Palabras que, cuando sueles un precio, no aportan texto al producto. Sirven
# para detectar las lineas que solo son precios, como '16,91 € (antes 29,99 €)'.
RE_PALABRA_PRECIO = re.compile(
    r'\b(?:ahora|antes|antes\s*rebajado|precio|precio\s*anterior|descuento|ahorras|'
    r'valia|valor|vp|pvp)\b', re.I
)
# Etiquetas del canal que se cuelan en el texto ('|#Chollos|', '#Amazon').
RE_HASHTAG = re.compile(r'\|?\s*#\w+\s*\|?', re.UNICODE)
# Llamada a la accion ripiada de otro canal: '👉 Míralo en Ofertitas.es'. Se
# quita la cola cuando viene con emoji delante o cuando acaba en un dominio;
# un 'ver' suelto al final de una frase de producto no se toca.
_CTA_VERBO = (r'(?:m[íi]ra\w*|m[áa]s\s+informaci[óo]n|descubre\w*|aprovecha\w*|'
              r'pincha\w*|click|entra\w*|visita\w*)')
RE_CTA_ENLACE = re.compile(
    r'(?:'
      r'[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u2B00-\u2BFF\u200d\u20e3]+\s*'
      + _CTA_VERBO + r'\b[^|>]*'
    r'|'
      + _CTA_VERBO + r'\b[^|>]*?\.\s*(?:es|com|net|eu)\b'
    r')\s*[|·]?\s*$',
    re.I | re.UNICODE
)

# Enlaces en markdown: '[📉 Miss Avisos te dice cuando baja de
# precio](https://t.me/MissAvisosbot?start=vigilaramazon...)'. Es la forma que
# tiene el canal de meter la CTA de otro bot con su deep-link de afiliado, y se
# publicaba tal cual en description de schema.org.
RE_MARKDOWN_ENLACE = re.compile(r'\[[^\]]*\]\([^)]*\)', re.UNICODE)
# Etiquetas internas que el canal usa para marcarse a si mismo. No describen el
# producto: son la maquetacion del mensaje, que se colaba en la descripcion.
RE_ETIQUETA_INTERNA = re.compile(
    r'\b(?:PRECIO\s+OFERTA|PRECIO\s+ACTUAL|PRECIO\s+ANTERIOR)\b', re.I
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

def _es_linea_solo_precios(linea):
    """True si la linea no tiene texto propio: solo precios y palabras de precio.

    El canal publica a veces el precio en una linea combinada ('16,91 €
    (antes 29,99 €)') en vez de en las lineas etiquetadas de siempre. Esa linea
    no es descripcion del producto, y ademas el precio ya esta en sus propios
    campos, asi que como descripcion solo duplicaba (o contradecía) el precio.
    """
    resto = RE_PRECIO_CUALQUIERA.sub(' ', linea)
    # Sin el precio solo quedan parentesos, signos y palabras como 'antes'.
    resto = re.sub(r'[^\w\s]', ' ', resto, flags=re.UNICODE)
    resto = RE_PALABRA_PRECIO.sub(' ', resto)
    return not re.search(r'\w', resto, re.UNICODE)

def extraer_descripcion(texto):
    """Extrae una descripcion del producto del mensaje del canal.

    Las lineas que no son el titulo, precios, enlaces ni hashtags pueden
    contener informacion util del producto. Se devuelven como descripcion.
    """
    texto_limpio = re.sub(r'[*_~`]+', '', texto or '')
    lineas = [x.strip() for x in texto_limpio.splitlines() if x.strip()]
    if not lineas:
        return ''

    descripcion_lineas = []
    for linea in lineas:
        if RE_EMOJI_ENLACE.match(linea):
            continue
        limpio = RE_EMOJI_INICIAL.sub('', linea).strip()
        if RE_LINEA_ETIQUETA.match(limpio):
            continue
        if RE_PRECIO_CUALQUIERA.fullmatch(limpio) or RE_ENLACE_PLANO.fullmatch(limpio):
            continue
        if limpio.startswith('#') or limpio.startswith('http'):
            continue
        if RE_SOLO_EMOJI.match(limpio):
            continue
        if len(limpio) < 3:
            continue
        # Si es el titulo, no lo incluir en la descripcion
        if limpio == extraer_titulo(texto):
            continue
        # Las etiquetas del canal se van antes de mirar si la linea es solo
        # precios: si no, '|#Chollos|' haria que una linea de precios pareciese
        # texto de producto.
        limpio = RE_HASHTAG.sub(' ', limpio)
        if _es_linea_solo_precios(limpio):
            continue
        limpio = _limpiar_resto_descripcion(limpio)
        if len(limpio) < 3:
            continue
        descripcion_lineas.append(limpio)

    descripcion = ' '.join(descripcion_lineas)[:500]
    if descripcion:
        log.debug(f"  [DESCRIPCION] '{descripcion[:80]}...'")
    return descripcion

def _limpiar_resto_descripcion(texto):
    """Quita de una linea lo que no describe el producto.

    Van fuera las etiquetas del canal ('|#Chollos|', '#Amazon'), las etiquetas
    internas que el canal usa para marcarse a si mismo ('PRECIO OFERTA'), los
    enlaces en markdown y el emoji de llamada a la accion con el dominio al que
    enlaza ('👉 Míralo en Ofertitas.es'): son ripeo de otros canales o ruido del
    propio canal, se publican como description de schema.org y no dicen nada
    del producto.

    El enlace en markdown se borra entero, con su texto y su URL: en una
    descripcion de producto casi siempre es la CTA de otro canal con su
    deep-link de afiliado ('[📉 Miss Avisos te dice cuando baja de
    precio](https://t.me/MissAvisosbot?start=vigilaramazon...)'), y quedarse
    con el texto sin el enlace dejaria el anuncio igual en la web.
    """
    texto = RE_HASHTAG.sub(' ', texto)
    texto = RE_MARKDOWN_ENLACE.sub(' ', texto)
    texto = RE_ETIQUETA_INTERNA.sub(' ', texto)
    texto = RE_CTA_ENLACE.sub('', texto)
    return re.sub(r'\s+', ' ', texto).strip(' |·-–—,;:')

def _es_titulo_marcador(titulo):
    """True si el titulo es el marcador de posicion 'Oferta Amazon'.

    El canal lo escribe en mayusculas ('OFERTA AMAZON') y en minusculas
    ('Oferta Amazon'), asi que la comparacion no puede ser exacta: con ella, las
    22 ofertas cuyo unico texto era ese marcador se publicaban con el titulo y
    la marca 'OFERTA AMAZON' en lugar de descartarse.
    """
    return (titulo or '').strip().upper() == 'OFERTA AMAZON'

def extraer_marca(titulo):
    """Extrae la marca del producto del titulo.

    La marca suele ser la primera o dos palabras del titulo, antes de un
    guion, dos puntos o el nombre del producto.
    """
    if not titulo or _es_titulo_marcador(titulo):
        return ''

    # Buscar marca antes de un guion o dos puntos
    m = re.match(r'^([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ0-9\s]{1,20}?)\s*[-:]\s*', titulo)
    if m:
        marca = _marca_util(m.group(1))
        if marca:
            log.debug(f"  [MARCA] '{marca}'")
            return marca

    # Si no hay guion, probar con las dos primeras palabras
    palabras = titulo.split()
    if len(palabras) >= 2:
        # 'Marks & Spencer' es una sola marca: si la segunda palabra es un
        # conector hay que coger la tercera, o la marca queda partida.
        conector = len(palabras) >= 3 and palabras[1].lower() in ('&', '+', 'and', 'y')
        marca = _marca_util(' '.join(palabras[:3 if conector else 2]))
        if marca:
            log.debug(f"  [MARCA] '{marca}'")
            return marca

    return ''

def _marca_util(texto):
    """Limpia un candidato a marca y lo descarta si no sirve como marca.

    El titulo trae emojis y ZWJ pegados al nombre ('⌨️ GXTrust', '‍♀️ ghd'),
    y las dos primeras palabras de un titulo sin guion suelen ser un sustantivo
    comun ('Alfombrilla de', 'Zapatillas', 'Neceser'). Publicar eso como
    itemprop="brand" es peor que no publicar marca, asi que se devuelve cadena
    vacia y el frontend se la salta.
    """
    # Emoji, selectores de variation y ZWJ: no son parte del nombre de la marca.
    marca = re.sub(
        r'[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u2B00-\u2BFF\u200d\u20e3]+', '', texto
    )
    marca = re.sub(r'[^\w\sÀ-ÿ&+.-]', ' ', marca, flags=re.UNICODE)
    marca = re.sub(r'\s+', ' ', marca).strip(' -–—.,')
    # Sin al menos dos letras no hay marca (quedan '&', '+', '-'...).
    if len(marca) < 2 or not re.search(r'[A-Za-zÀ-ÿ]{2}', marca, re.UNICODE):
        return ''
    # Una marca no termina en una preposicion suelta ('Alfombrilla de') ni en un
    # conector: eso significa que el nombre esta partido ('Marks &').
    if re.search(r'\b(?:de|del|la|el|los|las|para|con|sin|en|por|of|and|y)$', marca, re.I):
        return ''
    if re.search(r'[&+]$', marca):
        return ''
    return marca

def _gtin_valido(codigo):
    """Comprueba el digito de control de un GTIN (EAN-8, UPC-A o EAN-13).

    Un GTIN alterna pesos 3 y 1 de derecha a izquierda sobre todos los
    digitos menos el de control, y el de control es lo que falta para que la
    suma sea multiple de 10. Sin esta comprobacion, cualquier numero largo
    del mensaje (un telefono, un ISBN) se publicaba como codigo de barras.
    """
    if not codigo.isdigit() or len(codigo) not in (8, 12, 13):
        return False
    total = 0
    # El ultimo digito es el de control: no entra en la suma.
    for i, digito in enumerate(reversed(codigo[:-1])):
        total += int(digito) * (3 if i % 2 == 0 else 1)
    return (10 - total % 10) % 10 == int(codigo[-1])

def extraer_gtin(texto):
    """Busca un GTIN (EAN-13, UPC-A, EAN-8) en el mensaje.

    Los GTIN son solo digitos y se validan por digito de control, asi que un
    numero suelto (un telefono, un ISBN mal puesto) no se cuela.

    Aqui NO se buscan MPN: un codigo de pieza ('HC5880', 'RLC-810A') o un
    hashtag ('#BlackFriday26') no es un GTIN, y publicarlos como
    itemprop="gtin" es informacion falsa en los resultados de Google. Los MPN
    van en su propio campo, ver extraer_mpn.
    """
    if not texto:
        return ''

    # Los hashtags se quitan antes de buscar: '#BlackFriday26' no es un GTIN,
    # pero un hashtag solo de digitos ('#12345678') podria(validandose) colarse.
    texto = RE_HASHTAG.sub(' ', texto)

    # La comilla Lookbehind y la Lookahead evitan arrancar el codigo en mitad de
    # otro numero o de un precio con separador de millares.
    for m in re.finditer(r'(?<![\d.,])(\d{8}|\d{12,13})(?![\d.,])', texto):
        if _gtin_valido(m.group(1)):
            log.debug(f"  [GTIN] GTIN: {m.group(1)}")
            return m.group(1)

    return ''

def extraer_mpn(texto):
    """Busca un MPN (codigo de pieza del fabricante) en el mensaje.

    Un MPN lleva letras y digitos ('M210', 'i7-1355U', 'RLC-810A'). Se exige al
    menos un digito: un codigo de pieza los trae siempre, mientras que una
    palabra suelta no. Sin esa exigencia el regex devolvia la marca o un
    sustantivo del titulo ('Scottex', 'OFERTA', 'Zapatillas').

    El ASIN de los enlaces tampoco sirve, y el MPN se busca fuera de los
    enlaces: el tag de afiliado del propio bot ('?tag=gangas054-21') tiene guion
    y digitos, asi que si se buscara en el texto entero apareceria como codigo de
    pieza en casi todas las ofertas. Los hashtags tampoco sirven ('Blackfriday26').
    """
    if not texto:
        return ''

    texto_plano = RE_HASHTAG.sub(' ', RE_ENLACE_PLANO.sub(' ', texto))
    asins = {a.upper() for a in RE_ASIN.findall(texto or '')}
    for token in re.findall(r'[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*', texto_plano):
        if not 6 <= len(token) <= 20 or token.isdigit():
            continue
        if not any(c.isdigit() for c in token) or token.upper() in asins:
            continue
        log.debug(f"  [MPN] {token}")
        return token

    return ''

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
    """Devuelve la URL de la miniatura de la oferta, o '' si no hay ninguna.

    Orden de busqueda:
      1. URL de imagen que venga escrita en el propio mensaje
      2. URL de imagen en las entidades del mensaje
      3. Unfurling de la pagina publica del mensaje (https://t.me/canal/ID)

    No se descarga nada a disco: `image` guarda la URL, como dice el README.
    Antes este paso 1 bajaba la foto del mensaje a data/images/, lo que dejaba
    35 MB de binarios en el repositorio y rutas locales que el navegador no
    puede resolver desde GitHub Pages.
    """
    # 1) URL de imagen en el texto
    m = RE_IMAGEN_CUALQUIERA.search(texto or '')
    if m:
        url = m.group(0).rstrip('.,')
        log.debug(f"  [IMG] URL de imagen en el texto: {url[:80]}")
        return url

    # 2) URL de imagen en las entidades del mensaje
    if mensaje and getattr(mensaje, 'entities', None):
        for ent in mensaje.entities:
            url = getattr(ent, 'url', None)
            if url and RE_IMAGEN_CUALQUIERA.search(url):
                log.debug(f"  [IMG] URL de imagen en una entidad: {url[:80]}")
                return url

    # 3) Unfurling: la pagina publica del mensaje trae la miniatura en og:image
    if not USAR_UNFURL:
        log.debug("  [IMG] Unfurling desactivado (USAR_UNFURL=0)")
        return ''

    url_publica = url_publica_mensaje(mensaje)
    if url_publica:
        url = await _pedir_og_image(url_publica)
        if url:
            log.debug(f"  [IMG] Unfurling OK: {url[:80]}")
            return url

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

def _limite_de_archivo(archivo):
    """Devuelve cuantas ofertas caben en un JSON concreto.

    general.json es el feed global de la portada y admite MAX_OFERTAS; el resto
    de JSON son secciones de categoria y admiten MAX_OFERTAS_CATEGORIA. La
    decision se toma por nombre de fichero, y no pasando un parametro, para que
    ningun llamante pueda guardar en general.json con el tope de categoria o al
    reves: el feed global se llenaria con 30 ofertas sin que nadie lo pidiera.
    """
    return MAX_OFERTAS if archivo.name == 'general.json' else MAX_OFERTAS_CATEGORIA

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

    limite = _limite_de_archivo(archivo)
    datos.append(oferta)
    datos.sort(key=lambda x: x.get('id') or 0, reverse=True)
    datos_guardados = datos[:limite]

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
    """Borra data/images/ entero y devuelve cuantos ficheros ha eliminado.

    Las ofertas no guardan imagenes en disco: `image` guarda la URL de la
    miniatura (ver extraer_imagen, que ya no descarga nada). El directorio se
    borra en cada reinicio del catalogo porque si algo lo vuelve a recrear, lo
    unico que puede haber dentro son ficheros que el navegador no puede resolver
    desde GitHub Pages: 35 MB de basura en el repositorio.
    """
    if not IMAGES_PATH.exists():
        return 0
    try:
        borrados = sum(1 for p in IMAGES_PATH.rglob('*') if p.is_file())
        shutil.rmtree(IMAGES_PATH)
        log.info(f"[IMG] {IMAGES_PATH.name}/ borrado ({borrados} ficheros)")
        return borrados
    except Exception as e:
        log.error(f"[IMG] No se pudo borrar {IMAGES_PATH}: {e}")
        return 0

def _motivo_descarte(oferta):
    """Devuelve por que no se puede publicar la oferta, o None si se puede.

    El canal no es solo un volcado de enlaces: hay mensajes sueltos, avisos y
    junk. Una oferta sin enlace no lleva a ninguna parte (el boton de la tarjeta
    es 'Ver oferta en Amazon'), una sin titulo no se puede buscar y una sin
    precio no sirve en un sitio de errores de precio. Publicar esas tarjetas
    vacias es peor que no publicarlas, asi que se descartan antes de escribir.

    Se exige ademas que el titulo no sea el marcador de posicion 'Oferta Amazon',
    que es lo que devuelve extraer_titulo cuando el mensaje no trae ninguno. La
    comparacion es case-insensitive (ver _es_titulo_marcador) porque el canal lo
    escribe en mayusculas y las ofertas asi se colaban en la web.
    """
    if not oferta.get('amazon_url'):
        return 'sin enlace de Amazon'
    titulo = (oferta.get('title') or '').strip()
    if not titulo or _es_titulo_marcador(titulo):
        return 'sin titulo'
    if not oferta.get('price'):
        return 'sin precio'
    if len(titulo) < 3:
        return 'titulo demasiado corto'
    return None

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
    # Campos adicionales para schema.org
    descripcion = extraer_descripcion(texto)
    marca = extraer_marca(titulo)
    gtin = extraer_gtin(texto)
    mpn = extraer_mpn(texto)

    log.info(f"  [OFERTA] Titulo   : {titulo}")
    log.info(f"  [OFERTA] Precio   : {precio if precio else '(no detectado)'}")
    if precio_antes:
        log.info(f"  [OFERTA] Antes    : {precio_antes}")
    if descuento:
        log.info(f"  [OFERTA] Descuento: {descuento}")
    log.info(f"  [OFERTA] Enlace   : {enlace if enlace else '(no detectado)'}")
    log.info(f"  [OFERTA] Imagen   : {url_imagen if url_imagen else '(sin imagen)'}")
    log.info(f"  [OFERTA] Categoria: {categoria}")
    if descripcion:
        log.info(f"  [OFERTA] Desc     : {descripcion[:60]}...")
    if marca:
        log.info(f"  [OFERTA] Marca    : {marca}")
    if gtin:
        log.info(f"  [OFERTA] GTIN     : {gtin}")
    if mpn:
        log.info(f"  [OFERTA] MPN      : {mpn}")

    oferta = {
        'id':         mensaje.id,
        'date':       mensaje.date.isoformat() if mensaje.date else '',
        'title':      titulo,
        'price':      precio,
        'old_price':  precio_antes,
        'discount':   descuento,
        'amazon_url': enlace,
        'image':      url_imagen,
        'categoria':  categoria,
        'description': descripcion,
        'brand':       marca,
        'gtin':        gtin,
        'mpn':         mpn
    }

    # Descartar lo que no se puede publicar antes de escribir en los JSON.
    motivo = _motivo_descarte(oferta)
    if motivo:
        # Se apunta el motivo para que el resumen del backfill pueda decir
        # por que se quedaron fuera mensajes, y no solo cuantos.
        _DESCARTES[motivo] = _DESCARTES.get(motivo, 0) + 1
        log.warning(f"  [OFERTA] Descartada (ID={mensaje.id}, {motivo}): "
                    f"{(titulo or '')[:70]!r}")
        return False

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
        return False

    return True

# ─────────────────────────────────────────────
# HANDLER DE NUEVOS MENSAJES
# ─────────────────────────────────────────────
async def procesar_mensaje(msg, origen='nuevo'):
    """Clasifica y guarda un mensaje. Compartido por el handler y el backfill.

    Devuelve True solo si la oferta ha llegado a los JSON: lo que se descarta
    por no ser publicable cuenta como no procesado, que es lo que espera el
    recuento del backfill.
    """
    texto  = msg.text or getattr(msg, 'message', '') or ''

    if not texto and not msg.media:
        log.debug(f"[MENSAJE] ID={msg.id} ignorado: sin texto ni media")
        return False

    categoria = clasificar_oferta(texto)
    log.info(f"[PROCESO] Procesando ID={msg.id} ({origen}) -> Categoria: {categoria}")
    return await actualizar_json(categoria, msg)

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


def _regenerar_html():
    """Ejecuta los generadores de paginas.

    Se llama con el mismo lock que el push, justo antes de git add: escribir
    el HTML y subirlo tienen que ser la misma operacion, o el repositorio
    queda con los JSON de una tanda y el HTML de otra.

    Devuelve la lista de generadores que fallaron (vacia si todo fue bien).
    """
    fallos = []
    for script in GENERADORES:
        destino = REPO_PATH / script
        if not destino.exists():
            # No es un error: un despliegue parcial puede no traerse todos.
            log.warning(f"[HTML] {script} no existe, se omite")
            continue
        try:
            proc = subprocess.run(
                [sys.executable, str(destino)], cwd=REPO_PATH,
                capture_output=True, text=True, encoding='utf-8',
                errors='replace', timeout=120
            )
        except Exception as e:
            log.error(f"[HTML] Fallo al ejecutar {script}: {e}")
            fallos.append(script)
            continue

        if proc.returncode != 0:
            # Se registra la salida porque los generadores informative de por
            # si, y sin esto un fallo de sintaxis seria invisible.
            log.error(f"[HTML] {script} fallo: {(proc.stderr or proc.stdout or '').strip()}")
            fallos.append(script)
            continue

        # Los generadores imprimen un resumen por pagina; en el log interesa.
        resumen = (proc.stdout or '').strip().replace("\n", " | ")
        log.info(f"[HTML] {script}: {resumen or 'ok'}")
    return fallos

async def publicar_en_git(forzar=False):
    """Sube data/ y el HTML regenerado al repositorio para que GitHub Pages
    sirva el cambio.

    El bot escribe los JSON, pero sin esto la web solo se actualiza cuando
    alguien ejecuta git add/commit/push a mano. Se agrupa la subida cada
    PUBLICAR_CADA_SEGUNDOS segundos en lugar de un commit por oferta.

    El HTML se regenera aqui y no a mano porque las paginas de catalogo se
    sirven con las ofertas escritas dentro: sin regenerar, el repositorio
    tendria los JSON de una tanda y el HTML de la anterior, y un crawler no
    veria las ofertas nuevas hasta que alguien se acordase.

    Con REGENERAR_HTML=0 se comporta como antes (solo data/), por si hay que
    publicar los JSON sin tocar el HTML.
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
        log.info("[GIT] Publicando cambios de data/ y el HTML regenerado ...")
        try:
            # El HTML se regenera ANTES de mirar que haya cambios: si solo ha
            # cambiado una oferta, el HTML es lo unico que va a diferir y sin
            # esto el commit se haria vacio ("No hay cambios que publicar").
            # Se hace dentro del lock porque escribe en el arbol de trabajo.
            if REGENERAR_HTML:
                fallos = await asyncio.to_thread(_regenerar_html)
                if fallos:
                    # No se aborta: subir los JSON con el HTML viejo es mejor
                    # que no subir nada, y el error queda en el log.
                    log.error(f"[HTML] Generadores con fallo: {fallos}. "
                              "Se sube igualmente con el HTML anterior.")

            ok, salida = await asyncio.to_thread(_git, 'add', '--', 'data/')
            if not ok:
                log.error(f"[GIT] Fallo en 'git add data/': {salida}")
                return False

            # El HTML tambien entra en el commit: sin esto las paginas
            # regeneradas se quedarian sin subir y el bot las reescribiria en
            # cada tanda, dejando el arbol siempre sucio.
            if REGENERAR_HTML:
                ok, salida = await asyncio.to_thread(
                    _git, 'add', '--', *_paginas_generadas())
                if not ok:
                    log.error(f"[GIT] Fallo en 'git add' del HTML: {salida}")
                    return False

            ok, salida = await asyncio.to_thread(_git, 'status', '--porcelain')
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

def _vaciar_catalogo():
    """Deja vacios los JSON de ofertas de data/. Devuelve cuantos se vaciaron.

    Solo toca los ficheros cuyo contenido es una lista: si un diccionario como
    categorias.json acabara en data/, no se toca. Un JSON ilegible se cuenta
    como lista vacia (ver _leer_json) y por tanto se sobrescribe, que es justo
    lo que se quiere: un archivo corrupto no debe dejar la web sin datos para
    siempre.
    """
    vaciados = 0
    for archivo in sorted(DATA_PATH.glob('*.json')):
        try:
            if not isinstance(_leer_json(archivo), list):
                log.warning(f"[CATALOGO] {archivo.name} no es una lista de ofertas; se deja como esta")
                continue
            _escribir_json_atomico(archivo, [])
            vaciados += 1
        except Exception as e:
            log.error(f"[CATALOGO] No se pudo vaciar {archivo.name}: {e}")
    return vaciados

def _reiniciar_catalogo():
    """Borra todas las ofertas y las imagenes asociadas. Devuelve un resumen.

    Ofertas e imagenes se borran juntas y en un solo sitio a proposito: si el
    borrado quedara partido entre dos funciones, un fallo en mitad dejaria
    imagenes huerfanas o JSON sin vaciar sin que nadie se entere.
    """
    json_vaciados = _vaciar_catalogo()
    imagenes = limpiar_imagenes_huerfanas()
    # El recuento de descartes es por reconstruccion: al vaciar empieza una.
    _DESCARTES.clear()
    log.info(f"[CATALOGO] Reiniciado: {json_vaciados} JSON vacios, "
             f"{imagenes} imagenes borradas")
    return json_vaciados, imagenes

async def recuperar_mensajes_perdidos():
    """Reconstruye el catalogo con los ultimos mensajes del canal.

    events.NewMessage solo dispara con mensajes nuevos, asi que una parada de
    horas dejaba huecos en el JSON. Se procesan del mas antiguo al mas reciente
    para que el orden por ID en _guardar_en_archivo quede correcto.

    Con REINICIAR_CATALOGO los JSON se vacian antes de repoblar, de modo que
    lo publicado es siempre el estado actual del canal y no se acumulan ofertas
    caducadas ni retoques a mano.

    El vaciado va DESPUES de leer el historial, nunca antes: si Telegram falla,
    el canal esta vacio o no se puede acceder, un vaciado previo dejaria la web
    vacia y sin forma de reponerse. Ante cualquier fallo se conserva lo que
    hubiera.
    """
    if BACKFILL_LIMIT <= 0:
        if REINICIAR_CATALOGO:
            log.warning("[CATALOGO] BACKFILL_LIMIT=0 pero REINICIAR_CATALOGO=1: "
                        "no hay mensajes con los que reconstruir, se conserva el catalogo actual")
        else:
            log.info("[BACKFILL] Desactivado (BACKFILL_LIMIT=0)")
        return

    log.info(f"[BACKFILL] Recuperando hasta {BACKFILL_LIMIT} mensajes recientes...")
    try:
        mensajes = await client.get_messages(MI_CANAL, limit=BACKFILL_LIMIT)
    except Exception as e:
        log.error(f"[BACKFILL] No se pudo leer el historial: {e}. "
                  "Se conserva el catalogo actual.")
        return

    if not mensajes:
        log.warning("[BACKFILL] El canal no devolvio ningun mensaje. "
                    "Se conserva el catalogo actual.")
        return

    if REINICIAR_CATALOGO:
        async with LOCK_ARCHIVOS:
            json_vaciados, imagenes = _reiniciar_catalogo()
        log.info(f"[CATALOGO] Se reconstruyen con {len(mensajes)} mensajes del canal "
                 f"({json_vaciados} JSON vacios, {imagenes} imagenes borradas)")

    _DESCARTES.clear()
    procesados = 0
    for msg in reversed(mensajes):   # del mas antiguo al mas reciente
        try:
            if await procesar_mensaje(msg, origen='backfill'):
                procesados += 1
        except Exception as e:
            log.error(f"[BACKFILL] Fallo con el mensaje {getattr(msg, 'id', '?')}: {e}")

    log.info(f"[BACKFILL] {procesados}/{len(mensajes)} mensajes publicados "
             f"({len(mensajes) - procesados} descartados por no publicables o ya guardados)")
    if _DESCARTES:
        detalle = ", ".join(f"{motivo}: {n}" for motivo, n in
                            sorted(_DESCARTES.items(), key=lambda kv: -kv[1]))
        log.info(f"[BACKFILL] Motivos de descarte -> {detalle}")

    await _verificar_backfill(mensajes, procesados)


async def _verificar_backfill(mensajes, procesados):
    """Comprueba, al cerrar el backfill, que el catalogo esta completo y publicado.

    El log de arriba dice cuantos mensajes se procesaron, pero no responde a las
    dos preguntas que de verdad importan al arrancar: si lo que hay en disco son
    las ofertas que se han leido del canal, y si eso ha llegado a GitHub Pages.
    Sin esta comprobacion, un recorte por MAX_OFERTAS o un push rechazado solo
    se detectan tarde, con la web ya sirviendo un catalogo vacio.

    Se avisa por log en vez de abortar: el bot esta escuchando y debe seguir
    recogiendo las ofertas nuevas aunque el backfill haya quedado corto.
    """
    general = _leer_json(DATA_PATH / 'general.json')
    # El objetivo no es llenar los mensajes leidos, sino los huecos del
    # catalogo: MAX_OFERTAS. Con BACKFILL_LIMIT > MAX_OFERTAS (hay que leer de
    # mas porque no todos los mensajes son ofertas) comparar contra los
    # mensajes leidos daria un "FALTAN 30" que en realidad es el recorte
    # previsto y no una perdida.
    objetivo = min(MAX_OFERTAS, BACKFILL_LIMIT, len(mensajes))
    topes = [f'{p.name}={len(_leer_json(p))}'
             for p in sorted(DATA_PATH.glob('*.json')) if p.name != 'general.json']

    log.info(f"[VERIFICACION] general.json={len(general)} ofertas "
             f"(procesadas: {procesados}, leidas del canal: {len(mensajes)}); "
             f"por categoria -> {', '.join(topes) or 'sin categorias'}")

    # Las secciones se recortan a MAX_OFERTAS_CATEGORIA, asi que quedarse sin
    # llenarse no es por si sola una perdida: puede ser el tope alcanzado. Solo
    # se avisa cuando ademas sobraban mensajes sin leer, que si es senal de que
    # el canal no da para llenar la seccion.
    secciones = {p.name: len(_leer_json(p))
                 for p in DATA_PATH.glob('*.json') if p.name != 'general.json'}
    for nombre, llenado in sorted(secciones.items()):
        if llenado < MAX_OFERTAS_CATEGORIA and len(mensajes) > MAX_OFERTAS_CATEGORIA:
            log.warning(f"[VERIFICACION] La seccion {nombre} se ha quedado en "
                        f"{llenado}/{MAX_OFERTAS_CATEGORIA} con {len(mensajes)} "
                        f"mensajes leidos: no da para mas. Si se repite, sube "
                        f"BACKFILL_LIMIT (ahora {BACKFILL_LIMIT}).")

    if len(general) < objetivo:
        faltan = objetivo - len(general)
        log.warning(f"[VERIFICACION] FALTAN {faltan} ofertas de las {objetivo} que caben "
                    f"(de {len(mensajes)} mensajes leidos). Revisa los descartes de arriba; "
                    f"si son muchos los no publicables, sube BACKFILL_LIMIT "
                    f"(ahora {BACKFILL_LIMIT}).")
    else:
        log.info(f"[VERIFICACION] general.json completo: {len(general)}/{objetivo} ofertas")
        if len(mensajes) > objetivo:
            log.info(f"[VERIFICACION] Se dejan fuera los {len(mensajes) - objetivo} mensajes "
                     f"mas antiguos: es el recorte normal para quedarse con las "
                     f"{objetivo} ofertas mas recientes.")

    if not AUTO_PUBLICAR:
        log.warning("[VERIFICACION] AUTO_PUBLICAR=0: los JSON son correctos pero la web "
                    "no se actualizara hasta que alguien haga git add/commit/push a mano.")
        return

    if procesados:
        if await publicar_en_git(forzar=True):
            log.info(f"[VERIFICACION] Cambios publicados en {GIT_REMOTO}/{GIT_RAMA}. "
                     "GitHub Pages tardara unos minutos en servirlos.")
        else:
            log.error("[VERIFICACION] Los JSON se han escrito pero el push ha fallado: "
                      "la web sigue mostrando el catalogo anterior. "
                      f"Revisa el bloque [GIT] del log y sube data/"
                      + (" y el HTML regenerado" if REGENERAR_HTML else "")
                      + " a mano.")

# ─────────────────────────────────────────────
# PARADA LIMPIA
# ─────────────────────────────────────────────
def _pedir_parada(motivo):
    """Pide cerrar el bot y suelta la conexion para que main() pueda salir.

    No basta con marcar el evento: run_until_disconnected() quedaria esperando
    al servidor para siempre. Desconectar es lo que hace que esa espera
    termine y el bucle de escucha pueda comprobar _evento_parada.

    Se llama desde un manejador de senal, que corre en el hilo principal fuera
    del event loop, de ahi el call_soon_threadsafe para tocar el loop desde
    dentro. Reentrante a proposito: una segunda pulsacion de Ctrl+C, o una
    DURACION_S agotada mientras ya se esta parando, no deben romper nada.
    """
    if _evento_parada is not None and _evento_parada.is_set():
        return

    log.warning(f"[PARADA] {motivo}. Cerrando y publicando lo pendiente...")
    if _evento_parada is not None:
        _evento_parada.set()
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Sin loop corriendo (senal recibida entre tareas): desconectar de
        # forma sincrona es seguro porque el cliente no esta en uso.
        asyncio.run(client.disconnect())
        return
    loop.call_soon_threadsafe(lambda: asyncio.ensure_future(client.disconnect()))

def _instalar_manejadores_de_senales():
    """Convierte SIGINT/SIGTERM y Ctrl+C en una parada ordenada.

    Sin esto, parar el bot es un hardkill: el proceso muere sin pasar por el
    push final y las ofertas de los ultimos segundos se quedan sin publicar.
    Stop-Process de Windows llama a TerminateProcess y no entrega ninguna senal,
    asi que en Windows esto no arregla un Stop-Process -Force: para eso esta
    DURACION_SEGUNDOS, que deja al bot cerrar solo. En Unix, donde SIGTERM si
    se entrega, systemctl stop / kill ya salen por aqui.
    """
    import signal as _signal

    for nombre in ('SIGINT', 'SIGTERM'):
        sig = getattr(_signal, nombre, None)
        if sig is None:
            continue
        try:
            _signal.signal(sig, lambda s, f, n=nombre: _pedir_parada(f"Recibida {n}"))
        except (ValueError, OSError) as e:
            # ValueError: no estamos en el hilo principal. OSError: senal no
            # soportada en esta plataforma. En ambos casos el bot sigue
            # funcionando, solo que parandolo con Ctrl+C a secas.
            log.warning(f"[PARADA] No se pudo instalar el manejador de {nombre}: {e}")

async def _tarea_publicar_periodica():
    """Sube a git lo pendiente cada PUBLICAR_CADA_S segundos, aunque no entre nada.

    Sin esta tarea, publicar_en_git() solo se dispara al procesar un mensaje
    nuevo, y el throttle de PUBLICAR_CADA_S puede hacer que ese push se
    lose: una oferta que llega 10 s despues del push anterior se queda sin
    subir, y si el canal queda callado no vuelve a intentarlo nunca. Se perdia
    la oferta de verdad, no solo el registro en el log.

    Se llama con forzar=False a proposito: la tarea cede el agrupado a
    publicar_en_git, que ya sabe si toca push y ademas mira si hay cambios de
    verdad, asi que en los ciclos sin novedades no se ejecuta ni un git status
    que no sirva para nada.
    """
    while True:
        await asyncio.sleep(PUBLICAR_CADA_S)
        try:
            await publicar_en_git()
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("[GIT] Error en la publicacion periodica")

async def _tarea_duracion():
    """Cierra el bot pasado DURACION_S segundos, si se configuro.

    Es lo que permite usarlo como tarea programada: termina solo, con el push
    final hecho, en vez de tener que matarlo.
    """
    await asyncio.sleep(DURACION_S)
    _pedir_parada(f"DURACION_SEGUNDOS={DURACION_S} agotado")

async def main():
    global _evento_parada

    log.info("=" * 60)
    log.info(" BOT OFERTAS AMAZON - INICIANDO")
    log.info(f" Archivo de log: {LOG_PATH}")
    log.info("=" * 60)

    _evento_parada = asyncio.Event()
    _instalar_manejadores_de_senales()

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

    # Al arrancar, el catalogo se borra entero y se reconstruye con el
    # historial del canal (ver recuperar_mensajes_perdidos).
    await recuperar_mensajes_perdidos()

    # La publicacion periodica arranca DESPUES del backfill, nunca durante: si
    # no, empujaria a git un catalogo a medio construir, con los JSON vaciados
    # y solo algunas secciones repobladas.
    tareas_auxiliares = []
    if AUTO_PUBLICAR:
        tareas_auxiliares.append(asyncio.create_task(_tarea_publicar_periodica()))
    if DURACION_S > 0:
        tareas_auxiliares.append(asyncio.create_task(_tarea_duracion()))

    log.info("[CONECTADO] Bot escuchando mensajes nuevos...")
    # run_until_disconnected devuelve True si la conexion se perdio y hay que
    # reconectar, por eso se envuelve en un bucle en lugar de llamar una vez.
    # La parada pedida se comprueba antes de reconectar: _pedir_parada ya ha
    # desconectado, y sin esta comprobacion el bot volveria alevantarse y
    # seguiría escuchando justo cuando se le pedía cerrar.
    try:
        while not _evento_parada.is_set():
            try:
                reconectar = await client.run_until_disconnected()
            except (asyncio.CancelledError, KeyboardInterrupt):
                raise
            except Exception as e:
                log.exception(f"[ERROR] Conexion perdida: {e}. Reintentando en 10 s...")
                await asyncio.sleep(10)
                continue
            if _evento_parada.is_set():
                break
            if not reconectar:
                break
            log.warning("[CONEXION] Perdida. Reconectando en 5 s...")
            await asyncio.sleep(5)
            # Tras reconectar, las ofertas publicadas durante el corte se
            # perdieron: events.NewMessage solo dispara con lo que llega a partir
            # de ahora. Sin este backfill, un corte largo deja huecos que solo se
            # arreglarian reiniciando el bot a mano.
            try:
                await recuperar_mensajes_perdidos()
            except Exception as e:
                log.exception(f"[ERROR] Fallo reconstruyendo el catalogo tras reconectar: {e}")
            else:
                log.info("[CONEXION] Catalogo reconstruido tras reconectar")
    finally:
        # Las tareas auxiliares se cancelan aqui, no antes: mientras dure el
        # bucle son las que guarantees que nada se pierde si el proceso muere.
        for tarea in tareas_auxiliares:
            tarea.cancel()
        if tareas_auxiliares:
            await asyncio.gather(*tareas_auxiliares, return_exceptions=True)

    # Ultimo intento de subir lo pendiente antes de salir.
    if await publicar_en_git(forzar=True):
        log.info("[DESCONEXION] Bot detenido. Ofertas publicadas.")
    else:
        log.info("[DESCONEXION] Bot detenido.")
    try:
        await client.disconnect()
    except Exception:
        pass

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.warning("[DESCONEXION] Interrumpido por el usuario.")
    finally:
        # Publicacion de ultimo recurso. main() ya sube lo pendiente al salir
        # con publicar_en_git(forzar=True), asi que solo queda actuar si se ha
        # interrumpido antes de llegar ahi. Sigue haciendo falta: asyncio.run
        # cancela las tareas pendientes al interrumpir, y la periodica puede
        # ser justo la que tenia un push a medias.
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

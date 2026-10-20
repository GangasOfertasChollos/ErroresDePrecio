#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publica las ofertas del catalogo en X (Twitter) usando la API interna de X.

El script no usa la API de pago de X: habla el mismo protocolo que la web
(x.com -> GraphQL) con las cookies de una sesion real del navegador. Por eso
necesita `auth_token` y `ct0`, que se copian de las DevTools.

De donde salen las ofertas
---------------------------
Del catalogo que ya construye bot.py: `data/general.json` (feed global) o
`data/<categoria>.json`. No se vuelve a rastrear nada, ni Telegram ni Amazon:
este script solo formatea lo que ya esta scraped y lo publica.

Porque no hay dependencias
--------------------------
Solo la biblioteca estandar de Python. En un Ubuntu de proot (Termux) no hace
falta `pip install` ni Chromium ni root: `python3 publicar_x.py` y listo. Todas
las peticiones HTTP van con `urllib`, que ya viene con Python.

Lo que se rompe con el tiempo
-----------------------------
X rota cada pocas semanas los identificadores de sus operaciones GraphQL.
Ademas, en 2025 cambio el frontend por completo: las operaciones ya no se
llaman con un id numerico sino con ids de Relay (`ewPB3lRszYIJIpDvJ8dLCQ`) y
se piden a `api.x.com/graphql/<id>/<operacion>`. Por eso el script busca los
ids en el propio JavaScript de x.com, los guarda en cache y los vuelve a
buscar cuando X responde que no conoce la operacion.

Uso
----
    python3 publicar_x.py                 # publica las ofertas nuevas
    python3 publicar_x.py --simular       # ensaya sin publicar nada
    python3 publicar_x.py --limite 3      # como mucho 3 esta vez
    python3 publicar_x.py --categoria gaming-consolas
    python3 publicar_x.py --revisar       # comprueba la sesion y los ids
    python3 publicar_x.py --verificar     # lista los ultimos posts y sincroniza
"""

import argparse
import concurrent.futures
import hashlib
import json
import logging
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE LOGGING
# ─────────────────────────────────────────────
LOG_PATH = Path(__file__).resolve().parent / 'x.log'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_PATH, encoding='utf-8')
    ]
)
log = logging.getLogger('publicar_x')

# Las consolas de Windows no siempre aguantan los emojis de las ofertas.
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
    log.warning(f"No se encontro archivo .env en {_env_path}. Usando variables de entorno del sistema.")


def _leer_int(nombre, por_defecto):
    """Lee un entero del entorno tolerando valores vacios o invalidos."""
    bruto = str(os.getenv(nombre, '') or '').strip()
    if not bruto:
        return por_defecto
    try:
        return int(bruto)
    except ValueError:
        log.warning(f"Valor no numerico en {nombre}='{bruto}', se usa {por_defecto}")
        return por_defecto


def _leer_bool(nombre, por_defecto):
    """Lee un booleano del entorno: 0/false/no lo desactivan."""
    bruto = str(os.getenv(nombre, '') or '').strip().lower()
    if not bruto:
        return por_defecto
    return bruto not in ('0', 'false', 'no', 'off')


# ─────────────────────────────────────────────
# CREDENCIALES Y CONFIGURACIÓN
# ─────────────────────────────────────────────
REPO_PATH   = Path(__file__).resolve().parent
DATA_PATH   = REPO_PATH / 'data'
CACHE_PATH  = REPO_PATH / 'cache_x.json'   # ids de operacion y bearer token
ESTADO_PATH = REPO_PATH / 'estado_x.json'   # ofertas ya publicadas

# Cookies de la sesion de x.com (DevTools > Application > Cookies > x.com).
AUTH_TOKEN = os.getenv('X_AUTH_TOKEN', '').strip()
CT0        = os.getenv('X_CT0', '').strip()
# @usuario de la cuenta que publica. Solo se usa para dar contexto en los logs
# y para leer los ultimos posts.
USUARIO    = os.getenv('X_USUARIO', '').strip().lstrip('@')

# Bearer token: el que usa la web de X. Si no se indica, se busca en el
# JavaScript de x.com (ver descubrir_operaciones).
BEARER = os.getenv('X_BEARER', '').strip()

# Ids de las operaciones, si se ponen a mano: "nombre=id,nombre=id". Tiene
# prioridad sobre el descubrimiento automatico.
QUERY_IDS_MANUALES = os.getenv('X_QUERY_IDS', '').strip()

LIMITE_TWEETS   = _leer_int('X_MAX_TWEETS', 5)      # por ejecucion
PAUSA_SEGUNDOS  = _leer_int('X_PAUSA_SEGUNDOS', 90)  # entre un post y el siguiente
ESPERA_CUOTA    = _leer_int('X_ESPERA_CUOTA', 1800)   # cuando la cuenta se pasa de tweets
REINTENTOS_CUOTA = _leer_int('X_REINTENTOS_CUOTA', 8)  # veces que se reintenta tras la espera
TIMEOUT         = _leer_int('X_TIMEOUT', 30)
CON_IMAGEN      = _leer_bool('X_CON_IMAGEN', True)
SOLO_ID_MIN     = _leer_int('X_SOLO_ID_MIN', 0)      # solo ofertas con id > este

# El texto que se publica. Se puede cambiar entero por el .env; los campos
# disponibles son {titulo} {precio} {precio_antes} {descuento} {url}
# {descripcion} {categoria} {hashtags}.
PLANTILLA = os.getenv('X_PLANTILLA', '') or (
    "{titulo}\n"
    "\n"
    "{precios}\n"
    "\n"
    "{url}\n"
    "\n"
    "{descripcion}\n"
    "\n"
    "{hashtags}"
)

HASHTAGS_BASE = os.getenv('X_HASHTAGS', '#Amazon #Chollos').strip()
HASHTAGS_CATEGORIA = {
    'ropa-y-calzado':           '#Moda',
    'gaming-consolas':          '#Gaming',
    'higiene-cuidado-personal': '#CuidadoPersonal',
    'juguetes-infantil':        '#Juguetes',
    'moviles-electronica':      '#Tecnologia',
    'papeleria-oficina':        '#Papeleria',
    'general':                  '#Ofertas',
}

# Operacion de GraphQL que publica un post y operacion que lee los ultimos.
OPERACION_PUBLICAR = 'createTweetMutation'
OPERACION_LEER = 'UserTweets'

# Los ids de operacion caducan. Se reintentan cada DIAS_CACHE dias, y antes si
# X responde que no conoce la operacion.
DIAS_CACHE = 7

# Como se llama a cada chunk del JavaScript de x.com. El bundle grande
# (startup-dynamic) lleva la lista completa de assets, y ahi se busca el
# nombre de los ficheros que pueden contener la mutacion de publicar.
PATRON_CHUNKS = re.compile(
    r'compos|creat|publish|disclos|post|tweet|media|upload|note|timeline|profile',
    re.I)

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
)

# X ya no acepta solo el texto: la mutacion de publicar exige ademas una
# variable por cada "feature flag" que la web activa. Se llaman
# `__relay_internal__pv__xclientsfeatures<nombre>relayprovider` y, si falta
# alguna, X responde con un 422 diciendo cual falta. Esta es la lista que
# pide hoy la operacion createTweetMutation.
FLAGS_OPERACION = {
    '__relay_internal__pv__xclientsfeaturesappviewerisloggedinrelayprovider': True,
    '__relay_internal__pv__xclientsfeaturestranslationnoteautotranslationenabledrelayprovider': True,
    '__relay_internal__pv__xclientsfeaturestranslationgroktranslatedpostenabledrelayprovider': True,
}

# Cookies que X pone en la web (twid, guest_id, lang). No hacen falta para
# Identify, pero si las espera el gateway de la API de escritura: sin ellas
# responde 403 y no dice por que.
COOKIES_WEB = {}

# La web nueva de X. La API de graphql va a api.x.com y la subida de imagenes
# a upload.x.com.
HOSTO_GRAPHQL = 'https://api.x.com/graphql'
HOSTO_UPLOAD = 'https://upload.x.com/i/media/upload.json'
HOSTO_WEB = 'https://x.com'

# Tamano maximo de una imagen para un post (lo que acepta X).
MAX_IMAGEN = 5 * 1024 * 1024
# Cada segmento de la subida va en 4 MB, por debajo del limite de X.
SEGMENTO = 4 * 1024 * 1024


# ─────────────────────────────────────────────
# PETICIONES HTTP (solo biblioteca estandar)
# ─────────────────────────────────────────────
class Respuesta:
    """Respuesta HTTP minima: estado, cuerpo y cabeceras."""

    def __init__(self, estado, cuerpo, cabeceras):
        self.estado = estado
        self.cuerpo = cuerpo
        self.cabeceras = cabeceras

    @property
    def texto(self):
        return self.cuerpo.decode('utf-8', errors='replace')

    def json(self):
        try:
            return json.loads(self.texto)
        except (ValueError, TypeError):
            return None

    def ok(self):
        return 200 <= self.estado < 300


def _peticion(url, datos=None, cabeceras=None, metodo=None, intentos=3):
    """Pide una URL y devuelve una Respuesta. Nunca lanza por un error HTTP.

    Reintenta los 429 y los 5xx esperando cada vez mas, porque X limita mucho
    cuando se le acumulan las peticiones.
    """
    cabeceras = dict(cabeceras or {})
    espera = 5
    ultimo_error = None

    for intento in range(1, intentos + 1):
        peticion = urllib.request.Request(url, data=datos, headers=cabeceras, method=metodo)
        try:
            with urllib.request.urlopen(peticion, timeout=TIMEOUT) as respuesta:
                return Respuesta(respuesta.status, respuesta.read(), dict(respuesta.headers))
        except urllib.error.HTTPError as error:
            cuerpo = b''
            try:
                cuerpo = error.read()
            except Exception:
                pass
            estado = error.code
            if estado in (429, 500, 502, 503, 504) and intento < intentos:
                log.warning(f"  HTTP {estado}, reintento {intento}/{intentos - 1} en {espera}s")
                time.sleep(espera)
                espera *= 2
                continue
            return Respuesta(estado, cuerpo, dict(error.headers or {}))
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            ultimo_error = error
            log.warning(f"  Error de red ({error}), reintento {intento}/{intentos - 1} en {espera}s")
            if intento < intentos:
                time.sleep(espera)
                espera *= 2
                continue

    raise ConnectionError(f"No se pudo contactar con {url}: {ultimo_error}")


def _descargar_binario(url, limite=MAX_IMAGEN):
    """Descarga un binario (una imagen) y devuelve los bytes, o None."""
    respuesta = _peticion(url, cabeceras={'User-Agent': USER_AGENT})
    if not respuesta.ok():
        log.warning(f"  No se pudo descargar la imagen ({respuesta.estado}): {url[:80]}")
        return None
    if len(respuesta.cuerpo) > limite:
        log.warning(f"  La imagen pesa {len(respuesta.cuerpo)} bytes, mas del limite. Se descarta.")
        return None
    tipo = str(respuesta.cabeceras.get('Content-Type', '')).lower()
    if tipo and not tipo.startswith('image/'):
        log.warning(f"  La URL no devuelve una imagen ({tipo}). Se descarta.")
        return None
    return respuesta.cuerpo


def _multipart(campos, archivos):
    """Arma un cuerpo multipart/form-data. `archivos` es [(nombre, nombre_archivo, bytes)]."""
    borde = '----PublicarX' + hashlib.md5(str(time.time()).encode()).hexdigest()
    partes = []
    for nombre, valor in campos.items():
        partes.append(f'--{borde}\r\n'.encode())
        partes.append(f'Content-Disposition: form-data; name="{nombre}"\r\n\r\n'.encode())
        partes.append(f'{valor}\r\n'.encode())
    for nombre, nombre_archivo, datos in archivos:
        partes.append(f'--{borde}\r\n'.encode())
        partes.append(
            f'Content-Disposition: form-data; name="{nombre}"; filename="{nombre_archivo}"\r\n'.encode()
        )
        partes.append(b'Content-Type: application/octet-stream\r\n\r\n')
        partes.append(datos)
        partes.append(b'\r\n')
    partes.append(f'--{borde}--\r\n'.encode())
    return b''.join(partes), f'multipart/form-data; boundary={borde}'


# ─────────────────────────────────────────────
# SESIÓN DE X
# ─────────────────────────────────────────────
def _cookie_header(ct0=None):
    """Cabecera Cookie con la sesion."""
    token_csrf = CT0 if ct0 is None else ct0
    partes = []
    if AUTH_TOKEN:
        partes.append(f'auth_token={AUTH_TOKEN}')
    if token_csrf:
        partes.append(f'ct0={token_csrf}')
    for nombre, valor in COOKIES_WEB.items():
        if nombre not in ('auth_token', 'ct0'):
            partes.append(f'{nombre}={valor}')
    return '; '.join(partes)


def refrescar_cookies_web():
    """Pide a x.com las cookies de sesion y las guarda.

    La web responde con twid, guest_id y lang. El gateway de la API de
    escritura las usa para saber que sesion es: sin ellas se lleva un 403 sin
    cuerpo y sin explicacion.
    """
    global COOKIES_WEB
    try:
        respuesta = _peticion(f'{HOSTO_WEB}/', cabeceras={
            'User-Agent': USER_AGENT,
            'Cookie': _cookie_header(),
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'es-ES,es;q=0.9',
        })
    except ConnectionError as error:
        log.warning(f"  No se pudieron refrescar las cookies de x.com: {error}")
        return
    if not respuesta.ok():
        log.warning(f"  x.com devolvio HTTP {respuesta.estado} al pedir las cookies")
        return
    nuevas = {}
    for cabecera, valor in respuesta.cabeceras.items():
        if cabecera.lower() != 'set-cookie':
            continue
        for parte in valor.split(';'):
            nombre, _, dato = parte.strip().partition('=')
            if nombre in ('twid', 'guest_id', 'lang') and dato:
                nuevas[nombre] = dato
    if nuevas:
        COOKIES_WEB.update(nuevas)
        log.info(f"  Cookies de x.com: {', '.join(sorted(nuevas))}")


def _cabeceras_x(ct0=None, json_body=True, extra=None):
    """Cabeceras que X espera en las peticiones internas.

    El gateway de la API de escritura mira como llega la peticion. Con solo
    las cabeceras minimas devuelve un 403 sin cuerpo; con las que manda el
    navegador (sec-fetch-*, sec-ch-ua, x-client-transaction-id) la acepta.
    """
    token_csrf = CT0 if ct0 is None else ct0
    cabeceras = {
        'User-Agent': USER_AGENT,
        'Accept': '*/*',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Origin': 'https://x.com',
        'Referer': 'https://x.com/compose/post',
        'sec-ch-ua': '"Chromium";v="126", "Not.A/Brand";v="8", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'X-Twitter-Active-User': 'yes',
        'X-Twitter-Auth-Type': 'OAuth2Session',
        'x-client-transaction-id': str(uuid.uuid4()),
        'x-client-uuid': str(uuid.uuid4()),
        'Cookie': _cookie_header(ct0),
    }
    if json_body:
        cabeceras['Content-Type'] = 'application/json'
    if token_csrf:
        cabeceras['X-Csrf-Token'] = token_csrf
    if BEARER:
        cabeceras['Authorization'] = f'Bearer {BEARER}'
    if extra:
        cabeceras.update(extra)
    return cabeceras


def obtener_ct0():
    """Recupera el token CSRF si el usuario no lo pone en el .env.

    Con la cookie auth_token puesta, X devuelve el ct0 en la cabecera
    Set-Cookie de la primera peticion. Se prueban varias entradas por si la
    primera no lo sirve.
    """
    global CT0
    if CT0:
        return CT0
    if not AUTH_TOKEN:
        return ''

    log.info("No hay X_CT0 en el .env: se pide a X que lo devuelva con la sesion")
    for url in ('https://x.com/', 'https://x.com/i/api/1.1/guest/activate.json',
                'https://api.x.com/1.1/guest/activate.json'):
        try:
            respuesta = _peticion(url, cabeceras={'User-Agent': USER_AGENT, 'Cookie': _cookie_header('')})
        except ConnectionError as error:
            log.warning(f"  No se pudo pedir el ct0 a {url}: {error}")
            continue
        for cabecera, valor in respuesta.cabeceras.items():
            if cabecera.lower() != 'set-cookie':
                continue
            for parte in valor.split(';'):
                nombre, _, dato = parte.strip().partition('=')
                if nombre == 'ct0' and dato:
                    CT0 = dato
                    log.info(f"  ct0 obtenido de {url}")
                    return CT0
    return ''


def _ct0_de_la_respuesta(respuesta):
    """X manda un ct0 nuevo cuando el que se manda ya no vale.

    Lo manda en la cabecera Set-Cookie y, a veces, tambien en el cuerpo de la
    respuesta de error.
    """
    for cabecera, valor in respuesta.cabeceras.items():
        if cabecera.lower() != 'set-cookie':
            continue
        for parte in valor.split(';'):
            nombre, _, dato = parte.strip().partition('=')
            if nombre == 'ct0' and dato:
                return dato
    datos = respuesta.json()
    if isinstance(datos, dict):
        for clave in ('ct0', 'ct0_token'):
            if datos.get(clave):
                return str(datos[clave])
    return ''


# ─────────────────────────────────────────────
# DESCUBRIR LOS IDS DE OPERACION Y EL BEARER
# ─────────────────────────────────────────────
def _leer_cache():
    if not CACHE_PATH.exists():
        return {}
    try:
        with open(CACHE_PATH, encoding='utf-8') as _f:
            return json.load(_f)
    except (ValueError, OSError):
        return {}


def _escribir_cache(datos):
    try:
        with open(CACHE_PATH, 'w', encoding='utf-8') as _f:
            json.dump(datos, _f, ensure_ascii=False, indent=2)
    except OSError as error:
        log.warning(f"No se pudo guardar la cache: {error}")


def _scripts_de_x():
    """Devuelve las URLs de los JavaScript que carga x.com."""
    try:
        respuesta = _peticion(f'{HOSTO_WEB}/', cabeceras={
            'User-Agent': USER_AGENT,
            'Cookie': _cookie_header(),
            'Accept': 'text/html,application/xhtml+xml',
        })
    except ConnectionError as error:
        log.error(f"No se pudo abrir x.com: {error}")
        return []

    if not respuesta.ok():
        log.error(f"x.com devolvio HTTP {respuesta.estado}. Revisa X_AUTH_TOKEN.")
        return []

    html = respuesta.texto
    scripts = re.findall(r'<script[^>]+src="([^"]+)"', html)
    completas = []
    for src in scripts:
        if src.startswith('//'):
            src = 'https:' + src
        elif src.startswith('/'):
            src = HOSTO_WEB + src
        if src.endswith('.js') and src not in completas:
            completas.append(src)
    log.info(f"x.com carga {len(completas)} ficheros JavaScript")
    return completas


def _imports_de(url, texto):
    """Ficheros JavaScript que importa otro fichero JavaScript."""
    base = url.rsplit('/', 1)[0]
    imports = set()
    for patron in (r'["\'](assets/[^"\']+\.js)["\']', r'["\'](\./[^"\']+\.js)["\']',
                   r'["\'](\.\./[^"\']+\.js)["\']', r'["\'](/x-web/[^"\']+\.js)["\']'):
        for encontrado in re.findall(patron, texto):
            if encontrado.startswith('http'):
                destino = encontrado
            elif encontrado.startswith('assets/'):
                # los assets cuelgan de la raiz de la app, no del directorio
                # del fichero que los nombra
                destino = f'https://abs.twimg.com/x-web/x-web/{encontrado}'
            elif encontrado.startswith('/'):
                destino = 'https://abs.twimg.com' + encontrado
            else:
                destino = urllib.parse.urljoin(base + '/', encontrado)
            imports.add(destino.replace('/assets/assets/', '/assets/'))
    return imports


def _bajar_varios(urls, hilos=8):
    """Descarga varios ficheros a la vez. Devuelve {url: texto}."""

    def _baja(url):
        try:
            respuesta = _peticion(url, cabeceras={'User-Agent': USER_AGENT, 'Cookie': _cookie_header()},
                                   intentos=1)
            if respuesta.ok():
                return url, respuesta.texto
        except ConnectionError:
            pass
        return url, ''

    resultado = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=hilos) as pool:
        for url, texto in pool.map(_baja, urls):
            if texto:
                resultado[url] = texto
    return resultado


def _id_de_operacion(texto, operacion):
    """Saca el id de una operacion de GraphQL de un chunk de x.com.

    En el JavaScript minificado cada operacion se declara asi:
    `params:{id:`ABC123`,metadata:{},name:`createTweetMutation`,operationKind:`mutation`}`
    """
    patron = re.compile(
        r'params:\{id:`([^`]+)`,metadata:\{\},name:`' + re.escape(operacion) + r'`,operationKind:`(\w+)`')
    coincidencia = patron.search(texto)
    if coincidencia:
        return coincidencia.group(1)
    # Algunos bundles lo escriben con comillas en vez de acentos graves.
    patron = re.compile(
        r'params:\{id:"([^"]+)",metadata:\{\},name:"' + re.escape(operacion) + r'",operationKind:"(\w+)"')
    coincidencia = patron.search(texto)
    if coincidencia:
        return coincidencia.group(1)
    return ''


def _bearer_de(texto):
    """El bearer token va dentro del propio JavaScript de X."""
    coincidencia = re.search(r'Bearer\s+([A-Za-z0-9%\-_=]{40,})', texto)
    return coincidencia.group(1) if coincidencia else ''


def descubrir_operaciones(forzar=False):
    """Devuelve {operacion: queryId} para publicar y para leer.

    Se cachean DIAS_CACHE dias. Si ya estan en el .env, no se busca nada.
    """
    global BEARER

    if QUERY_IDS_MANUALES:
        manual = {}
        for trozo in QUERY_IDS_MANUALES.split(','):
            nombre, _, identificador = trozo.partition('=')
            if nombre.strip() and identificador.strip():
                manual[nombre.strip()] = identificador.strip()
        if manual:
            log.info(f"Usando los ids de operacion del .env: {manual}")
            return manual

    cache = _leer_cache()
    fecha = cache.get('fecha', 0)
    caducada = (time.time() - fecha) > DIAS_CACHE * 86400
    if not forzar and not caducada and cache.get('operaciones'):
        vence = time.strftime('%Y-%m-%d', time.localtime(fecha + DIAS_CACHE * 86400))
        log.info(f"Operaciones de la cache (vigente hasta {vence})")
        BEARER = BEARER or cache.get('bearer', '')
        return cache['operaciones']

    log.info("Buscando los ids de operacion en el JavaScript de x.com")

    # 1. La portada da el bundle de entrada. De ahi se siguen los imports un
    #    par de niveles: los bundles que se llaman "startup" son los grandes y
    #    son los que llevan la lista de assets y el token.
    entradas = _scripts_de_x()
    if not entradas:
        return cache.get('operaciones', {})

    todos = {}
    vistos = set()
    nivel = entradas
    for _ in range(3):
        faltan = [u for u in nivel if u not in vistos]
        if not faltan:
            break
        leidos = _bajar_varios(faltan)
        todos.update(leidos)
        vistos |= set(leidos)
        siguientes = set()
        for url, texto in leidos.items():
            siguientes |= _imports_de(url, texto)
        # Los startup van primero: son los grandes y los que sirven.
        nivel = sorted(siguientes, key=lambda u: (0 if 'startup' in u else 1, u))[:40]

    if not todos:
        log.error("No se pudo leer ningun JavaScript de x.com")
        return cache.get('operaciones', {})

    if not BEARER:
        for texto in todos.values():
            BEARER = _bearer_de(texto)
            if BEARER:
                log.info("  bearer token leido del JavaScript de x.com")
                break

    # 2. La lista de assets la lleva el bundle grande: de ahi se sacan los
    #    nombres de los ficheros que pueden tener la mutacion de publicar.
    assets = set()
    for texto in todos.values():
        assets |= set(re.findall(r'"(assets/[^"]+\.js)"', texto))
    log.info(f"  x.com tiene {len(assets)} assets")

    operaciones = {}
    for operacion in (OPERACION_PUBLICAR, OPERACION_LEER):
        identificador = _id_de_operacion('\n'.join(todos.values()), operacion)
        if identificador:
            operaciones[operacion] = identificador

    faltan = [o for o in (OPERACION_PUBLICAR, OPERACION_LEER) if o not in operaciones]
    if faltan:
        # 3. Se descargan los assets con nombre suspeito (los del compositor, los
        #    de publicacion, los de contenido) y se busca dentro.
        candidatos = sorted(a for a in assets if PATRON_CHUNKS.search(a))
        log.info(f"  se revisan {len(candidatos)} assets con nombre relacionado")
        base = 'https://abs.twimg.com/x-web/x-web/assets/'
        urls = [base + a.rsplit('/', 1)[-1] for a in candidatos]
        for tanda in range(0, len(urls), 24):
            grupo = urls[tanda:tanda + 24]
            leidos = _bajar_varios(grupo)
            for texto in leidos.values():
                for operacion in faltan:
                    if operacion in operaciones:
                        continue
                    identificador = _id_de_operacion(texto, operacion)
                    if identificador:
                        operaciones[operacion] = identificador
            if not [o for o in faltan if o not in operaciones]:
                break

    for operacion, identificador in operaciones.items():
        log.info(f"  {operacion} -> {identificador}")
    for operacion in (OPERACION_PUBLICAR, OPERACION_LEER):
        if operacion not in operaciones:
            log.warning(f"  {operacion}: no aparece en los JavaScript de x.com")

    if not BEARER:
        log.error("  No se ha podido leer el bearer token de x.com")

    _escribir_cache({
        'fecha': time.time(),
        'bearer': BEARER,
        'operaciones': operaciones,
    })
    return operaciones


# ─────────────────────────────────────────────
# SUBIDA DE IMAGEN Y PUBLICACIÓN
# ─────────────────────────────────────────────
def subir_imagen(url_imagen):
    """Sube una imagen a X y devuelve su media_id, o '' si no se pudo.

    El protocolo es el de siempre: INIT abre la sesion, APPEND manda los
    bytes en segmentos y FINALIZE cierra la subida.
    """
    if not url_imagen:
        return ''
    datos = _descargar_binario(url_imagen)
    if not datos:
        return ''

    tipo = 'image/jpeg'
    parametros = urllib.parse.urlencode({
        'command': 'INIT',
        'media_category': 'tweet_image',
        'media_type': tipo,
        'total_bytes': len(datos),
    })
    try:
        respuesta = _peticion(f'{HOSTO_UPLOAD}?{parametros}', datos=b'', metodo='POST',
                               cabeceras=_cabeceras_x(json_body=False))
    except ConnectionError as error:
        log.warning(f"  No se pudo iniciar la subida: {error}")
        return ''
    if not respuesta.ok():
        log.warning(f"  X rechazo la subida (HTTP {respuesta.estado}): {respuesta.texto[:200]}")
        return ''

    inicio = respuesta.json() or {}
    media_id = str(inicio.get('media_id_string') or '')
    if not media_id:
        log.warning(f"  X no devolvio media_id: {respuesta.texto[:200]}")
        return ''

    # Los bytes van en segmentos de 4 MB.
    for indice, inicio_segmento in enumerate(range(0, len(datos), SEGMENTO)):
        segmento = datos[inicio_segmento:inicio_segmento + SEGMENTO]
        parametros = urllib.parse.urlencode({
            'command': 'APPEND',
            'media_id': media_id,
            'segment_index': str(indice),
        })
        cuerpo, tipo_cuerpo = _multipart({}, [('media', 'oferta.jpg', segmento)])
        try:
            respuesta = _peticion(f'{HOSTO_UPLOAD}?{parametros}', datos=cuerpo, metodo='POST',
                                   cabeceras=_cabeceras_x(json_body=False,
                                                          extra={'Content-Type': tipo_cuerpo}))
        except ConnectionError as error:
            log.warning(f"  No se pudo mandar el segmento {indice}: {error}")
            return ''
        if not respuesta.ok():
            log.warning(f"  X rechazo el segmento {indice} (HTTP {respuesta.estado})")
            return ''

    parametros = urllib.parse.urlencode({'command': 'FINALIZE', 'media_id': media_id})
    try:
        respuesta = _peticion(f'{HOSTO_UPLOAD}?{parametros}', datos=b'', metodo='POST',
                               cabeceras=_cabeceras_x(json_body=False))
    except ConnectionError as error:
        log.warning(f"  No se pudo cerrar la subida: {error}")
        return ''
    if not respuesta.ok():
        log.warning(f"  X rechazo el cierre de la subida (HTTP {respuesta.estado})")
        return ''

    log.info(f"  Imagen subida (media_id {media_id})")
    return media_id


def _url_operacion(operacion, query_id):
    """URL de la operacion.

    La web nueva usa api.x.com/graphql con ids de Relay. La antigua usaba
    x.com/i/api/graphql con ids numericos: si el id parece numerico, se usa
    la ruta antigua, que sigue viva.
    """
    if query_id.isdigit():
        return f'https://x.com/i/api/graphql/{query_id}/{operacion}'
    return f'{HOSTO_GRAPHQL}/{query_id}/{operacion}'


def _extraer_id_post(datos):
    """Saca el id del post recien creado de las distintas formas que devuelve X."""
    if not isinstance(datos, dict):
        return ''
    # Formato nuevo: data.create_tweet.tweet_results.result.rest_id
    crear = datos.get('data', {})
    if isinstance(crear, dict):
        nodo = crear.get('create_tweet')
        if isinstance(nodo, dict):
            resultados = nodo.get('tweet_results')
            if isinstance(resultados, dict):
                if resultados.get('rest_id'):
                    return str(resultados['rest_id'])
                resultado = resultados.get('result')
                if isinstance(resultado, dict) and resultado.get('rest_id'):
                    return str(resultado['rest_id'])
            if nodo.get('rest_id'):
                return str(nodo['rest_id'])
    # Formato antiguo: data.create_tweet.results[0].result.rest_id
    for camino in (('data', 'create_tweet', 'results'),
                    ('data', 'tweet_result', 'results'),
                    ('data', 'create_tweet')):
        actual = datos
        for clave in camino:
            if not isinstance(actual, dict):
                actual = None
                break
            actual = actual.get(clave)
        if isinstance(actual, list) and actual:
            actual = actual[0]
        if isinstance(actual, dict):
            resultado = actual.get('result', actual)
            if isinstance(resultado, dict):
                identificador = resultado.get('rest_id') or resultado.get('id_str')
                if identificador:
                    return str(identificador)
                legado = resultado.get('legacy')
                if isinstance(legado, dict) and legado.get('id_str'):
                    return str(legado['id_str'])
    return ''


def _errores_de_x(datos):
    """Devuelve el texto del error que devuelve X dentro de un 200."""
    if not isinstance(datos, dict):
        return ''
    errores = datos.get('errors')
    if isinstance(errores, list) and errores:
        partes = []
        for error in errores:
            if isinstance(error, dict):
                mensaje = error.get('message') or error.get('code')
                if mensaje:
                    partes.append(str(mensaje))
            else:
                partes.append(str(error))
        if partes:
            return '; '.join(partes)
    crear = datos.get('data', {})
    if isinstance(crear, dict):
        nodo = crear.get('create_tweet')
        if isinstance(nodo, dict):
            for clave in ('error', 'errors'):
                if nodo.get(clave):
                    return str(nodo[clave])
    return ''


def publicar(texto, media_ids=None, operaciones=None):
    """Publica un post en X y devuelve (id_del_post, error)."""
    global CT0
    operaciones = operaciones or {}
    query_id = operaciones.get(OPERACION_PUBLICAR)
    if not query_id:
        return '', f"no se conoce la operacion {OPERACION_PUBLICAR}"

    variables = {'tweet_text': texto}
    variables.update(FLAGS_OPERACION)
    if media_ids:
        variables['media'] = {
            'media_entities': [{'media_id': str(m)} for m in media_ids],
            'possibly_sensitive': False,
        }

    cuerpo = {'queryId': query_id, 'variables': variables}
    url = _url_operacion(OPERACION_PUBLICAR, query_id)

    for intento in (1, 2):
        try:
            respuesta = _peticion(url, datos=json.dumps(cuerpo).encode('utf-8'), metodo='POST',
                                   cabeceras=_cabeceras_x())
        except ConnectionError as error:
            return '', str(error)

        # X manda un ct0 nuevo cuando el que se manda ya no vale. Se coge y se
        # reintenta, que es lo que hace la web.
        if respuesta.estado == 403 and intento == 1:
            token_nuevo = _ct0_de_la_respuesta(respuesta)
            if token_nuevo and token_nuevo != CT0:
                log.info("  X ha renovado el token CSRF: se reintenta")
                CT0 = token_nuevo
                continue
            # Un 403 sin cuerpo suele ser que faltan las cookies de la web.
            log.info("  X devuelve 403: se refrescan las cookies de x.com y se reintenta")
            refrescar_cookies_web()
            continue

        if not respuesta.ok():
            if respuesta.estado == 403 and not respuesta.texto.strip():
                return '', ('X ha devuelto 403 sin explicacion. Suele ser que las cookies '
                            'de la sesion no coinciden con las que tiene la web: vuelve a '
                            'copiar auth_token y ct0 del navegador.')
            return '', f'HTTP {respuesta.estado}: {respuesta.texto[:300]}'

        datos = respuesta.json()
        mensaje_error = _errores_de_x(datos)
        if mensaje_error:
            if '(344)' in mensaje_error or 'daily limit' in mensaje_error:
                return '', ('CUOTA: X dice que la cuenta ha llegado al limite diario de '
                            'tweets y mensajes. Se espera y se reintenta.')
            if 'automated' in mensaje_error or '(226)' in mensaje_error:
                return '', ('X ha bloqueado la publicacion por sospecha de automatizacion '
                            '(226). Suele pasar con cuentas nuevas, sin verificar o con '
                            'pocas publicaciones: publica a mano un tweet desde el navegador '
                            'y espera unos minutos antes de reintentar.')
            return '', mensaje_error

        identificador = _extraer_id_post(datos)
        if identificador:
            return identificador, ''
        return '', f'la respuesta no traia id de post: {respuesta.texto[:300]}'

    return '', 'X devolvio 403 y no renovo el token CSRF'


# ─────────────────────────────────────────────
# TEXTO DEL POST
# ─────────────────────────────────────────────
LIMITE_POST = 280
LONGITUD_URL = 23  # X cuenta cualquier URL como 23 caracteres, la mida que tenga

_RE_URL = re.compile(r'https?://\S+')


def _peso_caracter(caracter):
    """X cuenta como 2 los caracteres de ancho doble y los emojis."""
    codigo = ord(caracter)
    if (
        0x1100 <= codigo <= 0x115F
        or 0x2E80 <= codigo <= 0xA4CF
        or 0xAC00 <= codigo <= 0xD7A3
        or 0xF900 <= codigo <= 0xFAFF
        or 0xFE30 <= codigo <= 0xFE6F
        or 0xFF00 <= codigo <= 0xFF60
        or 0xFFE0 <= codigo <= 0xFFE6
        or 0x1F300 <= codigo <= 0x1F64F
        or 0x1F680 <= codigo <= 0x1F6FF
        or 0x1F900 <= codigo <= 0x1F9FF
        or 0x1FA70 <= codigo <= 0x1FAFF
    ):
        return 2
    return 1


def longitud_post(texto):
    """Longitud del post segun las reglas de X (las URLs valen 23)."""
    total = 0
    posicion = 0
    for coincidencia in _RE_URL.finditer(texto):
        total += sum(_peso_caracter(c) for c in texto[posicion:coincidencia.start()])
        total += LONGITUD_URL
        posicion = coincidencia.end()
    total += sum(_peso_caracter(c) for c in texto[posicion:])
    return total


def _precio_es(precio):
    """'39.01 EUR' -> '39,01 EUR' y '1299.00 EUR' -> '1.299,00 EUR'.

    El catalogo guarda el precio con punto decimal y sin separador de miles,
    asi que el punto se cambia por coma y las miles se agrupan.
    """
    if not precio:
        return ''
    texto = re.sub(r'(?<=\d)\.(?=\d{2}\b)', ',', precio)

    def _miles(correspondencia):
        entero = '{:,}'.format(int(correspondencia.group(1))).replace(',', '.')
        return entero + correspondencia.group(2)

    return re.sub(r'(?<!\d)(\d{4,})(,\d{2})', _miles, texto)


def _limpiar_descripcion(descripcion):
    """Quita el final de Telegram y los textos de aviso que no aportan nada."""
    if not descripcion:
        return ''
    texto = re.sub(r'\s*Canal:\s*https?://\S+.*$', '', descripcion).strip()
    texto = re.sub(r'^(Publicidad/Enlace afiliado\s*)+', '', texto).strip()
    if 'El precio puede cambiar' in texto:
        texto = texto.split('El precio puede cambiar')[0].strip()
    if len(texto) < 15:
        return ''
    return texto


def _recortar(texto, maximo):
    """Recorta un texto a un numero de caracteres de peso (sin partir emojis)."""
    if longitud_post(texto) <= maximo:
        return texto
    salida = []
    total = 0
    for caracter in texto:
        peso = _peso_caracter(caracter)
        if total + peso > maximo - 1:
            break
        salida.append(caracter)
        total += peso
    return ''.join(salida).rstrip() + '…'


def _hashtags_de(oferta):
    etiquetas = [t for t in HASHTAGS_BASE.split() if t]
    etiqueta_categoria = HASHTAGS_CATEGORIA.get(oferta.get('categoria', ''), '')
    if etiqueta_categoria and etiqueta_categoria not in etiquetas:
        etiquetas.append(etiqueta_categoria)
    return ' '.join(etiquetas)


def componer_post(oferta):
    """Arma el texto del post a partir de una oferta del catalogo."""
    titulo = (oferta.get('title') or '').strip()
    precio = _precio_es((oferta.get('price') or '').strip())
    precio_antes = _precio_es((oferta.get('old_price') or '').strip())
    descuento = (oferta.get('discount') or '').strip()
    url = (oferta.get('amazon_url') or '').strip()
    descripcion = _limpiar_descripcion(oferta.get('description'))
    hashtags = _hashtags_de(oferta)

    # La linea de precios se arma con lo que haya: no todos los precios traen
    # descuento y algunos no traen precio anterior.
    precios = []
    if precio:
        precios.append(f'\U0001f4b8 {precio}')
    if precio_antes and precio_antes != precio:
        precios.append(f'(antes {precio_antes})')
    if descuento:
        precios.append(f'\U0001f4c9 {descuento}')
    linea_precios = ' | '.join(precios)

    def texto(descripcion_texto, titulo_texto):
        return PLANTILLA.format(
            titulo=titulo_texto,
            precios=linea_precios,
            precio=precio,
            precio_antes=precio_antes,
            descuento=descuento,
            url=url,
            descripcion=descripcion_texto,
            categoria=oferta.get('categoria', ''),
            hashtags=hashtags,
        )

    # El orden de recortes: primero la descripcion, que es lo mas prescindible,
    # luego el titulo, y los hashtags se conservan hasta el final.
    candidato = texto(descripcion, titulo)
    if longitud_post(candidato) <= LIMITE_POST:
        return candidato

    candidato = texto('', titulo)
    if longitud_post(candidato) <= LIMITE_POST:
        return candidato

    titulo_corto = _recortar(titulo, max(60, LIMITE_POST - longitud_post(texto('', '')) - 10))
    candidato = texto('', titulo_corto)
    if longitud_post(candidato) <= LIMITE_POST:
        return candidato

    # Ultimo recurso: quitar el precio anterior y acortar otra vez.
    precios_sin_antes = [p for p in precios if not p.startswith('(antes')]
    linea_precios = ' | '.join(precios_sin_antes)
    candidato = texto('', _recortar(titulo, 80))
    if longitud_post(candidato) <= LIMITE_POST:
        return candidato

    return _recortar(candidato, LIMITE_POST)


# ─────────────────────────────────────────────
# ESTADO: QUE SE HA PUBLICADO YA
# ─────────────────────────────────────────────
def leer_estado():
    if not ESTADO_PATH.exists():
        return {'publicados': {}}
    try:
        with open(ESTADO_PATH, encoding='utf-8') as _f:
            datos = json.load(_f)
    except (ValueError, OSError):
        return {'publicados': {}}
    if not isinstance(datos, dict):
        return {'publicados': {}}
    datos.setdefault('publicados', {})
    return datos


def guardar_estado(estado):
    try:
        with open(ESTADO_PATH, 'w', encoding='utf-8') as _f:
            json.dump(estado, _f, ensure_ascii=False, indent=2)
    except OSError as error:
        log.error(f"No se pudo guardar el estado: {error}")


def cargar_ofertas(archivo=None, categoria=None):
    """Lee las ofertas del catalogo, de mas reciente a mas antigua."""
    if archivo:
        ruta = Path(archivo)
    elif categoria:
        ruta = DATA_PATH / f'{categoria}.json'
    else:
        ruta = DATA_PATH / 'general.json'

    if not ruta.exists():
        log.error(f"No existe el archivo de ofertas: {ruta}")
        return []

    try:
        with open(ruta, encoding='utf-8') as _f:
            ofertas = json.load(_f)
    except (ValueError, OSError) as error:
        log.error(f"No se pudo leer {ruta}: {error}")
        return []

    if not isinstance(ofertas, list):
        log.error(f"{ruta} no contiene una lista de ofertas")
        return []

    ofertas.sort(key=lambda o: o.get('id', 0), reverse=True)
    return ofertas


# ─────────────────────────────────────────────
# MODO VERIFICAR: LEER LOS ULTIMOS POSTS
# ─────────────────────────────────────────────
def ultimos_posts(operaciones, usuario, cantidad=20):
    """Lee los ultimos posts de la cuenta. Devuelve [(id, texto)]."""
    if not usuario:
        return []
    query_id = operaciones.get(OPERACION_LEER)
    if not query_id:
        log.warning(f"No se conoce la operacion {OPERACION_LEER}: no se pueden leer los posts")
        return []

    variables = {'screenName': usuario, 'count': cantidad}
    url = (f'{_url_operacion(OPERACION_LEER, query_id)}?variables='
           + urllib.parse.quote(json.dumps(variables, separators=(',', ':'))))
    try:
        respuesta = _peticion(url, cabeceras=_cabeceras_x(json_body=False))
    except ConnectionError as error:
        log.error(f"No se pudieron leer los posts: {error}")
        return []

    if not respuesta.ok():
        log.error(f"X devolvio HTTP {respuesta.estado} al leer los posts: {respuesta.texto[:300]}")
        return []

    datos = respuesta.json() or {}
    encontrados = []
    for instruccion in _instrucciones(datos):
        for entrada in instruccion.get('entries', []) or []:
            resultado = _post_de_entrada(entrada)
            if resultado:
                encontrados.append(resultado)
    return encontrados


def _instrucciones(datos):
    """Saca la lista de instrucciones del timeline, sea del formato viejo o nuevo."""
    if not isinstance(datos, dict):
        return []
    datos = datos.get('data', datos)
    candidatos = [
        datos.get('user_result_by_screen_name'),
        datos.get('user'),
        datos.get('user_result'),
    ]
    for candidato in candidatos:
        if not isinstance(candidato, dict):
            continue
        resultado = candidato.get('result', candidato)
        if not isinstance(resultado, dict):
            continue
        for clave in ('profile_with_replies_timeline_v2', 'profile_with_timeline_v2', 'timeline_v2'):
            linea = resultado.get(clave)
            if isinstance(linea, dict):
                linea = linea.get('timeline')
            if isinstance(linea, dict):
                linea = linea.get('timeline')
            if isinstance(linea, dict) and linea.get('instructions'):
                return linea['instructions']
    return []


def _post_de_entrada(entrada):
    """Extrae (id, texto) de una entrada del timeline."""
    if not isinstance(entrada, dict):
        return None
    contenido = entrada.get('content') or {}
    item = (contenido.get('itemContent') or {}).get('tweet_results') or {}
    resultado = item.get('result')
    if not isinstance(resultado, dict):
        return None
    identificador = resultado.get('rest_id') or resultado.get('id_str')
    if not identificador:
        return None
    texto = ''
    legado = resultado.get('legacy')
    if isinstance(legado, dict):
        texto = legado.get('full_text', '')
    if not texto:
        texto = resultado.get('text', '') or resultado.get('full_text', '')
    return (str(identificador), texto)


# ─────────────────────────────────────────────
# PROGRAMA
# ─────────────────────────────────────────────
def revisar_sesion(operaciones):
    """Comprueba que las credenciales y los ids sirven. No publica nada."""
    print('\n== Sesion de X ==')
    if AUTH_TOKEN:
        print(f'  auth_token  : presente ({AUTH_TOKEN[:6]}...{AUTH_TOKEN[-4:]})')
    else:
        print('  auth_token  : FALTA (ponlo en el .env como X_AUTH_TOKEN)')
    print(f'  ct0         : {"presente" if CT0 else "se pedira a X"}')
    print(f'  usuario     : {("@" + USUARIO) if USUARIO else "(sin definir)"}')
    print(f'  bearer      : {"presente" if BEARER else "no se ha podido leer"}')

    print('\n== Operaciones ==')
    if not operaciones:
        print('  No se pudo descubrir ninguna operacion.')
        print('  X cambio el JavaScript: revisa https://x.com y copia el id a mano')
        print('  en el .env como X_QUERY_IDS=createTweetMutation=<id>.')
    for operacion, identificador in operaciones.items():
        print(f'  {operacion:22} {identificador}')

    if not USUARIO:
        print('\n  Pon X_USUARIO en el .env para poder leer los ultimos posts.')
        return
    if not operaciones.get(OPERACION_LEER):
        return
    posts = ultimos_posts(operaciones, USUARIO)
    print(f'\n== Cuenta ==\n  ultimos posts leidos: {len(posts)}')
    for identificador, texto in posts[:5]:
        print(f'    {identificador}: {(texto or "")[:70]}')
    print()


def seleccionar_pendientes(ofertas, publicados, limite):
    """Ofertas todavia no publicadas, de la mas reciente a la mas antigua."""
    pendientes = []
    for oferta in ofertas:
        identificador = str(oferta.get('id', ''))
        if not identificador or identificador in publicados:
            continue
        if not (oferta.get('title') or '').strip() or not (oferta.get('amazon_url') or '').strip():
            continue
        if SOLO_ID_MIN and oferta.get('id', 0) <= SOLO_ID_MIN:
            continue
        pendientes.append(oferta)
        if len(pendientes) >= limite:
            break
    return pendientes


def simular(argumentos):
    """Enseña como quedarian los posts sin publicar nada. No necesita red."""
    ofertas = cargar_ofertas(archivo=argumentos.archivo, categoria=argumentos.categoria)
    if not ofertas:
        return 1

    estado = leer_estado()
    publicados = estado.get('publicados', {})
    pendientes = seleccionar_pendientes(ofertas, publicados, argumentos.limite)
    log.info(f"{len(pendientes)} ofertas pendientes (de {len(ofertas)} en el catalogo)")

    for oferta in pendientes:
        texto = componer_post(oferta)
        print('\n' + '-' * 56)
        print(texto)
        print(f"[longitud: {longitud_post(texto)}/280]")
    return 0


def main():
    analizador = argparse.ArgumentParser(
        description='Publica las ofertas del catalogo en X (Twitter).')
    analizador.add_argument('--limite', type=int, default=LIMITE_TWEETS,
                            help=f'cuantas ofertas publicar como maximo (por defecto {LIMITE_TWEETS})')
    analizador.add_argument('--categoria', help='publicar solo una categoria (data/<categoria>.json)')
    analizador.add_argument('--archivo', help='publicar las ofertas de un archivo JSON concreto')
    analizador.add_argument('--simular', action='store_true',
                            help='enseñar como quedarian los posts sin publicar nada')
    analizador.add_argument('--sin-imagen', action='store_true', help='publicar sin imagen')
    analizador.add_argument('--revisar', action='store_true',
                            help='comprobar la sesion y los ids de operacion, sin publicar')
    analizador.add_argument('--verificar', action='store_true',
                            help='leer los ultimos posts de la cuenta y sincronizar el estado')
    analizador.add_argument('--refrescar-cache', action='store_true',
                            help='buscar otra vez los ids de operacion en el JavaScript de X')
    argumentos = analizador.parse_args()

    if argumentos.simular:
        # El simulador no necesita sesion ni red: solo compone los textos.
        return simular(argumentos)

    if not AUTH_TOKEN:
        log.error("Falta X_AUTH_TOKEN. Copia la cookie auth_token de x.com (DevTools > "
                  "Application > Cookies > https://x.com) y ponla en el .env.")
        return 1

    obtener_ct0()
    refrescar_cookies_web()
    operaciones = descubrir_operaciones(forzar=argumentos.refrescar_cache)

    if argumentos.revisar:
        revisar_sesion(operaciones)
        return 0

    if argumentos.verificar:
        if not USUARIO:
            print("Falta X_USUARIO en el .env: no se sabe que cuenta leer.")
            return 1
        posts = ultimos_posts(operaciones, USUARIO)
        if not posts:
            print("No se pudieron leer los posts de la cuenta.")
            return 1
        print(f"\nUltimos {len(posts)} posts de la cuenta:\n")
        for identificador, texto in posts:
            print(f"  https://x.com/{USUARIO}/status/{identificador}")
            print(f"    {(texto or '').replace(chr(10), ' ')}\n")
        return 0

    ofertas = cargar_ofertas(archivo=argumentos.archivo, categoria=argumentos.categoria)
    if not ofertas:
        return 1

    estado = leer_estado()
    publicados = estado.get('publicados', {})
    pendientes = seleccionar_pendientes(ofertas, publicados, argumentos.limite)
    log.info(f"{len(pendientes)} ofertas pendientes de publicar (de {len(ofertas)} en el catalogo)")

    if not pendientes:
        print("No hay ofertas nuevas que publicar.")
        return 0

    con_imagen = CON_IMAGEN and not argumentos.sin_imagen
    publicados_ahora = 0

    for indice, oferta in enumerate(pendientes, 1):
        identificador = str(oferta.get('id', ''))
        texto = componer_post(oferta)
        log.info(f"[{indice}/{len(pendientes)}] Oferta {identificador}: {oferta.get('title', '')[:60]!r}")
        log.info(f"  Texto ({longitud_post(texto)}/280): {texto[:90]!r}")

        media_ids = []
        if con_imagen and oferta.get('image'):
            media_id = subir_imagen(oferta['image'])
            if media_id:
                media_ids.append(media_id)

        id_post = ''
        error = ''
        for intento_cuota in range(REINTENTOS_CUOTA + 1):
            id_post, error = publicar(texto, media_ids=media_ids, operaciones=operaciones)
            if id_post:
                break

            # X dice que la cuenta se ha pasado de tweets y mensajes por hoy.
            # No es un fallo del script: se espera y se reintenta la misma.
            if error.startswith('CUOTA'):
                if intento_cuota >= REINTENTOS_CUOTA:
                    log.error(f"  Se agotaron los reintentos de cuota: {error}")
                    break
                log.warning(f"  {error}")
                log.warning(f"  Se espera {ESPERA_CUOTA}s y se reintenta la misma oferta")
                time.sleep(ESPERA_CUOTA)
                continue

            log.error(f"  No se pudo publicar la oferta {identificador}: {error}")
            # Si X no reconoce la operacion, los ids estan caducados: se buscan
            # otra vez y se reintenta una vez.
            if 'Unknown' in error or 'not found' in error.lower() or 'no se conoce' in error:
                log.warning("  Los ids de operacion pueden estar caducados: se buscan otra vez")
                operaciones = descubrir_operaciones(forzar=True)
                id_post, error = publicar(texto, media_ids=media_ids, operaciones=operaciones)
                if not id_post:
                    log.error(f"  Sigue sin publicarse: {error}")
            break

        if not id_post:
            break

        publicados_ahora += 1
        publicados[identificador] = {
            'tweet_id': id_post,
            'fecha': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'titulo': oferta.get('title', ''),
        }
        estado['publicados'] = publicados
        estado['ultimo'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        guardar_estado(estado)
        log.info(f"  Publicado: https://x.com/{USUARIO or 'i'}/status/{id_post}")

        if indice < len(pendientes):
            log.info(f"  Pausa de {PAUSA_SEGUNDOS}s antes del siguiente post")
            time.sleep(PAUSA_SEGUNDOS)

    print(f"\nPublicados {publicados_ahora} de {len(pendientes)} pendientes.")
    return 0 if publicados_ahora else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log.warning("Interrumpido por el usuario")
        sys.exit(130)

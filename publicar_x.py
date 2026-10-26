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
llaman con un id numerico sino con ids de Relay (`wR5Z_lEibLvkew3tF9w-Sg`) y
se piden a `api.x.com/graphql/<id>/<operacion>`. Por eso el script busca los
ids en el propio JavaScript de x.com, los guarda en cache y los vuelve a
buscar cuando X responde que no conoce la operacion.

De la publicacion hay dos mutaciones: la que usa la web de ahora
(`CreateTweet`) y la del camino antiguo de la API (`createTweetMutation`).
Cada una tiene sus propias reglas y X no las aplica igual: una puede
responder que la peticion parece automatica (226) mientras la otra va bien.
Por eso el script prueba las dos antes de rendirse.

Uso
----
    python3 publicar_x.py                 # una oferta en cada franja, todos los dias
    python3 publicar_x.py --ahora         # publica ya las pendientes, sin esperar
    python3 publicar_x.py --simular       # ensaya sin publicar nada
    python3 publicar_x.py --limite 3      # como mucho 3 esta vez
    python3 publicar_x.py --horas 09:00,13:00,18:00,21:30
    python3 publicar_x.py --categoria gaming-consolas
    python3 publicar_x.py --revisar       # comprueba la sesion y los ids
    python3 publicar_x.py --verificar     # lista los ultimos posts y sincroniza

Por defecto el script se queda corriendo y publica una oferta en cada franja
(08:00, 12:00, 17:00 y 21:00, configurable con X_HORAS). Si arranca cuando una
franja ya ha pasado, la salta y sigue con la siguiente. Con --ahora vuelve al
comportamiento de antes: publica las pendientes seguidas, con la pausa de
seguridad entre una y otra.

El post principal va sin enlaces: se publican en una respuesta al propio post,
porque X resta alcance a los posts que llevan enlaces. Con --enlace-en-post
vuelven al post principal.

Las franjas se leen en la zona X_ZONA (Europe/Madrid por defecto), no en la
hora del sistema: en Termux el reloj suele estar en UTC. Para dejarlo corriendo
en Android: termux-wake-lock y tmux o nohup. El proceso ignora SIGHUP, asi que
cerrar la terminal no lo para; se para con Ctrl+C o kill.
"""

import argparse
import concurrent.futures
import hashlib
import json
import logging
import os
import random
import re
import signal
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9
    ZoneInfo = None

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


def _parsear_horas(bruto, por_defecto=(8 * 60, 12 * 60, 17 * 60, 21 * 60)):
    """Convierte '08:00,12:00,17:00,21:00' en minutos desde medianoche.

    Se ignoran los trozos que no tengan forma HH:MM o que se salgan de rango.
    Si no queda ninguna hora valida se usan las de por defecto.
    """
    minutos = []
    for trozo in str(bruto or '').split(','):
        trozo = trozo.strip()
        if not trozo:
            continue
        coincidencia = re.fullmatch(r'(\d{1,2}):(\d{2})', trozo)
        if not coincidencia:
            log.warning(f"Franja horaria no valida: {trozo!r} (se ignora)")
            continue
        hora, minuto = int(coincidencia.group(1)), int(coincidencia.group(2))
        if hora > 23 or minuto > 59:
            log.warning(f"Franja horaria fuera de rango: {trozo!r} (se ignora)")
            continue
        total = hora * 60 + minuto
        if total not in minutos:
            minutos.append(total)
    if not minutos:
        log.warning("No hay franjas horarias validas: se usan las de por defecto")
        minutos = list(por_defecto)
    return sorted(minutos)


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

# La ultima operacion con la que X dejo pasar un post. Se guarda en el estado
# para probar esa primero la proxima vez: X no aplica las mismas reglas a las
# dos mutaciones y cambia segun la cuenta y el dia.
ULTIMA_OPERACION = ''

# Ids de las operaciones, si se ponen a mano: "nombre=id,nombre=id". Tiene
# prioridad sobre el descubrimiento automatico.
QUERY_IDS_MANUALES = os.getenv('X_QUERY_IDS', '').strip()

LIMITE_TWEETS   = _leer_int('X_MAX_TWEETS', 5)      # por ejecucion inmediata
# Entre un post y el siguiente. X no deja publicar dos seguidos: con 90 s de
# pausa la segunda salia con el error 226 ("parece automatica"). El ritmo que
# aguanta es de minutos.
PAUSA_SEGUNDOS  = _leer_int('X_PAUSA_SEGUNDOS', 600)
ESPERA_CUOTA    = _leer_int('X_ESPERA_CUOTA', 1800)   # cuando la cuenta se pasa de tweets
REINTENTOS_CUOTA = _leer_int('X_REINTENTOS_CUOTA', 8)  # veces que se reintenta tras la espera
# La respuesta con el enlace se reintenta menos: si la cuota esta agotada, el
# post principal ya salio y no conviene bloquear la siguiente franja 4 horas.
REINTENTOS_CUOTA_RESPUESTA = _leer_int('X_REINTENTOS_CUOTA_RESPUESTA', 1)
# Cuando X dice que la peticion parece automatica (226). Suele ser que se ha
# publicado hace poco: esperando un rato entra. Se reintenta menos veces que
# la cuota, porque repetir mucho tambien se ve mal.
ESPERA_AUTOMATIZACION = _leer_int('X_ESPERA_AUTOMATIZACION', 900)
REINTENTOS_AUTOMATIZACION = _leer_int('X_REINTENTOS_AUTOMATIZACION', 3)
TIMEOUT         = _leer_int('X_TIMEOUT', 30)
CON_IMAGEN      = _leer_bool('X_CON_IMAGEN', True)
SOLO_ID_MIN     = _leer_int('X_SOLO_ID_MIN', 0)      # solo ofertas con id > este

# Franjas horarias de la publicacion programada: una oferta en cada una.
# Se pueden cambiar en el .env con X_HORAS="08:00,12:00,17:00,21:00".
_horas_env = str(os.getenv('X_HORAS', '') or '').strip()
HORAS = _parsear_horas(_horas_env) if _horas_env else [8 * 60, 12 * 60, 17 * 60, 21 * 60]
# Si el script arranca justo despues de una franja, se considera que todavia
# llega a ella durante estos segundos. Pasado ese margen, la franja se salta.
MARGEN_FRANJA = _leer_int('X_MARGEN_FRANJA', 120)

# Zona horaria de las franjas. En Termux el reloj del sistema suele estar en
# UTC, asi que sin esto las 08:00 serian las 10:00 en Espana en verano. Se
# puede cambiar con X_ZONA. Si falta la base de datos de zonas (tzdata), se
# usa la hora del sistema y se avisa en el log.
ZONA = str(os.getenv('X_ZONA', 'Europe/Madrid') or '').strip()
_ZONA = None
if ZONA:
    if ZoneInfo is None:
        log.warning("zoneinfo no esta disponible: se usa la hora del sistema")
    else:
        try:
            _ZONA = ZoneInfo(ZONA)
        except Exception:
            log.warning(f"No se pudo cargar la zona horaria {ZONA!r}: se usa la hora "
                        "del sistema. En Termux, instala tzdata: pkg install tzdata")


def ahora_local():
    """La hora de pared en la zona configurada, sin informacion de zona.

    Se quita el tzinfo para que las comparaciones con las franjas (que son
    horas locales) sean directas.
    """
    if _ZONA is not None:
        return datetime.now(_ZONA).replace(tzinfo=None)
    return datetime.now()

# El texto que se publica. Se puede cambiar entero por el .env; los campos
# disponibles son {titulo} {precio} {precio_antes} {descuento} {precios}
# {pregunta} {url} {enlaces} {descripcion} {categoria} {hashtags}.
#
# El orden es el que se pidio: primero los precios, luego la pregunta, luego
# el titulo con la descripcion y al final los enlaces (o nada, si los enlaces
# van en la respuesta). Los hashtags van con la descripcion.
PLANTILLA = (os.getenv('X_PLANTILLA', '') or '').replace('\\n', '\n') or (
    "{precios}\n"
    "\n"
    "{pregunta}\n"
    "\n"
    "{titulo}\n"
    "\n"
    "{descripcion}\n"
    "\n"
    "{hashtags}\n"
    "\n"
    "{enlaces}"
)

# Los enlaces van en una respuesta al post, no en el post principal: X resta
# alcance a los posts que llevan enlaces. Con X_ENLACE_RESPUESTA=0 vuelven al
# post principal (comportamiento antiguo).
ENLACE_EN_RESPUESTA = _leer_bool('X_ENLACE_RESPUESTA', True)
# Segundos entre el post principal y la respuesta con el enlace. Dos posts
# seguidos pueden disparar el 226 ("parece automatico").
PAUSA_RESPUESTA = _leer_int('X_PAUSA_RESPUESTA', 30)
# Texto de la respuesta. Campos: {intro} {enlaces} {url} {titulo} {precio}.
PLANTILLA_RESPUESTA = (
    (os.getenv('X_PLANTILLA_RESPUESTA', '') or '').replace('\\n', '\n')
    or "\U0001f517 {intro}\n\n{enlaces}"
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
#
# La web de X (la de 2025 en adelante) llama a las operaciones por su nombre de
# Relay: CreateTweet para publicar, UserTweets para leer el perfil y
# UserByScreenName para buscar la cuenta. La mutacion antigua
# (createTweetMutation) sigue viva, pero es la que usa el camino viejo de la
# API: cuando la cuenta se pasa de tweets por el dia, esa es la que responde con
# el error 344 de "limite diario". Por eso se usa la de ahora, y la vieja solo
# como recurso si la nueva no aparece en el JavaScript de X.
OPERACION_PUBLICAR = 'CreateTweet'
OPERACION_LEER = 'UserTweets'
OPERACION_USUARIO = 'UserByScreenName'
# La mutacion vieja, por si la nueva no se encuentra.
OPERACION_PUBLICAR_VIEJA = 'createTweetMutation'
# El id de la mutacion vieja. Ya no sale del JavaScript de x.com (la web usa la
# de ahora), pero el camino sigue vivo: es el que responde con el error 344 de
# limite diario en vez de quejarse de la automatizacion. Si X lo rota, se
# sustituye aqui o en el .env con X_QUERY_IDS=createTweetMutation=<id>.
ID_PUBLICAR_VIEJA = 'ewPB3lRszYIJIpDvJ8dLCQ'

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
# alguna, X responde con un 422 diciendo cual falta.
#
# Esto es solo para la mutacion vieja (createTweetMutation): la de ahora
# (CreateTweet) lleva las banderas en el parametro `features` del cuerpo, y
# el script las saca del propio JavaScript de x.com, asi que no hay que
# mantener una lista a mano.
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


def _operacion_de_x(texto, operacion):
    """Saca una operacion del JavaScript de x.com en el formato de ahora.

    La web de 2025 en adelante declara cada operacion asi:
        e.exports={queryId:"wR5Z_lEibLvkew3tF9w-Sg",operationName:"CreateTweet",
                   operationType:"mutation",
                   metadata:{featureSwitches:["flag1","flag2"],fieldToggles:["withAlgo"]}}

    Los feature switches son la lista de banderas que la web activa para esa
    operacion: hay que mandarlas en la peticion (van en el parametro `features`
    del cuerpo) o X responde con un 422 diciendo cual falta.

    Devuelve {queryId, operationName, operationType, featureSwitches,
    fieldToggles} o None si la operacion no aparece.
    """
    patron = re.compile(
        r'queryId:"([^"]+)",operationName:"' + re.escape(operacion) + r'",operationType:"(\w+)"'
        r'(?:,metadata:\{featureSwitches:\[([^\]]*)\],fieldToggles:\[([^\]]*)\]\})?')
    coincidencia = patron.search(texto)
    if not coincidencia:
        return None

    def _lista(bruto):
        return [x.strip().strip('"') for x in (bruto or '').split(',') if x.strip()]

    return {
        'queryId': coincidencia.group(1),
        'operationName': operacion,
        'operationType': coincidencia.group(2),
        'featureSwitches': _lista(coincidencia.group(3)),
        'fieldToggles': _lista(coincidencia.group(4)),
    }


def _normalizar_operacion(nombre, dato):
    """Normaliza una operacion a dict, venga como dict o como id suelto.

    Las caches viejas guardaban solo el id: ese formato se sigue aceptando.
    """
    if isinstance(dato, dict):
        base = {
            'queryId': dato.get('queryId', ''),
            'operationName': dato.get('operationName', nombre),
            'operationType': dato.get('operationType', ''),
            'featureSwitches': list(dato.get('featureSwitches') or []),
            'fieldToggles': list(dato.get('fieldToggles') or []),
        }
        return base if base['queryId'] else None
    if isinstance(dato, str) and dato:
        return {'queryId': dato, 'operationName': nombre, 'operationType': '',
                'featureSwitches': [], 'fieldToggles': []}
    return None


def _bearer_de(texto):
    """El bearer token va dentro del propio JavaScript de X."""
    coincidencia = re.search(r'Bearer\s+([A-Za-z0-9%\-_=]{40,})', texto)
    return coincidencia.group(1) if coincidencia else ''


def descubrir_operaciones(forzar=False):
    """Devuelve {operacion: {queryId, operationName, ...}} para publicar y para leer.

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
            return {n: _normalizar_operacion(n, d) for n, d in manual.items()}

    cache = _leer_cache()
    fecha = cache.get('fecha', 0)
    caducada = (time.time() - fecha) > DIAS_CACHE * 86400
    if not forzar and not caducada and cache.get('operaciones'):
        vence = time.strftime('%Y-%m-%d', time.localtime(fecha + DIAS_CACHE * 86400))
        log.info(f"Operaciones de la cache (vigente hasta {vence})")
        BEARER = BEARER or cache.get('bearer', '')
        return {n: _normalizar_operacion(n, d) for n, d in cache['operaciones'].items()}

    log.info("Buscando los ids de operacion en el JavaScript de x.com")

    # 1. La portada da el bundle de entrada. De ahi se siguen los imports un
    #    par de niveles: los bundles que se llaman "startup" son los grandes y
    #    son los que llevan la lista de assets y el token.
    entradas = _scripts_de_x()
    if not entradas:
        return {n: _normalizar_operacion(n, d) for n, d in cache.get('operaciones', {}).items()}

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
        return {n: _normalizar_operacion(n, d) for n, d in cache.get('operaciones', {}).items()}

    if not BEARER or forzar or caducada:
        encontrado = ''
        for texto in todos.values():
            encontrado = _bearer_de(texto)
            if encontrado:
                log.info("  bearer token leido del JavaScript de x.com")
                break
        if encontrado:
            BEARER = encontrado

    # 2. La lista de assets la lleva el bundle grande: de ahi se sacan los
    #    nombres de los ficheros que pueden tener la mutacion de publicar.
    assets = set()
    for texto in todos.values():
        assets |= set(re.findall(r'"(assets/[^"]+\.js)"', texto))
    log.info(f"  x.com tiene {len(assets)} assets")

    operaciones = {}
    juntos = '\n'.join(todos.values())
    nombres = (OPERACION_PUBLICAR, OPERACION_LEER, OPERACION_USUARIO,
               OPERACION_PUBLICAR_VIEJA)

    # Primero el formato de ahora: queryId + operationName + feature switches.
    for nombre in nombres:
        encontrada = _operacion_de_x(juntos, nombre)
        if encontrada:
            operaciones[nombre] = encontrada

    # Y si no aparece, el formato viejo (params:{id:...}).
    for nombre in nombres:
        if nombre in operaciones:
            continue
        identificador = _id_de_operacion(juntos, nombre)
        if identificador:
            operaciones[nombre] = _normalizar_operacion(nombre, identificador)

    faltan = [o for o in nombres if o not in operaciones]
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
                    encontrada = _operacion_de_x(texto, operacion)
                    if encontrada:
                        operaciones[operacion] = encontrada
                        continue
                    identificador = _id_de_operacion(texto, operacion)
                    if identificador:
                        operaciones[operacion] = _normalizar_operacion(operacion, identificador)
            if not [o for o in faltan if o not in operaciones]:
                break

    for nombre, operacion in operaciones.items():
        log.info(f"  {nombre} -> {operacion['queryId']}")
    for nombre in (OPERACION_PUBLICAR, OPERACION_LEER):
        if nombre not in operaciones:
            log.warning(f"  {nombre}: no aparece en los JavaScript de x.com")

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


def _url_operacion(nombre, query_id):
    """URL de la operacion.

    La web nueva usa api.x.com/graphql con ids de Relay. La antigua usaba
    x.com/i/api/graphql con ids numericos: si el id parece numerico, se usa
    la ruta antigua, que sigue viva.
    """
    if query_id.isdigit():
        return f'https://x.com/i/api/graphql/{query_id}/{nombre}'
    return f'{HOSTO_GRAPHQL}/{query_id}/{nombre}'


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


def _variables_publicar(texto, media_ids, reply_to=''):
    """Las variables que la web manda al publicar.

    La web de ahora construye el post asi: el texto, las imagenes que se
    adjuntan y un par de campos que siempre van (aunque valgan vacio). Para
    responder a otro post se anade `reply` con el id del original.
    """
    variables = {
        'tweet_text': texto,
        'media': {
            'media_entities': [{'media_id': str(m)} for m in (media_ids or [])],
            'possibly_sensitive': False,
        },
        'semantic_annotation_ids': [],
        'disallowed_reply_options': None,
    }
    if reply_to:
        variables['reply'] = {
            'in_reply_to_tweet_id': str(reply_to),
            'exclude_reply_user_ids': [],
        }
    return variables


def _cuerpo_publicar(operacion, variables):
    """El cuerpo de la peticion, segun el formato de la operacion.

    La web de ahora manda las variables como un objeto normal y las banderas
    (los feature switches) aparte, en `features` y `fieldToggles`. La mutacion
    vieja las queria dentro de las variables, con el nombre largo.
    """
    cuerpo = {'variables': dict(variables), 'queryId': operacion['queryId']}
    if operacion.get('featureSwitches'):
        cuerpo['features'] = {f: True for f in operacion['featureSwitches']}
    if operacion.get('fieldToggles'):
        cuerpo['fieldToggles'] = {t: True for t in operacion['fieldToggles']}
    if not operacion.get('featureSwitches'):
        # Mutacion vieja: las banderas van dentro de las variables.
        cuerpo['variables'].update(FLAGS_OPERACION)
    return cuerpo


def _operaciones_publicar(operaciones, preferida=''):
    """Las operaciones con las que se puede publicar, en orden de preferencia.

    La de ahora (CreateTweet) es la que usa la web, pero X la marca como
    "automatica" a veces. La vieja (createTweetMutation) es la del camino
    antiguo de la API: responde con el error 344 de limite diario, pero no se
    queja de la automatizacion. Por eso se prueban las dos: cada una tiene sus
    propias reglas y X no las aplica igual.

    La de ahora va siempre primera. La vieja queda de reserva si la nueva falla
    con 226/344, pero no se pone delante aunque fuese la ultima que funciono:
    en octubre de 2026 devolvio un id de un post que X luego no mostraba.
    """
    lista = []
    moderna = _normalizar_operacion(OPERACION_PUBLICAR, operaciones.get(OPERACION_PUBLICAR))
    if moderna:
        lista.append(moderna)
    vieja = _normalizar_operacion(OPERACION_PUBLICAR_VIEJA,
                                  operaciones.get(OPERACION_PUBLICAR_VIEJA))
    if not vieja:
        # La mutacion vieja no sale del JavaScript de ahora (la web ya no la
        # usa), pero sigue viva: se guarda su id aqui y se puede reponer con
        # X_QUERY_IDS=createTweetMutation=<id> en el .env.
        vieja = _normalizar_operacion(OPERACION_PUBLICAR_VIEJA, ID_PUBLICAR_VIEJA)
    if vieja:
        lista.append(vieja)
    if preferida == OPERACION_PUBLICAR_VIEJA:
        log.warning("La mutacion vieja fue la ultima que funciono, pero se prueba "
                    "primero CreateTweet: la vieja puede publicar un post no visible.")
    return lista


def _publicar_con(operacion, variables):
    """Manda el post con una operacion concreta. Devuelve (id_del_post, error)."""
    global CT0
    cuerpo = _cuerpo_publicar(operacion, variables)
    url = _url_operacion(operacion['operationName'], operacion['queryId'])

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
                return '', ('AUTOMATIZACION: X dice que la peticion parece automatica '
                            '(226).')
            if '(186)' in mensaje_error or 'shorter' in mensaje_error:
                return '', 'X dice que el texto es demasiado largo (186).'
            if '(170)' in mensaje_error:
                return '', 'X no ha recibido bien el texto o la imagen (170).'
            return '', mensaje_error

        identificador = _extraer_id_post(datos)
        if identificador:
            return identificador, ''
        return '', f'la respuesta no traia id de post: {respuesta.texto[:300]}'

    return '', 'X devolvio 403 y no renovo el token CSRF'


def publicar(texto, media_ids=None, operaciones=None, preferida='', reply_to=''):
    """Publica un post en X y devuelve (id_del_post, error).

    Si `reply_to` lleva el id de otro post, se publica como respuesta a ese.
    """
    global ULTIMA_OPERACION
    candidatas = _operaciones_publicar(operaciones or {}, preferida)
    if not candidatas:
        return '', f"no se conoce la operacion {OPERACION_PUBLICAR}"

    variables = _variables_publicar(texto, media_ids, reply_to=reply_to)
    error = ''
    for indice, operacion in enumerate(candidatas):
        identificador, error = _publicar_con(operacion, variables)
        if identificador:
            ULTIMA_OPERACION = operacion['operationName']
            return identificador, ''

        # Si X dice que la peticion parece automatica, se prueba con la otra
        # operacion: X no aplica las mismas reglas a las dos.
        if error.startswith('AUTOMATIZACION') and indice + 1 < len(candidatas):
            log.warning(f"  {operacion['operationName']}: {error}")
            log.info(f"  Se prueba con {candidatas[indice + 1]['operationName']}")
            continue
        break

    if error.startswith('AUTOMATIZACION'):
        error += (' No conviene reintentar seguido: publica a mano un tweet desde '
                  'el navegador y espera unos minutos.')
    return '', error


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

    texto = re.sub(r'(?<!\d)(\d{4,})(,\d{2})', _miles, texto)
    # "9,99€" -> "9,99 €": el simbolo siempre separado, para que todos los
    # precios se lean igual.
    return re.sub(r'\s*\u20ac', ' \u20ac', texto).strip()


def _limpiar_descripcion(descripcion):
    """Quita el final de Telegram y los textos de aviso que no aportan nada."""
    if not descripcion:
        return ''
    texto = re.sub(r'\s*Canal:\s*https?://\S+.*$', '', descripcion).strip()
    texto = re.sub(r'^(Publicidad/Enlace afiliado\s*)+', '', texto).strip()
    if 'El precio puede cambiar' in texto:
        texto = texto.split('El precio puede cambiar')[0].strip()
    # "Ropa y calzado Precio recomendado: 59,95 € 31,95 €" no es una
    # descripcion: es la categoria y los precios, que ya van en el bloque de
    # arriba. Se descarta para no repetirlos.
    if re.fullmatch(
        r'(?:[^:\n.!?]{0,40}\s+)?precio\s+'
        r'(?:recomendado|m[aá]s\s+bajo|mediano|habitual|anterior)\s*:.*',
        texto, re.I | re.S,
    ):
        return ''
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


# Preguntas que se intercalan entre los precios y la descripcion. Son las que
# pidio el usuario y unas cuantas mas del mismo tono. Se elige una al azar por
# post, evitando repetir la anterior.
PREGUNTAS = [
    '🤔 ¿Qué te parece?',
    '👀 ¿Lo vas a dejar pasar?',
    '🔥 ¿Te atreves?',
    '🛒 ¿Se viene a casa?',
    '💭 ¿Lo comprarías?',
    '⏳ ¿Aprovechas o lo dejas?',
    '😱 ¿Precio real o error?',
    '🙋 ¿Quién se lo lleva?',
]
_ULTIMA_PREGUNTA = ''


def pregunta_aleatoria():
    """Una pregunta distinta de la anterior, para no repetir en posts seguidos."""
    global _ULTIMA_PREGUNTA
    opciones = [p for p in PREGUNTAS if p != _ULTIMA_PREGUNTA] or list(PREGUNTAS)
    elegida = random.choice(opciones)
    _ULTIMA_PREGUNTA = elegida
    return elegida


def _enlaces_de(oferta):
    """Las URLs del post, sin repetir.

    El catalogo trae `amazon_url`; si alguna oferta trae ademas `url`,
    `enlace`, `links` o `enlaces`, se anaden detras. `X_ENLACE_EXTRA` permite
    sumar un enlace fijo (por ejemplo, la web) sin tocar el catalogo.
    """
    urls = []
    for clave in ('amazon_url', 'url', 'enlace', 'links', 'enlaces'):
        valor = oferta.get(clave)
        if isinstance(valor, str):
            candidatos = [valor]
        elif isinstance(valor, (list, tuple, set)):
            candidatos = list(valor)
        else:
            continue
        for candidato in candidatos:
            candidato = str(candidato or '').strip()
            if candidato and candidato not in urls:
                urls.append(candidato)
    extra = str(os.getenv('X_ENLACE_EXTRA', '') or '').strip()
    if extra and extra not in urls:
        urls.append(extra)
    return urls


def _precios_de_descripcion(descripcion):
    """Saca (precio anterior, precio actual) del texto de Telegram.

    Los mensajes del canal muchas veces traen "Precio recomendado: 9,99 €
    7,45 €" aunque el catalogo se haya quedado sin `old_price`. El primer
    importe es el anterior y el segundo el actual.
    """
    coincidencia = re.search(
        r'precio\s+(?:recomendado|m[aá]s\s+bajo|mediano|habitual|anterior)\s*:\s*'
        r'([\d.,]+\s*\u20ac)\s+([\d.,]+\s*\u20ac)',
        descripcion or '', re.I,
    )
    if not coincidencia:
        return '', ''
    return coincidencia.group(1).strip(), coincidencia.group(2).strip()


def _mismo_precio(uno, otro):
    """Compara dos precios salvando los espacios ('9,99 €' y '9,99€')."""
    return _precio_es(uno).replace(' ', '') == _precio_es(otro).replace(' ', '')


def _sin_urls(texto):
    """Quita URLs y dominios sueltos (el post principal no debe llevar ninguno)."""
    texto = re.sub(r'(?:https?://|www\.)\S+', '', texto or '')
    # Tambien "amazon.es/dp/..." o "amzn.to/..." sin el https:// delante: X
    # los detecta igual como enlace.
    texto = re.sub(
        r'\b(?:[a-z0-9-]+\.)+(?:com|es|net|org|io|co|ly|to|me|tv|app|shop|store|'
        r'info|biz)\b(?:/\S*)?',
        '', texto, flags=re.I,
    )
    return texto.strip()


def componer_post(oferta, incluir_enlaces=True):
    """Arma el texto del post a partir de una oferta del catalogo.

    Orden: precios (actual, anterior y descuento), pregunta aleatoria, titulo
    con la descripcion y enlaces al final. Con `incluir_enlaces=False` no se
    pone ningun enlace: van aparte, en una respuesta al post.
    """
    titulo = (oferta.get('title') or '').strip()
    descripcion_bruta = oferta.get('description') or ''
    desc_antes, desc_actual = _precios_de_descripcion(descripcion_bruta)
    precio_bruto = (oferta.get('price') or '').strip()
    precio_antes_bruto = (oferta.get('old_price') or '').strip()
    if not precio_bruto and desc_actual:
        precio_bruto = desc_actual
    if not precio_antes_bruto and desc_antes:
        # El precio anterior de la descripcion solo se usa si el actual
        # coincide: asi no se mezcla el precio de otra oferta.
        if not oferta.get('price') or _mismo_precio(desc_actual, oferta.get('price')):
            precio_antes_bruto = desc_antes
    precio = _precio_es(precio_bruto)
    precio_antes = _precio_es(precio_antes_bruto)
    descuento = (oferta.get('discount') or '').strip()
    descripcion = _limpiar_descripcion(descripcion_bruta)
    hashtags = _hashtags_de(oferta)
    pregunta = pregunta_aleatoria()
    enlaces_lista = _enlaces_de(oferta)
    if incluir_enlaces:
        enlaces = '\n'.join(enlaces_lista)
        url = enlaces_lista[0] if enlaces_lista else ''
    else:
        # Ni los enlaces ni una URL suelta en el titulo o la descripcion.
        enlaces = ''
        url = ''
        descripcion = _sin_urls(descripcion)
        titulo = _sin_urls(titulo)

    # La linea de precios se arma con lo que haya: no todos los precios traen
    # descuento y algunos no traen precio anterior.
    precios = []
    if precio:
        precios.append(f'\U0001f4b8 Ahora: {precio}')
    if precio_antes and precio_antes != precio:
        precios.append(f'Antes: {precio_antes}')
    if descuento:
        precios.append(f'\U0001f4c9 {descuento}')
    linea_precios = ' | '.join(precios)

    def texto(descripcion_texto, titulo_texto, precios_texto=None):
        candidato = PLANTILLA.format(
            titulo=titulo_texto,
            precios=linea_precios if precios_texto is None else precios_texto,
            precio=precio,
            precio_antes=precio_antes,
            descuento=descuento,
            pregunta=pregunta,
            url=url,
            enlaces=enlaces,
            descripcion=descripcion_texto,
            categoria=oferta.get('categoria', ''),
            hashtags=hashtags,
        )
        # Si la descripcion va vacia quedan tres saltos seguidos: se dejan dos.
        return re.sub(r'\n{3,}', '\n\n', candidato).strip()

    # El orden de recortes: primero se recorta la descripcion, luego se quita,
    # despues se acorta el titulo y, al final, se quita el precio anterior.
    candidato = texto(descripcion, titulo)
    if longitud_post(candidato) <= LIMITE_POST:
        return candidato

    base = texto('', titulo)
    hueco = LIMITE_POST - longitud_post(base) - 4
    if descripcion and hueco >= 30:
        candidato = texto(_recortar(descripcion, hueco), titulo)
        if longitud_post(candidato) <= LIMITE_POST:
            return candidato

    if longitud_post(base) <= LIMITE_POST:
        return base

    titulo_corto = _recortar(titulo, max(60, LIMITE_POST - longitud_post(texto('', '')) - 10))
    candidato = texto('', titulo_corto)
    if longitud_post(candidato) <= LIMITE_POST:
        return candidato

    # Ultimo recurso: quitar el precio anterior y acortar otra vez.
    precios_sin_antes = [p for p in precios if not p.startswith('Antes:')]
    candidato = texto('', _recortar(titulo, 80), ' | '.join(precios_sin_antes))
    if longitud_post(candidato) <= LIMITE_POST:
        return candidato

    return _recortar(candidato, LIMITE_POST)


def componer_respuesta(oferta):
    """Arma la respuesta con los enlaces de la oferta.

    El post principal va sin enlaces para no perder alcance; esta respuesta es
    la que lleva el enlace de Amazon (y los extra, si los hay). Devuelve '' si
    la oferta no tiene ningun enlace.
    """
    enlaces = _enlaces_de(oferta)
    if not enlaces:
        return ''
    intro = ('Aquí tienes el enlace:' if len(enlaces) == 1
             else 'Aquí tienes los enlaces:')
    campos = {
        'intro': intro,
        'enlaces': '\n'.join(enlaces),
        'url': enlaces[0],
        'titulo': (oferta.get('title') or '').strip(),
        'precio': _precio_es((oferta.get('price') or '').strip()),
    }
    texto = re.sub(r'\n{3,}', '\n\n', PLANTILLA_RESPUESTA.format(**campos)).strip()
    if longitud_post(texto) <= LIMITE_POST:
        return texto

    # Si no cabe, se quitan adornos antes que enlaces. Nunca se parte una URL:
    # un enlace cortado no lleva a ninguna parte.
    texto = '\n'.join(enlaces)
    if longitud_post(texto) <= LIMITE_POST:
        return texto
    elegidos = []
    for enlace in enlaces:
        prueba = '\n'.join(elegidos + [enlace])
        if longitud_post(prueba) > LIMITE_POST:
            break
        elegidos.append(enlace)
    return '\n'.join(elegidos) if elegidos else _recortar(enlaces[0], LIMITE_POST)


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
def _id_de_usuario(operaciones, usuario):
    """El id numerico de la cuenta (lo que la web llama userId).

    La operacion de leer el perfil (UserTweets) de ahora pide el id numerico
    de la cuenta, no el @usuario. El id se saca con UserByScreenName.
    """
    operacion = _normalizar_operacion(OPERACION_USUARIO, operaciones.get(OPERACION_USUARIO))
    if not operacion:
        return ''
    cuerpo = {
        'queryId': operacion['queryId'],
        'variables': {'screen_name': usuario, 'withSafetyModeUserFields': True},
    }
    url = _url_operacion(operacion['operationName'], operacion['queryId'])
    try:
        respuesta = _peticion(url, datos=json.dumps(cuerpo).encode('utf-8'), metodo='POST',
                               cabeceras=_cabeceras_x())
    except ConnectionError as error:
        log.error(f"No se pudo buscar la cuenta {usuario}: {error}")
        return ''
    if not respuesta.ok():
        log.error(f"X devolvio HTTP {respuesta.estado} al buscar la cuenta {usuario}")
        return ''
    datos = respuesta.json() or {}
    resultado = ((datos.get('data') or {}).get('user') or {}).get('result') or {}
    return str(resultado.get('rest_id') or '') if isinstance(resultado, dict) else ''


def ultimos_posts(operaciones, usuario, cantidad=20):
    """Lee los ultimos posts de la cuenta. Devuelve [(id, texto)]."""
    if not usuario:
        return []
    operacion = _normalizar_operacion(OPERACION_LEER, operaciones.get(OPERACION_LEER))
    if not operacion:
        log.warning(f"No se conoce la operacion {OPERACION_LEER}: no se pueden leer los posts")
        return []

    variables = {'screenName': usuario, 'count': cantidad}
    if operacion.get('featureSwitches'):
        # La operacion de ahora pide el id numerico de la cuenta y manda las
        # banderas aparte, como parametros de la URL.
        id_usuario = _id_de_usuario(operaciones, usuario)
        if not id_usuario:
            log.warning(f"No se pudo saber el id de {usuario}: no se leen los posts")
            return []
        variables = {
            'userId': id_usuario,
            'count': cantidad,
            'includePromotedContent': True,
            'withQuickPromoteEligibilityTweetFields': True,
            'withCommunity': False,
            'withVoice': False,
        }

    parametros = {'variables': json.dumps(variables, separators=(',', ':'))}
    if operacion.get('featureSwitches'):
        parametros['features'] = json.dumps({f: True for f in operacion['featureSwitches']},
                                            separators=(',', ':'))
    if operacion.get('fieldToggles'):
        parametros['fieldToggles'] = json.dumps({t: True for t in operacion['fieldToggles']},
                                                separators=(',', ':'))
    url = (_url_operacion(operacion['operationName'], operacion['queryId'])
           + '?' + urllib.parse.urlencode(parametros))
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


def _buscar_instrucciones(dato, profundidad=0):
    """Busca la lista 'instructions' del timeline dentro de la respuesta.

    La forma depende de la operacion: la vieja laponia en
    `profile_with_timeline_v2.timeline.timeline` y la de ahora en
    `timeline.timeline`. Se busca por los dos caminos.
    """
    if profundidad > 6 or not isinstance(dato, dict):
        return []
    instrucciones = dato.get('instructions')
    if isinstance(instrucciones, list) and instrucciones:
        return instrucciones
    for clave in ('timeline', 'timeline_v2', 'profile_with_timeline_v2',
                  'profile_with_replies_timeline_v2'):
        encontradas = _buscar_instrucciones(dato.get(clave), profundidad + 1)
        if encontradas:
            return encontradas
    return []


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
        instrucciones = _buscar_instrucciones(resultado)
        if instrucciones:
            return instrucciones
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
    zona = ZONA if _ZONA is not None else f'{ZONA or "sistema"} no disponible (hora del sistema)'
    print(f'  hora local  : {ahora_local():%Y-%m-%d %H:%M:%S}  ({zona})')
    print(f'  franjas     : {_formatear_horas(HORAS)}')
    print(f'  enlaces     : {"en una respuesta al post" if ENLACE_EN_RESPUESTA else "en el post"}'
          f' (pausa {PAUSA_RESPUESTA}s)')

    print('\n== Operaciones ==')
    if not operaciones:
        print('  No se pudo descubrir ninguna operacion.')
        print('  X cambio el JavaScript: revisa https://x.com y copia el id a mano')
        print('  en el .env como X_QUERY_IDS=CreateTweet=<id>.')
    for nombre, operacion in operaciones.items():
        operacion = _normalizar_operacion(nombre, operacion) or {}
        banderas = len(operacion.get('featureSwitches') or [])
        print(f'  {nombre:22} {operacion.get("queryId", "?")}  ({banderas} banderas)')

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
    """Ofertas todavia no publicadas, de la mas reciente a la mas antigua.

    `limite` 0 o negativo devuelve todas.
    """
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
        if limite and len(pendientes) >= limite:
            break
    return pendientes


def _formatear_horas(horas):
    return ', '.join(f'{minutos // 60:02d}:{minutos % 60:02d}' for minutos in horas)


def proxima_franja(ahora, horas, margen=0, estricta=False):
    """Primera franja publicable a partir de `ahora`.

    Con `estricta=False`, una franja que acaba de pasar sigue contando durante
    `margen` segundos (para cuando el script arranca justo despues). Con
    `estricta=True` solo se devuelven franjas posteriores a `ahora`, que es lo
    que hace falta despues de publicar para no repetir la misma franja.
    """
    if not horas:
        horas = HORAS
    horas = sorted(horas)

    for dias in (0, 1):
        dia = (ahora + timedelta(days=dias)).date()
        for minutos in horas:
            momento = datetime.combine(dia, datetime.min.time()) + timedelta(minutes=minutos)
            if estricta:
                if momento > ahora:
                    return momento
            elif momento >= ahora - timedelta(seconds=max(0, margen)):
                return momento

    # Inalcanzable con una lista no vacia; deja la funcion cerrada.
    dia = ahora.date() + timedelta(days=1)
    return datetime.combine(dia, datetime.min.time()) + timedelta(minutes=horas[0])


def esperar_hasta(momento):
    """Duerme hasta `momento` en tramos de un minuto.

    Los tramos cortos hacen que Ctrl+C responda y que un cambio de hora no
    deje el proceso dormido una hora de mas.
    """
    while True:
        restante = (momento - ahora_local()).total_seconds()
        if restante <= 0:
            return
        time.sleep(min(restante, 60))


def simular(argumentos):
    """Enseña como quedarian los posts sin publicar nada. No necesita red."""
    ofertas = cargar_ofertas(archivo=argumentos.archivo, categoria=argumentos.categoria)
    if not ofertas:
        return 1

    limite = argumentos.limite if argumentos.limite is not None else len(argumentos.horas)
    estado = leer_estado()
    publicados = estado.get('publicados', {})
    pendientes = seleccionar_pendientes(ofertas, publicados, limite)
    log.info(f"{len(pendientes)} ofertas pendientes (de {len(ofertas)} en el catalogo)")

    enlace_en_respuesta = ENLACE_EN_RESPUESTA and not argumentos.enlace_en_post
    for oferta in pendientes:
        texto = componer_post(oferta, incluir_enlaces=not enlace_en_respuesta)
        print('\n' + '-' * 56)
        print(texto)
        print(f"[longitud: {longitud_post(texto)}/280]")
        if enlace_en_respuesta:
            respuesta = componer_respuesta(oferta)
            if respuesta:
                print('\n  Respuesta con el enlace:')
                print(respuesta)
                print(f"  [longitud: {longitud_post(respuesta)}/280]")
    return 0


def _publicar_texto(texto, operaciones, preferida='', media_ids=None,
                    reply_to='', etiqueta='post', reintentos_cuota=None):
    """Publica un texto con los reintentos de cuota y automatizacion.

    Devuelve (id_post, error, operaciones, preferida). Se usa tanto para el
    post principal como para la respuesta con el enlace.
    """
    if reintentos_cuota is None:
        reintentos_cuota = REINTENTOS_CUOTA
    id_post = ''
    error = ''
    intentos_cuota = 0
    intentos_automatizacion = 0
    while True:
        id_post, error = publicar(texto, media_ids=media_ids, operaciones=operaciones,
                                  preferida=preferida, reply_to=reply_to)
        if id_post:
            return id_post, '', operaciones, ULTIMA_OPERACION or preferida

        # X dice que la cuenta se ha pasado de tweets y mensajes por hoy.
        # No es un fallo del script: se espera y se reintenta el mismo texto.
        if error.startswith('CUOTA'):
            if intentos_cuota >= reintentos_cuota:
                log.error(f"  Se agotaron los reintentos de cuota ({etiqueta}): {error}")
                return '', error, operaciones, preferida
            intentos_cuota += 1
            log.warning(f"  {error}")
            log.warning(f"  Se espera {ESPERA_CUOTA}s y se reintenta el {etiqueta}")
            time.sleep(ESPERA_CUOTA)
            continue

        # X dice que la peticion parece automatica. Suele ser que se ha
        # publicado hace poco: se espera y se reintenta el mismo texto.
        if error.startswith('AUTOMATIZACION'):
            if intentos_automatizacion >= REINTENTOS_AUTOMATIZACION:
                log.error(f"  Se agotaron los reintentos ({etiqueta}): {error}")
                return '', error, operaciones, preferida
            intentos_automatizacion += 1
            log.warning(f"  {error}")
            log.warning(f"  Se espera {ESPERA_AUTOMATIZACION}s y se reintenta el {etiqueta}")
            time.sleep(ESPERA_AUTOMATIZACION)
            continue

        log.error(f"  No se pudo publicar el {etiqueta}: {error}")
        # Si X no reconoce la operacion o responde con un create_tweet vacio,
        # los ids o las banderas estan caducados: se buscan otra vez y se
        # reintenta una vez.
        if ('Unknown' in error or 'not found' in error.lower()
                or 'no se conoce' in error or 'no traia id de post' in error):
            log.warning("  Los ids de operacion pueden estar caducados: se buscan otra vez")
            operaciones = descubrir_operaciones(forzar=True)
            id_post, error = publicar(texto, media_ids=media_ids, operaciones=operaciones,
                                      preferida=preferida, reply_to=reply_to)
            if id_post:
                return id_post, '', operaciones, ULTIMA_OPERACION or preferida
            log.error(f"  Sigue sin publicarse el {etiqueta}: {error}")
        return '', error, operaciones, preferida


def publicar_una(oferta, operaciones, preferida='', con_imagen=True,
                 enlace_en_respuesta=None):
    """Publica una sola oferta.

    Devuelve (id_post, error, operaciones, preferida, id_respuesta,
    error_respuesta). Si el post principal sale bien pero la respuesta con el
    enlace falla, `error` va vacio (la oferta ya esta publicada) y el fallo de
    la respuesta se devuelve aparte.
    """
    if enlace_en_respuesta is None:
        enlace_en_respuesta = ENLACE_EN_RESPUESTA

    identificador = str(oferta.get('id', ''))
    texto = componer_post(oferta, incluir_enlaces=not enlace_en_respuesta)
    log.info(f"Oferta {identificador}: {oferta.get('title', '')[:60]!r}")
    log.info(f"  Texto ({longitud_post(texto)}/280): {texto[:120]!r}")

    media_ids = []
    if con_imagen and oferta.get('image'):
        media_id = subir_imagen(oferta['image'])
        if media_id:
            media_ids.append(media_id)

    id_post, error, operaciones, preferida = _publicar_texto(
        texto, operaciones, preferida, media_ids=media_ids, etiqueta='post')
    if not id_post:
        return '', error, operaciones, preferida, '', ''

    id_respuesta = ''
    error_respuesta = ''
    if enlace_en_respuesta:
        respuesta = componer_respuesta(oferta)
        if respuesta:
            log.info(f"  Respuesta con el enlace ({longitud_post(respuesta)}/280): "
                     f"{respuesta[:80]!r}")
            if PAUSA_RESPUESTA > 0:
                log.info(f"  Pausa de {PAUSA_RESPUESTA}s antes de la respuesta")
                time.sleep(PAUSA_RESPUESTA)
            id_respuesta, error_respuesta, operaciones, preferida = _publicar_texto(
                respuesta, operaciones, preferida, reply_to=id_post,
                etiqueta='respuesta',
                reintentos_cuota=REINTENTOS_CUOTA_RESPUESTA)
            if id_respuesta:
                log.info(f"  Respuesta publicada: "
                         f"https://x.com/{USUARIO or 'i'}/status/{id_respuesta}")
            else:
                log.error(f"  No se pudo publicar la respuesta con el enlace: "
                          f"{error_respuesta}")
        else:
            log.warning("  La oferta no tiene enlaces: no hay respuesta que publicar")

    return id_post, '', operaciones, preferida, id_respuesta, error_respuesta


def registrar_publicacion(estado, oferta, id_post, operacion='', franja=None,
                          respuesta_id='', respuesta_error=''):
    """Anota una oferta ya publicada en el estado y guarda el fichero.

    `franja` es el momento de la franja programada. Se guarda para que, si el
    proceso se reinicia justo despues de publicar, no vuelva a publicar otra
    oferta en la misma franja. Si la respuesta con el enlace fallo, se guarda
    el motivo para poder revisarlo.
    """
    identificador = str(oferta.get('id', ''))
    publicados = estado.setdefault('publicados', {})
    registro = {
        'tweet_id': id_post,
        'fecha': ahora_local().strftime('%Y-%m-%dT%H:%M:%S'),
        'titulo': oferta.get('title', ''),
    }
    if respuesta_id:
        registro['respuesta_id'] = respuesta_id
    if respuesta_error:
        registro['respuesta_error'] = respuesta_error
    publicados[identificador] = registro
    estado['ultimo'] = ahora_local().strftime('%Y-%m-%dT%H:%M:%S')
    operacion = operacion or ULTIMA_OPERACION
    if operacion:
        estado['operacion'] = operacion
    if franja:
        estado['ultima_franja'] = franja.strftime('%Y-%m-%dT%H:%M')
    guardar_estado(estado)


def publicar_ahora(argumentos, operaciones):
    """Publica las pendientes de golpe, con la pausa de seguridad entre posts."""
    limite = argumentos.limite if argumentos.limite is not None else LIMITE_TWEETS
    if limite <= 0:
        limite = LIMITE_TWEETS

    ofertas = cargar_ofertas(archivo=argumentos.archivo, categoria=argumentos.categoria)
    if not ofertas:
        return 1

    estado = leer_estado()
    publicados = estado.get('publicados', {})
    preferida = estado.get('operacion', '')
    if preferida:
        log.info(f"Primero se prueba {preferida}, que fue la que funciono la ultima vez")
    pendientes = seleccionar_pendientes(ofertas, publicados, limite)
    log.info(f"{len(pendientes)} ofertas pendientes de publicar (de {len(ofertas)} en el catalogo)")

    if not pendientes:
        print("No hay ofertas nuevas que publicar.")
        return 0

    con_imagen = CON_IMAGEN and not argumentos.sin_imagen
    enlace_en_respuesta = ENLACE_EN_RESPUESTA and not argumentos.enlace_en_post
    publicados_ahora = 0

    for indice, oferta in enumerate(pendientes, 1):
        log.info(f"[{indice}/{len(pendientes)}]")
        id_post, error, operaciones, preferida, id_respuesta, error_respuesta = publicar_una(
            oferta, operaciones, preferida, con_imagen,
            enlace_en_respuesta=enlace_en_respuesta)
        if not id_post:
            break

        publicados_ahora += 1
        registrar_publicacion(estado, oferta, id_post, preferida,
                              respuesta_id=id_respuesta, respuesta_error=error_respuesta)
        log.info(f"  Publicado: https://x.com/{USUARIO or 'i'}/status/{id_post}")
        if error_respuesta:
            log.warning(f"  El post salio sin el enlace en la respuesta: {error_respuesta}")

        if indice < len(pendientes):
            log.info(f"  Pausa de {PAUSA_SEGUNDOS}s antes del siguiente post")
            time.sleep(PAUSA_SEGUNDOS)

    print(f"\nPublicados {publicados_ahora} de {len(pendientes)} pendientes.")
    return 0 if publicados_ahora else 1


def publicar_programado(argumentos, operaciones):
    """Una oferta en cada franja horaria, todos los dias, hasta que se pare.

    El catalogo y el estado se releen en cada franja: mientras el script
    espera, bot.py puede haber anadido ofertas nuevas. Si no hay ninguna
    pendiente, la franja se salta y se sigue con la siguiente.
    """
    horas = argumentos.horas or HORAS
    total = argumentos.limite if argumentos.limite is not None else 0
    if total < 0:
        total = 0
    con_imagen = CON_IMAGEN and not argumentos.sin_imagen
    enlace_en_respuesta = ENLACE_EN_RESPUESTA and not argumentos.enlace_en_post

    estado = leer_estado()
    franja = proxima_franja(ahora_local(), horas, margen=MARGEN_FRANJA)
    ultima_franja = estado.get('ultima_franja', '')
    if ultima_franja and franja.strftime('%Y-%m-%dT%H:%M') == ultima_franja:
        # El proceso se reinicio dentro del margen de una franja que ya se
        # publico: no se publica otra oferta en la misma franja.
        log.info(f"La franja {ultima_franja} ya se publico: se salta")
        franja = proxima_franja(franja + timedelta(seconds=1), horas, estricta=True)
    publicados_total = 0
    log.info(f"Publicacion programada: {_formatear_horas(horas)}"
             f" ({'sin limite' if not total else f'hasta {total} posts'})")

    while True:
        restante = (franja - ahora_local()).total_seconds()
        if restante > 0:
            log.info(f"Proxima oferta: {franja:%Y-%m-%d %H:%M} "
                     f"(faltan {max(1, round(restante / 60))} min)")
        else:
            log.info(f"Franja actual: {franja:%Y-%m-%d %H:%M}")
        esperar_hasta(franja)

        try:
            # Se releen catalogo y estado en cada franja: el bot puede haber
            # anadido ofertas nuevas mientras el script esperaba.
            ofertas = cargar_ofertas(archivo=argumentos.archivo, categoria=argumentos.categoria)
            estado = leer_estado()
            publicados = estado.get('publicados', {})
            preferida = estado.get('operacion', '')
            pendientes = seleccionar_pendientes(ofertas, publicados, 1)

            if not pendientes:
                log.warning(f"[{franja:%Y-%m-%d %H:%M}] No hay ofertas nuevas: se salta la franja")
            else:
                oferta = pendientes[0]
                log.info(f"[{franja:%Y-%m-%d %H:%M}] Oferta {oferta.get('id')}")
                refrescar_cookies_web()
                # Si la cache de ids ha caducado, se renueva aqui: el proceso
                # puede llevar dias corriendo y X rota las operaciones.
                operaciones = descubrir_operaciones()
                (id_post, error, operaciones, preferida,
                 id_respuesta, error_respuesta) = publicar_una(
                    oferta, operaciones, preferida, con_imagen,
                    enlace_en_respuesta=enlace_en_respuesta)
                if id_post:
                    registrar_publicacion(estado, oferta, id_post, preferida,
                                          franja=franja, respuesta_id=id_respuesta,
                                          respuesta_error=error_respuesta)
                    publicados_total += 1
                    log.info(f"  Publicado ({publicados_total} en esta ejecucion): "
                             f"https://x.com/{USUARIO or 'i'}/status/{id_post}")
                    if error_respuesta:
                        log.warning(f"  El post salio sin el enlace en la respuesta: "
                                    f"{error_respuesta}")
                else:
                    log.error(f"  La oferta {oferta.get('id')} no se publico: {error}")
        except Exception as error:
            # Un fallo inesperado no debe parar el proceso: se apunta y se
            # sigue con la siguiente franja.
            log.exception(f"Error inesperado en la franja {franja:%Y-%m-%d %H:%M}: {error}")

        if total and publicados_total >= total:
            break
        franja = proxima_franja(ahora_local(), horas, estricta=True)

    print(f"\nPublicados {publicados_total} posts. Fin de la publicacion programada.")
    return 0 if publicados_total else 1


def main():
    analizador = argparse.ArgumentParser(
        description='Publica las ofertas del catalogo en X (Twitter).')
    analizador.add_argument('--limite', type=int, default=None,
                            help='cuantas ofertas publicar en total (programado: 0 o vacio = '
                                 f'sin limite; --ahora: por defecto {LIMITE_TWEETS})')
    analizador.add_argument('--categoria', help='publicar solo una categoria (data/<categoria>.json)')
    analizador.add_argument('--archivo', help='publicar las ofertas de un archivo JSON concreto')
    analizador.add_argument('--simular', action='store_true',
                            help='enseñar como quedarian los posts sin publicar nada')
    analizador.add_argument('--sin-imagen', action='store_true', help='publicar sin imagen')
    analizador.add_argument('--enlace-en-post', action='store_true',
                            help='poner los enlaces en el post principal en vez de en una '
                                 'respuesta (por defecto van en una respuesta)')
    analizador.add_argument('--ahora', action='store_true',
                            help='publicar ya las pendientes en vez de esperar a las franjas')
    analizador.add_argument('--horas', default='',
                            help='franjas horarias separadas por comas '
                                 '(por defecto X_HORAS o 08:00,12:00,17:00,21:00)')
    analizador.add_argument('--revisar', action='store_true',
                            help='comprobar la sesion y los ids de operacion, sin publicar')
    analizador.add_argument('--verificar', action='store_true',
                            help='leer los ultimos posts de la cuenta y sincronizar el estado')
    analizador.add_argument('--refrescar-cache', action='store_true',
                            help='buscar otra vez los ids de operacion en el JavaScript de X')
    argumentos = analizador.parse_args()
    argumentos.horas = _parsear_horas(argumentos.horas) if argumentos.horas.strip() else list(HORAS)

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

    if argumentos.ahora:
        return publicar_ahora(argumentos, operaciones)
    return publicar_programado(argumentos, operaciones)


def _al_parar(signum, _frame):
    """Parada limpia con SIGTERM (kill, tmux kill-session...)."""
    log.warning(f"Senal {signum} recibida: se para la publicacion")
    raise KeyboardInterrupt


if __name__ == '__main__':
    # En Termux, cerrar la terminal manda SIGHUP. Si no se ignora, el proceso
    # se muere aunque el usuario no lo haya parado. Para pararlo de verdad:
    # Ctrl+C, `kill <pid>` o `pkill -f publicar_x.py`.
    if hasattr(signal, 'SIGHUP'):
        try:
            signal.signal(signal.SIGHUP, signal.SIG_IGN)
        except (ValueError, OSError):
            pass
    try:
        signal.signal(signal.SIGTERM, _al_parar)
    except (AttributeError, ValueError, OSError):
        pass
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log.warning("Interrumpido por el usuario")
        sys.exit(130)

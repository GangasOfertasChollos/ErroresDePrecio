"""Reenvia al grupo de Telegram cada oferta del canal, en el tema de su categoria.

El grupo de destino es un foro: cada categoria es un tema (topic) con su id
numerico. El reparto lo hace el mismo clasificador que usa la web
(clasificador.py), asi que una oferta que en la web aparece en "Ropa y calzado"
se reenvia al tema de ropa y no a otro.

El diccionario se edita en categorias.json y los ids de los temas en
temas_telegram.json. Este archivo no guarda ninguna palabra clave.

Uso:

    python reenvioCategorias.py                    # escucha y reenvia
    python reenvioCategorias.py --simulado         # escucha, clasifica y no envia
    python reenvioCategorias.py --clasificar "Zapatillas Nike Air"
    python reenvioCategorias.py --temas            # lista los temas del grupo
    python reenvioCategorias.py --historial 20     # simula sobre el canal, sin enviar

Para probar el reparto sin Telegram:  python tests/test_reenvio_categorias.py
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import clasificador
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.tl.functions.messages import GetForumTopicsRequest

LOG_PATH = RAIZ / 'reenvio.log'
TEMAS_PATH = RAIZ / 'temas_telegram.json'

log = logging.getLogger('reenvio_categorias')


# ─────────────────────────────────────────────
# CONFIGURACION
# ─────────────────────────────────────────────
def cargar_env(ruta=None):
    """Carga .env sin pisar lo que ya venga del entorno del sistema."""
    ruta = Path(ruta) if ruta else RAIZ / '.env'
    if not ruta.exists():
        return
    with open(ruta, encoding='utf-8') as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith('#') or '=' not in linea:
                continue
            clave, _, valor = linea.partition('=')
            os.environ.setdefault(clave.strip(), valor.strip())


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


def _leer_bool(nombre, por_defecto=False):
    bruto = str(os.getenv(nombre, '') or '').strip().lower()
    if not bruto:
        return por_defecto
    return bruto in ('1', 'true', 'yes', 'si', 'sí')


cargar_env()

API_ID = _leer_int('API_ID', 0)
API_HASH = os.getenv('API_HASH', '').strip()
CANAL_ORIGEN = os.getenv('TELEGRAM_CHANNEL', '@GangasOfertasChollos').strip()
# Los grupos con enlace t.me/c/... llevan el prefijo -100 delante del id.
GRUPO_DESTINO_ID = _leer_int('GRUPO_DESTINO_ID', -1004484167619)
# Sesion propia: si se reutiliza la de bot.py los dos procesos pelean por el
# mismo archivo SQLite y Telegram responde "database is locked".
SESSION_NAME = os.getenv('SESSION_NAME', 'sesion_reenvio').strip() or 'sesion_reenvio'
SIMULADO = _leer_bool('REENVIO_SIMULADO', False)


def cargar_temas(ruta=None):
    """Lee el id de tema (topic) que corresponde a cada categoria."""
    ruta = Path(ruta) if ruta else TEMAS_PATH
    with open(ruta, encoding='utf-8') as f:
        datos = json.load(f)
    if not isinstance(datos, dict):
        raise ValueError(f'{ruta} debe contener un objeto JSON categoria -> id de tema')

    temas = {}
    for categoria, topic_id in datos.items():
        if str(categoria).startswith('_'):
            continue
        if not isinstance(topic_id, int) or isinstance(topic_id, bool):
            raise ValueError(f'El tema de {categoria!r} en {ruta} debe ser un numero entero')
        temas[str(categoria)] = topic_id
    return temas


def validar_temas(temas, diccionario):
    """Comprueba que cada categoria del diccionario tiene tema de destino.

    Devuelve la lista de avisos (categorias del mapeo que ya no estan en el
    diccionario). Si falta un tema es un error: esa categoria acabaria toda en
    General sin que nadie se entere.
    """
    faltan = [c for c in diccionario if c not in temas]
    if faltan:
        raise ValueError(
            'Faltan temas en temas_telegram.json para: ' + ', '.join(faltan)
        )
    if clasificador.CATEGORIA_GENERAL not in temas:
        raise ValueError(
            f"Falta el tema de la categoria de descarte "
            f"'{clasificador.CATEGORIA_GENERAL}' en temas_telegram.json"
        )
    return [c for c in temas
            if c != clasificador.CATEGORIA_GENERAL and c not in diccionario]


def resolver_tema(categoria, temas):
    """Devuelve el id de tema de una categoria, con General como respaldo."""
    return temas.get(categoria, temas[clasificador.CATEGORIA_GENERAL])


# ─────────────────────────────────────────────
# CLASIFICACION
# ─────────────────────────────────────────────
_DICCIONARIO = None
_PATRONES = None


def preparar_clasificador():
    """Carga el diccionario y compila los patrones una sola vez."""
    global _DICCIONARIO, _PATRONES
    if _PATRONES is None:
        _DICCIONARIO = clasificador.cargar_diccionario()
        _PATRONES = clasificador.precompilar_patrones(_DICCIONARIO)
    return _DICCIONARIO, _PATRONES


def clasificar(texto):
    """Devuelve (categoria, detalle) para el texto de una oferta."""
    _, patrones = preparar_clasificador()
    detalle = clasificador.explicar(texto, patrones)
    return detalle['categoria'], detalle


# ─────────────────────────────────────────────
# ENVIO
# ─────────────────────────────────────────────
async def reenviar(cliente, mensaje, texto, media, tema):
    """Copia el mensaje en el tema indicado, respetando el formato original.

    Se copia (send_message) en vez de reenviar (forward) para que el grupo no
    muestre el cartel de "Reenviado de"; el texto y las entidades se pasan tal
    cual, y `parse_mode=None` evita que Telethon interprete asteriscos o
    guiones bajos del titulo como markdown.
    """
    for intento in (1, 2):
        try:
            await cliente.send_message(
                entity=GRUPO_DESTINO_ID,
                message=texto,
                file=media,
                reply_to=tema,
                link_preview=media is None,
                formatting_entities=mensaje.entities,
                parse_mode=None,
            )
            return
        except FloodWaitError as e:
            if intento == 2:
                raise
            log.warning(f"Telegram pide esperar {e.seconds}s antes de seguir")
            await asyncio.sleep(e.seconds + 1)


def crear_handler(cliente, temas, simulado=False):
    """Construye el manejador de mensajes nuevos del canal."""

    @cliente.on(events.NewMessage(chats=CANAL_ORIGEN))
    async def clasificar_y_reenviar(event):
        mensaje = event.message
        texto = mensaje.text or getattr(mensaje, 'message', '') or ''
        # Solo se copia el archivo si de verdad es una foto o un documento: una
        # vista previa de enlace (MessageMediaWebPage) no se puede enviar.
        media = mensaje.photo or mensaje.document or None

        if not texto.strip() and not media:
            log.debug(f"[IGNORADO] ID={mensaje.id}: sin texto ni archivo")
            return

        categoria, detalle = clasificar(texto)
        tema = resolver_tema(categoria, temas)
        resumen = ', '.join(detalle['coincidencias'][:6]) or 'sin coincidencias'
        if detalle['origen'] == 'etiqueta':
            resumen = 'por la etiqueta del canal: ' + resumen
        log.info(f"[{categoria} -> tema {tema}] ID={mensaje.id} "
                 f"({resumen}) {texto[:70]!r}")

        if simulado:
            log.info("  (simulado: no se envia nada)")
            return

        try:
            await reenviar(cliente, mensaje, texto, media, tema)
        except Exception as e:
            log.error(f"[ERROR] ID={mensaje.id} no se pudo reenviar al tema "
                      f"{tema} ({categoria}): {e}")
            if 'topic' in str(e).lower():
                log.error("  El id del tema no parece valido. "
                          "Compruebalo con: python reenvioCategorias.py --temas")

    return clasificar_y_reenviar


# ─────────────────────────────────────────────
# MODOS DE EJECUCION
# ─────────────────────────────────────────────
def crear_cliente():
    if not API_ID or not API_HASH:
        raise SystemExit("API_ID o API_HASH no configurados. Revisa tu archivo .env")
    return TelegramClient(SESSION_NAME, API_ID, API_HASH)


async def listar_temas(cliente, temas):
    """Imprime los temas reales del grupo para comprobar el mapeo."""
    entidad = await cliente.get_input_entity(GRUPO_DESTINO_ID)
    resultado = await cliente(GetForumTopicsRequest(
        peer=entidad, offset_date=None, offset_id=0, offset_topic=0, limit=100))
    reales = {t.id: getattr(t, 'title', '') for t in resultado.topics}
    print("\nTemas del grupo (id real -> titulo):")
    for topic_id, titulo in sorted(reales.items()):
        print(f"  {topic_id:>4}  {titulo}")
    print("\nMapeo de temas_telegram.json:")
    for categoria, topic_id in sorted(temas.items(), key=lambda kv: kv[1]):
        real = reales.get(topic_id)
        estado = 'OK' if real is not None else 'NO EXISTE'
        print(f"  {topic_id:>4}  {categoria:<26} {estado}"
              + (f" ({real})" if real else ""))


async def simular_historial(cliente, temas, limite):
    """Clasifica los ultimos mensajes del canal sin enviar nada."""
    total = 0
    por_categoria = {}
    print(f"\nSimulacion sobre los ultimos {limite} mensajes de {CANAL_ORIGEN}:")
    async for mensaje in cliente.iter_messages(CANAL_ORIGEN, limit=limite):
        texto = mensaje.text or getattr(mensaje, 'message', '') or ''
        if not texto.strip() and not mensaje.media:
            continue
        total += 1
        categoria, detalle = clasificar(texto)
        por_categoria[categoria] = por_categoria.get(categoria, 0) + 1
        tema = resolver_tema(categoria, temas)
        primera_linea = (texto.splitlines() or ['(sin texto)'])[0]
        marcas = ', '.join(detalle['coincidencias'][:4])
        print(f"  [{categoria:<26} tema {tema:>3}] {primera_linea[:60]}"
              + (f"  <- {marcas}" if marcas else ""))

    print(f"\n{total} mensajes clasificados:")
    for categoria, cuenta in sorted(por_categoria.items(), key=lambda kv: -kv[1]):
        print(f"  {cuenta:>4}  {categoria} (tema {resolver_tema(categoria, temas)})")
    print("\nNo se ha enviado nada: esta simulacion solo lee el canal.")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Reenvia las ofertas del canal al tema de su categoria.')
    parser.add_argument('--clasificar', metavar='TEXTO',
                        help='clasifica un texto y muestra el tema, sin conectar')
    parser.add_argument('--temas', action='store_true',
                        help='lista los temas reales del grupo y comprueba el mapeo')
    parser.add_argument('--historial', type=int, metavar='N',
                        help='simula N mensajes del canal (no envia nada)')
    parser.add_argument('--simulado', action='store_true',
                        help='escucha y clasifica, pero no reenvia')
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_PATH, encoding='utf-8'),
        ],
    )
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

    diccionario, _ = preparar_clasificador()
    temas = cargar_temas()
    for aviso in validar_temas(temas, diccionario):
        log.warning(f"temas_telegram.json tiene un tema para '{aviso}', "
                    f"que ya no existe en categorias.json")
    log.info(f"Diccionario: {len(diccionario)} categorias, "
             f"{sum(len(v) for v in diccionario.values())} palabras clave")
    log.info(f"Temas: {temas}")

    if args.clasificar is not None:
        categoria, detalle = clasificar(args.clasificar)
        print(f"\nTexto:     {args.clasificar}")
        print(f"Categoria: {categoria}")
        print(f"Tema:      {resolver_tema(categoria, temas)}")
        print(f"Coincidencias: {detalle['coincidencias'] or 'ninguna'}")
        if detalle['origen'] == 'etiqueta':
            print("  (decidido por la etiqueta 📂 del propio post)")
        for otra in detalle['todas']:
            if otra['categoria'] != categoria:
                print(f"  (tambien {otra['categoria']}: {otra['coincidencias']})")
        return 0

    if args.temas or args.historial:
        async def ejecutar():
            cliente = crear_cliente()
            async with cliente:
                if args.temas:
                    await listar_temas(cliente, temas)
                if args.historial:
                    await simular_historial(cliente, temas, args.historial)
        asyncio.run(ejecutar())
        return 0

    simulado = args.simulado or SIMULADO
    cliente = crear_cliente()
    crear_handler(cliente, temas, simulado=simulado)
    log.info("---------------------------------------")
    log.info(f"Escuchando {CANAL_ORIGEN} -> grupo {GRUPO_DESTINO_ID}")
    log.info(f"Sesion: {SESSION_NAME}" + ("  (SIMULADO: no se envia nada)" if simulado else ""))
    log.info("Ctrl + C para detenerlo.")
    log.info("---------------------------------------")
    cliente.start()
    cliente.run_until_disconnected()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

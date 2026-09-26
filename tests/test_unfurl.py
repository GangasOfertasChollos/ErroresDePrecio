"""Prueba del unfurling con la red simulada.

Se comprueba que el bot pide la pagina publica del mensaje, extrae su og:image
y cachea el resultado, sin tocar la red de verdad. El HTML es una copia
reduced del que devuelve t.me, con los mismos atributos.
"""
import os, sys, asyncio, importlib.util, urllib.error
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
os.environ.update(dict(API_ID="1", API_HASH="h", TELEGRAM_CHANNEL="@supertacanyones"))
spec = importlib.util.spec_from_file_location("bot", RAIZ / "bot.py")
bot = importlib.util.module_from_spec(spec); spec.loader.exec_module(bot)

fallos = 0
def check(n, cond, det=""):
    global fallos
    if cond: print("  OK   " + n)
    else: fallos += 1; print("  FALLO " + n + " -> " + str(det))

HTML_TME = """<!DOCTYPE html><html><head>
<meta property="og:title" content="SUPERTACA\u00d1ONES">
<meta property="og:image" content="https://cdn4.telesco.pe/file/ABCDEF.jpg">
<meta property="og:description" content="VANSKIVA - Parche de silicona">
<meta name="twitter:image" content="https://cdn4.telesco.pe/file/OTRA.jpg">
</head><body></body></html>"""

HTML_SIN_IMAGEN = """<!DOCTYPE html><html><head>
<meta property="og:title" content="SUPERTACA\u00d1ONES">
<meta property="og:description" content="sin foto">
</head><body></body></html>"""

# Los atributos pueden venir en el otro orden: content antes que property
HTML_ORDEN_INVERSO = """<html><head>
<meta content="https://cdn4.telesco.pe/file/INVERSO.jpg" property="og:image">
</head></html>"""


class RespuestaFalsa:
    def __init__(self, html, status=200):
        self._html = html.encode("utf-8")
        self.status = status
    def read(self): return self._html
    def close(self): pass


class Chat: username = "supertacanyones"
class Msg:
    def __init__(self, mid=13197, chat=Chat()):
        self.id = mid; self.chat = chat; self.text = ""; self.media = None; self.entities = None


def instalar_red(html, error=None, registrar=None):
    def urlopen(peticion, timeout=None, *a, **k):
        url = getattr(peticion, "full_url", str(peticion))
        if registrar is not None:
            registrar.append(url)
        if error:
            raise error
        return RespuestaFalsa(html)
    return urlopen


async def main():
    print("\n== 1. Extrae la og:image de la pagina del mensaje ==")
    urls = []
    original = bot.urllib.request.urlopen
    bot.urllib.request.urlopen = instalar_red(HTML_TME, registrar=urls)
    bot._CACHE_IMAGENES.clear()

    msg = Msg()
    url = await bot.extraer_imagen("sin imagen en el texto", msg)
    check("devuelve la URL de og:image", url == "https://cdn4.telesco.pe/file/ABCDEF.jpg", url)
    check("ha pedido t.me/<canal>/<id>",
          urls == ["https://t.me/supertacanyones/13197"], urls)
    check("ignora twitter:image y usa og:image", url.endswith("ABCDEF.jpg"), url)

    print("\n== 2. Cache: la segunda vez no vuelve a pedirlo ==")
    urls.clear()
    url2 = await bot.extraer_imagen("sin imagen en el texto", msg)
    check("misma URL sin peticion", url2 == url and urls == [], urls)

    print("\n== 3. La URL del texto tiene prioridad (0 peticiones) ==")
    urls.clear()
    directo = await bot.extraer_imagen(
        "https://m.media-amazon.com/images/I/71x._AC_SL1500_.jpg", msg)
    check("usa la URL del texto", directo == "https://m.media-amazon.com/images/I/71x._AC_SL1500_.jpg", directo)
    check("no ha hecho ninguna peticion", urls == [], urls)

    print("\n== 4. La pagina sin og:image devuelve vacio sin romperse ==")
    bot._CACHE_IMAGENES.clear()
    bot.urllib.request.urlopen = instalar_red(HTML_SIN_IMAGEN)
    check("imagen vacia", await bot.extraer_imagen("nada", Msg(777)) == "")

    print("\n== 5. Acepta los atributos en el orden inverso ==")
    bot._CACHE_IMAGENES.clear()
    bot.urllib.request.urlopen = instalar_red(HTML_ORDEN_INVERSO)
    r = await bot.extraer_imagen("nada", Msg(778))
    check("extrae con content antes que property", r == "https://cdn4.telesco.pe/file/INVERSO.jpg", r)

    print("\n== 6. Errores de red no rompen el bot ==")
    bot._CACHE_IMAGENES.clear()
    for nombre, exc in [
        ("timeout", TimeoutError("tardo")),
        ("HTTP 404", urllib.error.HTTPError("u", 404, "no", {}, None)),
        ("error de conexion", OSError("sin red")),
    ]:
        bot._CACHE_IMAGENES.clear()
        bot.urllib.request.urlopen = instalar_red("", error=exc)
        r = await bot.extraer_imagen("nada", Msg(abs(hash(nombre)) % 1000))
        check(f"{nombre} -> imagen vacia", r == "", r)

    print("\n== 7. Sin username de canal no se hace ninguna peticion ==")
    bot._CACHE_IMAGENES.clear()
    urls.clear()
    bot.urllib.request.urlopen = instalar_red(HTML_TME, registrar=urls)
    r = await bot.extraer_imagen("nada", Msg(555, chat=None))
    check("imagen vacia", r == "", r)
    check("cero peticiones a la red", urls == [], urls)

    print("\n== 8. USAR_UNFURL=0 desactiva todo ==")
    # id propio: 13197 ya esta en cache del test 1
    bot._CACHE_IMAGENES.clear(); urls.clear()
    bot.USAR_UNFURL = False
    r = await bot.extraer_imagen("nada", Msg(31337))
    check("no pide nada y devuelve vacio", r == "" and urls == [], (r, urls))
    bot.USAR_UNFURL = True

    print("\n== 9. Las entidades del mensaje tambien se miran ==")
    bot._CACHE_IMAGENES.clear(); urls.clear()
    class Ent:
        url = "https://m.media-amazon.com/images/I/DESDEENTIDAD.jpg"
    class MsgEnt(Msg):
        def __init__(self, mid):
            super().__init__(mid)
            self.entities = [Ent()]
    r = await bot.extraer_imagen("nada", MsgEnt(4242))
    check("usa la URL de la entidad", r == "https://m.media-amazon.com/images/I/DESDEENTIDAD.jpg", r)
    check("no ha ido a la red por ella", urls == [], urls)

    bot.urllib.request.urlopen = original

asyncio.run(main())
print("\n" + "=" * 56)
print("TODO CORRECTO" if fallos == 0 else f"{fallos} FALLOS")
sys.exit(1 if fallos else 0)

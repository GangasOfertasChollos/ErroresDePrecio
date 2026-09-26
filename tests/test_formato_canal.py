"""Pruebas del formato real de mensajes del canal y del unfurling de imagenes.

Los mensajes de ejemplo son literales de los que publica el canal, con sus
emojis, el bloque de precios etiquetado y el hashtag final.
"""
import os, sys, json, asyncio, importlib.util, shutil, tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
os.environ.update(dict(API_ID="1", API_HASH="h", TELEGRAM_CHANNEL="@x", USAR_UNFURL="0"))
spec = importlib.util.spec_from_file_location("bot", RAIZ / "bot.py")
bot = importlib.util.module_from_spec(spec); spec.loader.exec_module(bot)

fallos = 0
def check(n, cond, det=""):
    global fallos
    if cond: print("  OK   " + n)
    else: fallos += 1; print("  FALLO " + n + " -> " + str(det))

# ── Mensajes literales del canal ──
VANSKIVA = (
    "\U0001FA79 VANSKIVA \u2013 Parche de silicona para cicatrices 4 cm x 1,5 m\n"
    "\n"
    "\U0001F4B8 Ahora: 13,99 \u20ac\n"
    "\U0001F3F7\ufe0f Antes: 25,99 \u20ac\n"
    "\U0001F4C9 Descuento: -46 %\n"
    "\U0001F4B0 Ahorras: 12,00 \u20ac\n"
    "\U0001F517\n"
    "\n"
    "https://www.amazon.es/dp/B0GCQX9YY4?tag=gangas054-21\n"
    "\n"
    "\u2728 Parche reutilizable, recortable e impermeable para el cuidado de cicatrices.\n"
    "\n"
    "#Amazon "
)
CGBE = (
    "\u2702\ufe0f CGBE \u2013 Tijeras de cocina multiusos\n"
    "\n"
    "\U0001F4B8 Ahora: 7,49 \u20ac\n"
    "\U0001F3F7\ufe0f Antes: 16,99 \u20ac\n"
    "\U0001F4C9 Descuento: -56 %\n"
    "\U0001F4B0 Ahorras: 9,50 \u20ac\n"
    "\U0001F517https://amzlink.to/az0ARDYkVFVcK\n"
    "\n"
    "\U0001F357 Cuchillas de acero inoxidable, mango antideslizante y aptas para carne, pescado, pollo y verduras."
)

print("\n== 1. Extraccion del formato del canal ==")
for nombre, M, esperado in [
    ("VANSKIVA", VANSKIVA, dict(
        titulo="VANSKIVA \u2013 Parche de silicona para cicatrices 4 cm x 1,5 m",
        precio="13.99 \u20ac", antes="25.99 \u20ac", descuento="-46%",
        enlace="https://www.amazon.es/dp/B0GCQX9YY4?tag=gangas054-21", asin="B0GCQX9YY4")),
    ("CGBE", CGBE, dict(
        titulo="CGBE \u2013 Tijeras de cocina multiusos",
        precio="7.49 \u20ac", antes="16.99 \u20ac", descuento="-56%",
        enlace="https://amzlink.to/az0ARDYkVFVcK", asin=None)),
]:
    check(f"{nombre}: titulo sin emoji", bot.extraer_titulo(M) == esperado["titulo"], bot.extraer_titulo(M))
    check(f"{nombre}: precio de oferta", bot.extraer_precio(M) == esperado["precio"], bot.extraer_precio(M))
    check(f"{nombre}: precio anterior", bot.extraer_precio_antes(M) == esperado["antes"], bot.extraer_precio_antes(M))
    check(f"{nombre}: descuento", bot.extraer_descuento(M) == esperado["descuento"], bot.extraer_descuento(M))
    check(f"{nombre}: enlace con la query de afiliado",
          bot.extraer_enlace_amazon(M) == esperado["enlace"], bot.extraer_enlace_amazon(M))
    m = bot.RE_ASIN.search(bot.extraer_enlace_amazon(M))
    asin = m.group(1) if m else None
    check(f"{nombre}: ASIN", asin == esperado["asin"], asin)

print("\n== 2. El acortador del canal se reconoce ==")
check("amzlink.to detectado", "amzlink.to" in bot.extraer_enlace_amazon(CGBE))
check("amazon.es detectado", "amazon.es" in bot.extraer_enlace_amazon(VANSKIVA))
for dominio in ["amzn.to/abc", "amzn.eu/abc", "amzlink.to/abc", "amazon.com/x", "amazon.de/x"]:
    check(f"soporta {dominio}", bool(bot.RE_ENLACE_PLANO.match(f"https://{dominio}")))
check("no acepta un dominio cualquiera",
      not bot.RE_ENLACE_PLANO.match("https://ejemplo.com/oferta"))
check("no acepta una suplantacion",
      not bot.RE_ENLACE_PLANO.match("https://amazon.es.evil.com/x"))

print("\n== 3. El titulo no se traga la estructura del mensaje ==")
for etiqueta in ("\U0001F4B8 Ahora:", "\U0001F3F7\ufe0f Antes:", "\U0001F4C9 Descuento:",
                 "\U0001F4B0 Ahorras:", "\U0001F517"):
    t = bot.extraer_titulo(etiqueta + " lo que sea")
    check(f"descarta linea que empieza por {etiqueta!r}", t == "Oferta Amazon", t)
check("descarta el hashtag", bot.extraer_titulo("#Amazon") == "Oferta Amazon")
check("descarta el enlace suelto",
      bot.extraer_titulo("https://www.amazon.es/dp/B0X") == "Oferta Amazon")
check("descarta el precio suelto", bot.extraer_titulo("13,99 \u20ac") == "Oferta Amazon")
check("descarta la descripcion con emoji inicial",
      bot.extraer_titulo("\u2728 Parche reutilizable") == "Parche reutilizable")

print("\n== 4. Precios: nunca confunde el anterior con el de oferta ==")
# El orden importa: 'Ahora' tiene prioridad sobre 'Antes'
t = "\U0001F3F7\ufe0f Antes: 25,99 \u20ac\n\U0001F4B8 Ahora: 13,99 \u20ac"
check("gana 'Ahora' aunque 'Antes' salga primero", bot.extraer_precio(t) == "13.99 \u20ac", bot.extraer_precio(t))
check("'Antes' se guarda aparte", bot.extraer_precio_antes(t) == "25.99 \u20ac", bot.extraer_precio_antes(t))
check("precio con miles", bot.extraer_precio("Ahora: 1.299,00 \u20ac") == "1299.00 \u20ac", bot.extraer_precio("Ahora: 1.299,00 \u20ac"))
check("precio entero sin decimales", bot.extraer_precio("Ahora: 199 \u20ac") == "199.00 \u20ac", bot.extraer_precio("Ahora: 199 \u20ac"))
check("sin etiquetas vuelve al metodo general", bot.extraer_precio("Por solo 39,95 \u20ac") == "39.95 \u20ac")

print("\n== 5. La palabra 'cuchillas' ya no manda a higiene ==")
check("tijeras de cocina -> general", bot.clasificar_oferta(CGBE) == "general", bot.clasificar_oferta(CGBE))
check("cuchillas de afeitar -> higiene",
      bot.clasificar_oferta("Cuchillas de afeitar Gillette Mach3") == "higiene-cuidado-personal")

print("\n== 6. URL publica del mensaje (base del unfurling) ==")
class Chat: username = "supertacanyones"
class Msg:
    def __init__(self, mid, chat): self.id = mid; self.chat = chat; self.text = ""; self.media = None; self.entities = None

check("construye t.me/canal/id",
      bot.url_publica_mensaje(Msg(13197, Chat())) == "https://t.me/supertacanyones/13197",
      bot.url_publica_mensaje(Msg(13197, Chat())))
check("sin username de canal devuelve ''", bot.url_publica_mensaje(Msg(1, None)) == "")
check("sin mensaje devuelve ''", bot.url_publica_mensaje(None) == "")

print("\n== 7. Unfurling: la imagen del texto tiene prioridad y no se pide nada ==")
async def test_unfurl():
    await bot.extraer_imagen("https://m.media-amazon.com/images/I/71abc._AC_SL1500_.jpg", Msg(1, Chat()))
    return True
check("URL de imagen del texto se usa tal cual",
      asyncio.run(test_unfurl()) is True)
check("no hay peticiones de red si el mensaje trae la URL",
      bot._CACHE_IMAGENES == {}, bot._CACHE_IMAGENES)

class MsgFoto:  # sin URL de imagen y sin canal -> no se puede obtener nada
    id = 5; chat = None; text = "nada"; media = object(); entities = None
bot._CACHE_IMAGENES.clear()
bot.USAR_UNFURL = True
r = asyncio.run(bot.extraer_imagen("nada aqui", MsgFoto()))
check("sin URL y sin canal -> imagen vacia, sin peticion", r == "", r)
check("la cache sigue vacia (no se hizo ninguna peticion)", bot._CACHE_IMAGENES == {})

print("\n== 8. Oferta completa con los dos campos nuevos ==")
async def flujo():
    tmp = Path(tempfile.mkdtemp())
    bot.DATA_PATH = tmp
    class M:
        id = 777; date = None; media = None; entities = None
        text = VANSKIVA
    await bot.actualizar_json(bot.clasificar_oferta(VANSKIVA), M())
    datos = json.loads((tmp / "general.json").read_text(encoding="utf-8"))
    shutil.rmtree(tmp, ignore_errors=True)
    return datos
oferta = asyncio.run(flujo())[0]
check("guarda el precio de oferta", oferta["price"] == "13.99 \u20ac", oferta["price"])
check("guarda el precio anterior", oferta["old_price"] == "25.99 \u20ac", oferta.get("old_price"))
check("guarda el descuento", oferta["discount"] == "-46%", oferta.get("discount"))
check("guarda el ASIN via la query de afiliado", "B0GCQX9YY4" in oferta["amazon_url"])
check("el titulo va limpio en el JSON", oferta["title"].startswith("VANSKIVA"), oferta["title"])
check("el titulo no lleva emojis sueltos", not oferta["title"][0].isspace())

print("\n" + "=" * 56)
print("TODO CORRECTO" if fallos == 0 else f"{fallos} FALLOS")
sys.exit(1 if fallos else 0)

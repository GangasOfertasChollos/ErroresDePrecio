"""Pruebas de las funciones puras de bot.py sin tocar Telegram."""
import os, sys, json, time, asyncio, importlib.util, shutil, tempfile, inspect
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
os.environ["API_ID"] = "12345"
os.environ["API_HASH"] = "hash_de_prueba"
os.environ["TELEGRAM_CHANNEL"] = "@GangasOfertasChollos"

spec = importlib.util.spec_from_file_location("bot", RAIZ / "bot.py")
bot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot)

fallos = 0
def check(nombre, condicion, detalle=""):
    global fallos
    if condicion:
        print(f"  OK   {nombre}")
    else:
        fallos += 1
        print(f"  FALLO {nombre} -> {detalle}")

print("\n== _formatear_precio ==")
casos = [
    ("199", "199.00 €"), ("1.299", "1299.00 €"), ("199,50", "199.50 €"),
    ("1.299,50", "1299.50 €"), ("1,299.50", "1299.50 €"), ("19,99", "19.99 €"),
    ("9.99", "9.99 €"), ("0,99", "0.99 €"), ("12.345,67", "12345.67 €"),
]
for entrada, esperado in casos:
    check(f"{entrada!r} -> {esperado}", bot._formatear_precio(entrada) == esperado,
          f"obtenido {bot._formatear_precio(entrada)!r}")

print("\n== extraer_precio ==")
check("prioridad 'Ahora 199€'", bot.extraer_precio("Ahora 199€") == "199.00 €",
      bot.extraer_precio("Ahora 199€"))
check("prioridad 'Precio: 1.299,50€'", bot.extraer_precio("Precio: 1.299,50€") == "1299.50 €",
      bot.extraer_precio("Precio: 1.299,50€"))
check("tachado markdown se ignora",
      bot.extraer_precio("~~299,99€~~ 199€") == "199.00 €", bot.extraer_precio("~~299,99€~~ 199€"))
check("sin keywords toma el mas bajo",
      bot.extraer_precio("299,99€ antes, 149,50€ ahora") == "149.50 €",
      bot.extraer_precio("299,99€ antes, 149,50€ ahora"))
check("sin precio -> ''", bot.extraer_precio("Sin precios aqui") == "")
check("texto vacio -> ''", bot.extraer_precio("") == "")

print("\n== extraer_titulo ==")
check("primera linea", bot.extraer_titulo("Zapatillas Nike\nAhora 39€") == "Zapatillas Nike")
check("markdown fuera", bot.extraer_titulo("**Sony** headphones") == "Sony headphones")
check("salta linea de solo precio", bot.extraer_titulo("49,99€\nSony headphones") == "Sony headphones",
      bot.extraer_titulo("49,99€\nSony headphones"))
check("texto vacio", bot.extraer_titulo("") == "Oferta Amazon")

print("\n== extraer_gtin (solo codigos que son de verdad un GTIN) ==")
# El fallback MPN antiguo devolvia la marca o un sustantivo del titulo y se
# publicaba como itemprop="gtin", que es informacion falsa.
for texto in ("Scottex Papel Higienico Humedo", "OFERTA Chollo Zapatillas",
              "Zapatillas Auriculares Inalambricos", "Mando DualSense PS5",
              "Logitech G, Mouse", "Cepillos Interdentales"):
    check(f"sin codigo real -> '' ({texto[:24]!r})", bot.extraer_gtin(texto) == "",
          bot.extraer_gtin(texto))
check("EAN-13 con digito de control valido", bot.extraer_gtin("EAN 8412345678905") == "8412345678905",
      bot.extraer_gtin("EAN 8412345678905"))
check("EAN-13 sin digito de control valido -> ''", bot.extraer_gtin("EAN 8412345678907") == "",
      bot.extraer_gtin("EAN 8412345678907"))
check("UPC-A con digito de control valido", bot.extraer_gtin("codigo 012345678905") == "012345678905",
      bot.extraer_gtin("codigo 012345678905"))
check("EAN-8 con digito de control valido", bot.extraer_gtin("ref 12345670") == "12345670",
      bot.extraer_gtin("ref 12345670"))
check("un telefono no es un GTIN", bot.extraer_gtin("Llama al 600123456789") == "",
      bot.extraer_gtin("Llama al 600123456789"))
check("el ASIN del enlace no es un GTIN",
      bot.extraer_gtin("https://www.amazon.es/dp/B07CCWCNFR?tag=x") == "",
      bot.extraer_gtin("https://www.amazon.es/dp/B07CCWCNFR?tag=x"))
check("MPN con digitos NO es un GTIN", bot.extraer_gtin("modelo i7-1355U") == "",
      bot.extraer_gtin("modelo i7-1355U"))
check("MPN solo con letras no", bot.extraer_gtin("modelo GXTrust") == "",
      bot.extraer_gtin("modelo GXTrust"))
# El tag de afiliado del propio bot tiene guion y digitos: si se buscara en el
# texto entero, 'gangas054-21' salia como codigo de pieza en casi todas las ofertas.
check("el tag de afiliado no es un GTIN",
      bot.extraer_gtin("Teclado\nhttps://www.amazon.es/dp/B0GTW78BS4?tag=gangas054-21") == "",
      bot.extraer_gtin("Teclado\nhttps://www.amazon.es/dp/B0GTW78BS4?tag=gangas054-21"))
check("precio con miles no es un GTIN", bot.extraer_gtin("Ahora: 1.299,00 € antes 2.999,00 €") == "",
      bot.extraer_gtin("Ahora: 1.299,00 € antes 2.999,00 €"))
check("sin texto -> ''", bot.extraer_gtin("") == "")
check("None -> ''", bot.extraer_gtin(None) == "")

print("\n== extraer_gtin nunca devuelve un hashtag ni un MPN ==")
# Los 28 gtin que havia en data/ eran hashtags ('Blackfriday26') o codigos de
# pieza ('HC5880', '6-Cores', 'RLC-810A'): ninguno era un GTIN y todos se
# publicaban como itemprop="gtin". Un hashtag solo de digitos podria(validandose
# el control) colarse, asi que se quitan antes de buscar.
for texto in ("#BlackFriday26 Auriculares", "#12345678 Auriculares",
              "#BlackFriday26\nEAN 8412345678905"):
    check(f"el hashtag no es un GTIN ({texto.splitlines()[0]!r})",
          "12345678" not in bot.extraer_gtin(texto) or "8412345678905" in bot.extraer_gtin(texto),
          bot.extraer_gtin(texto))
check("hashtag + EAN real -> gana el EAN", bot.extraer_gtin("#12345678 EAN 8412345678905") == "8412345678905",
      bot.extraer_gtin("#12345678 EAN 8412345678905"))

print("\n== extraer_mpn: el codigo de pieza va en su propio campo ==")
check("MPN con digitos", bot.extraer_mpn("modelo i7-1355U") == "i7-1355U", bot.extraer_mpn("modelo i7-1355U"))
check("codigo de pieza del canal", bot.extraer_mpn("MDR-ZX110 Headset") == "MDR-ZX110",
      bot.extraer_mpn("MDR-ZX110 Headset"))
check("MPN solo con letras no", bot.extraer_mpn("modelo GXTrust") == "", bot.extraer_mpn("modelo GXTrust"))
check("el hashtag no es un MPN", bot.extraer_mpn("#BlackFriday26 Auriculares") == "",
      bot.extraer_mpn("#BlackFriday26 Auriculares"))
check("el ASIN no es un MPN", bot.extraer_mpn("https://www.amazon.es/dp/B07CCWCNFR?tag=x") == "",
      bot.extraer_mpn("https://www.amazon.es/dp/B07CCWCNFR?tag=x"))
check("el tag de afiliado no es un MPN",
      bot.extraer_mpn("Teclado\nhttps://www.amazon.es/dp/B0GTW78BS4?tag=gangas054-21") == "",
      bot.extraer_mpn("Teclado\nhttps://www.amazon.es/dp/B0GTW78BS4?tag=gangas054-21"))
check("sin texto -> ''", bot.extraer_mpn("") == "")
check("None -> ''", bot.extraer_mpn(None) == "")

print("\n== el marcador 'Oferta Amazon' se detecta en cualquier caja ==")
# El canal lo escribe en MAYUSCULAS. La comparacion era exacta, asi que 22
# ofertas se publicaban con title y brand 'OFERTA AMAZON' en vez de descartarse:
# 14 de 98 en general.json y 6 de 12 en moviles-electronica.json.
for variante in ("Oferta Amazon", "OFERTA AMAZON", "oferta amazon", "  OFERTA AMAZON  "):
    check(f"marcador detectado: {variante!r}", bot._es_titulo_marcador(variante), variante)
    check(f"se descarta: {variante!r}",
          bot._motivo_descarte({"amazon_url": "https://amazon.es/dp/B1",
                                "title": variante, "price": "9.00 €"}) == "sin titulo", variante)
    check(f"no se publica como marca: {variante!r}", bot.extraer_marca(variante) == "", variante)
check("un titulo real con 'Amazon' no es el marcador", not bot._es_titulo_marcador("Amazon Echo Dot 4"))
check("y su marca si se extrae (dos primeras palabras)", bot.extraer_marca("Amazon Echo Dot 4") == "Amazon Echo",
      bot.extraer_marca("Amazon Echo Dot 4"))

print("\n== extraer_descripcion (el precio no es una descripcion) ==")
# La CTA de otro bot en markdown, con su deep-link de afiliado, se publicaba
# tal cual: '[📉 Miss Avisos te dice cuando baja de
# precio](https://t.me/MissAvisosbot?start=vigilaramazon...)'. Se borra entera,
# con su texto y su URL, porque quedarse con el texto deja el anuncio igual.
_cta = bot.extraer_descripcion(
    "Collar con gps para perros\n"
    "Baja a 49.50 € [📉 Miss Avisos te dice cuando baja de precio]"
    "(https://t.me/MissAvisosbot?start=vigilaramazonB0GT9R4QMQ) Iguala a MM!!")
check("la CTA de otro bot no sale en la descripcion", "MissAvisos" not in _cta, _cta)
check("ni su deep-link de afiliado", "t.me" not in _cta, _cta)
check("ni el markdown que lo envuelve", "](http" not in _cta, _cta)
check("pero el texto del producto se queda", "Collar" in _cta or "49.50" in _cta, _cta)
# 'PRECIO OFERTA' es la etiqueta interna del canal: es maquetacion del mensaje,
# no descripcion del producto, y salia en 22 ofertas.
_int = bot.extraer_descripcion(
    "Auriculares de conduccion osea AfterShokz\n"
    "IP55 por 60,90€. Antes 89,95€ PRECIO OFERTA Los auriculares in-ear")
check("la etiqueta interna del canal no sale", "PRECIO OFERTA" not in _int.upper(), _int)
check("pero la descripcion del producto si", "in-ear" in _int, _int)
# El canal publica a veces '16,91 € (antes 29,99 €)' en una sola linea: como
# descripcion duplicaba el precio y ademas se publicaba como description.
check("linea de precio combinada se descarta",
      bot.extraer_descripcion("Zapatillas Nike\n\n16,91 € (antes 29,99 €)") == "",
      bot.extraer_descripcion("Zapatillas Nike\n\n16,91 € (antes 29,99 €)"))
check("linea de precio con hashtag se descarta",
      bot.extraer_descripcion("Pack 6 desodorantes\n7,23 € (antes 15,39 €) |#Chollos|") == "",
      bot.extraer_descripcion("Pack 6 desodorantes\n7,23 € (antes 15,39 €) |#Chollos|"))
check("el hashtag se quita de la descripcion",
      bot.extraer_descripcion("Zapatillas\n\nAjuste perfecto. |#Chollos|") == "Ajuste perfecto.",
      bot.extraer_descripcion("Zapatillas\n\nAjuste perfecto. |#Chollos|"))
check("CTA ripeada de otro canal se quita",
      bot.extraer_descripcion("Zapatillas\n\n\U0001F449 Míralo en Ofertitas.es") == "",
      bot.extraer_descripcion("Zapatillas\n\n\U0001F449 Míralo en Ofertitas.es"))
check("CTA al final de una linea real solo quita la cola",
      bot.extraer_descripcion("Zapatillas\n\nBotín de cuero con suela de goma. \U0001F449 Míralo en Ofertitas.es")
      == "Botín de cuero con suela de goma.",
      bot.extraer_descripcion("Zapatillas\n\nBotín de cuero con suela de goma. \U0001F449 Míralo en Ofertitas.es"))
check("'ver' al final de una frase no se toca",
      bot.extraer_descripcion("Zapatillas\n\nImpermeable, se nota al ver el resultado.")
      == "Impermeable, se nota al ver el resultado.",
      bot.extraer_descripcion("Zapatillas\n\nImpermeable, se nota al ver el resultado."))
check("descripcion con un precio dentro se conserva",
      bot.extraer_descripcion("Zapatillas\n\nFiltros MPT6474/10 para 10 euros de cafe.")
      == "Filtros MPT6474/10 para 10 euros de cafe.",
      bot.extraer_descripcion("Zapatillas\n\nFiltros MPT6474/10 para 10 euros de cafe."))

print("\n== extraer_marca (sin emojis ni fragmentos) ==")
check("emoji inicial fuera", bot.extraer_marca("\u2328️ GXTrust - Teclado TKL 80%") == "GXTrust",
      bot.extraer_marca("\u2328️ GXTrust - Teclado TKL 80%"))
check("ZWJ fuera", bot.extraer_marca("‍♀️ ghd Plancha de pelo") == "ghd",
      bot.extraer_marca("‍♀️ ghd Plancha de pelo"))
check("marca antes de guion se queda", bot.extraer_marca("Tommy Hilfiger - Camiseta Azul") == "Tommy Hilfiger",
      bot.extraer_marca("Tommy Hilfiger - Camiseta Azul"))
check("'Marks & Spencer' no se parte", bot.extraer_marca("Marks & Spencer Secador") == "Marks & Spencer",
      bot.extraer_marca("Marks & Spencer Secador"))
for titulo in ("Alfombrilla de gaming XXL", "Neceser de viaje", "Sofá de dos plazas",
               "Pulverizador de facial", "Marks &"):
    check(f"fragmento no es marca ({titulo!r})", bot.extraer_marca(titulo) == "",
          bot.extraer_marca(titulo))

print("\n== clasificar_oferta (normalizada, tildes ignoradas) ==")
casos_cat = [
    ("Zapatillas Nike Air Running", "ropa-y-calzado"),
    ("Camiseta Adidas originals", "ropa-y-calzado"),
    ("Smartphone Xiaomi Redmi Note", "moviles-electronica"),
    ("Mando DualSense para PS5", "gaming-consolas"),
    ("Nintendo Switch OLED consola", "gaming-consolas"),
    ("Set de LEGO Star Wars", "juguetes-infantil"),
    ("Champu anticaida Tresemmé", "higiene-cuidado-personal"),
    ("Cuaderno A4 y boligrafos", "papeleria-oficina"),
    ("Producto sin ninguna palabra clave", "general"),
]
for texto, esperado in casos_cat:
    check(f"{texto!r} -> {esperado}", bot.clasificar_oferta(texto) == esperado,
          f"obtenido {bot.clasificar_oferta(texto)}")

print("\n== tildes ==")
check("pantalón == pantalon", bot.clasificar_oferta("Pantalón vaqueros") == "ropa-y-calzado")
check("bañador == banador", bot.clasificar_oferta("Bañador infantil") == "ropa-y-calzado")

print("\n== extraer_enlace_amazon ==")
check("amazon.es", bot.extraer_enlace_amazon("Mira https://www.amazon.es/dp/B0ABC123/x ") == "https://www.amazon.es/dp/B0ABC123/x")
check("amzn.to", bot.extraer_enlace_amazon("Chollazo https://amzn.to/abc") == "https://amzn.to/abc")
check("sin enlace", bot.extraer_enlace_amazon("nada aqui") == "")

print("\n== callbacks de autenticacion ==")
# Telethon tipa code_callback como Callable[[], str] y lo invoca sin argumentos
# (telethon/client/auth.py). Si se le anade un parametro obligatorio, el arranque
# revienta con TypeError en cuanto la sesion necesita autorizacion.
import inspect
import builtins

check("solicitar_codigo no exige argumentos",
      not inspect.signature(bot.solicitar_codigo).parameters
      or all(p.default is not inspect.Parameter.empty
             for p in inspect.signature(bot.solicitar_codigo).parameters.values()),
      f"firma {inspect.signature(bot.solicitar_codigo)}")
check("pedir_telefono no exige argumentos",
      not inspect.signature(bot.pedir_telefono).parameters
      or all(p.default is not inspect.Parameter.empty
             for p in inspect.signature(bot.pedir_telefono).parameters.values()),
      f"firma {inspect.signature(bot.pedir_telefono)}")

_entrada_real = builtins.input
try:
    builtins.input = lambda prompt="": "600111222"
    check("pedir_telefono devuelve lo tecleado", bot.pedir_telefono() == "600111222")
    check("pedir_telefono recuerda el telefono", bot._TELEFONO == "600111222", f"{bot._TELEFONO!r}")

    builtins.input = lambda prompt="": "12345"
    check("solicitar_codigo se puede llamar sin argumentos", bot.solicitar_codigo() == "12345")

    builtins.input = lambda prompt="": "   "
    check("codigo vacio -> None", bot.solicitar_codigo() is None)

    def _EOF(prompt=""):
        raise EOFError
    builtins.input = _EOF
    check("EOF no revienta", bot.solicitar_codigo() is None)
    check("EOF en telefono no revienta", bot.pedir_telefono() == "")
finally:
    builtins.input = _entrada_real

print("\n== escritura atomica / orden por ID / limite ==")
prueba = Path(tempfile.mkdtemp(prefix="_prueba_json_"))

async def prueba_escritura():
    bot.DATA_PATH = prueba
    f = prueba / "general.json"
    # insertar de forma desordenada a proposito
    for mid in [105, 101, 110, 103, 99, 108]:
        await bot.actualizar_json("general", MensajeFalso(mid))
    datos = json.loads(f.read_text(encoding="utf-8"))
    return datos

class MensajeFalso:
    """Mensaje con los tres datos que una oferta necesita para publicarse.

    Si le falta el enlace o el precio, actualizar_json lo descarta (ver
    _motivo_descarte) y este test de escritura no escribiria nada.
    """
    def __init__(self, mid):
        self.id = mid
        self.date = None
        self.media = None
        self.text = (f"Zapatillas oferta numero {mid}\n"
                     f"Ahora 10,00 €\nhttps://www.amazon.es/dp/B{mid:09d}")
        self.message = self.text
        self.entities = None

class MensajeIncompleto(MensajeFalso):
    def __init__(self, mid, texto):
        super().__init__(mid)
        self.text = texto
        self.message = texto

print("\n== _motivo_descarte ==")
casos_descarte = [
    ({"amazon_url": "", "title": "Zapatillas", "price": "9.00 €"}, "sin enlace de Amazon"),
    ({"amazon_url": "https://amazon.es/dp/B1", "title": "", "price": "9.00 €"}, "sin titulo"),
    ({"amazon_url": "https://amazon.es/dp/B1", "title": "Oferta Amazon", "price": "9.00 €"}, "sin titulo"),
    ({"amazon_url": "https://amazon.es/dp/B1", "title": "Zapatillas", "price": ""}, "sin precio"),
    ({"amazon_url": "https://amazon.es/dp/B1", "title": "ab", "price": "9.00 €"}, "titulo demasiado corto"),
]
for oferta, esperado in casos_descarte:
    check(f"descartada: {esperado}",
          bot._motivo_descarte(oferta) == esperado, bot._motivo_descarte(oferta))
check("oferta completa -> publicable",
      bot._motivo_descarte({"amazon_url": "https://amazon.es/dp/B1", "title": "Zapatillas Nike",
                            "price": "9.00 €"}) is None)

print("\n== actualizar_json no escribe lo que no es publicable ==")
async def prueba_descarte():
    d = Path(tempfile.mkdtemp(prefix="_prueba_descarte_"))
    bot.DATA_PATH = d
    casos = [
        (9001, "Zapatillas Nike\nAhora 39,99 €"),                    # sin enlace
        (9002, "Aviso del canal\nhttps://t.me/canal/1"),             # sin enlace ni precio
        (9003, "Camiseta\nhttps://www.amazon.es/dp/B0SINPRECIO"),    # sin precio
        (9004, "Solo texto sin nada"),                              # sin nada
        (9005, "Champu Tresemme\nAhora 11,99 €\nhttps://www.amazon.es/dp/B0OK"),
    ]
    guardados = []
    for mid, texto in casos:
        if await bot.actualizar_json("general", MensajeIncompleto(mid, texto)):
            guardados.append(mid)
    ids_en_json = [o["id"] for o in json.loads((d / "general.json").read_text(encoding="utf-8"))]
    shutil.rmtree(d, ignore_errors=True)
    return guardados, ids_en_json

_g, _j = asyncio.run(prueba_descarte())
check("solo se publica la oferta completa", _g == [9005], _g)
check("el JSON solo contiene la oferta completa", _j == [9005], _j)

async def main():
    datos = await prueba_escritura()
    ids = [d["id"] for d in datos]
    check("orden descendente por ID", ids == sorted(ids, reverse=True), f"ids={ids}")
    check("no se recorta por debajo del limite", len(datos) == 6, f"n={len(datos)}")
    check("conserva los 6 mas recientes", ids == [110, 108, 105, 103, 101, 99], f"ids={ids}")

    # El recorte se comprueba contra MAX_OFERTAS, no contra un numero fijo:
    # el limite es configurable y el valor por defecto subio a 100 al anadir
    # el reinicio del catalogo, asi que un 30 fijo aqui solo daria fallos falsos.
    tope = bot.MAX_OFERTAS

    # recorte real: tope + 15 mensajes, deben quedar los 'tope' mas nuevos
    for f in prueba.glob("*.json"):
        f.unlink()
    n = tope + 15
    await asyncio.gather(*[bot.actualizar_json("general", MensajeFalso(500 + i)) for i in range(n)])
    ids = [d["id"] for d in json.loads((prueba / "general.json").read_text(encoding="utf-8"))]
    check(f"{n} mensajes -> quedan {tope}", len(ids) == tope, f"n={len(ids)}")
    check(f"quedan los {tope} mas recientes",
          ids == list(range(500 + n - 1, 500 + n - 1 - tope, -1)), f"ids={ids}")

    # TOPE POR SECCION: las categorias se recortan a MAX_OFERTAS_CATEGORIA,
    # que es menor que el del feed global. El feed global no se deja intacto al
    # probar las categorias: se lee aparte para que un fallo aqui no oculte al
    # de general, y viceversa.
    for f in prueba.glob("*.json"):
        f.unlink()
    tope_cat = bot.MAX_OFERTAS_CATEGORIA
    n_cat = tope_cat + 15
    await asyncio.gather(*[bot.actualizar_json("gaming-consolas", MensajeFalso(500 + i))
                           for i in range(n_cat)])
    ids_cat = [d["id"] for d in json.loads((prueba / "gaming-consolas.json").read_text(encoding="utf-8"))]
    check(f"seccion: {n_cat} mensajes -> quedan {tope_cat}", len(ids_cat) == tope_cat, f"n={len(ids_cat)}")
    check(f"seccion: quedan los {tope_cat} mas recientes",
          ids_cat == list(range(500 + n_cat - 1, 500 + n_cat - 1 - tope_cat, -1)), f"ids={ids_cat}")
    # n_cat supera el tope de seccion pero no llega al del feed global, asi que
    # general.json debe conservarlos TODOS. Si el tope se aplicase por error a
    # general, aqui se quedaria en tope_cat en lugar de n_cat.
    ids_gen = [d["id"] for d in json.loads((prueba / "general.json").read_text(encoding="utf-8"))]
    check(f"la seccion no arrastra su tope al feed global (guarda los {n_cat})",
          len(ids_gen) == n_cat, f"n={len(ids_gen)}, esperado={n_cat}")
    check("el feed global y la seccion tienen topes distintos",
          tope_cat < tope, f"categoria={tope_cat}, general={tope}")

    # CONCURRENCIA: todos a la vez. El cerrojo mantiene coherente el archivo,
    # y el orden por ID asegura que sobreviven los mas recientes.
    for f in prueba.glob("*.json"):
        f.unlink()
    await asyncio.gather(*[bot.actualizar_json("general", MensajeFalso(200 + i)) for i in range(n)])
    ids = [d["id"] for d in json.loads((prueba / "general.json").read_text(encoding="utf-8"))]
    check(f"{n} escrituras concurrentes sin perdidas", len(ids) == tope, f"n={len(ids)}")
    check("orden correcto tras concurrencia", ids == sorted(ids, reverse=True), f"ids={ids}")
    check(f"conserva los {tope} mas nuevos",
          ids == list(range(200 + n - 1, 200 + n - 1 - tope, -1)), f"ids={ids}")

    # el fichero nunca debe quedar corrupto ni con extension .tmp colgando
    check("sin ficheros .tmp residuales", not list(prueba.glob("*.tmp")), list(prueba.glob("*.tmp")))
    check("JSON valido en disco",
          isinstance(json.loads((prueba / "general.json").read_text(encoding="utf-8")), list))

    # ── PUBLICACION PERIODICA ──
    # El fallo que se comprueba aqui: una oferta que entra justo despues de
    # un push se queda sin subir por el agrupado, y sin otro mensaje nunca
    # sale. Se reproduce con el agrupado real y un publicar_en_git simulado
    # que lo respeta igual, para no tocar el repositorio de verdad.
    print("\n== la oferta atascada por el agrupado se publica sola ==")
    intervalo = bot.PUBLICAR_CADA_S
    # Se encoge el agrupado en vez de esperar al real: lo que se prueba es la
    # logica de "publicar cada N sin que entre nada", no el reloj.
    bot.PUBLICAR_CADA_S = 0.05
    publicaciones = []

    async def publicar_falso(forzar=False):
        ahora = time.monotonic()
        if not forzar and (ahora - bot._ultima_publicacion) < bot.PUBLICAR_CADA_S:
            return False
        bot._ultima_publicacion = ahora
        publicaciones.append(forzar)
        return True

    original = bot.publicar_en_git
    bot.publicar_en_git = publicar_falso
    try:
        # El agrupado, por si mismo: dos intentos seguidos dentro de la
        # ventana dan un solo push, que es lo que evita un commit por oferta.
        # _ultima_publicacion se pone a 0 para simular "hace mucho que no se
        # publica": con el reloj ya actualizado el primer intento caeria dentro
        # de la ventana, que es justo el agrupado funcionando.
        bot._ultima_publicacion = 0.0
        check("el agrupado deja pasar un intento fuera de la ventana",
              await bot.publicar_en_git() is True, "no publico")
        check("el agrupado agrupa el segundo intento inmediato",
              await bot.publicar_en_git() is False, "publico dos veces seguidas")
        check("el agrupado no se salta con forzar=True",
              await bot.publicar_en_git(forzar=True) is True, "forzar no publico")

        # Y el fallo original: sin que entre ningun mensaje, la tarea tiene que
        #.publish por su cuenta.
        publicaciones.clear()
        bot._ultima_publicacion = time.monotonic()
        tarea = asyncio.create_task(bot._tarea_publicar_periodica())
        await asyncio.sleep(0.3)   # varias ventanas de agrupado
        tarea.cancel()
        await asyncio.gather(tarea, return_exceptions=True)
        check("la tarea periodica publica sola, sin mensajes nuevos",
              len(publicaciones) >= 1, f"publicaciones={len(publicaciones)}")
        check("no publica en cada vuelta (el agrupado la frena)",
              len(publicaciones) < 6, f"publicaciones={len(publicaciones)}")

        # Y el cierre ordenado, que es la otra via de salida.
        publicaciones.clear()
        await bot.publicar_en_git(forzar=True)
        check("el cierre ordenado publica lo pendiente",
              len(publicaciones) == 1, f"publicaciones={len(publicaciones)}")
    finally:
        bot.publicar_en_git = original
        bot.PUBLICAR_CADA_S = intervalo

    # ── PARADA LIMPIA ──
    print("\n== parar el bot no es un hardkill ==")
    # main() consulta _evento_parada entre reconnect y reconnect: si no se
    # comprobara, se levantaria otra vez justo cuando se le pide cerrar.
    fuente = inspect.getsource(bot.main)
    check("main() sale del bucle cuando se pide parar",
          "_evento_parada.is_set()" in fuente, "no comprueba el evento de parada")
    # El orden importa y no basta con que la comprobacion exista: si se
    # comprueba despues de reconectar, el bot se levanta otra vez justo cuando
    # se le pide cerrar, que es el fallo que evita este break.
    check("main() comprueba la parada antes de reconectar",
          fuente.index("if _evento_parada.is_set():\n                break")
          < fuente.index("[CONEXION] Perdida"),
          "comprueba la parada despues de reconectar")
    check("main() cancela las tareas auxiliares", "tarea.cancel()" in fuente, "no cancela nada")
    check("main() desconecta al salir", "await client.disconnect()" in fuente, "no desconecta")

    # El manejador de senales es lo que convierte Ctrl+C/SIGTERM en una parada
    # ordenada. Sin el, hay que matar el proceso y se pierde lo pendiente.
    for nombre in ("_pedir_parada", "_instalar_manejadores_de_senales", "_tarea_duracion"):
        check(f"existe {nombre}()", callable(getattr(bot, nombre, None)), "no encontrada")
    fuente_senales = inspect.getsource(bot._instalar_manejadores_de_senales)
    check("se atienden SIGINT y SIGTERM",
          "SIGINT" in fuente_senales and "SIGTERM" in fuente_senales, "falta alguna senal")

    # La periodica no puede arrancar antes del backfill: si no, empujaria a git
    # un catalogo a medio construir, con los JSON recien vaciados.
    check("la tarea periodica se crea despues de recuperar_mensajes_perdidos()",
          fuente.index("recuperar_mensajes_perdidos()")
          < fuente.index("_tarea_publicar_periodica()"),
          "se crea antes del backfill")

asyncio.run(main())

shutil.rmtree(prueba, ignore_errors=True)

print("\n" + ("=" * 50))
print("TODO CORRECTO" if fallos == 0 else f"{fallos} PRUEBAS FALLIDAS")
sys.exit(1 if fallos else 0)

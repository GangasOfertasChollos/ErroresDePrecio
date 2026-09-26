"""Pruebas de las funciones puras de bot.py sin tocar Telegram."""
import os, sys, json, asyncio, importlib.util
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

print("\n== escritura atomica / orden por ID / limite ==")
import tempfile
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
    def __init__(self, mid):
        self.id = mid
        self.date = None
        self.media = None
        self.text = f"Oferta numero {mid}"
        self.message = self.text
        self.entities = None

async def main():
    datos = await prueba_escritura()
    ids = [d["id"] for d in datos]
    check("orden descendente por ID", ids == sorted(ids, reverse=True), f"ids={ids}")
    check("no se recorta por debajo del limite", len(datos) == 6, f"n={len(datos)}")
    check("conserva los 6 mas recientes", ids == [110, 108, 105, 103, 101, 99], f"ids={ids}")

    # recorte real: 45 mensajes, deben quedar los 30 mas nuevos
    for f in prueba.glob("*.json"):
        f.unlink()
    await asyncio.gather(*[bot.actualizar_json("general", MensajeFalso(500 + i)) for i in range(45)])
    ids = [d["id"] for d in json.loads((prueba / "general.json").read_text(encoding="utf-8"))]
    check("45 mensajes -> quedan 30", len(ids) == bot.MAX_OFERTAS, f"n={len(ids)}")
    check("quedan los 30 mas recientes (515-544)",
          ids == list(range(544, 514, -1)), f"ids={ids}")

    # CONCURRENCIA: 60 mensajes a la vez. El cerrojo mantiene coherente el
    # archivo, y el orden por ID asegura que sobreviven los mas recientes.
    for f in prueba.glob("*.json"):
        f.unlink()
    await asyncio.gather(*[bot.actualizar_json("general", MensajeFalso(200 + i)) for i in range(60)])
    ids = [d["id"] for d in json.loads((prueba / "general.json").read_text(encoding="utf-8"))]
    check("60 escrituras concurrentes sin perdidas", len(ids) == bot.MAX_OFERTAS, f"n={len(ids)}")
    check("orden correcto tras concurrencia", ids == sorted(ids, reverse=True), f"ids={ids}")
    check("conserva los 30 mas nuevos (230-259)",
          ids == list(range(259, 229, -1)), f"ids={ids}")

    # el fichero nunca debe quedar corrupto ni con extension .tmp colgando
    check("sin ficheros .tmp residuales", not list(prueba.glob("*.tmp")), list(prueba.glob("*.tmp")))
    check("JSON valido en disco",
          isinstance(json.loads((prueba / "general.json").read_text(encoding="utf-8")), list))

asyncio.run(main())

import shutil
shutil.rmtree(prueba, ignore_errors=True)

print("\n" + ("=" * 50))
print("TODO CORRECTO" if fallos == 0 else f"{fallos} PRUEBAS FALLIDAS")
sys.exit(1 if fallos else 0)

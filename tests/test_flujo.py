"""Prueba de extremo a extremo: un mensaje de Telegram -> JSON -> HTML en la pagina.

Simula un mensaje real con foto, comprueba que el bot lo clasifica y guarda bien,
y despues renderiza el HTML con assets/app.js y verifica que la oferta aparece
con su precio, su enlace y su JSON-LD.
"""
import os, sys, json, asyncio, subprocess, importlib.util, shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tests"))

TMP = Path(os.environ.get("TEMP", ".")) / "gangas_e2e"
if TMP.exists():
    shutil.rmtree(TMP)
TMP.mkdir(parents=True)

# Copia del proyecto con data/ vacio, para no tocar los datos reales
for f in ["bot.py", "categorias.json"]:
    shutil.copy(RAIZ / f, TMP / f)
(TMP / "data").mkdir()
for j in (ORIGEN := (RAIZ / "data")).glob("*.json"):
    (TMP / "data" / j.name).write_text("[]\n", encoding="utf-8")
shutil.copytree(RAIZ / "assets", TMP / "assets")
for h in RAIZ.glob("*.html"):
    shutil.copy(h, TMP / h.name)

os.environ.update(dict(API_ID="1", API_HASH="h", TELEGRAM_CHANNEL="@x"))
spec = importlib.util.spec_from_file_location("bot", TMP / "bot.py")
bot = importlib.util.module_from_spec(spec); spec.loader.exec_module(bot)

fallos = 0
def check(n, cond, det=""):
    global fallos
    if cond: print("  OK   " + n)
    else: fallos += 1; print("  FALLO " + n + " -> " + str(det))


class MsgReal:
    """Mensaje de Telegram con foto, como los que publica el canal."""
    def __init__(self, mid, texto):
        self.id = mid
        self.date = None
        self.media = object()
        self.text = texto
        self.message = texto
        self.entities = None

    async def download_media(self, file=None, **_):
        await asyncio.sleep(0.001)
        destino = Path(file)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(b"PNG-falso")
        return str(destino)


MENSAJES = [
    (1001, "Zapatillas Nike Air Zoom Running\nAntes ~~299,99\u20ac~~\nAhora 89,95\u20ac\n"
           "https://www.amazon.es/dp/B0XYZ123/ref=sr_1_1"),
    (1002, "Smartphone Xiaomi Redmi Note 13 Pro\nPrecio: 249,99\u20ac\n"
           "https://amzn.to/abc123"),
    (1003, "Set LEGO Star Wars 75301\n~~119,99\u20ac~~ 89,99\u20ac\n"
           "https://www.amazon.es/dp/B0LEGO1"),
    (1004, "Mando DualSense PS5\nPor solo 59,95\u20ac\nhttps://www.amazon.es/dp/B0MANDO1"),
    (1005, "Champu Tresemme Keratin Smooth\nAhora 11,99\u20ac\nhttps://www.amazon.es/dp/B0CHAMP1"),
]


async def main():
    print("\n== 0. Las imagenes ya no se guardan en disco ==")
    # El bot no descarga nada: `image` guarda la URL de la miniatura. Este test
    # se asegura de que data/images/ no aparece por el camino.
    await bot.procesar_mensaje(MsgReal(1000, "Camiseta de prueba\nAhora 10,00\u20ac\n"
                                             "https://www.amazon.es/dp/B0TEST"), origen="e2e")
    check("no se crea data/images/", not (TMP / "data" / "images").exists(),
          list((TMP / "data").iterdir()))
    oferta0 = json.loads((TMP / "data" / "general.json").read_text(encoding="utf-8"))[0]
    check("la oferta se guarda con la imagen vacia (sin unfurl)", oferta0["image"] == "",
          oferta0["image"])
    check("limpiar_imagenes_huerfanas ya no borra nada", bot.limpiar_imagenes_huerfanas() == 0)

    print("\n== 1. El bot procesa 5 mensajes con foto ==")
    for mid, texto in MENSAJES:
        await bot.procesar_mensaje(MsgReal(mid, texto), origen="e2e")

    print("\n== 2. Clasificacion ==")
    esperado_cat = {1001: "ropa-y-calzado", 1002: "moviles-electronica",
                    1003: "juguetes-infantil", 1004: "gaming-consolas",
                    1005: "higiene-cuidado-personal"}
    general = json.loads((TMP / "data" / "general.json").read_text(encoding="utf-8"))
    por_id = {o["id"]: o for o in general}
    for mid, cat in esperado_cat.items():
        check(f"mensaje {mid} -> {cat}", por_id[mid]["categoria"] == cat, por_id[mid]["categoria"])

    print("\n== 3. Precios extraidos ==")
    esperado_precio = {1001: "89.95 €", 1002: "249.99 €", 1003: "89.99 €",
                       1004: "59.95 €", 1005: "11.99 €"}
    for mid, precio in esperado_precio.items():
        check(f"mensaje {mid} -> {precio}", por_id[mid]["price"] == precio, por_id[mid]["price"])

    print("\n== 4. Enlaces ==")
    for mid, _ in MENSAJES:
        check(f"mensaje {mid}: enlace de amazon",
              por_id[mid]["amazon_url"].startswith(("https://www.amazon.es/", "https://amzn.to/")),
              por_id[mid]["amazon_url"])
        check(f"mensaje {mid}: sin binarios en disco",
              not por_id[mid]["image"].startswith("data/"), por_id[mid]["image"])

    print("\n== 5. Cada oferta esta en su JSON de categoria y en general ==")
    for mid, cat in esperado_cat.items():
        en_cat = json.loads((TMP / "data" / f"{cat}.json").read_text(encoding="utf-8"))
        check(f"mensaje {mid} presente en {cat}.json",
              any(o["id"] == mid for o in en_cat), [o["id"] for o in en_cat])
    # +1 oferta del paso 0 (id 1000, "Camiseta" -> ropa y calzado)
    check("general.json tiene las 6 ofertas", len(general) == 6, len(general))
    check("general.json ordenado de mayor a menor id",
          [o["id"] for o in general] == [1005, 1004, 1003, 1002, 1001, 1000],
          [o["id"] for o in general])

    print("\n== 6. La pagina HTML renderiza la oferta ==")
    r = subprocess.run(["node", str(RAIZ / "tests" / "test_app.js")],
                       capture_output=True, text=True, cwd=TMP, encoding="utf-8", errors="replace")
    salida = r.stdout or ""
    check("test_app.js pasa con los datos generados", "TODO CORRECTO" in salida,
          (salida.strip().splitlines() or ["(sin salida)"])[-1])
    check("node no reporta errores", r.returncode == 0, r.stderr[-300:])

    print("\n== 7. El HTML de la pagina es coherente con el JSON ==")
    html_cat = (TMP / "ropa-y-calzado.html").read_text(encoding="utf-8")
    check("la pagina carga assets/app.js", 'src="assets/app.js"' in html_cat)
    check("la pagina declara su feed", 'data-feed="ropa-y-calzado"' in html_cat)
    check("la pagina declara og:image", "assets/og-image.png" in html_cat)
    check("no queda ningun binario en data/", not (TMP / "data" / "images").exists())

asyncio.run(main())
shutil.rmtree(TMP, ignore_errors=True)
print("\n" + "=" * 56)
print("TODO CORRECTO" if fallos == 0 else f"{fallos} FALLOS")
raise SystemExit(1 if fallos else 0)

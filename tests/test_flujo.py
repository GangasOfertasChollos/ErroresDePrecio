"""Prueba de extremo a extremo: un mensaje de Telegram -> JSON -> HTML en la pagina.

Simula un mensaje real con foto, comprueba que el bot lo clasifica y guarda bien,
y despues renderiza el HTML con assets/app.js y verifica que la oferta aparece
con su precio, su enlace y su JSON-LD.
"""
import os, sys, json, asyncio, subprocess, importlib.util, shutil, logging, tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tests"))

# Directorio propio de esta ejecucion, con un nombre unico: con un nombre fijo
# dos ejecuciones simultaneas (o una anterior que dejo el directorio a medias)
# se pisan y el import de bot.py falla con FileNotFoundError de forma
# intermitente, muy dificil de reproducir.
TMP = Path(tempfile.mkdtemp(prefix="gangas_e2e_"))
print(f"  (directorio de trabajo: {TMP})")

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

def cerrar_log_del_bot():
    """Cierra el bot.log que el modulo abre al importarse.

    logging.basicConfig installs un FileHandler sobre TMP/bot.log y el log
    raiz no expone la lista: los handlers se buscamos en todos los loggers.
    Sin cerrarlos, Windows mantiene el fichero bloqueado, rmtree no puede
    borrarlo y cada ejecucion deja una copia del proyecto en TEMP.
    """
    for lg in [logging.getLogger()] + [logging.getLogger(n)
                                      for n in logging.root.manager.loggerDict]:
        for h in list(getattr(lg, "handlers", [])):
            if isinstance(h, logging.FileHandler):
                h.close()
                lg.removeHandler(h)

cerrar_log_del_bot()

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


class ClienteFalso:
    """Sustituye al cliente de Telethon y cuenta las descargas de imagen.

    El paso que se elimino de extraer_imagen bajaba la foto con
    `client.download_media(mensaje.media, file=...)`, o sea usando el cliente
    del bot, no el metodo del mensaje. Con el cliente real sin conectar, la
    descarga fallaba y el except se comia el error, de modo que data/images/
    no llegaba a crearse por casualidad y el test pasaba sin comprobar nada.
    Aqui el cliente falso escribe el fichero de verdad, asi que si alguien
    vuelve a meter la descarga, el test falla.
    """
    descargas = 0

    async def download_media(self, media, file=None, **_):
        ClienteFalso.descargas += 1
        destino = Path(file)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(b"PNG-falso")
        return str(destino)

    async def get_messages(self, canal=None, limit=0, **_):
        # El historial del canal: los mensajes de MENSAJES, del mas nuevo al
        # mas viejo, como los devuelve Telethon.
        return [MsgReal(mid, texto) for mid, texto in reversed(MENSAJES)][:limit]


bot.client = ClienteFalso()


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
    check("el bot no intenta descargar la foto del mensaje", ClienteFalso.descargas == 0,
          f"{ClienteFalso.descargas} descargas")
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
    check("ninguno de los 6 mensajes con foto ha descargado nada", ClienteFalso.descargas == 0,
          f"{ClienteFalso.descargas} descargas")

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

    print("\n== 8. Cada arranque vacia el catalogo y lo reconstruye ==")
    # Con REINICIAR_CATALOGO los JSON se vacian y se repueblan con el
    # historial, para que nunca acumulen ofertas caducadas ni edits a mano.
    check("REINICIAR_CATALOGO viene activado", bot.REINICIAR_CATALOGO is True,
          bot.REINICIAR_CATALOGO)

    # Una oferta caduca que no esta en el historial actual: al reiniciar el
    # catalogo tiene que desaparecer, no quedarse pegada.
    caducada = dict(por_id[1001], id=9999, title="Oferta caducada de hace un mes")
    (TMP / "data" / "general.json").write_text(
        json.dumps([caducada] + general, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    check("antes de reiniciar, la caducada sigue ahi",
          any(o["id"] == 9999 for o in
              json.loads((TMP / "data" / "general.json").read_text(encoding="utf-8"))))

    await bot.recuperar_mensajes_perdidos()

    general2 = json.loads((TMP / "data" / "general.json").read_text(encoding="utf-8"))
    check("la oferta caducada se ha ido al reiniciar",
          not any(o["id"] == 9999 for o in general2), [o["id"] for o in general2])
    check("el catalogo se ha reconstruido con los 5 mensajes del canal",
          [o["id"] for o in general2] == [1005, 1004, 1003, 1002, 1001],
          [o["id"] for o in general2])
    check("reiniciar no duplica ofertas", len(general2) == len({o["id"] for o in general2}))
    # La oferta 1000 se proceso en el paso 0 pero no viene del historial:
    # al reconstruir desde el canal desaparece, que es lo que se busca.
    check("lo que no esta en el canal desaparece", 1000 not in [o["id"] for o in general2],
          [o["id"] for o in general2])

    print("\n== 8b. Las imagenes tambien se borran ==")
    # Si algo vuelve a crear data/images/, el reinicio lo elimina: dentro solo
    # puede haber binarios que el navegador no puede resolver desde GitHub Pages.
    imagenes = TMP / "data" / "images"
    imagenes.mkdir(parents=True, exist_ok=True)
    for n in (700, 701, 702):
        (imagenes / f"oferta_{n}.jpg").write_bytes(b"JPEG-falso" * 100)
    (imagenes / "sub").mkdir()
    (imagenes / "sub" / "oferta_703.jpg").write_bytes(b"JPEG-falso")
    check("hay imagenes antes de reiniciar", len(list(imagenes.rglob("*.jpg"))) == 4,
          list(imagenes.rglob("*.jpg")))

    await bot.recuperar_mensajes_perdidos()

    check("data/images/ borrado tras reiniciar", not imagenes.exists(), list(TMP.joinpath("data").iterdir()))
    check("no queda ninguna imagen suelta en data/",
          not any(p.suffix.lower() in (".jpg", ".jpeg", ".png", ".gif", ".webp")
                  for p in (TMP / "data").rglob("*")),
          [str(p) for p in (TMP / "data").rglob("*") if p.is_file()])

    print("\n== 8c. Lo no publicable se descarta ==")
    # Un mensaje sin enlace no lleva a ninguna parte, y uno sin precio no
    # sirve en un sitio de errores de precio: no deben acabar en los JSON.
    for mid, texto in [(2001, "Zapatillas Nike Air\nAhora 39,99 \u20ac"),
                       (2002, "Aviso: el canal cambia de horario\nhttps://t.me/canal/1"),
                       (2003, "Camiseta de prueba\nhttps://www.amazon.es/dp/B0SINPRECIO")]:
        await bot.procesar_mensaje(MsgReal(mid, texto), origen="e2e")
    tras = json.loads((TMP / "data" / "general.json").read_text(encoding="utf-8"))
    ids_tras = [o["id"] for o in tras]
    check("mensaje sin enlace no se publica", 2001 not in ids_tras, ids_tras)
    check("mensaje sin precio no se publica", 2003 not in ids_tras, ids_tras)
    check("todas las ofertas publicadas tienen enlace",
          all(o["amazon_url"] for o in tras), [o["id"] for o in tras if not o["amazon_url"]])
    check("todas las ofertas publicadas tienen precio",
          all(o["price"] for o in tras), [o["id"] for o in tras if not o["price"]])

    print("\n== 9. Si Telegram falla, el catalogo se conserva ==")
    # El vaciado va despues de leer el historial a proposito: si la lectura
    # falla, un vaciado previo dejaria la web vacia y sin repuesto.
    antes = (TMP / "data" / "general.json").read_text(encoding="utf-8")

    class ClienteSinHistorial(ClienteFalso):
        async def get_messages(self, *a, **kw):
            raise ConnectionError("sin red")

    bot.client = ClienteSinHistorial()
    await bot.recuperar_mensajes_perdidos()
    check("general.json intacto tras un fallo de Telegram",
          (TMP / "data" / "general.json").read_text(encoding="utf-8") == antes,
          "el catalogo se vacio pese al fallo")

    class ClienteSinMensajes(ClienteFalso):
        async def get_messages(self, *a, **kw):
            return []

    bot.client = ClienteSinMensajes()
    await bot.recuperar_mensajes_perdidos()
    check("general.json intacto si el canal no devuelve mensajes",
          (TMP / "data" / "general.json").read_text(encoding="utf-8") == antes,
          "el catalogo se vacio pese a no haber mensajes")
    bot.client = ClienteFalso()

    print("\n== 10. Cuantos mensajes hay que leer para llenar los huecos ==")
    # Solo se publica el mensaje que tiene enlace, titulo y precio. De los
    # ultimos 100 mensajes del canal 84 eran ofertas, asi que leer 100 no llena
    # 100 huecos: BACKFILL_LIMIT tiene que ser MAYOR que MAX_OFERTAS. Al
    # reves (leer menos de lo que se guarda) no hay forma de llenar el
    # catalogo, y el bot lo avisa y corrige al arrancar.
    check("MAX_OFERTAS por defecto = 100", bot.MAX_OFERTAS == 100, bot.MAX_OFERTAS)
    check("BACKFILL_LIMIT por defecto = 130", bot.BACKFILL_LIMIT == 130, bot.BACKFILL_LIMIT)
    print("\n== 11. La verificacion avisa si el catalogo queda corto ==")
    # _verificar_backfill no lanza: avisa por log y el bot sigue escuchando.
    general3 = json.loads((TMP / "data" / "general.json").read_text(encoding="utf-8"))
    check("general.json tiene todas las ofertas del canal",
          len(general3) == 5, f"{len(general3)} de 5")

    # Se captura el log para comprobar el aviso, no solo que no reviente.
    class Manos(logging.Handler):
        def __init__(self): super().__init__(); self.lineas = []
        def emit(self, registro): self.lineas.append(registro.getMessage())

    manos = Manos()
    bot.log.addHandler(manos)

    await bot._verificar_backfill(list(range(1001, 1006)), len(general3))
    texto = "\n".join(manos.lineas)
    check("catalogo completo: lo dice", "general.json completo: 5/5" in texto, texto[-300:])
    check("recuento por categoria en el log", "por categoria ->" in texto, texto[-300:])

    # Con MAX_OFERTAS recortando por debajo de lo leido, general.json se queda
    # corto: debe avisar del numero exacto que falta, y seguir sin abortar.
    manos.lineas.clear()
    (TMP / "data" / "general.json").write_text("[]\n", encoding="utf-8")
    await bot._verificar_backfill(list(range(1001, 1006)), 5)
    texto = "\n".join(manos.lineas)
    check("catalogo corto: avisa cuantas faltan", "FALTAN 5 ofertas de las 5" in texto, texto[-300:])
    check("catalogo corto: sugiere subir BACKFILL_LIMIT", "sube BACKFILL_LIMIT" in texto, texto[-300:])
    check("catalogo corto: no aborta", True)

    manos.lineas.clear()
    (TMP / "data" / "general.json").write_text(
        json.dumps(general3, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    bot.AUTO_PUBLICAR = False
    await bot._verificar_backfill(list(range(1001, 1006)), len(general3))
    texto = "\n".join(manos.lineas)
    check("sin AUTO_PUBLICAR avisa de que la web no se actualiza",
          "AUTO_PUBLICAR=0" in texto, texto[-300:])
    bot.AUTO_PUBLICAR = True
    bot.log.removeHandler(manos)

    check("se leen mas mensajes de los que se guardan", bot.BACKFILL_LIMIT > bot.MAX_OFERTAS,
          f"BACKFILL_LIMIT={bot.BACKFILL_LIMIT} MAX_OFERTAS={bot.MAX_OFERTAS}")
    # El recorte debe dejar exactamente MAX_OFERTAS cuando sobran.
    print("\n== 12. El recorte guarda las MAX_OFERTAS mas recientes ==")
    # Va al final porque vacia data/: la seccion 11 necesita el catalogo.
    for f in (TMP / "data").glob("*.json"):
        f.unlink()
    tope_previo = bot.MAX_OFERTAS
    bot.MAX_OFERTAS = 8
    for i in range(30):
        mid = 3000 + i
        # URL distinta por mensaje: _guardar_en_archivo deduplica por
        # amazon_url, asi que con el mismo texto solo se guardaria el primero.
        await bot.actualizar_json("general", MsgReal(mid,
            f"Zapatillas Nike Air Zoom Running {mid}\nAhora 89,95\u20ac\n"
            f"https://www.amazon.es/dp/B{mid:07d}"))
    ids = [o["id"] for o in json.loads((TMP / "data" / "general.json").read_text(encoding="utf-8"))]
    check("el recorte deja las MAX_OFERTAS mas recientes", len(ids) == 8, f"n={len(ids)}")
    check("y son las 8 mas nuevas", ids == list(range(3029, 3021, -1)), f"ids={ids}")
    bot.MAX_OFERTAS = tope_previo
    for f in (TMP / "data").glob("*.json"):
        f.unlink()

    await bot.recuperar_mensajes_perdidos()   # se repuebla el temporal

try:
    asyncio.run(main())
finally:
    # La limpieza va en finally: si main() revienta, el directorio se borra
    # igual y no se acumulan copias del proyecto en TEMP.
    shutil.rmtree(TMP, ignore_errors=True)
print("\n" + "=" * 56)
print("TODO CORRECTO" if fallos == 0 else f"{fallos} FALLOS")
raise SystemExit(1 if fallos else 0)

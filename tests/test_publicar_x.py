"""Pruebas del script de publicacion en X.

Lo que se comprueba aqui es la parte que no depende de X: como se mide la
longitud de un post (X cuenta las URLs como 23 caracteres y los emojis como
dos), como se arma el texto a partir de una oferta y como se lleva el estado
de lo ya publicado.

Para el descubrimiento de los ids de operacion y la subida de imagen hace
falta una sesion real de x.com: eso se prueba a mano con
`python3 publicar_x.py --revisar`.
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("publicar_x", RAIZ / "publicar_x.py")
px = importlib.util.module_from_spec(spec)
spec.loader.exec_module(px)

fallos = 0


def check(nombre, condicion, detalle=""):
    global fallos
    if condicion:
        print("  OK   " + nombre)
    else:
        fallos += 1
        print("  FALLO " + nombre + " -> " + str(detalle))


# ── Ofertas de ejemplo, con la forma que tienen en data/*.json ──
OFERTA = {
    "id": 10617,
    "date": "2026-10-19T16:00:48+00:00",
    "title": "BOLSO BANDOLERA DKNY BRYANT AVE \U0001f5a4\u2728",
    "price": "39.01 \u20ac",
    "old_price": "99.00 \u20ac",
    "discount": "-61%",
    "amazon_url": "https://www.amazon.es/dp/B0F9B3BKZ4?tag=gangas029-21",
    "image": "https://cdn4.telesco.pe/file/AB.jpg",
    "categoria": "ropa-y-calzado",
    "description": ("\u00a1Elegancia a precio incre\u00edble! Bolso DKNY negro con logotipo, "
                    "dise\u00f1o moderno y bandolera ajustable. \u00a1Aprovecha esta ofertaza! "
                    "\U0001f5a4\u2728 Canal: https://t.me/GangasOfertasChollos"),
    "brand": "BOLSO BANDOLERA",
    "gtin": "",
    "mpn": "",
}

print("\n== 1. Longitud del post: las reglas de X ==")
check("texto normal cuenta 1 por caracter", px.longitud_post("hola") == 4, px.longitud_post("hola"))
check("la URL cuenta como 23", px.longitud_post("https://a.com/xyz") == 23, px.longitud_post("https://a.com/xyz"))
check("URL y texto se suman", px.longitud_post("a https://a.com/b") == 2 + 23, px.longitud_post("a https://a.com/b"))
check("el emoji cuenta como 2", px.longitud_post("\U0001f5a4") == 2, px.longitud_post("\U0001f5a4"))
check("la letra acentuada cuenta como 1", px.longitud_post("\u00e1") == 1, px.longitud_post("\u00e1"))
check("el euro cuenta como 1", px.longitud_post("39,01 \u20ac") == 7, px.longitud_post("39,01 \u20ac"))
check("el limite es 280", px.LIMITE_POST == 280, px.LIMITE_POST)

print("\n== 2. Precio: el JSON lo guarda con punto, X en español con coma ==")
check("39.01 -> 39,01", px._precio_es("39.01 \u20ac") == "39,01 \u20ac", px._precio_es("39.01 \u20ac"))
check("los miles se separan con punto", px._precio_es("1299.00 \u20ac") == "1.299,00 \u20ac",
      px._precio_es("1299.00 \u20ac"))
check("un precio de dos cifras no cambia", px._precio_es("16.17 \u20ac") == "16,17 \u20ac",
      px._precio_es("16.17 \u20ac"))
check("sin precio devuelve vacio", px._precio_es("") == "", px._precio_es(""))

print("\n== 3. La descripcion: se quita el final de Telegram ==")
limpia = px._limpiar_descripcion(OFERTA["description"])
check("no deja la URL del canal", "t.me" not in limpia, limpia)
check("no deja la palabra Canal", "Canal" not in limpia, limpia)
check("conserva el texto de verdad", limpia.startswith("\u00a1Elegancia"), limpia)
check("un aviso de publicidad no cuenta como descripcion",
      px._limpiar_descripcion("Publicidad/Enlace afiliado El precio puede cambiar.") == "",
      px._limpiar_descripcion("Publicidad/Enlace afiliado El precio puede cambiar."))
check("sin descripcion devuelve vacio", px._limpiar_descripcion("") == "", px._limpiar_descripcion(""))

print("\n== 4. El post que se arma ==")
texto = px.componer_post(OFERTA)
print("\n" + texto + "\n")
check("cabe en 280", px.longitud_post(texto) <= 280, px.longitud_post(texto))
check("lleva el titulo", "DKNY" in texto, texto)
check("lleva el precio con coma", "39,01 \u20ac" in texto, texto)
check("lleva el precio anterior", "99,00 \u20ac" in texto, texto)
check("lleva el descuento", "-61%" in texto, texto)
check("lleva el enlace de afiliado", "gangas029-21" in texto, texto)
check("lleva la descripcion", "Elegancia" in texto, texto)
check("no arrastra el final de Telegram", "t.me" not in texto, texto)
check("lleva hashtags", "#Amazon" in texto, texto)
check("el hashtag de la categoria", "#Moda" in texto, texto)

print("\n== 5. Titulos largos: se recortan, no se desbordan ==")
larga = dict(OFERTA)
larga["title"] = "COLCHON DE ESPUMA 135 CM CON ALMOHADA EXTRAIBLE Y TEJIDO TRANPIRABLE " \
                 "CERTIFICADO OEKO TEX PARA USO DIARIO EN HABITACIONES DOBLES " \
                 "GRIS CLARO CON CARCASA LAVABLE A MAQUINA Y GUARDA PROTECTOR DE 40 CM"
larga["description"] = "Colchon viscoelastico de espuma HR de alta densidad con nucleo de " \
                       "coco y fibra termoreguladora, transpirable, indeformable y con " \
                       "sistema de ventilacion lateral para un descanso profundo y silencioso " \
                       "durante toda la noche, con fundatxt suave y lavable a 40 grados."
texto_largo = px.componer_post(larga)
check("el post largo tambien cabe", px.longitud_post(texto_largo) <= 280, px.longitud_post(texto_largo))
check("no se pierde el enlace", "gangas029-21" in texto_largo, texto_largo)
check("no se pierden los hashtags", "#Amazon" in texto_largo, texto_largo)

print("\n== 6. Recortar no parte emojis por la mitad ==")
recortado = px._recortar("\U0001f5a4\U0001f5a4\U0001f5a4 texto", 4)
check("respeta el limite", px.longitud_post(recortado) <= 4, px.longitud_post(recortado))
check("no deja emojis rotos", "\ufffd" not in recortado, recortado)

print("\n== 7. Ofertas sin precio o sin descripcion ==")
pobre = dict(OFERTA)
pobre["price"] = ""
pobre["old_price"] = ""
pobre["discount"] = ""
pobre["description"] = ""
texto_pobre = px.componer_post(pobre)
check("se arma igualmente", px.longitud_post(texto_pobre) <= 280, texto_pobre)
check("sin la linea de precios", "\U0001f4b8" not in texto_pobre, texto_pobre)
check("con el enlace", "gangas029-21" in texto_pobre, texto_pobre)

print("\n== 8. El catalogo de verdad: todas las ofertas caben ==")
catalogo = RAIZ / "data" / "general.json"
if catalogo.exists():
    ofertas = json.loads(catalogo.read_text(encoding="utf-8"))
    desbordadas = [o for o in ofertas if px.longitud_post(px.componer_post(o)) > 280]
    check(f"las {len(ofertas)} ofertas de general.json caben en 280", not desbordadas, desbordadas[:2])
else:
    print("  (sin data/general.json, se salta)")

print("\n== 9. Estado: no se publica dos veces la misma oferta ==")
tmp = Path(tempfile.mkdtemp())
estado_original = px.ESTADO_PATH
px.ESTADO_PATH = tmp / "estado_x.json"
try:
    estado = px.leer_estado()
    check("sin archivo devuelve estado vacio", estado.get("publicados") == {}, estado)
    estado["publicados"]["10617"] = {"tweet_id": "123", "fecha": "2026-10-19"}
    px.guardar_estado(estado)
    releido = px.leer_estado()
    check("guarda y vuelve a leer", "10617" in releido["publicados"], releido)
    check("guarda el id del post", releido["publicados"]["10617"]["tweet_id"] == "123", releido)
finally:
    px.ESTADO_PATH = estado_original
    shutil.rmtree(tmp, ignore_errors=True)

print("\n== 10. Las ofertas se leen de mas reciente a mas antigua ==")
tmp = Path(tempfile.mkdtemp())
archivo = tmp / "prueba.json"
archivo.write_text(json.dumps([
    {"id": 1, "title": "a", "amazon_url": "u"},
    {"id": 9, "title": "b", "amazon_url": "u"},
    {"id": 5, "title": "c", "amazon_url": "u"},
]), encoding="utf-8")
try:
    leidas = px.cargar_ofertas(archivo=str(archivo))
    check("la mas reciente primero", [o["id"] for o in leidas] == [9, 5, 1], [o["id"] for o in leidas])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("\n" + "=" * 56)
print("TODO CORRECTO" if fallos == 0 else f"{fallos} FALLOS")
sys.exit(1 if fallos else 0)

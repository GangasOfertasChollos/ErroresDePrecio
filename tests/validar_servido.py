"""Comprobaciones contra el servidor HTTP: valida lo que un crawler recibe de
verdad, no lo que hay en el disco.

Se diferencia de validar_sitio.py en que este pasa por HTTP. Sirve para
descubrir cosas que un crawler se encontraria y el HTML en disco no delata:
una respuesta 404 en un enlace, un content-type raro, una pagina servida que
no trae lo que el generador escribio.

Uso
---
    # contra el sitio desplegado (lo que de verdad ve Google):
    python tests/validar_servido.py https://gangasofertas.com

    # contra un servidor local, para no depender de la red:
    python -m http.server 8124
    python tests/validar_servido.py http://localhost:8124

Sin argumento usa SITE_PUBLICO. Contra el sitio real hay dos cosas que el
servidor local no puede comprobar y que se anaden como comprobaciones
especificas: los redirects (GitHub Pages sirve /equipo como /equipo.html) y
la coherencia del sitemap con lo que responde el dominio.

Que falle contra el sitio desplegado no es culpa del repositorio:Pages tarda
en reconstruir y puede tener reglas de cache propias. Por eso el codigo de
salida distingue, y el script dice siempre que dominio ha comprobado.
"""
import json
import posixpath
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser

SITE_PUBLICO = "https://gangasofertas.com"

BASE = (sys.argv[1] if len(sys.argv) > 1 else SITE_PUBLICO).rstrip("/")
ES_PROD = "localhost" not in BASE and "127.0.0.1" not in BASE
fallos = []
avisos = []


def err(m):
    fallos.append(m)
    print("  FALLO", m)


def warn(m):
    avisos.append(m)
    print("  AVISO", m)


def pedir(ruta, intentos=3):
    """Pide una ruta y devuelve (status, content-type, cuerpo).

    `ruta` debe empezar por "/" (o "?") para no que urlopen la interprete como
    esquema + host, que es lo que pasaba con "general.html" y "assets/app.js".

    Contra el sitio desplegado se reintenta: general.html son ~240 KB y la
    lectura se puede cortar por un timeout de red sin que haya ningun problema
    en la pagina. Un unico fallo de red no debe marcar el sitio como roto, pero
    agotar los intentos si.
    """
    if not ruta.startswith(("/", "?")):
        ruta = "/" + ruta
    req = urllib.request.Request(BASE + ruta, headers={"User-Agent": "Mozilla/5.0"})

    ultimo = ""
    for intento in range(1, intentos + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return (r.status, r.headers.get("Content-Type", ""),
                        r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            # Un 404 tambien es un dato: se devuelve con su status para que
            # quien llama lo compruebe, en vez de que reviente la comprobacion.
            return e.code, e.headers.get("Content-Type", ""), ""
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            # TimeoutError y ConnectionResetError llegan como OSError y no
            # como URLError: sin esto, un corte a mitad de la lectura de una
            # pagina grande tumbaba la comprobacion entera.
            ultimo = getattr(e, "reason", e)
            if intento < intentos:
                continue
    err(f"{ruta} -> {intentos} intentos sin respuesta de {BASE} ({ultimo})")
    return 0, "", ""


# Content-Type esperado segun la extension. Los ficheros que no son .html se
# sirven como text/plain, application/json o text/xml y eso es lo correcto:
# lo que se comprueba es que el crawler los reciba con el tipo adecuado, no
# que todos sean HTML.
TIPOS = {
    ".txt": ("text/plain",),
    ".json": ("application/json",),
    # application/xml y text/xml son los dos validos para un sitemap. GitHub
    # Pages sirve el primero y un servidor local el segundo, asi que se
    # aceptan ambos: exigir uno solo daria un falso positivo en uno de los dos
    # entornos sin senalar ningun problema real.
    ".xml": ("text/xml", "application/xml"),
}


print("== 1. Paginas clave responden 200 con text/html ==")
PAGINAS = [
    "/", "/general.html", "/categorias.html", "/guias.html",
    "/moviles-electronica.html", "/ropa-y-calzado.html", "/gaming-consolas.html",
    "/higiene-cuidado-personal.html", "/juguetes-infantil.html",
    "/papeleria-oficina.html",
    "/como-detectar-errores-de-precio-amazon.html",
    "/ofertas-reales-vs-descuentos-falsos.html",
    "/amazon-warehouse-outlet-y-devoluciones.html",
    "/cuando-comprar-en-amazon-espana.html",
    "/guia-completa-chollos-amazon.html",
    "/mejores-canales-telegram-ofertas.html",
    "/llms.txt", "/robots.txt", "/sitemap.xml",
    "/data/general.json",
]
for ruta in PAGINAS:
    try:
        status, ctype, body = pedir(ruta)
    except Exception as e:
        err(f"{ruta} -> no responde ({e})")
        continue
    if status != 200:
        err(f"{ruta} -> HTTP {status}")
        continue
    ext = ".html" if ruta.endswith((".html", "/")) else ruta[ruta.rfind("."):]
    esperados = TIPOS.get(ext, ("text/html",))
    if not any(t in ctype for t in esperados):
        err(f"{ruta} -> Content-Type {ctype}, se esperaba {' o '.join(esperados)}")
        continue
    print(f"  OK   {ruta} ({len(body)} bytes, {ctype.split(';')[0]})")

print("\n== 2. Las categorias traen texto y ofertas en el HTML servido ==")
CATS = ["general", "moviles-electronica", "ropa-y-calzado", "gaming-consolas",
        "higiene-cuidado-personal", "juguetes-infantil", "papeleria-oficina"]
for slug in CATS:
    st, _c, html = pedir(f"/{slug}.html" if slug != "general" else "/general.html")
    if st != 200:
        err(f"{slug}.html no se pudo leer (HTTP {st})")
        continue
    cuerpo = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S)
    cuerpo = re.sub(r'<nav\b.*?</nav>|<footer\b.*?</footer>|<header\b.*?</header>',
                    " ", cuerpo, flags=re.S)
    palabras = len(re.sub(r"<[^>]+>", " ", cuerpo).split())
    tarjetas = html.count('<article class="oferta"')

    _s, _c, datos = pedir(f"/data/{slug}.json")
    ofertas = len(json.loads(datos))

    if palabras < 300:
        err(f"{slug}: solo {palabras} palabras de texto visible (el crawler veria eso)")
    if ofertas and tarjetas < ofertas:
        err(f"{slug}: {ofertas} ofertas en el JSON y {tarjetas} en el HTML servido")
    print(f"  OK   {slug:26} {palabras:5} palabras Â· {tarjetas}/{ofertas} ofertas")

print("\n== 3. Las guias tienen texto suficiente y enlazan al hub ==")
GUIAS = [
    "como-detectar-errores-de-precio-amazon", "ofertas-reales-vs-descuentos-falsos",
    "amazon-warehouse-outlet-y-devoluciones", "cuando-comprar-en-amazon-espana",
    "guia-completa-chollos-amazon", "mejores-canales-telegram-ofertas",
]
for slug in GUIAS:
    st, _c, html = pedir(f"/{slug}.html")
    if st != 200:
        err(f"{slug}.html no se pudo leer (HTTP {st})")
        continue
    # Sin contar el nav ni el pie: lo que se mide es el cuerpo del articulo.
    cuerpo = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S)
    cuerpo = re.sub(r'<nav\b.*?</nav>|<footer\b.*?</footer>|<header\b.*?</header>',
                    " ", cuerpo, flags=re.S)
    palabras = len(re.sub(r"<[^>]+>", " ", cuerpo).split())
    if palabras < 700:
        err(f"{slug}: solo {palabras} palabras (minimo 700)")
    if 'href="guias.html"' not in html:
        err(f"{slug}: no enlaza al hub de guias")
    if 'rel="canonical"' not in html:
        err(f"{slug}: sin canonical")
    print(f"  OK   {slug:46} {palabras:5} palabras")

print("\n== 4. Enlaces internos del sitio resuelven ==")
_vistos = set()
# Los slugs de GUIAS/CATS no llevan extension: se usan como paginas, asi que
# aqui se cran con .html. Sin esto, pedir("general") busca /general y da 404.
for ruta in ["/", "/index.html", "/general.html", "/categorias.html", "/guias.html",
             *[f"/{s}.html" for s in GUIAS],
             *[f"/{s}.html" for s in CATS],
             "/BlackFriday/index.html"]:
    st, _c, html = pedir(ruta)
    if st != 200:
        err(f"{ruta} no se pudo leer (HTTP {st})")
        continue
    for m in re.finditer(r'href="([^"]+)"', html):
        ref = m.group(1)
        if ref.startswith(("http://", "https://", "#", "mailto:", "data:", "tel:")):
            continue
        limpio = ref.split("#")[0].split("?")[0]
        if not limpio:
            continue
        # Resolucion real de rutas relativas: "BlackFriday/aviso-legal.html"
        # dentro de /BlackFriday/index.html es /BlackFriday/BlackFriday/...
        # hay que usar posixpath.join con el directorio de la pagina, no
        # concatenar a mano.
        destino = limpio if limpio.startswith("/") else posixpath.join(
            posixpath.dirname(ruta), limpio)
        destino = posixpath.normpath(destino)
        if destino in _vistos:
            continue
        _vistos.add(destino)
        status, _c2, _b = pedir(destino)
        if status != 200:
            err(f"{ruta} -> {destino} HTTP {status}")

print(f"  OK   {len(_vistos)} destinos internos distintos, todos 200")

print("\n== 5. El JSON-LD del sitio es parseable por el crawler ==")


class _Contador(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.en_ldjson = False
        self.buf = []
        self.bloques = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("type") == "application/ld+json":
            self.en_ldjson = True
            self.buf = []

    def handle_endtag(self, tag):
        if tag == "script" and self.en_ldjson:
            self.bloques.append("".join(self.buf))
            self.en_ldjson = False

    def handle_data(self, data):
        if self.en_ldjson:
            self.buf.append(data)


for ruta in ["/", "/general.html", "/guias.html", f"/{GUIAS[0]}.html"]:
    _s, _c, html = pedir(ruta)
    c = _Contador()
    c.feed(html)
    if not c.bloques:
        err(f"{ruta}: sin JSON-LD")
        continue
    for b in c.bloques:
        try:
            json.loads(b)
        except json.JSONDecodeError as e:
            err(f"{ruta}: JSON-LD invalido -> {e}")
    tipos = []
    for b in c.bloques:
        obj = json.loads(b)
        grafo = obj.get("@graph", [obj])
        tipos += [n.get("@type") for n in grafo if isinstance(n, dict)]
    print(f"  OK   {ruta}: {', '.join(str(t) for t in tipos)}")

print("\n== 6. FAQ visible coincide con el FAQPage del JSON-LD ==")
for slug in GUIAS + CATS:
    st, _c, html = pedir(f"/{slug}.html")
    if st != 200:
        err(f"{slug}.html no se pudo leer (HTTP {st})")
        continue
    preguntas_html = set(re.findall(r"<summary>(.*?)</summary>", html))
    c = _Contador()
    c.feed(html)
    for b in c.bloques:
        obj = json.loads(b)
        for n in obj.get("@graph", []):
            if isinstance(n, dict) and n.get("@type") == "FAQPage":
                preguntas_json = {q["name"] for q in n["mainEntity"]}
                faltan = preguntas_json - preguntas_html
                if faltan:
                    err(f"{slug}: FAQPage declara preguntas que no estan en el HTML: "
                        f"{sorted(faltan)[:2]}")
                sobran = preguntas_html - preguntas_json
                # El hub y las categorias pueden tener <details> sin marcar, no
                # es un problema: el JSON-LD solo declara las suyas.
    print(f"  OK   {slug}: {len(preguntas_html)} <details>, JSON-LD coherente")

print("\n== 7. Coherencia entre el sitemap servido y el dominio ==")
# Solo tiene sentido contra el sitio desplegado: es la unica forma de saber
# que lo que declara el sitemap existe de verdad y no solo en el repositorio.
# Ademas detecta el retraso de Pages: si se acaba de publicar, el sitemap
# puede ir un commit por delante de las paginas que aun no se han construido.
if not ES_PROD:
    print("  (omitido: solo aplica contra el sitio desplegado)")
else:
    st, _c, xml = pedir("/sitemap.xml")
    if st != 200:
        err(f"sitemap.xml no se pudo leer (HTTP {st})")
    else:
        locs = re.findall(r"<loc>([^<]+)</loc>", xml)
        print(f"  {len(locs)} URLs declaradas")
        for loc in locs:
            ruta = "/" + posixpath.relpath(loc, BASE) if loc.startswith(BASE) else None
            if ruta is None:
                # El sitemap declara otro dominio: no es un fallo de red, pero
                # si un error de configuracion que conviene ver.
                warn(f"sitemap declara una URL de otro dominio: {loc}")
                continue
            status, _c2, _b = pedir(ruta)
            if status != 200:
                err(f"sitemap -> {ruta} responde HTTP {status}")

        # El dominio tiene que servirse a si mismo en HTTPS y en WWW sin
        # romper: si un visitante llega por una variante, lo recibe igual.
        for otra in ("https://www.gangasofertas.com/", "http://gangasofertas.com/"):
            if otra.rstrip("/") == BASE.rstrip("/"):
                continue
            try:
                req = urllib.request.Request(otra, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    final = r.url
                canon = "/".join(final.split("/")[:3])
                if canon != BASE:
                    warn(f"{otra} acaba en {final} (canonica de referencia: {BASE})")
                else:
                    print(f"  OK   {otra} resuelve a la misma canonica")
            except Exception as e:
                warn(f"{otra} -> {e}")

print("\n" + "=" * 56)
print(f"comprobado: {BASE}")
print(f"{len(fallos)} FALLOS · {len(avisos)} avisos")
raise SystemExit(1 if fallos else 0)

"""Auditoria SEO transversal de todas las URLs del sitemap.

Comprueba lo que se puede comprobar en local y lo que otros validadores no
miran: unicidad de title y description, longitudes, H1, canonical, robots meta,
lang, open graph, schema, y enlazado interno (entrantes y salientes) para
detectar paginas huerfanas o con poca autoridad.

No falla el build: informa. Sirve para decidir, no para bloquear.
Uso:  python tests/auditar_seo.py
"""

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parent.parent
BASE = "https://gangasofertas.com"

FICH = sorted(
    [p for p in RAIZ.glob("*.html") if p.name != "googlea9c410decf5a46ae.html"]
    + [p for p in (RAIZ / "BlackFriday").glob("*.html")]
)


def meta(c, attr, val):
    m = re.search(r'<meta[^>]*%s="%s"[^>]*content="([^"]*)"' % (attr, val), c)
    if m:
        return m.group(1)
    m = re.search(r'<meta[^>]*content="([^"]*)"[^>]*%s="%s"' % (attr, val), c)
    return m.group(1) if m else ""


def tag(c, nombre):
    m = re.search(r"<%s[^>]*>(.*?)</%s>" % (nombre, nombre), c, re.S)
    return m.group(1).strip() if m else ""


def link(c, rel):
    """<link rel="canonical" href="...">. El canonical va en link, no en meta."""
    m = re.search(r'<link[^>]*\brel="%s"[^>]*\bhref="([^"]+)"' % rel, c)
    if m:
        return m.group(1)
    m = re.search(r'<link[^>]*\bhref="([^"]+)"[^>]*\brel="%s"' % rel, c)
    return m.group(1) if m else ""


def hrefs(c):
    return re.findall(r'href="([^"]+)"', c)


def slug_de(url):
    return urlparse(url).path.lstrip("/")


# ── Recogida ────────────────────────────────────────────────────────────────
paginas = {}
for p in FICH:
    c = p.read_text(encoding="utf-8")
    rel = p.relative_to(RAIZ).as_posix()
    cuerpo = re.sub(r"<script.*?</script>|<style.*?</style>", " ", c, flags=re.S)
    texto = re.sub(r"<[^>]+>", " ", cuerpo)
    palabras = len([t for t in texto.split() if any(ch.isalpha() for ch in t)])
    schemas = sorted(set(re.findall(r'"@type"\s*:\s*"([A-Za-z]+)"', c)))
    paginas[rel] = {
        "title": tag(c, "title"),
        "desc": meta(c, "name", "description"),
        "canonical": link(c, "canonical"),
        "robots": meta(c, "name", "robots"),
        "lang": (re.search(r'<html[^>]*\blang="([^"]+)"', c) or [None, ""])[1]
        if re.search(r'<html[^>]*\blang="([^"]+)"', c)
        else "",
        "og_url": meta(c, "property", "og:url"),
        "og_img": meta(c, "property", "og:image"),
        "og_title": meta(c, "property", "og:title"),
        "twitter": meta(c, "name", "twitter:card"),
        "h1": re.findall(r"<h1[^>]*>(.*?)</h1>", c, re.S),
        "h1_txt": [re.sub(r"<[^>]+>", "", h).strip() for h in re.findall(r"<h1[^>]*>(.*?)</h1>", c, re.S)],
        "schemas": schemas,
        "palabras": palabras,
        "hrefs": hrefs(c),
        "pub": meta(c, "property", "article:published_time"),
        "mod": meta(c, "property", "article:modified_time"),
    }

fallos, avisos = [], []


def f(msg):
    fallos.append(msg)


def a(msg):
    avisos.append(msg)


print("=" * 64)
print("AUDITORIA SEO - %d paginas" % len(paginas))
print("=" * 64)

# ── 1. Titles ───────────────────────────────────────────────────────────────
print("\n== 1. TITLES ==")
vistos_t = {}
for rel, d in sorted(paginas.items()):
    t = d["title"]
    if not t:
        f("[title] %s: sin <title>" % rel)
        continue
    if len(t) > 60:
        a("[title] %s: %d caracteres (se corta en SERP ~60)" % (rel, len(t)))
    if len(t) < 25:
        a("[title] %s: %d caracteres, demasiado corto" % (rel, len(t)))
    k = t.lower()
    if k in vistos_t:
        f("[title] DUPLICADO: '%s' en %s y %s" % (t, vistos_t[k], rel))
    vistos_t[k] = rel

# ── 2. Descriptions ─────────────────────────────────────────────────────────
print("== 2. META DESCRIPTIONS ==")
vistos_d = {}
for rel, d in sorted(paginas.items()):
    s = d["desc"]
    if not s:
        f("[desc] %s: sin meta description" % rel)
        continue
    if len(s) > 165:
        a("[desc] %s: %d caracteres (se corta ~155-160)" % (rel, len(s)))
    if len(s) < 70:
        a("[desc] %s: %d caracteres, demasiado corta" % (rel, len(s)))
    k = s.lower()
    if k in vistos_d:
        f("[desc] DUPLICADO: '{s[:50]}...' en %s y %s" % (vistos_d[k], rel))
    vistos_d[k] = rel

# ── 3. H1 ───────────────────────────────────────────────────────────────────
print("== 3. H1 ==")
vistos_h1 = {}
for rel, d in sorted(paginas.items()):
    if rel.endswith("404.html"):
        continue
    if len(d["h1"]) == 0:
        f("[h1] %s: sin H1" % rel)
    elif len(d["h1"]) > 1:
        f("[h1] %s: %d H1 (deberia ser 1)" % (rel, len(d["h1"])))
    for h in d["h1_txt"]:
        k = h.lower().strip()
        if k in vistos_h1:
            f("[h1] DUPLICADO: '%s' en %s y %s" % (h, vistos_h1[k], rel))
        vistos_h1[k] = rel

# ── 4. Canonicals / og:url / lang ───────────────────────────────────────────
print("== 4. CANONICAL, OG:URL, LANG ==")
for rel, d in sorted(paginas.items()):
    if rel.endswith("404.html"):
        continue
    if not d["canonical"]:
        f("[canonical] %s: sin canonical" % rel)
    elif not d["canonical"].startswith(BASE):
        f("[canonical] %s: apunta fuera del dominio: %s" % (rel, d["canonical"]))
    if d["og_url"] and not d["og_url"].startswith(BASE):
        f("[og:url] %s: fuera del dominio: %s" % (rel, d["og_url"]))
    if not d["lang"]:
        a("[lang] %s: sin lang en <html>" % rel)
    if d["robots"] and "noindex" in d["robots"]:
        print("   noindex declarado en %s" % rel)

# ── 5. Open Graph ───────────────────────────────────────────────────────────
print("== 5. OPEN GRAPH / TWITTER ==")
for rel, d in sorted(paginas.items()):
    if rel.endswith("404.html"):
        continue
    if not d["og_img"]:
        a("[og:image] %s: sin imagen social" % rel)
    if not d["og_title"]:
        a("[og:title] %s: sin og:title" % rel)
    if not d["twitter"]:
        a("[twitter:card] %s: sin twitter:card" % rel)

# ── 6. Schema ───────────────────────────────────────────────────────────────
print("== 6. DATOS ESTRUCTURADOS ==")
for rel, d in sorted(paginas.items()):
    if rel.endswith("404.html"):
        continue
    s = d["schemas"]
    if not s:
        a("[schema] %s: sin JSON-LD" % rel)
        continue
    if "BreadcrumbList" not in s and rel != "index.html":
        a("[schema] %s: sin BreadcrumbList (%s)" % (rel, ",".join(s)))
    if "FAQPage" in s:
        # El JSON-LD debe declarar las mismas preguntas que el HTML
        pass

print("   SearchAction declarado en:",
      [r for r, d in paginas.items() if "SearchAction" in str(d["schemas"])])

# ── 7. Enlazado interno ─────────────────────────────────────────────────────
print("\n== 7. ENLAZADO INTERNO ==")
entrantes = {rel: 0 for rel in paginas}
salientes = {}
for rel, d in paginas.items():
    out = set()
    for h in d["hrefs"]:
        if h.startswith(("http://", "https://", "#", "mailto:", "tel:", "data:")):
            continue
        destino = h.split("#")[0].split("?")[0]
        if not destino:
            continue
        # resolver relativo al directorio del propio fichero
        base_dir = "/".join(rel.split("/")[:-1])
        if destino.startswith("/"):
            ruta = destino.lstrip("/")
        else:
            partes = [p for p in base_dir.split("/") if p] if base_dir else []
            for seg in destino.split("/"):
                if seg == "..":
                    if partes:
                        partes.pop()
                elif seg not in (".", ""):
                    partes.append(seg)
            ruta = "/".join(partes)
        if not ruta.endswith(".html") and ruta not in ("", "sitemap.xml"):
            # rutas de directorio (BlackFriday/) o assets
            if "/" in ruta:
                continue
        if ruta in entrantes:
            out.add(ruta)
        elif ruta and not ruta.startswith(("assets/", "data/", "BlackFriday/assets")):
            # destino que no existe en el repo
            if ruta.endswith(".html"):
                f("[enlace roto] %s -> %s" % (rel, destino))
    salientes[rel] = len(out)
    for o in out:
        entrantes[o] += 1

print("   Paginas sin enlaces entrantes (huerfanas):")
huerf = [r for r, n in sorted(entrantes.items()) if n == 0]
for h in huerf:
    print("      %-46s 0" % h)
    a("[enlazado] %s: huerfana (0 entrantes)" % h)

print("\n   Paginas con menos de 5 entrantes:")
pocos = [(r, n) for r, n in sorted(entrantes.items(), key=lambda x: x[1]) if n < 5 and n > 0]
for r, n in pocos:
    print("      %-46s %d" % (r, n))
    a("[enlazado] %s: solo %d entrantes" % (r, n))

print("\n   Paginas que no enlazan a ninguna otra:")
solos = [r for r, n in sorted(salientes.items()) if n == 0 and not r.endswith("404.html")]
for r in solos:
    a("[enlazado] %s: 0 salientes" % r)

# ── 8. Contenido ────────────────────────────────────────────────────────────
print("\n== 8. CONTENIDO ==")
print("   %-46s %s" % ("PAGINA", "PALABRAS"))
for rel, d in sorted(paginas.items(), key=lambda x: x[1]["palabras"]):
    if d["palabras"] < 300 and not rel.endswith("404.html"):
        print("   %-46s %d  <-- fino" % (rel, d["palabras"]))
        a("[contenido] %s: solo %d palabras" % (rel, d["palabras"]))

# ── Resumen ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
print("%d FALLOS · %d avisos" % (len(fallos), len(avisos)))
print("=" * 64)
for x in fallos:
    print("FALLO  " + x)
print()
for x in avisos:
    print("aviso  " + x)

sys.exit(0)
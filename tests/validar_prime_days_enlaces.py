"""Comprueba enlaces y assets de una seccion en profundidad (validar_sitio.py
solo revisa los HTML de la raiz con RAIZ.glob, asi que no ve PrimeDays/).

Mismo criterio que el validador del repo: se resuelve cada referencia
relativa contra el directorio del propio HTML.
"""
import re
import sys
from pathlib import Path

# parent.parent porque el script vive en tests/, no en la raiz del repo.
RAIZ = Path(__file__).resolve().parent.parent
SECCION = RAIZ / "PrimeDays"

fallos, avisos = [], []

# 1. Enlaces internos y assets.
for html in sorted(SECCION.glob("*.html")):
    txt = html.read_text(encoding="utf-8")
    for m in re.finditer(r'(?:href|src)="([^"]+)"', txt):
        ref = m.group(1)
        if ref.startswith(("http://", "https://", "#", "mailto:", "data:")):
            continue
        limpio = ref.split("#")[0].split("?")[0]
        if not limpio:
            continue
        destino = RAIZ / limpio.lstrip("/") if limpio.startswith("/") else html.parent / limpio
        if not destino.exists():
            fallos.append(f"{html.name} -> {ref} (no existe)")

# 2. JSON-LD valido y con los tipos esperados.
import json
for html in sorted(SECCION.glob("*.html")):
    bloques = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>',
        html.read_text(encoding="utf-8"), re.S)
    if not bloques:
        fallos.append(f"{html.name}: sin JSON-LD")
        continue
    for b in bloques:
        try:
            obj = json.loads(b)
        except json.JSONDecodeError as e:
            fallos.append(f"{html.name}: JSON-LD invalido -> {e}")
            continue
        tipos = [n.get("@type") for n in obj.get("@graph", [])]
        print(f"  OK   {html.name}: {', '.join(str(t) for t in tipos)}")
        if "BreadcrumbList" not in tipos:
            fallos.append(f"{html.name}: el grafo no lleva BreadcrumbList")

# 3. FAQ visible == FAQ del schema. Si divergen, el rich result muestra
#    preguntas que no estan en la pagina, que es penalizado.
for html in sorted(SECCION.glob("*.html")):
    txt = html.read_text(encoding="utf-8")
    m = re.search(r'"@type":\s*"FAQPage".*?"mainEntity":\s*\[(.*?)\n\s*\]', txt, re.S)
    if not m:
        continue
    preguntas_schema = re.findall(r'"name":\s*"([^"]+)"', m.group(1))
    # Solo cuenta las preguntas, no los "text" de las respuestas.
    preguntas_html = re.findall(r"<summary>(.+?)</summary>", txt)
    def limpia(s):
        return re.sub(r"<[^>]+>", "", s).strip()
    vis = [limpia(p) for p in preguntas_html]
    # El schema puede traer mas preguntas que la pagina muestra en la parte
    # visible: en la portada solo se enseñan 4 de las 8. Se avisa, no falla.
    if len(vis) != len(preguntas_schema):
        avisos.append(
            f"{html.name}: {len(vis)} <summary> visibles frente a "
            f"{len(preguntas_schema)} en FAQPage (puede ser un bloque resumido)")
    for p in preguntas_schema:
        if limpia(p) not in vis:
            fallos.append(f"{html.name}: pregunta del schema no visible -> {p}")

# 4. Estructura minima.
for html in sorted(SECCION.glob("*.html")):
    txt = html.read_text(encoding="utf-8")
    h1 = txt.count("<h1>")
    if h1 != 1:
        fallos.append(f"{html.name}: {h1} H1")
    for tag, attr in [("title", None), ("meta", 'name="description"'),
                      ("link", 'rel="canonical"')]:
        if attr and attr not in txt:
            fallos.append(f"{html.name}: falta {attr}")
    if "<title>" not in txt:
        fallos.append(f"{html.name}: falta <title>")
    if len(re.findall(r'<h1>(.*?)</h1>', txt)) and "<main" not in txt:
        avisos.append(f"{html.name}: el H1 no esta dentro de <main>")

# 5. Enlaces al canal con los atributos de monetizacion correctos.
for html in sorted(SECCION.glob("*.html")):
    txt = html.read_text(encoding="utf-8")
    enlaces = re.findall(r'<a[^>]+href="https://t\.me/GangasOfertasChollos"[^>]*>', txt)
    if not enlaces:
        fallos.append(f"{html.name}: sin enlaces al canal")
    for e in enlaces:
        if 'rel="sponsored nofollow noopener"' not in e:
            fallos.append(f"{html.name}: enlace al canal sin sponsored/nofollow -> {e[:90]}")

print()
for f in fallos:
    print("  FALLO", f)
for a in avisos:
    print("  AVISO", a)
print("=" * 56)
print(f"{len(fallos)} FALLOS · {len(avisos)} avisos")
sys.exit(1 if fallos else 0)
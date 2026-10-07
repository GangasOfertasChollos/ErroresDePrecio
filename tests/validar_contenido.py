"""Comprueba la extension del copy de las categorias y el alto de las paginas.

No es un test de contenido (no puede decir si un texto es bueno), sino de
volumen: sirve para detectar que una categoria se ha quedado corta o que el
copy se ha truncado sin que nadie se dé cuenta.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
# El modulo vive en la raiz del repo, no en tests/.
sys.path.insert(0, str(RAIZ))

import contenido_categoria as cc  # noqa: E402

MIN_PALABRAS = 600
MAX_DESC = 160
MAX_TITULO = 65

fallos = []


def err(m):
    fallos.append(m)
    print("  FALLO", m)


print("== Extension del copy por categoria ==")
for slug, d in cc.CONTENIDO.items():
    for campo in ("titulo_seo", "descripcion", "h1", "intro", "secciones",
                  "como_elegir", "faq", "relacionados"):
        if campo not in d:
            err(f"{slug}: falta el campo {campo!r}")

    palabras = sum(len(p.split()) for p in d["intro"])
    palabras += sum(len(p.split()) for _, ps in d["secciones"] for p in ps)
    palabras += sum(len(p.split()) for _, p in d["como_elegir"])

    if palabras < MIN_PALABRAS:
        err(f"{slug}: solo {palabras} palabras de copy (minimo {MIN_PALABRAS})")
    if len(d["descripcion"]) > MAX_DESC:
        err(f"{slug}: meta description de {len(d['descripcion'])} caracteres "
            f"(maximo {MAX_DESC}) se va a recortar en Google")
    if len(d["titulo_seo"]) > MAX_TITULO:
        err(f"{slug}: title de {len(d['titulo_seo'])} caracteres "
            f"(maximo {MAX_TITULO})")
    if not d["faq"]:
        err(f"{slug}: sin FAQ, la pagina se queda sin FAQPage")
    for rel in d["relacionados"]:
        if rel not in cc.CONTENIDO:
            err(f"{slug}: 'relacionados' apunta a {rel!r}, que no existe")

    print(f"  OK   {slug:26} {palabras:4} palabras · {len(d['faq'])} FAQ")

print("\n== Los HTML generados contienen el copy ==")
for slug in cc.CONTENIDO:
    html = (RAIZ / f"{slug}.html")
    if not html.exists():
        err(f"{slug}.html no existe")
        continue
    txt = html.read_text(encoding="utf-8")
    d = cc.CONTENIDO[slug]
    # Una muestra por pagina: si aparece el H2 de la primera seccion y el
    # primer parrafo del intro, el bloque editorial se emitio entero.
    h2 = d["secciones"][0][0]
    frase = d["intro"][0][:60]
    if h2 not in txt:
        err(f"{slug}.html: no aparece el H2 {h2!r} (el copy no se emitio)")
    if frase not in txt:
        err(f"{slug}.html: no aparece el inicio del texto editorial")
    # Y las ofertas deben estar en el HTML servido, no solo en el JSON: era
    # justo el problema que motivó este módulo.
    import json
    ofertas = json.loads((RAIZ / "data" / f"{slug}.json").read_text(encoding="utf-8"))
    import re
    estaticas = len(re.findall(r'<article class="oferta"', txt))
    if ofertas and estaticas < len(ofertas):
        err(f"{slug}.html: {len(ofertas)} ofertas en el JSON pero solo "
            f"{estaticas} tarjetas en el HTML servido")
    print(f"  OK   {slug}.html: {estaticas} tarjetas servidas en el HTML")

if not fallos:
    print("\n  OK   todas las categorias tienen copy suficiente y servible")
raise SystemExit(1 if fallos else 0)
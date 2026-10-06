"""Comprueba que ninguna pagina de PrimeDays desborda horizontalmente en movil.

Sin navegador no se puede medir el layout, asi que aqui se comprueba lo que
causa el desbordamiento y que si se puede medir sin render: los anchos fijos
y los elementos que no se parten. Un <pre> o una palabra larga saltan el
contenedor y, en un movil, obligan a hacer scroll horizontal para leer el
titulo. Es el fallo de maquetacion mas comun en paginas de ofertas.
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SECCION = RAIZ / "PrimeDays"

fallos, avisos = [], []

# 1. Elements con ancho fijo que no caben en 360 px (el movil mas estrecho
#    que se mira, descontando el padding del wrap).
for html in sorted(SECCION.glob("*.html")):
    txt = html.read_text(encoding="utf-8")
    for m in re.finditer(r'(?:width|min-width)\s*:\s*(\d+)px', txt):
        ancho = int(m.group(1))
        if ancho > 360:
            fallos.append(f"{html.name}: ancho fijo de {ancho}px (no cabe en 360)")
    # min-width de las celdas de tabla viene del CSS, no del HTML: se omite.

# 2. Cadenas largas sin cortes: en un movil, un token de mas de ~28
#    caracteres que no este en un elemento con overflow lateral empuja la
#    pagina. Se miran las URLs y los identificadores largos.
for html in sorted(SECCION.glob("*.html")):
    txt = html.read_text(encoding="utf-8")
    plano = re.sub(r"<[^>]+>", " ", txt)
    plano = re.sub(r"\s+", " ", plano)
    for token in re.findall(r"[A-Za-z0-9_.\-]{29,}", plano):
        # Las URLs solo aparecen en atributos href/src: no se renderizan.
        if re.search(r"(https?://|/)[^\s]*" + re.escape(token), txt):
            continue
        avisos.append(f"{html.name}: token largo sin cortes -> {token[:50]}")

# 3. La hoja de estilos debe tratar el desborde de las tablas y del
#    countdown, que son los dos bloques anchos de la seccion.
css = (SECCION / "assets" / "css" / "style.css").read_text(encoding="utf-8")
for regla in (".table-scroll", "overflow-x", "flex-wrap", ".countdown"):
    if regla not in css:
        fallos.append(f"style.css: falta {regla}, y sin ella el movil desborda")

# 4. El <meta viewport> tiene que estar: sin el, el movil escala la pagina
#    y todo se ve en miniatura.
for html in sorted(SECCION.glob("*.html")):
    txt = html.read_text(encoding="utf-8")
    m = re.search(r'<meta name="viewport" content="([^"]+)"', txt)
    if not m:
        fallos.append(f"{html.name}: sin meta viewport")
    elif "width=device-width" not in m.group(1):
        fallos.append(f"{html.name}: viewport sin width=device-width -> {m.group(1)}")

print()
for f in sorted(set(fallos)):
    print("  FALLO", f)
for a in sorted(set(avisos)):
    print("  AVISO", a)
print("=" * 56)
print(f"{len(set(fallos))} FALLOS · {len(set(avisos))} avisos")
sys.exit(1 if fallos else 0)